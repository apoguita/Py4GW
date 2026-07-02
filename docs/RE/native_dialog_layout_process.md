# Native GW Dialog Construction & Layout — complete process (WASM-first RE)

Last updated 2026-07-01. WASM-first RE; EXE symbols renamed in `/Gw.exe (06-14)`. This is the authoritative
spec for building a native GW window whose controls **render, lay out, are clickable, and close cleanly**.

## THE ONE ROOT CAUSE

Py4GW creates control frames but **never runs the native two-phase layout pass**, and parents controls on
the window chrome instead of a real **content-page** frame. Every in-client symptom is this single gap:

| Symptom | Cause (all the same root) |
|---|---|
| checkbox crashes on `[X]` | control not under a content page → destroyed without `IUi::PopCloser` re-arm → dangling hot-item |
| radio/hyperlink buried behind window, unclickable | no content page → render at window layer (z-fight); no `FrameMouseEnable` → inert |
| edit blank | no `UiCtlBorderProc` sibling + no layout rect → collapses to 0×0 |
| slider width huge | no layout pass → keeps range-derived native width instead of a column-clamped rect |
| tabs layout wrong | no layout pass |
| button/progress/group OK | happen to work without layout |

## The native 3-level tree

```
WINDOW (chrome)            childId 0xd,  style 0x254000
  proc: IUi::UiCtlDlgBaseProc (0x00876610) + chained IUi::UiCtlDlgProc (0x00876880)
  └─ CONTENT PAGE          childId 0x2710..0x2718 (band, up to 9 stacked pages), style 0x80
       proc: IUi::UiCtlContentPageProc (0x00876740), userdata = window handle
       auto-fills the window client rect; made interactive by FrameMouseEnable(page,1,0)
       └─ CONTROLS          checkbox / slider / droplist / label / edit(+border) / list
            children of the TOP content page; NO rect at create — positioned by the layout pass
```

`childId` magnitude = stacking order within a parent (higher = later = on top). Only the top page is
mouse-enabled; lower pages paint but are inert.

## The two-phase creation+layout (what Py4GW is missing)

Dispatched by the dialog's `TCtlInstance<>::MsgProc` (ref: `CDlgOptGeneral::MsgProc` EXE 0x0088bba0):

1. **msg 9 (create):** alloc instance; construct a `CCtlLayout` (at instance+8); `CCtlLayout::SetFrameId(contentFrame)`;
   run `OnFrameCreate` → `FrameCreate` every control (no rect). Then `CCtlLayout::Clear()`; call virtual
   `OnCtlLayout(&layout)` to **build a SizeNode tree** (Row/Column/Child/Gap/End); then **`FrameScheduleSize(frame)`**
   + `FrameNativeSizeChanged(frame)` to request a size pass.
2. **msg 0x38 (size):** build a `Rect4f` from the size msg → `CCtlLayout::Size(&layout,&rect)` →
   `Ui::CLayout::Size` (0x00602060) → `SizeInternal` (0x00602190, recursive) → per leaf: `FrameGetChild(frameId,childId)`
   then **`Frame_ApplyLayoutRect` (0x0062e8a0)** = the terminal per-control placement Py4GW never performs.

`FrameScheduleSize` is the pump that converts the built tree into applied rects. Omit either the tree-build or
the schedule and children stay unpositioned.

### CCtlLayout builder API (EXE / WASM)
- `CCtlLayout::ctor` WASM 0x80dfa34c (vtable `DAT_00167118`, node array @+8/+0x10)
- `SetFrameId(uint)` 0x80dfa3da · `Clear()` 0x80dfa377 · `Size(Rect4f*)` 0x80dfa3eb
- `Row(H,V,expand)` 0x80dfb15b · `Column(H,V,expand)` 0x80dfa95a · `Child(childId,H,V,expand)` 0x80dfa5a4 (EXE 0x00601880) · `Gap(f,H,V)` 0x80dfaf1d · `End()` 0x80dfacf9
- align flags: `DAT_0016711c[H] | DAT_0016712c[V]`; `+0x80` H-stretch / `+0x100` V-stretch when expand!=0

`CDlgOptGeneral::OnCtlLayout` (WASM 0x80fd3338): `Column(0,0,1); LayoutSliders(l,3.0); LayoutCheckboxes(l,3.0); End();`
- LayoutSliders: per slider `Row(0,0,1); Child(labelId,…); Child(sliderId,…); End();` → slider clamped to column width (fixes huge width).
- LayoutCheckboxes: per checkbox `Gap(3.0); Child(cbId,0,0,expand);` → vertical stack, 3px gap, each gets a rect.

## Per-control creation (all `FrameCreate(parent, style, childId, proc, userdata, name)`)

| Control | style | proc (EXE / WASM) | notes |
|---|---|---|---|
| checkbox | 0x10000 | UiCtlBtnProc 0x00877e60 / 0x80df1d1e | `CtlBtnCheck(h,v)` for initial state |
| label | 0 | CtlTextProc 0x80db4695 | `FrameSetDefaultTextStyle` |
| droplist | 0 | UiCtlDropListProc 0x80e47ca4 | `CtlDropListClear/AddItem/SetSelection` |
| slider | 0 | UiCtlSliderProc 0x80fcd65d | range via userdata; width from layout |
| edit | 0 (0x1000000=password) | Account::EditProc → base UiCtlEditProc 0x00888aa0 | needs Border sibling (below); `CtlEditSetMaxCharCount 0x00604aa0` |

Parent = the content page. FrameCreate registers child+proc only; **no rect** — layout assigns it.

### Edit needs a Border sibling (childId 0xb), created BEFORE the edit:
```
border = FrameCreate(parent, 0, 0xb, IUi::UiCtlBorderProc(0x00879090), 0, L"Border")
FrameMouseEnable(border, 0, 0xffffffff)      // click-through to the edit
IUi::FrameSetLayer(border, -1)               // behind the edit so it frames, not covers
IUi::FrameSetSubclassFlags(border, UiCtlBorderProc, 0x10, 0)  // 0x10 = inset edit-box texture
```
Border paints the 9-slice box (msg 8 → `FrameContentAddImageTemplate`); layout gives border+edit the SAME rect.

## Close (why the native `[X]` never crashes)

- `[X]` → `IUi::UiCtlDlgProc` msg 0xb → **`IUi::PopCloser(win)`** (0x008766e0): scans band 0x2718→0x2710,
  `FrameDestroy` the **topmost** page, then `FrameMouseEnable(nextPage,1,0)` to re-arm the revealed page.
  That re-arm forces the hot-item/hit-test to re-resolve onto a live frame → **no dangling pointer**.
- Full window destroy: `FrameDestroy(win)` (0x0062c550 → `IFrame::DestroyRecursive` 0x0062ab40) frees window +
  all pages + all controls in ONE recursive pass. **Never** `FrameDestroy` controls/pages individually out
  from under the window — that is the crash class Py4GW hits.

## EXE symbols renamed this pass
`0x00873880 IUi::CompositeDlgBuilder` · `0x00876610 IUi::UiCtlDlgBaseProc` · `0x00876740 IUi::UiCtlContentPageProc` ·
`0x00876880 IUi::UiCtlDlgProc` · `0x008766e0 IUi::PopCloser` · `0x0062d330 IUi::GetContentContainer` ·
`0x00877d90 IUi::DlgActivateRefresh` · `0x0062f150 FrameSetMsgHandler` · `0x0062d380 FrameGetGeometry` ·
`0x00647db0 FrameBind` · `0x0062bfc0 FrameCreate` · `0x0062c550 FrameDestroy` · `0x0062ab40 IFrame::DestroyRecursive` ·
`0x0062cfc0 FrameGetChild` · `0x0062ede0 FrameMouseEnable` · `0x00602060 Ui::CLayout::Size` ·
`0x00602190 Ui::CLayout::SizeInternal` · `0x00602a10 Ui::CLayout::SizeQueryInternal` · `0x006018e0 Ui::CLayout::Child` ·
`0x00601880 CCtlLayout::Child` · `0x0062e8a0 Frame_ApplyLayoutRect` · `0x0088c150 CDlgOptGeneral::OnFrameCreate` ·
`0x0088bba0 CDlgOptGeneral::MsgProc` · `0x00867fe0 IUi::Account::CEmail::OnFrameCreate` ·
`0x00879090 IUi::UiCtlBorderProc` · `0x008699b0 IUi::Account::EditProc` · `0x008852e0 IUi::CCtlEdit::OuterProc` ·
`0x00888aa0 IUi::UiCtlEditProc` · `0x00604aa0 IUi::CtlEditSetMaxCharCount` · `0x0062f5a0 IUi::FrameSetLayer` ·
`0x0062fa20 IUi::FrameSetSubclassFlags` · `0x0062b8e0 IUi::FrameContentAddImageTemplate` · `0x00647170 IUi::FrameMsgCallBase`

## Implementation plan (one cohesive change — NOT per-control patches)

1. Bind the missing natives: `UiCtlContentPageProc` (0x00876740), the `CCtlLayout` builder verbs + `Size`,
   `FrameScheduleSize`/`FrameNativeSizeChanged`, `FrameSetSubclassFlags` (0x0062fa20), `UiCtlBorderProc` (0x00879090).
2. `CreateNativeWindow`: create the window with style incl. `0x200`, then create ONE content page
   (`UiCtlContentPageProc`, band childId 0x2710, userdata=window) + `FrameMouseEnable(page,1,0)`.
3. All control helpers parent to the content page (not the window).
4. Add a layout API: build a `CCtlLayout` tree over the content frame (Column + Child/Gap per control) and
   call `FrameScheduleSize` so the native msg-0x38 pass positions/sizes/depth-orders everything.
5. Edit: also create the Border sibling; let layout co-position it.
6. Close: route destroy through `PopCloser` / recursive `FrameDestroy(win)`; drop the ad-hoc control destroys.

Prior failed attempt (reverted): used the plain container `FUN_0051d8e0` as the host and no layout pass — that
is why it crashed/blanked. The fix requires the real `UiCtlContentPageProc` **and** the layout pass.

## TWO native window archetypes (2026-07-01, in-client verified)

There are two distinct ways the game builds a hosted-control window; Py4GW must pick one, not mix:

1. **Confirmation-dialog archetype** (`IUi::CompositeDlgBuilder` @ EXE 0x00873880 case 1): window created with
   base proc **`IUi::UiCtlDlgMsgProc`** (EXE 0x00876610 / WASM 0x80e586ff — msg 4 installs frame vtable idx
   `0xae9`), style `0x254000`, childId `0xd`, then chrome `IUi::UiCtlDlgProc` chained. Controls are DIRECT
   children positioned by the `CCtlLayout` pass. In-client: this window + a **button** work and close via `[X]`
   cleanly, but a **checkbox as a direct child still crashes** — because direct children require the full
   `CCtlLayout`/dialog-instance machinery (`CDlgOptGeneral`-style `MsgProc`) that a bare window lacks.

2. **Dev-window archetype (DevText / the reliable one)** — `IUi::NDlgDevText::CTextDialogFrame::OnCreate`
   (WASM 0x81392596). Recipe:
   - `win = FrameCreate(parent, style=0x20380, childId=0, proc=IUi::UiCtlViewProc (WASM 0x80e584cc), userdata={0, CtlFrameListProc (WASM 0x80e805f1), 0}, name=0)` — a **CtlView hosting a CtlFrameList**.
   - fill with **`CtlFrameListCreateItem(win, …)`** rows (each row a control proc — text, button, etc.).
   - `FrameNewSubclass(win, IUi::UiCtlDlgProc, 0x59)` — chrome; then `FrameSetTitle`.
   → **This is exactly Py4GW's working `CreateButtonList` + `AddControlItem` path.** The game's dev windows
   host controls as **frame-list ITEMS**, never as bare direct children. This is why Py4GW's button (an item)
   works and the direct-child checkbox crashes — and it is NATIVE, not a bypass (DevText is a real dev window).

## 7-WINDOW COMPARISON — the DEFINITIVE pattern (2026-07-01, high confidence)

RE'd SoundTest, Graphics, Gamepad, Customize, DevText, GeneralOptions, ConfirmDialog and compared them.

### Common setup phases (EVERY window does these, in order)
1. **Instantiate frame** with a class `MsgProc` (looked up by a proc-table index).
2. **Alloc the dialog C++ instance** on the create message and store its pointer in the frame userdata slot
   (`frame[2]`); `*(instance+4)` is the parent handle used for every child `FrameCreate`.
3. **Dispatch to the class `OnFrameCreate`** (the content builder).
4. **Create controls** with the correct per-type proc + style.
5. **Seed values** in a crash-safe order (slider range `0x56` BEFORE value `0x57`; droplist add-items then select; checkbox `CtlBtnCheck`).
6. **Size pass** — either a `CCtlLayout` measure/arrange, or native self-size.
7. **Chain unhandled msgs** to `IUi::FrameMsgCallBase` (EXE 0x0062ee70).
8. **Chrome + teardown** — `IUi::UiCtlDlgProc` flags `0x59`; close via msg `0xb → IUi::PopCloser → recursive FrameDestroy`, freeing the instance.

### The decisive axis — CONTROL HOSTING
- **Direct children + `CCtlLayout`** (SoundTest, Graphics, Gamepad, GeneralOptions, ConfirmDialog): supports **checkbox / slider / droplist / edit**. This is the ONLY pattern in which the complex controls are correctly sized and given a stable owning dispatcher.
- **Frame-list items** (DevText): safe **only** for non-interactive **text / buttons**.
- **Hybrid** (Customize): a CtlView whose `UiCtlPlaceProc` place-rows each *self-create* their own checkbox.
- Key trap: in GeneralOptions the PAGE is itself a CtlView list-item, yet its CONTROLS are still direct
  children — **list-item hosting of a page does NOT imply list-item hosting of controls.** (This is why
  hosting a checkbox/slider/edit as a bare `add_control_item` row crashes/blanks.)

### The 3 load-bearing pieces Py4GW LACKS (the whole bug)
Py4GW bolts checkbox/slider/edit on as **ad-hoc direct children** of the chrome window with **(a)** no owning
`TCtlInstance` dialog object in the frame userdata, **(b)** no embedded `CCtlLayout` + `SetFrameId`, **(c)** no
`CCtlLayout` size pass (msg `0x38` SizeQuery / `0x37` Size). So: **checkbox** never gets measured/arranged and
has no dispatcher; **slider** isn't laid out and its input subscription dangles on ad-hoc destroy (the close
crash); **edit** has no `UiCtlDlg` content owner at all → crash. Text/button work only because they're the sole
controls that survive the ad-hoc path.

### Reliable pattern to implement (an "instanced content dialog" host)
1. `FrameCreate` a content frame whose `MsgProc` is a Py4GW-authored `TCtlInstance`-style dispatcher.
2. On create (msg 9): `MemAlloc` a small instance that embeds a `CCtlLayout`; store the pointer in `frame[2]`; `CCtlLayout::SetFrameId(frameId)`.
3. Parent EVERY control as a **direct child** of that frame — checkbox `UiCtlBtnProc` (idx 0xa9d, style 0x10000), slider `UiCtlSliderProc` (idx 0xbe8), droplist `UiCtlDropListProc` (idx 0xaef), label `CtlTextProc` (idx 0xa81); each a unique childId.
4. Seed values crash-safe (slider `0x56` before `0x57`; droplist items then select; checkbox `CtlBtnCheck`).
5. Build a Row/Column `CCtlLayout` tree; apply on **msg 0x38 → `Ui::CLayout::SizeQuery` (EXE 0x00602900)** then **msg 0x37 → `Ui::CLayout::Size` (EXE 0x00602060)**, re-triggered by `FrameScheduleSize`.
6. Route everything else to `IUi::FrameMsgCallBase`.
7. **Edit**: port the ConfirmDialog nested-content pattern — a `UiCtlDlg` content child (`IUi::CompositeDlgContentProc` EXE 0x008895d0) hosting the edit by childId (`FrameMsgSend 0x56/0x58`).
8. Teardown via chrome msg `0xb → PopCloser → recursive FrameDestroy`, freeing the instance + `CCtlLayout` dtor. This removes the slider dangling-pointer UAF generically.
9. Keep the frame-list-item path ONLY for non-interactive text/button rows.

**The one new thing Py4GW must author: a C++ `MsgProc` dispatcher (the engine calls it) that owns the
instance + `CCtlLayout` lifecycle and runs the size pass.** That is the missing "owner" every native
control-hosting window has and Py4GW never had.
