# GW UI Elements — Corrected Creation Recipes (Ghidra-verified)

> Reverse-engineered from `Gw.wasm` (symbols) + `Gw.exe (06-14)` via a 40-agent Ghidra swarm
> (2 independent angles per topic + per-topic consensus), 2026-06-30. Every claim below is
> backed by a decompile. Supersedes the prior (partly-wrong) frame-list-item recipes.

> ## ✅ IMPLEMENTED & IN-CLIENT-TESTED (2026-07-01)
>
> These recipes are no longer just "fix plans" — they are **implemented** in `include/py_ui.h`,
> bound in `src/py_ui.cpp`, and exposed via `Py4GWCoreLib/GWUI.py`. A second 21-agent Ghidra swarm
> (2026-07-01) root-caused the remaining in-client failures and the fixes are shipped. For the
> consolidated address/flag/status table and the definitive per-control recipe, **see
> `native_button_pipeline.md` → "MASTER REFERENCE"**. Deltas discovered during implementation that
> refine the recipes below:
>
> - **Selectable list** must be created with flags **`0x20128`** (not `0x20000`) or its selection
>   state is never allocated → `FUN_00613b30` null-deref assert on the first select.
> - **Radio/hyperlink rows must use a NULL-safe row proc.** The selectable list highlights a row by
>   sending child msg `0x57` with a NULL out-ptr: `CtlTextBtnProc`/`CtlTextProc` write through it and
>   crash. Radio → **`CtlBtnProc 0x0060f4f0`** rows; hyperlink → **`CtlTextSelectable 0x00617df0`**
>   (item flags `0xe001`). Select rows by the create-time **child KEY = insert_index (start at 1)**,
>   not the AddItem frame-id return.
> - **Checkbox** needs the paint-gate bit → flags **`0x48300`** (`0x40000` | face `0x8000` | `0x300`).
>   Without `0x40000` it falls back to the base flat proc = a generic rectangle.
> - **Edit** uses the **outer `CCtlEdit 0x008852e0`**, and must be **sized with the anchor-6 setter
>   `0x0062F770`**, not `FrameSetSize` (which the window layout resets to 0×0 → invisible).
> - **Tabs** need the styled **`UiCtlPageProc 0x00885590`** layered (FrameNewSubclass) over base
>   `CtlPageProc` BEFORE any AddTab (keep flags `0x40000`), else tab buttons render untextured.
> - **Slider** two-layer create is correct; **release its auto-scroll CTimer via mouse-up msg `0x2e`
>   before destroy** (`DestroySliderControlByFrameId`) or a leaked repeating timer crashes later.
> - **Destroy:** GWCA `DestroyUIComponent` silently no-ops on 06-14 (its resolver scans the old source
>   path `\Code\Gw\Ui\Frame\FrApi.cpp`; the build renamed it to `\Code\Engine\Frame\FrApi.cpp`). Call
>   the native id-based destroyer **`FUN_0062c550(frame_id)`** directly.

## Summary

| Topic | Verdict | Confidence |
|---|---|---|
| LAYOUT & SIZING | confirmed | high |
| Textures & image lists | confirmed | high |
| Text button | confirmed | high |
| Flat button | confirmed | high |
| Checkbox | confirmed | high |
| Radio button | likely | high |
| Slider | confirmed | high |
| Styled GW button | confirmed | high |
| Dropdown | likely | high |
| Editable text control | likely | high |
| ProgressBar | likely | high |
| Tabs control | likely | high |
| Group header | likely | high |

---

## LAYOUT & SIZING (cross-cutting): why frame-list items render full-width, and the engine-native mechanism for real fixed size/position

**Verdict:** confirmed &nbsp; **Confidence:** high

### Root cause

Two distinct self-laying-out managed parents overwrite child geometry every relayout. (1) The frame list ("extremely wide"): CCtlFrameList::OnFrameMsgSizeQuery discards item content width and reports the container width unless list style bit 0x4000 is set, and OnFrameMsgSize then forces every item's width to the list's assigned width (only height comes from the item's native msg-0x38 size). (2) The window/container ("children overlapped"): a self-laying-out parent repositions its direct children from alignment, not from the caller's FrameSetPosition. In both cases a child never owns its rect while the parent runs a layout pass, so post-create FrameSetSize/FrameSetPosition is transient. The engine's own solution for non-vertical/fixed geometry is the frame list's per-instance size (msg 0x62) and size-query (msg 0x63) handlers, which fully bypass the built-in stretch/stack loop.

### Verified recipe

The frame-list ("CCtlFrameList") owns its items' geometry via a two-pass size protocol, verified by decompiling Gw.wasm this pass:

WIDTH FORCE (root of "extremely wide"). CCtlFrameList::OnFrameMsgSizeQuery @ ram:80e7dd06 sums item native sizes (out.width = max(item nativeW), out.height += nativeH) then executes the decisive line: iVar1 = FrameTestStyles(list, 0x4000); if (iVar1 == 0) *out.width = *param2 (the container-proposed width). So UNLESS list style bit 0x4000 is set, the list throws away the content width and reports the container width. CCtlFrameList::OnFrameMsgSize @ ram:80e7d758 then, per item, calls FrameGetNativeSize(item) and FrameSetPosition(item, position={x:0, y:runningY}, size={listWidth, nativeHeight}) — item WIDTH is unconditionally overwritten to the list's assigned width; only HEIGHT flows from the item's native size (msg 0x38). These reconcile: with 0x4000 set the list shrink-wraps (list width = max native width), so the forced item width == content width; without it, list width == container width == full-window items. Confirmed.

ENGINE ESCAPE HATCH (the recommended real fix). The list has two optional per-instance callback slots: a size handler at instance+0x04 (installed via msg 0x62; CtlFrameListSetSizeHandler @ ram:80e83137 does FrameMsgSend(list,0x62,fnptr,0)) and a size-query handler at instance+0x08 (msg 0x63=99; CtlFrameListSetSizeQueryHandler @ ram:80e8320d). In BOTH OnFrameMsgSize and OnFrameMsgSizeQuery, if the slot is non-null the list does an indirect call handler(TArray<uint>& itemFrameIds, FrameMsgSize/Query&) and RETURNS, entirely bypassing the built-in stretch/stack loop. Confirmed in the decompile of both.

GEOMETRY PRIMITIVE (arg order resolved). FrameSetPosition(uint, Coord2f, Coord2f) @ ram:809a9448 forwards both Coord2f unchanged to IFrame::CRect::SetPosition(frame+0xD0, a, b, anchor=6). The frame-list caller passes a=position{x,y}, b=size{w,h}. So the two-Coord2f overload is (frameId, POSITION, SIZE) with anchor forced to 6 — this corrects Angle B, which had it reversed as (size,pos). FrameGetNativeSize @ ram:809a86af reads CRect::GetNativeSize (native-size field at frame+0xD0), which is what the list sums/maxes; FrameSetSize writes the actual on-screen rect, which the list overwrites on its next relayout, so post-create FrameSetSize on a list item is transient.

RECOMMENDED RECIPE (Mechanism B — works for every proc, including flat button):
1. CreateNativeWindow -> CreateScrollableContentByFrameId(window,0) -> frame_list_id.
2. Install BOTH handlers on frame_list_id BEFORE adding items: SendFrameUIMessage(frame_list_id, 0x63, &sizeQueryHandlerFnPtr, 0) and SendFrameUIMessage(frame_list_id, 0x62, &sizeHandlerFnPtr, 0).
3. sizeQueryHandler(items, q): for each item FrameGetNativeSize(item); q.out = {max width, sum height} (or a caller-fixed container size). This stops the container-width override.
4. sizeHandler(items, s): runningY=0; for each item FrameGetNativeSize(item) then FrameSetPosition(item, position={x:0 (or caller x), y:runningY}, size={item nativeW (NOT list width), nativeH}); runningY += nativeH. Optionally a FixedRectSizeHandler reading a per-item {x,y,w,h} table for absolute/grid layout.
5. Add items as before (CtlFrameListCreateItemByFrameId). The list now defers ALL geometry to your handlers. Handlers MUST be native C function pointers (the list does call_indirect on them) living in Py4GW.dll, not Python.

Alternative Mechanism A (shrink-wrap only): OR 0x4000 into the inner CCtlFrameList create-flags word so the query pass keeps content width; still requires every item proc to answer msg 0x38 (flat CtlBtnProc/CtlEditProc do not, so they still collapse). There is no standalone FrameSetStyles export, so 0x4000 must be set at frame-create time — the msg 0x62/0x63 handler route is the cleaner, more reliable change. Do NOT parent controls directly to the CreateNativeWindow root and FrameSetPosition them: any self-laying-out managed parent (window root or frame list) re-stomps child geometry each relayout (this is the "children overlapped" symptom); keep controls inside the frame list and drive geometry through the size handler.

### C++ fix plan

In include/py_ui.h + src/py_ui.cpp:
1) Add two static C++ handlers with the exact engine signature void(*)(TArray<uint32_t>& itemFrameIds, const FrameMsgSize&) and void(*)(TArray<uint32_t>&, const FrameMsgSizeQuery&):
   - NoStretchSizeQueryHandler: iterate items, FrameGetNativeSize each, write q.out = {max(nativeW), sum(nativeH)} (mirrors the 0x4000 branch of ram:80e7dd06). This overrides the container-width force.
   - NoStretchSizeHandler: runningY=0; for each item FrameGetNativeSize(item) then FrameSetPosition(item, position={0,runningY}, size={item.nativeW, item.nativeH}); runningY += nativeH. Use the ITEM's own width, never the list width (mirrors ram:80e7d758 minus the width force). IMPORTANT: FrameSetPosition arg order is (frameId, POSITION, SIZE); anchor is forced to 6 by the export — do not pass anchor and do not swap the Coord2f args.
   - Optional FixedRectSizeHandler reading a caller-supplied per-item {x,y,w,h} table for absolute/grid placement.
2) Add helper SetFrameListNoStretchByFrameId(uint32_t frame_list_id): SendFrameUIMessage(frame(frame_list_id), 0x63, &NoStretchSizeQueryHandler, nullptr) then SendFrameUIMessage(..., 0x62, &NoStretchSizeHandler, nullptr) (this is exactly CtlFrameListSetSizeQueryHandler @ ram:80e8320d / SetSizeHandler @ ram:80e83137). Call it right after CreateScrollableContentByFrameId and before adding items. Bind in src/py_ui.cpp; stub in stubs/PyUIManager.pyi.
3) Stop relying on post-create FrameSetSizeByFrameId for flat/edit list items (py_ui.h AddFlatButtonItem ~4490) — FrameSetSize writes the actual rect (CRect+0xD0) which OnFrameMsgSize overwrites next relayout. Route those through the size handler (2) instead (or give them a proc that answers msg 0x38).
4) Remove/avoid the CreateControlChildByFrameId-parents-to-window-root + manual FrameSetPosition path (root relayout stomps it -> overlap). Keep all controls inside the frame list and let the size handler own geometry.
5) Handlers MUST be native C function pointers in Py4GW.dll (the list does call_indirect); they cannot be Python callables. Note: base class / correct proc / textures / multi-layer crash (checkbox, radio, slider, dropdown, styled button) are ORTHOGONAL to this layout angle and handled in the per-control recipes, not here.

### Open questions (needs live decompile)

Verified on Gw.wasm this pass; still need the shipped-binary confirmation on Gw.exe (06-14): decompile the EXE twins of CCtlFrameList::OnFrameMsgSizeQuery (wasm ram:80e7dd06), CCtlFrameList::OnFrameMsgSize (ram:80e7d758), CtlFrameListSetSizeHandler (ram:80e83137), CtlFrameListSetSizeQueryHandler (ram:80e8320d) to confirm the same 0x4000/0x2000 style bits, the msg 0x62/0x63 install path, and the handler-slot offsets (size@instance+0x04, size-query@instance+0x08). Separately, the direct-window-child overlap path was NOT decompiled this pass: verify Angle B's CContainerFrame::OnFrameSize (ram:812a660d, alignment-only reposition) and the position-lock UiGenerateFramePositionLockFlags (ram:80ec1bca) / container msg 0x34 before relying on any container-child layout; the frame-list msg-0x62/0x63 handler route is preferred precisely because it sidesteps that unverified path.

---

## Textures & image lists — why styled_button rendered nothing, and how s_btnCheckImageList / sm_rateArrowImageList / s_editCaretMaterial are created and warmed

**Verdict:** confirmed &nbsp; **Confidence:** high

### Root cause

styled_button rendered NOTHING (not a crash, not "proc not handled") because the bare-proc frame-list-item path failed TWO independent gates inside IUi::UiCtlBtnProc's msg-0x01 paint, both confirmed in the Gw.wasm decompile: (1) the item was created with style 0x300, lacking the 0x40000 bit, so sub-0's `FrameTestStyles(frame,0x40000); if(==0) return;` early-returns and no 9-slice background chrome is drawn; and (2) s_btnCheckImageList (_DAT_ram_005a857c / EXE 0x010819cc) was NULL because no Store ever opened and no msg 0x05 fired this session, so sub-1's FrameContentAddImage received a null HFrameImageList and added no state/face geometry (a silent no-op). Both together = fully invisible control. Angle A correctly identified GATE 2 but MISSED GATE 1; Angle B identified both — the decompile confirms both are real and both are required.

### Verified recipe

STYLED BUTTON (IUi::UiCtlBtnProc, WASM ram:80df1d1e, EXE 0x00877e60) as a frame-list item, done correctly — BOTH gates required together:

GATE 1 (background chrome): The proc's msg 0x01 sub-0 (label code_r0x80df2b0d, taken when *param2==0) executes FrameTestStyles(frame,0x40000) and `if (result==0) return;` BEFORE any FrameContentAddImageTemplate 9-slice pass. CONFIRMED in WASM decompile. The frame-list item is created with style 0x300 only, so the whole background pass early-returns → no chrome. Fix: create the item with the 0x40000 style bit set so the native list FrameCreates it as 0x40300 (the exact style GW's Trade/Store styled buttons use; 0x40000 = "draw background template", 0x300 = F_VISIBLE|F_ENABLED). item_flags merges into the FrameCreate style (same mechanism by which 0x10000 toggle / 0x80000 momentary are read via FrameTestStyles), so OR 0x40000 into item_flags.

GATE 2 (state/face art): msg 0x01 sub-1 (label code_r0x80df306d, *param2==1) computes a 0..5 state index then FrameContentAddImage(frame, rect, _DAT_ram_005a857c /*=s_btnCheckImageList, EXE 0x010819cc*/, stateIdx, ...). Cold (no store/merchant opened this session) the global is NULL → FrameContentAddImage gets a null HFrameImageList and adds no geometry. It NO-OPS (does not crash) — this matches observed "shows nothing". Fix (warm it): resolve the global (scan the store in UiCtlBtnProc's msg-0x05 block; current build 0x010819cc — resolve, do not hardcode); if *global==0, send the freshly-created item exactly ONE msg 0x05 (SendFrameUIMessage(item_frame, 0x05, null, null)). The msg-0x05 handler (code_r0x80df24fb) asserts "!s_btnCheckImageList" ONLY when the global is already non-null; while null it safely runs FrameImageListCreate(0x11 pixfmt, 7 texop, 0x12=18 subimages, {21,21} subImageSize, {128,32} artDims, &PTR_DAT_ram_0102112a path, 6 flags) and stores the handle. NEVER send 0x05 when non-null (assertion + handle leak). All verified in WASM.

Both gates independent: without GATE 1 the chrome never draws even if the image list is warm; without GATE 2 the face/state art never draws even with style 0x40000. Fix both.

PRACTICAL DEFAULT: for a guaranteed rendered+clickable button keep the FLAT engine primitive CtlBtnProc (EXE 0x0060f4f0) — it paints a solid material via GrBuildSolidMaterial with NO image-list and NO 0x40000 dependency (already-confirmed-working flat_button; size via FrameSetSize, click state via msg 0x59). Reserve the styled UiCtlBtnProc path only when both gates are satisfied, or when cloning an already-initialized live button subtree (Options/Trade) where the class-static art is already present.

PROGRESS (sm_rateArrowImageList): CtlProgressProc (ram:80f6ce9a) delegates 1:1 to CtlProgress::CProgressFrame::FrameProc (ram:80f6cf82) — CONFIRMED single-layer, self-allocating (msg 0x09 MemAllocs its own 0x34 instance, only falls to FrameMsgCallBase at default). It does NOT crash from missing base. Its rate-arrow overlay reads class-static sm_rateArrowImageList; cold-null → arrows just don't draw (solid fill may still show). Warm by opening any progress window / running class-init before relying on rate arrows. NOTE: progress was NOT in the in-client test set — structurally supported, not directly observed.

EDIT (s_editCaretMaterial): proc-owned lazy static built inside the styled IUi::UiCtlEditBoxProc (ram:80e0e89e) on first use of any edit/chat box. In a live in-game session a chat box exists, so it is effectively already warm — textures are not the edit blocker; sizing (no msg 0x38 min-size) is. Untested in-client.

GENERAL RULE: engine-primitive procs (CtlBtnProc solid, CtlTextBtnProc text) own NO image lists and render self-contained. Styled IUi::UiCtl* wrappers own art through class-static handles initialized by (a) the styled proc's own msg 0x05 (button — can be driven directly), or (b) a store-sent registered broadcast (0x20000004), or (c) first-use in the proc (edit caret). A bare-proc cold frame-list item satisfies none, so styled art is NULL.

### C++ fix plan

Two changes, both in C:/Users/Apo/Py4GW/include/py_ui.h (mirror in ResolveNamedControlProc callers if styled_button is ever created via CreateControlChildByFrameId):

(1) UIManager::AddControlItemByFrameId (~line 4538): when control=="styled_button", OR 0x40000 into item_flags BEFORE calling CtlFrameListCreateItemByFrameId, so the native list FrameCreates the item as 0x40300 instead of 0x300 (turns on sub-0's background 9-slice pass). Do NOT do this for flat_button/text_button — they self-paint and must not take the 9-slice pass.

(2) Add UIManager::EnsureBtnCheckImageList(uint32_t styled_btn_item_id) and call it from AddControlItemByFrameId immediately AFTER a successful styled_button item is created:
    - Resolve the s_btnCheckImageList global address once (scan the `mov [global],eax` store inside UiCtlBtnProc's msg-0x05 block; current 06-14 build 0x010819cc — resolve from the proc, cache it, do NOT hardcode). Add companion IsBtnCheckImageListReady() = (global && *global).
    - if (*(uint32_t*)global == 0) SendFrameUIMessage(GetFrameById(item_id), (UIMessage)0x05, nullptr, nullptr);  // guard on ==0 only; the proc's own "!s_btnCheckImageList" assertion enforces this. Sending while null runs FrameImageListCreate and populates the global for this and every future styled button.

Both are required together (change 1 alone = warm list but no chrome; change 2 alone = chrome but no face art).

Safest overall: keep the flat CtlBtnProc path as the DEFAULT for any "button" request (rendered+clickable, no texture dependency); only attempt the styled UiCtlBtnProc image path when EnsureBtnCheckImageList reports the global != 0 after warming.

(3) Progress (optional, untested): CtlProgressProc will NOT crash cold (self-allocating single-layer); it just won't show rate arrows. Add an analogous EnsureRateArrowImageList (resolve global via the "!sm_rateArrowImageList" assertion site in CProgressFrame) if arrows are needed; no style flag required. Do NOT create styled controls (checkbox/radio styled, progress, edit) expecting their class-static art from a bare cold item — those want their class MsgProc / first-use warm-up.

### Open questions (needs live decompile)

1) EXE confirmation (WASM twin already proves the model): decompile Gw.exe (06-14) IUi::UiCtlBtnProc @ 0x00877e60 to (a) confirm the sub-0 FrameTestStyles(frame,0x40000) early-return is present in the injected binary, and (b) read the exact `mov [0x010819cc],eax` store in the msg-0x05 block to lock the s_btnCheckImageList global address/resolver for this build. 2) FrameContentAddImage(HFrameImageList) @ ram:809b2b97 — confirm it truly no-ops on a NULL image-list handle (vs an internal guard) so the "no-op not crash" behavior is airtight; observed evidence (styled_button shows nothing, no crash) already supports this. 3) Whether a STANDALONE styled button auto-registers for the 0x20000004 broadcast (FrameMsgRegister) — not needed if using the direct msg-0x05-to-item warm path (simpler, self-contained), but decompile IFrame::CMsg::DispatchRegistered (from FrameMsgSendRegistered ram:809b8869) if the broadcast path is ever preferred. 4) sm_rateArrowImageList global store address inside CProgressFrame OnFrameMsgClassInitialize/ContentAdd (ram:80f79df6 / ram:80f80492 / EXE 0x008812e0) for EnsureRateArrowImageList. 5) Progress and edit were NOT exercised in the 2026-06-30 in-client test — their reconciled verdicts (progress no-crash self-alloc; edit blocked by size not textures) are structurally supported by decompile but not directly observed.

---

## Text button (CtlTextBtnProc) — clickable button whose click is parent-notify-only; how to make it register clicks and stop looking like a cyan hyperlink

**Verdict:** confirmed &nbsp; **Confidence:** high

### Root cause

Two compounding facts, both confirmed by decompile: (1) CtlTextBtnProc surfaces a click ONLY as FrameMsgNotifyParent(notifyId 8) on mouse-up; when the button is created as an item in a PLAIN frame list (AddControlItemByFrameId → plain list), that parent has no notify-consuming subclass, so notify 8 is dispatched against an empty table and dropped — hence 'no click'. (2) The Python/C++ click probe IsButtonPushedByFrameId sends msg 0x59, which for CtlBtnProc is IsPushed but for CtlTextBtnProc is GetText (case 0x59 copies the caption via FUN_0046be40 and leaves the boolean result 0), so polling can never see a press. CtlTextBtnProc has no pollable pushed-state message at all. The proc itself is correct; the failure is entirely the non-notifying parent plus reuse of the flat button's 0x59 poll.

### Verified recipe

CtlTextBtnProc (EXE FUN_00616c00 @ 0x00616c00 = WASM ram:80d9ce76) IS a genuine clickable button that paints TEXT ONLY (no background rect) with baked colors normal 0xff64beeb / hover 0xff78d2ff — that is why it looks like a cyan hyperlink. Its ONLY click output is a PARENT notification: on mouse-up (msg 0x25) it calls FUN_0062ee80 (FrameMsgNotifyParent) with notifyId 8 UNCONDITIONALLY. mouse-down (0x24) sets an internal pushed bit and fires notify 7 (push) only if style 0x2000 is set; key/enter (0x20) also notify 7; release paths notify 9. There is NO message that reads back the pushed bit, and msg 0x59 on this proc = GetText (copies the caption into the caller buffer), NOT IsPushed. So it can never be polled for a press.

CANONICAL CLICKABLE RECIPE (decompile-verified, helpers already in py_ui.h):
1. window = CreateNativeWindow(...).
2. list = CreateSelectableScrollableContentByFrameId(window)  — inner list proc = CCtlFrameListSelectable::FrameProc @ 0x00613850 (NOT the plain list).
3. item = AddButtonItemToFrameListByFrameId(list, encoded_caption)  — proc CtlTextBtnProc @ 0x00616c00; caption MUST be an encoded payload via BuildStandaloneLiteralEncodedTextPayload (raw wide-string crashes). flags|0x300 renders fine.
4. Each frame: code = GetFrameListSelectionByFrameId(list)  — msg 0x67; nonzero code == the clicked row. Flow that makes this work: item mouse-up → notify 8 → selectable list case 0x31 → FUN_00613b60 = SetSelection → highlight + pollable via 0x67. All four steps confirmed in the injected binary.
5. Cosmetics to kill the hyperlink look: after create send msg 0x5b=SetColor and 0x5d=SetHoverColor (ABGR); change caption with msg 0x5f=SetText (the flat button's 0x5e does something else here — propagates name to children).

ALTERNATIVE (standalone text button not inside a list): parent it under a window carrying a dialog subclass — FrameNewSubclassByFrameId(window, UiCtlDlgProc @ 0x00876880, 0) — FrameCreate CtlTextBtnProc as a child, set style 0x2000 if you also want a mouse-down push(7), and surface notifyId==8/childId from that parent's OnFrameNotify to Python via a latch/callback. This is more general but requires exposing the notify; the selectable-list path is preferred because it is already wired and pollable.

DO NOT: create the clickable text button as an item in a PLAIN frame list (its parent has no OnFrameNotify, so notify 8 is swallowed silently), and DO NOT poll it with IsButtonPushedByFrameId (msg 0x59 = GetText here). If you specifically need a self-pollable pushed state without any parent wiring, use the FLAT button CtlBtnProc (EXE 0x0060f4f0) via AddFlatButtonItemToFrameListByFrameId — its 0x59 genuinely = IsPushed.

### C++ fix plan

1. Route clickable text buttons through a notify-consuming parent. In the test harness UI_RE/ui_elements_test.py and in AddControlItemByFrameId (py_ui.h ~4538): when control is 'text_button'/'hyperlink', the target frame_list_id MUST be one created by CreateSelectableScrollableContentByFrameId (py_ui.h:4661, selectable proc 0x00613850), never the plain scrollable list. Read clicks each frame via GetFrameListSelectionByFrameId (py_ui.h:4683, msg 0x67).
2. Add a dedicated helper AddClickableTextButtonToSelectableList(window, encoded_text) that lazily creates/reuses one selectable inner list, calls AddButtonItemToFrameListByFrameId, returns the item id, and documents that clicks are read via GetFrameListSelectionByFrameId — so callers can never wire a text button into a notify-less parent.
3. Never pair CtlTextBtnProc with IsButtonPushedByFrameId (py_ui.h:3442); guard/document that msg 0x59 == GetText for the text button. Keep IsButtonPushedByFrameId only for CtlBtnProc flat buttons (AddFlatButtonItemToFrameListByFrameId).
4. Add cosmetic setters so callers override the baked hyperlink colors/caption: SetTextButtonColorByFrameId → SendFrameUIMessage msg 0x5b; SetTextButtonHoverColorByFrameId → msg 0x5d; SetTextButtonTextByFrameId → msg 0x5f. (Do NOT reuse 0x5e for the text button caption.)
5. Optional standalone path: FrameNewSubclassByFrameId(window, UiCtlDlgProc @ 0x00876880, 0) then FrameCreate CtlTextBtnProc as child with style|0x2000, and expose the parent OnFrameNotify notifyId==8/childId to Python as a per-frame 'clicked' latch.
6. Docs: in docs/RE/ui_controls_catalog.md and ui_elements_creation_recipes.md, replace the 'not a button' verdict for CtlTextBtnProc with 'clickable, notify-8 only, NO pollable pushed state, msg 0x59==GetText; requires a selectable-list or dialog-subclass parent'.

### Open questions (needs live decompile)

none blocking. Verified on both Gw.wasm and the injected Gw.exe (06-14): CtlTextBtnProc FUN_00616c00 (0x24/0x25 notify 7/8, 0x59=GetText, no pushed getter, 0x5b/0x5d/0x5f setters) and the selectable list FUN_00613850 (case 0x31 notify-8→FUN_00613b60 SetSelection, case 0x67 GetSelection). Non-load-bearing corrections to Angle B: msg 0x56 is a programmatic PUSH (notify 7), not a click; there is no msg 0x0c hand-cursor case in this proc (cursor is likely set by a base class). Out of scope for this topic: the 'extremely wide' frame-list layout stretch and the separate checkbox/radio/slider/dropdown/styled-button recipes remain unsolved and are tracked as their own root failures.

---

## Flat button (CtlBtnProc @ 0x0060f4f0): correct proc, why it renders full-width + untextured as a frame-list item, and how to build it as a discrete self-sizing button

**Verdict:** confirmed &nbsp; **Confidence:** high

### Root cause

"EXTREMELY WIDE" is caused by the FRAME LIST, not by CtlBtnProc. Every control was created via AddControlItemByFrameId -> CtlFrameListCreateItem (EXE 0x00612900), which merely does FrameMsgSend(list, 0x57, &{flags,index,item_proc,encoded_text}); CCtlFrameList then FrameCreates the item and runs its own vertical-stack arrange pass that forces each item's rect to x=0 / width=list-content-width / height=item's queried height on every (re)layout. Proof: the current helper already calls FrameSetSizeByFrameId(item,120,22) yet the item still renders full-width — the list overwrites item width each frame. Hence flat_button/checkbox/radio/slider all look identically full-width, and a frame-list item can NEVER be a discrete button. "NO TEXTURE" is by design (CtlBtnProc paints a solid material, no image list). Correction to prior RE docs: CtlBtnProc DOES self-size (case 0x38 FUN_00610580 + case 0x13 preferred-size from Property+0x24/+0x28); the "no msg 0x38 / thin strip" claim in native_button_pipeline.md 5.2 and ui_controls_catalog is WRONG for the 06-14 build. The earlier direct-child "overlap" was a separate bug: CreateControlChildByFrameId hardcodes x=10,y=10 for every child and never calls FrameSort, so children stack at the same spot.

### Verified recipe

PROC: CtlBtnProc @ EXE 0x0060f4f0 (= FUN_0060f4f0, WASM CtlBtnProc ram:80dbe9be) IS the correct proc for a PLAIN (flat, solid-color) button. Keep it; do NOT swap to the styled/textured UiCtlBtnProc (EXE 0x00877e60) which needs the lazily-built s_btnCheckImageList (0x010819cc, only warm after a Store/Shop window opens) and therefore renders NOTHING cold.

SELF-SIZING (verified from 06-14 decompile): CtlBtnProc self-sizes. case 0x38 -> FUN_00610580 (OnCtlLayout) measures the caption via FUN_0062fee0 and writes width/height into the out-rect extent (param_3[2]); case 0x13 (size-query) reads ICtlBtn::Property+0x24 (width) and +0x28 (height) and, if BOTH are > 0, returns them as the preferred size (else falls through to base). So free-standing it sizes to ~text width, and it also supports a forced fixed size via Property+0x24/+0x28.

STRUCT/MSGS (verified): Property is 0x2C bytes (case 0x09 -> FUN_006102b0 allocates; case 0x0B -> FUN_005acaeb(p,0x2c) frees). Property+0x00 low bits: bit0 = checked (msg 0x58 returns &1), bit2 = pushed (msg 0x59 returns >>2 &1). msg 0x5E -> FUN_00610420 sets caption; msg 0x5B sets solid color; msg 0x56/0x24 -> ICtlBtn::Click (FUN_0060f2a0). Default case falls to thunk_FUN_00647170 (a direct base thunk, NOT a multi-layer vtable base needing separate registration) -> crash-safe, unlike slider/dropdown.

TEXTURE (by design): case 1 (paint) builds a SOLID material via FUN_00679a60(&color,0x20003e0,0) then fills the frame rect inset 1px (local_34..local_28 = rect +1/+1/-1/-1) via FUN_0062b2d0. color = 0xff808080 normal, 0xff404040 disabled, 0xff8080ff checked-or-pushed. No image list / 9-slice — a solid rectangle is expected, not a bug.

RECIPE A — plain discrete flat button (accept solid color): create it as a DIRECT CHILD of a normal container/dialog window, NOT as a frame-list item. 1) window = CreateNativeWindow(...); 2) FrameNewSubclass(window, UiCtlDlgProc @ 0x00876880, 0) so OnFrameNotify (7/8/9) dispatches clicks (a bare CContainerFrame has an empty notify table and swallows clicks); 3) btn = FrameCreate(window, style=0x300 [F_VISIBLE|F_ENABLED], uniqueChildId, CtlBtnProc, userData, name); 4) set caption via msg 0x5E FIRST so msg 0x38 can measure; 5) SIZE: either rely on self-size (0x38), or force a fixed discrete size by writing Property+0x24=width / +0x28=height (both > 0) via the frame context, then FrameScheduleSize + FrameContentInvalidate so case 0x13 reports {w,h}; 6) POSITION: use a UNIQUE childId/order and FrameSort(btn,1,prevSibling) (how the game arranges dialog buttons) — do NOT hardcode the same x,y for every child. Behavior flags: OR 0x10000 = toggle, 0x80000 = momentary.

RECIPE B — full-width stacked row: keep the CtlFrameListCreateItem path ONLY for menus/lists where full-width rows are wanted. It can never yield a discrete-width button.

### C++ fix plan

1) include/py_ui.h: relabel AddControlItemByFrameId / AddFlatButtonItemToFrameListByFrameId as a FULL-WIDTH LIST-ROW helper. Keep CtlBtnProc as the proc but drop/comment the dead FrameSetSizeByFrameId(item,120,22) at ~line 4583 (the list overrides item width every layout). No proc change.
2) Add a NEW discrete-button helper (e.g. AddFlatButtonChildByFrameId) that does NOT touch the frame list: (a) resolve CtlBtnProc via ResolveCtlBtnProc with ToFunctionStart -> 0x0060f4f0 (not the mid-function pattern); (b) FrameCreate(parentWindow, 0x300, childId, CtlBtnProc, userData, name) as a DIRECT child of a real CreateNativeWindow container; (c) set caption via msg 0x5E first; (d) for a fixed size, write Property float32 at +0x24 (width) / +0x28 (height) via the button's frame context (Property = 0x2C bytes) then FrameScheduleSize + FrameContentInvalidate — this survives parent relayout better than a bare FrameSetPosition; otherwise let msg 0x38 self-size; (e) position with FrameSort(btn,1,prevSibling) and a unique childId (do not hardcode x=10,y=10); (f) install OnFrameNotify on the parent via FrameNewSubclass(parent, UiCtlDlgProc @ 0x00876880, 0) for click dispatch.
3) Fix CreateControlChildByFrameId (~line 4617): stop hardcoding x=10,y=10 for every child; call FrameSort instead of / in addition to FrameSetPosition; require the parent to be a CreateNativeWindow dialog with UiCtlDlgProc subclassed.
4) Docs: correct native_button_pipeline.md 5.2 and ui_controls_catalog.md — the 06-14 CtlBtnProc HAS case 0x38 (FUN_00610580) and case 0x13 preferred-size; the width problem is the frame list, not a missing size handler. Do NOT route checkbox/radio/slider/dropdown/styled-button through the generic item creator; each needs its own recipe (separate work item).

### Open questions (needs live decompile)

To fully lock STABLE free-child positioning (medium confidence on layout mechanics): (1) Decompile the CreateNativeWindow/CContainerFrame parent's OnCtlLayout and EXE FrameSort to confirm whether a free child's position is honored via FrameSort(child,1,prevSibling) vs a raw FrameSetPosition, and the exact FramePosition struct layout (byte offsets of pos vs extent; IFrame::CRect at frame+0xD0). (2) Confirm which UIMessage/path writes ICtlBtn::Property+0x24/+0x28 (the preferred-size fields case 0x13 reads) — none of the visible cases in 0x0060f4f0 write them, so FrameSetSize likely writes the frame rect, not Property; decompile the FrameSetSize path and CtlBtnProc callers. (3) Confirm EXE UiCtlDlgProc @ 0x00876880 is a valid OnFrameNotify subclass for a plain (non-dialog) container and that CreateNativeWindow hasn't already installed a conflicting subclass (avoid double-subclass) — decompile 0x00876880 and the window-create subclass call. Already RESOLVED via decompile: CtlBtnProc identity/self-size (0x38=FUN_00610580, 0x13=Property+0x24/+0x28), solid-paint colors, Property size 0x2C, crash-safe base thunk_FUN_00647170, and CtlFrameListCreateItem (0x00612900) = FrameMsgSend 0x57.

---

## Checkbox — the REAL proc is IUi::UiCtlBtnProc + style 0x8000 (GWCA CreateCheckboxFrame), NOT UiCtlBtnToggleProc and NOT CtlBtnProc+0x10000

**Verdict:** confirmed &nbsp; **Confidence:** high

### Root cause

The in-client "checkbox identical to flat_button" failure had three compounded errors, all in the C++ helper, none in Python: (a) WRONG PROC — the helper routed checkbox/radio to the flat CtlBtnProc (EXE 0x0060f4f0), which has no checkbox art, so it renders like flat_button; (b) WRONG FLAG — it used item_flags 0x10000 instead of the checkbox style bit 0x8000 that UiCtlBtnProc's paint branch tests; (c) WRONG CREATION PATH — it created the control as a frame-list ITEM via AddControlItemByFrameId/CtlFrameListCreateItem, which stretches items full-width AND skips UiCtlBtnProc's class-init (msg 4 base-class wiring + msg 5 s_btnCheckImageList build), so no art, no base chain, no persistent checked state. The correct proc (UiCtlBtnProc) only becomes a working checkbox when created through CreateUIComponent (as a real child) with 0x8000 set, because that path runs class-init.

### Verified recipe

REAL working GW checkbox (the one GWCA already ships and that the decompile confirms):

- PROC: IUi::UiCtlBtnProc — WASM ram:80df1d1e, EXE 0x00877e60 (verified FUN_00877e60 this session). One self-contained FrameProc. Resolve via Scanner::FindAssertion("UiCtlBtn.cpp","!s_btnCheckImageList") -> ToFunctionStart (already done in UIMgr.cpp:1421 as ButtonFrame_Callback). Do NOT use CtlBtnProc (flat 0x0060f4f0) and do NOT use UiCtlBtnToggleProc (0x00886370).

- FACTORY: CreateCheckboxFrame (UIMgr.cpp:2184) = CreateButtonFrame(parent_frame_id, component_flags | 0x8000, child_index, name_enc, label) -> CreateUIComponent(...ButtonFrame_Callback...). Create as a real CHILD of a managed window/GroupHeader, NOT as a frame-list item.

- FLAGS: base 0x300 (F_VISIBLE|F_ENABLED) OR 0x8000 (checkbox style bit). Decompile case 1 gates the box/check art on FrameTestStyles(frame,0x8000). NOT 0x10000, NOT 0x20000.

- CHILD INDEX: auto-increment past existing children (CreateButtonFrame loop at UIMgr.cpp:2042-2046). No manual image list, no FrameSetSize needed for the box itself.

- IMAGE LIST: none passed manually. UiCtlBtnProc owns s_btnCheckImageList (EXE global 0x010819cc / DAT_010819cc). Decompile case 5 (class-init) builds it via FrameImageListCreate (FUN_0062d790(0x11,7,0x12,...)) guarded by the !s_btnCheckImageList assert (FUN_00487a80(0x45)); case 6 tears it down. It initializes lazily on first creation through the CreateUIComponent path — which is why the frame-list-item path produced no art (class-init never ran).

- BASE CLASS: auto-wired. Decompile case 4 (OnFrameClassInitialize) sets the base proc = FUN_0060f4f0 (flat CtlBtnProc), which owns the persistent checked bit and click/toggle. Default/unhandled msgs delegate to it via FrameMsgCallBase (thunk_FUN_00647170). Because CreateUIComponent runs class-init, the base chain exists, so create/destroy/input delegation is safe (unlike the single-proc frame-list path).

- CHECKED STATE: read via CtlBtnIsChecked(frame) = SendFrameUIMessage(frame,0x58,0,&out); checked=(out==1). Set via SendFrameUIMessage(frame,0x57,(void*)checked,null) (GWCA CheckboxFrame::IsChecked @ UIMgr.cpp:3761 / SetChecked @ :3767). User click auto-toggles (base handles it). Do NOT use msg 0x59 (that is the flat-button "pushed" bit, not the checkbox state).

UiCtlBtnToggleProc (0x00886370) is a SEPARATE box-art toggle (uses a different image list 0x00c01b8c and a two-HFrameImageList payload, needs its TCtlInstance base); it is NOT the checkbox to use and is unsafe to cold-create — treat like Slider/Dropdown and abandon single-proc creation.

### C++ fix plan

In include/py_ui.h and vendor/gwca/Source/UIMgr.cpp:
1) STOP routing checkbox/radio to the flat proc: remove "checkbox"/"radio" from the ResolveCtlBtnProc branch in BOTH AddControlItemByFrameId (~line 4547) and ResolveNamedControlProc (~line 4593). Remove any use of item_flags 0x10000 for checkboxes.
2) Route the checkbox helper to the existing CreateCheckboxFrame (UIMgr.cpp:2184) = CreateButtonFrame(parent, component_flags|0x8000, child_index, name_enc, label) with ButtonFrame_Callback = IUi::UiCtlBtnProc (already resolved at UIMgr.cpp:1421 via "!s_btnCheckImageList"). Pass component_flags = 0x300; the helper ORs 0x8000.
3) Create it as a DIRECT CHILD of a real window/GroupHeader via CreateUIComponent with an auto-incremented child_index (loop already at UIMgr.cpp:2042-2046). Do NOT create via AddControlItemByFrameId/CtlFrameListCreateItem (frame-list item path) — that is what causes full-width stretch and skips class-init.
4) Do NOT FrameSetSize the checkbox box (the proc self-sizes its square); the label sizing is separate.
5) State API: keep CheckboxFrame::IsChecked (msg 0x58) / SetChecked (msg 0x57) unchanged — confirmed correct. Add IsCheckedByFrameId (msg 0x58); do NOT reuse the flat-button IsButtonPushedByFrameId (msg 0x59) for checkboxes.
6) Do NOT register IUi::UiCtlBtnToggleProc (0x00886370) via CreateUIComponent — it needs its TCtlInstance base + a two-handle image-list payload + the warm 0x00c01b8c global; abandon single-proc creation for it like SliderFrame/DropList.

### Open questions (needs live decompile)

Resolved this session (decompiled FUN_00877e60): 0x8000 selects the checkbox-art paint branch (case 1), s_btnCheckImageList (0x010819cc) is lazily built in class-init (case 5) and torn down in case 6, and the base CtlBtnProc (0x0060f4f0) is registered in class-init (case 4). No Ghidra work blocks the checkbox fix.

Still open (orthogonal to proc selection, blocks final in-client polish): (1) LAYOUT — root failure #1 is unsolved: frame-list items stretch full width, and the direct-child attempt (CreateControlChildByFrameId + FrameSetPosition) did not apply positions (children overlapped). Need the window/GroupHeader child positioning/layout mechanism (which UIMessage or layout-manager frame drives child geometry) so multiple CreateUIComponent children lay out instead of overlap. (2) Confirm SetChecked semantics: GWCA uses msg 0x57 to set; verify against the base CtlBtnProc (0x0060f4f0) that 0x57 sets and 0x58 gets the persistent checked bit (decompile FUN_0060f4f0 msg 0x57/0x58) — non-blocking. (3) If a native box-art toggle (UiCtlBtnToggleProc 0x00886370) is ever required, still need its TCtlInstance parent (EXE FUN_0056b810 case 9) and the warm 0x00c01b8c image-list global — deferred, not needed for the checkbox.

---

## Radio button — REAL mechanism (mutually-exclusive toggle group)

**Verdict:** likely &nbsp; **Confidence:** high

### Root cause

Our "radio" was created as a frame-list ITEM using CtlBtnProc + item_flags 0x10000 — i.e. aliased to flat_button. It rendered identically to flat_button (wide, untextured, plain) and had NO radio behaviour because the parent (the managed frame list) does NOT carry style 0x100000, so ICtlBtn::Click step (4) parent test fails and the sibling-clearing enumeration never runs → the items are just N independent toggle buttons, not a mutually-exclusive group. (Compounded by: frame list stretches items full-width, flat proc has no art, and the item-flag 0x10000 → runtime style-word 0x10000 translation is itself unverified.) Angle B's diagnosis is correct and is now proven against the decompiled engine.

### Verified recipe

A GW radio group is EMERGENT, not a dedicated proc. Confirmed by decompiling ICtlBtn::Click (WASM ram:80dc36b3): on click the engine (1) FrameIsEnabled → bail if disabled; (2) if FrameTestStyles(self,0x10000) [TOGGLE] → *property ^= 1, invalidate, scheduleSize, NotifyParent((bit&1)|8) i.e. 8=checked/9=unchecked; (3) if FrameTestStyles(self,0x80000) [MOMENTARY] → *property |= 1, NotifyParent(8); (4) parent = FrameGetParent(self); if FrameTestStyles(parent,0x100000) [RADIO parent] → it runs TWO sibling sweeps FrameEnumChild(parent,6,...) and FrameEnumChild(parent,5,...), and for each sibling that FrameHasClass(child,&DAT_ram_00000a7c) [CtlBtn class] it FrameMsgSend(child,0x57,0,0) to clear that sibling's toggle bit (stopping at frames that themselves carry 0x100000) → this is the mutual exclusion, done entirely in-engine; (5) fallback NotifyParent(self,7)=push always. So the REAL recipe = a PARENT frame carrying style 0x100000 whose children are CtlBtn-class (0xa7c) toggle buttons (runtime style 0x10000); the engine auto-deselects siblings on click. Read state by polling each child pushed bit (msg 0x59) or subclassing the parent OnFrameNotify (8=checked). PRAGMATIC BUILDABLE EQUIVALENT (confirmed to render in-client, no image-list/layout blockers): a SELECTABLE frame list (CreateSelectableScrollableContentByFrameId → text rows via AddTextItemToFrameListByFrameId); its single-selection semantic (SetSelection clears the prior row) gives the same mutual exclusion, polled via GetFrameListSelectionByFrameId (msg 0x67).

### C++ fix plan

1. Stop aliasing radio → flat_button: remove the "CtlBtnProc + 0x10000 item as radio" path from the generic AddControlItemByFrameId usage. 2. PRIMARY (ship this — renders, safe cold): add CreateRadioGroupByFrameId(window_id, options[], default_index) composing existing verified helpers — CreateSelectableScrollableContentByFrameId (py_ui.h ~4465) + AddTextItemToFrameListByFrameId (~4408) per option + GetFrameListSelectionByFrameId (~4487) to read; add SetFrameListSelectionByFrameId(list_id, child_code) sending list msg 0x66 for default_index. Exclusion is free via the selectable list single-selection semantic. 3. FAITHFUL-NATIVE (optional, gated, matches Angle B true mechanism): add a NEW FrameAddStyleByFrameId(frame,0x100000) helper (none exists in GWCA — confirmed) to OR the radio style onto a real parent frame; create each option as a CtlBtn-class toggle child (style 0x10000), verify the runtime style word post-create (create-flag→style translation unverified) and OR 0x10000 directly if absent; flat CtlBtnProc children have no msg 0x38 → force FrameSetSize; round-radio glyph art needs UiCtlBtnProc/checkbox image list (s_btnCheckImageList) so gate behind an EnsureBtnCheckImageList warm-up (guard _DAT…857c==NULL) and fall back to PRIMARY when cold. Bind new funcs in src/py_ui.cpp and stubs/PyUIManager.pyi.

### Open questions (needs live decompile)

Live Ghidra still needed only to make the FAITHFUL-NATIVE path safe (the PRIMARY selectable-list path needs none): (a) EXACT semantics of CtlBtn msg 0x57 in the sibling-clear context — decompile CtlBtnProc (WASM ram:80dbe9be / EXE entry 0x0060f4f0) case 0x57 to confirm it CLEARS/sets-unchecked rather than blindly flipping bit0 (docs are inconsistent: §4 says "flips bit0", §5 says "set one on"; a blind flip would wrongly turn already-off siblings ON). (b) Map EXE addresses for ICtlBtn::Click, FrameEnumChild, FrameHasClass, FrameGetParent in "/Gw.exe (06-14)" (EXE is stripped — only WASM carries these symbols; ICtlBtn::Click confirmed at WASM ram:80dc36b3). (c) Verify item/create-flag 0x10000 lands as runtime frame style 0x10000, and that a bare 0x100000 parent frame can be created with CtlBtn children positioned without the still-unsolved window child-layout problem (children previously overlapped).

---

## Slider (CtlSliderProc base 0x00615fe0 + wrapper UiCtlSliderProc 0x0087f440): correct creation recipe and the click-crash root cause, reconciled and decompile-verified against /Gw.exe (06-14).

**Verdict:** confirmed &nbsp; **Confidence:** high

### Root cause

TWO independent real defects in the C++ frame-list-item path (AddControlItemByFrameId -> CtlFrameListCreateItem 0x00612900, which merely sends msg 0x57 to the FrameList — it does NOT run a typed-control FrameCreate):

(1) WRONG userData -> garbage range + wide render. The item path passes BuildStandaloneLiteralEncodedTextPayload("Slider") as userData. CtlSliderProc msg 9 reads userData as int32[2] {min,max}, so min=0x01070108, max=0x006C0053 (max<min). msg 0x38 size-query makes width proportional to (max-min) -> intrinsically huge, compounding the frame-list's own full-width row stretch = "extremely wide". A later SetValue would also trip the 0x57 min<=v<=max assertion.

(2) CLICK CRASH = base-class-delegation depth assertion, NOT a missing control-instance slot. Decompile settles the disagreement between the angles: the create succeeds and the slider renders, which PROVES param_1[2] (the control-data slot) is valid — case 9 writes `*piVar1 = CInstance` and later size-query reads it back without faulting. So Angle A's "item path never provides param_1[2] -> deref crash" is refuted. The actual mechanism (Angle B, now positively confirmed): CtlSliderProc's click handlers (0x24/0x2c/0x2e) run and then fall through to FrameMsgCallBase (thunk_FUN_00647170 -> FUN_00647170), which walks the frame's subclass base table and asserts FUN_00487a80(0x223) if `*(uint*)(frame+0xB0) <= param_1[5]` (and 0x24b deeper). The item path registers only the single resolved base proc and never runs the msg-4 base-declaration cascade a typed FrameCreate performs, so frame+0xB0 (subclass depth) is too shallow. Crucially, FUN_00647170 EARLY-RETURNS when `param_1[1]==9` (create) or `==0xb` (destroy) — those messages skip the depth assertion entirely — which is exactly why creation did NOT crash but the FIRST non-exempt message (a click, 0x24) does. Contributing structural mismatch: the base notifies its parent via FUN_0062ee80 with slider codes 7/9, but the item's parent is a generic FrameList with no slider-aware OnFrameNotify.

### Verified recipe

The game never builds a slider as a frame-list text item; it builds a real typed-control frame (via the CCtlLayout / LayoutSliders template path) whose msg-4 cascade installs the full subclass base chain, then layers the textured wrapper. Buildable recipe:

1) PROC CHAIN: create the frame with a typed-control FrameCreate whose registered base is CtlSliderProc (EXE 0x00615fe0), then FrameNewSubclass the WRAPPER UiCtlSliderProc (EXE 0x0087f440) on top. Confirmed msg-4 handshake: wrapper case 4 does `*(code**)param_2[3]=FUN_00615fe0` (declares base=CtlSliderProc); CtlSliderProc case 4 does `*(code**)param_2[3]=FUN_006123a0` (declares its own base). The typed-control FrameCreate MUST run this msg-4 cascade so the frame's subclass table (frame+0xA8, count at frame+0xB0) holds the whole chain [wrapper -> CtlSliderProc -> FUN_006123a0 -> ...]. This is precisely what lets clicks survive FrameMsgCallBase (see root_cause). Wrapper msg-1 paints the GW art: textured bar via FUN_0062b8e0 (template PTR_DAT_00bf4694, enabled/disabled pair) + thumb via FUN_0062b3e0 (PTR_DAT_00bf469c). Without the wrapper you get the base's plain solid-gray paint.
2) PARENT: a real dialog/window frame that owns an OnFrameNotify dispatcher, NOT a bare FrameList. On drag the base calls FUN_0062ee80 (NotifyParent) with codes 7 (grab, msg 0x24 via FUN_00616690) and 9 (value-changed, msg 0x2e) carrying the computed value; the parent must consume these.
3) FLAGS: 0x300 (F_VISIBLE|F_ENABLED). Orientation bit 0x2000 is optional and is set by the APP consumer's own subclass msg-4 (FUN_004d49a0 does `*(uint*)param_2[1] |= 0x2000`), NOT by the wrapper — the base merely TESTS it via FUN_0062fe20(frame,0x2000) in the mouse/size cases.
4) userData AT CREATE = pointer to int32[2] {min,max}. CtlSliderProc case 9 reads `puVar2=*param_2; if(puVar2){ CInstance[+0xC]=puVar2[0]; CInstance[+0x10]=puVar2[1]; }`. NEVER pass an encoded-text payload. If null, min/max stay 0 and you MUST send SetRange immediately.
5) SIZE: force explicit FrameSetSize (~150x18). Do not rely on msg 0x38 self-size — it computes width proportional to (max-min): `local_20=(float)(*(iVar8+0x10)-*(iVar8+0xc)); *(float*)param_2[2]=local_20*...*_DAT_009407b0`.
6) VALUE PROTOCOL (confirmed): 0x56 SetRange, param_2[0]=min, param_2[1]=max -> CInstance+0xC/+0x10 then invalidate; SEND FIRST. 0x57 SetValue, value passed BY VALUE as (int)param_2, asserts min<=v<=max (FUN_00487a80(0x18a)/(0x18b)) — out of range = fatal assert; sets position=(v-min)/(max-min). 0x58 GetValue, param_2=int* out (null-check assert 0x181), returns min+round(position*(max-min)). Never send 0x5E (no caption in the switch).
7) CInstance = 0x30 bytes (allocated msg 9 at CtlSlider.cpp:0x233): +0x08 frame handle, +0x0C min i32, +0x10 max i32, +0x14 position float(0..1), +0x2c HObject freed on destroy (msg 0x0B).

### C++ fix plan

All changes in C:\Users\Apo\Py4GW.
(A) include/py_ui.h AddControlItemByFrameId (~4538) and ResolveNamedControlProc (~4590): REMOVE the "slider" case from the generic item path (and likewise dropdown/edit/progress/tabs — every multi-layer typed control). Do not encode a caption into userData for them and do not resolve/register the bare base proc as a list item. Make the branch delegate to the dedicated creator below or hard-error.
(B) Add ResolveUiCtlSliderProc() resolving the WRAPPER 0x0087f440 (byte pattern "\x55\x8B\xEC\x83\xEC\x18\x53\x8B\x5D\x08\x56\x57\x8B\x43\x04\x48\x83\xF8\x58").
(C) Add a dedicated direct-child creator (mirror CreateControlChildByFrameId ~4617, but slider-specific): use the existing typed path — vendor/gwca/Source/UIMgr.cpp CreateSliderFrame (~2279, SliderFrame_Callback=CtlSliderProc) + py_ui.h CreateSliderFrameByFrameId (~3361) — calling GW::SliderFrame::Create(parent, 0x300, child, ...) with a `int32 range[2]={min,max}` pointer as userData (NOT encoded text). Immediately after: FrameNewSubclass_Func(frameId, ResolveUiCtlSliderProc()/*0x0087f440*/, 0) to layer the texture (SliderFrame_WrapperCallback + FrameNewSubclass_Func are already resolved in the code but the item path bypasses them). Then FrameSetSize(~150,18). Then SendFrameUIMessage 0x56 with &range (SetRange) FIRST, then 0x57 with (int)initial (SetValue). GetValue = 0x58 with &int out.
(D) Parent must be a real managed window/dialog (CreateNativeWindow) whose notify dispatcher consumes slider notify codes 7/8/9 — NOT a scrollable FrameList. Do NOT send msg 0x5E and do NOT invoke the caption/button-family size block.
(E) If a list-item placement is ever required, after create verify in-client that frame+0xB0 (subclass count) equals the full hierarchy depth; if not, the msg-4 cascade did not run and the list-item path is unusable for the slider (guaranteed 0x223 assert on click).

### Open questions (needs live decompile)

Root cause and fix are decompile-confirmed; remaining items are optional hardening, none block implementation. (1) Decompile the FrameList msg-0x57 handler (reached from CtlFrameListCreateItem 0x00612900 via FUN_0062ef40) in /Gw.exe (06-14) to positively show it registers only the single item proc and does NOT run the typed-control msg-4 base cascade (concrete proof frame+0xB0 is too shallow). (2) Confirm the deeper base link FUN_006123a0 -> FUN_0062c370 and that 0062c370 is the CtlFrame primitive (not load-bearing for the fix). (3) Optional: live debugger click to confirm the fault lands at FUN_00487a80(0x223)/(0x24b) inside FUN_00647170 rather than in the parent-notify FUN_0062ee80/FUN_00647fc0 path.

---

## Styled GW button (IUi::UiCtlBtnProc @ EXE 0x00877e60 / WASM ram:80df1d1e) — why it renders nothing and the real 9-slice recipe

**Verdict:** confirmed &nbsp; **Confidence:** high

### Root cause

Deterministic missing style bit 0x40000. UiCtlBtnProc's paint (msg 0x01) sub-pass 0 wraps the ENTIRE 9-slice body in `if (FUN_0062fe20(frame,0x40000) != 0)` (FrameTestStyles on the frame style word at +0x190); the size-query (case 0x15) is gated identically. The current helper AddControlItemByFrameId passes item_flags=0, and the frame list ORs 0x300, so the effective style is 0x300 with bit 0x40000 CLEAR -> body + size-query are skipped every paint -> nothing draws. This is NOT a crash (creation and cold paint succeed via base CtlBtnProc) and NOT primarily the image list. Real in-game consumers use 0x40300 (Trade) / 0x40302 (Store) = 0x40000 | 0x300, independently confirming the requirement. A distinct secondary gate: the state-overlay/checkbox layer (sub-pass 1) reads the cold image list DAT_010819cc and adds nothing extra when null — but that only removes the hover/press/check art, not the body.

### Verified recipe

PROC: UiCtlBtnProc @ EXE 0x00877e60 (WASM ram:80df1d1e). Resolve build-independently: Scanner::FindAssertion("UiCtlBtn.cpp","!s_btnCheckImageList",0,0) -> ToFunctionStart(addr,0xFF). Base class = CtlBtnProc (FUN_0060f4f0), reported via msg 0x04; unhandled msgs go to thunk_FUN_00647170 (FrameMsgCallBase, a static call to base — LOW crash risk, unlike Slider/Dropdown which need a registered child/base the single-proc path never sets up).

CREATE AS A FRAME-LIST ITEM (the confirmed managed-parent path), with the load-bearing style bit set:
1. CreateNativeWindow -> CreateScrollableContentByFrameId(window,0) -> frame_list_id.
2. proc = ResolveUiCtlBtnProc() (assertion scan above).
3. encoded = BuildStandaloneLiteralEncodedTextPayload(text)  (raw wide string crashes).
4. CtlFrameListCreateItemByFrameId(frame_list_id, item_flags, insert_index, (uint32_t)proc, encoded), with item_flags = 0x40000 | (checkbox?0x8000:0) | (min120?0x4:0x2). The list FrameCreates the child with style = item_flags|0x300 (verified in FrameList_Callback FUN_00612c80 case 0x57), so 0x40000 alone -> style 0x40300; +0x2 -> 0x40302 (the real Store value, 100px min width); +0x4 -> 120px. NEVER pass item_flags=0 (that yields style 0x300, the bug).
5. FrameContentInvalidate(item) after create so it repaints.

SIZE/LAYOUT: item self-sizes on msg 0x38 (min-width clamp from style bits 0x2/0x4). Because the frame list stretches items to full width, also issue an explicit FrameSetSize after create to avoid full-width stretch.

TEXTURE / 9-SLICE: body art draws cold from static .data pointers PTR_DAT_00bf4560..0584 with template coords &DAT_00bf4510 (FUN_0062b8e0 = FrameContentAddImageTemplate) — it needs ONLY the 0x40000 style bit, no image list. The per-class image list s_btnCheckImageList (DAT_010819cc @ EXE 0x010819cc / WASM _DAT_ram_005a857c) is needed ONLY for the hover/press/checked state OVERLAY (sub-pass 1, FUN_0062b290) and the checkbox glyph. Gate on *(uint32_t*)0x010819cc != 0 (i.e. only show while a store/merchant/storage/guild window is open, which the game builds+keeps the list alive for); if null, fall back to flat CtlBtnProc/CtlTextBtnProc. Do NOT self-build via msg 0x05 — a later real store-open re-runs case 5, finds the global non-null, and hits assert(0x45)/FUN_00487a80 (no-return) = latent crash.

CLICKS: base CtlBtnProc drives it — pushed-state readable via msg 0x59; it emits FrameMsgNotifyParent(parent, 7/8/9). Capture via a parent subclass with the real dialog OnFrameNotify (UiCtlDlgProc @ 0x00876880) or build the list selectable and poll GetFrameListSelectionByFrameId.

### C++ fix plan

In include/py_ui.h:
1) ResolveUiCtlBtnProc(): FindAssertion("UiCtlBtn.cpp","!s_btnCheckImageList",0,0) -> ToFunctionStart(addr,0xFF) (== 0x00877e60 on 06-14). Cache it.
2) In AddControlItemByFrameId (and the parallel ResolveNamedControlProc / direct-child path) special-case control=="styled_button"/"checkbox": OR 0x40000 into item_flags BEFORE CtlFrameListCreateItemByFrameId (add 0x8000 for checkbox; choose 0x2 default / 0x4 for 120px min width). Currently (~line 4573) item_flags is passed unchanged (=0 -> 0x300) — this single OR is the deterministic fix for the invisible body.
3) ResolveBtnCheckImageListGlobal() + IsBtnCheckImageListReady(): resolve s_btnCheckImageList build-independently by scanning the `mov [global],eax` immediately after the FUN_0062d790/FrameImageListCreate call in the proc's msg-5 block (06-14 addr 0x010819cc); IsReady returns *(void* const*)addr != nullptr. In the styled-button branch, if !IsBtnCheckImageListReady(): log and transparently fall back to ResolveCtlBtnProc() flat button (no image dependency). Do NOT add a msg-0x05 force path (latent store-open assert(0x45) crash).
4) After creating the styled item, call FrameContentInvalidate(item); keep an explicit FrameSetSize (e.g. 120,22) to defeat the frame list's full-width stretch, plus the existing msg-0x5E/0x5F caption handling.
Bind in src/py_ui.cpp as before; no new stub surface needed — only the style-flag semantics and the image-list gate.

### Open questions (needs live decompile)

None block the styled-button fix. Optional byte-exact confirmations (not required): (a) decompile FrameList_Callback FUN_00612c80 case 0x57 to visually confirm the child FrameCreate style arg = item_flags|0x300 (strongly implied and consistent with observed 0x300 behavior; verified by Angle A); (b) decompile a real caller (CShop/CTrade OnFrameCreate) to confirm the exact constant 0x40300 vs 0x40302 min-width bit choice. SEPARATE, still-open topic (root failure #1, out of scope here): the frame-list full-width stretch / direct-child positioning (CreateControlChildByFrameId + FrameSetPosition not applying) is not yet reverse-engineered — needs the window/list layout code decompiled independently of this button work.

---

## Dropdown (classic CtlDropList) — verified two-layer creation recipe, crash root cause, populate/read

**Verdict:** likely &nbsp; **Confidence:** high

### Root cause

Two independent defects combined. (1) WRONG PROC/PATH: our helper resolved the dropdown proc via FindAssertion and registered it as a single frame-list ITEM (CtlFrameListCreateItem). The frame-list-item path registers one raw function pointer with no subclass/base chain, so the wrapper's delegated create (msg 0x09 -> FrameMsgCallBase) reaches the generic frame base instead of CtlDropListProc; the 100-byte CtlDropList::Prop and the child listbox are never allocated, and the wrapper's paint/size then dereference the missing Prop/child -> null-deref crash. GW never creates a dropdown this way — it creates it as a DIRECT managed child (FrameCreate type 0xaef) so the wrapper's msg-0x04 self-registration wires the base. (2) WRONG ADDRESS in the catalog: 0x0087f5f0 is NOT the base — live decompile shows FUN_0087f5f0 is only 0x1F9 bytes (0x0087f5f0-0x0087f7e9), a small C-API dispatch shim with no paint and no FrameMsgCallBase. The real base is FUN_006144e0 (~0xE1D bytes) and the styled wrapper is FUN_00878d90. Angle B's mapping 0x0087f5f0==base was incorrect; Angle A's address analysis is confirmed.

### Verified recipe

The classic GW dropdown is a TWO-LAYER frame control. Both layers are now pinned in the injected EXE ("/Gw.exe (06-14)") by live decompile and match the WASM named symbols:

- STYLED WRAPPER = IUi::UiCtlDropListProc = EXE FUN_00878d90 @ 0x00878d90 (WASM ram:80e47ca4). Verified: msg 0x01 paints the box via image templates FUN_0062b8e0(PTR_DAT_00bf45cc/c4/c8 chosen by state) + the arrow via FUN_0062b3e0(PTR_DAT_00bf45d0, flag 0x100000) + caption via case 0x64 FUN_0062bb30(text); msg 0x04 does `*(code**)param_2[3] = FUN_006144e0;` i.e. SELF-REGISTERS the base; DEFAULT case calls FrameMsgCallBase (thunk_FUN_00647170) into that base. NOTE: its paint uses statically-initialized PTR_DAT_* image templates (no DAT==0 lazy-guard like the styled button), so it is NOT subject to the cold-image-list null-deref that kills styled buttons.
- ENGINE BASE = CtlDropListProc = EXE FUN_006144e0 @ 0x006144e0 (WASM ram:80e3c9a3). Verified: msg 0x09 create -> FUN_00615670 which calls MemAlloc FUN_0047f340("P:\\Code\\Engine\\Controls\\CtlDropList.cpp", 0x11c) allocating the ~100-byte CtlDropList::Prop, stores it at frame+? (*(int**)param_1[2]=Prop), and can pre-parse a wchar_t option-list from the create payload. It self-handles paint(0x01, plain solid-color rects), size(0x38), add, get/set selection, open, and registers ITS own base FUN_006123a0 on msg 0x04.

GROUND-TRUTH CREATE PATH (from real consumer IUi::Controls::CDistrictSelectionDialogFrame::OnFrameMsgCreate, WASM ram:8135729e): each dropdown is a DIRECT CHILD of the managed dialog frame:
  droplist = FrameCreate(dialogFrame, 0x300, childId, <wrapper type 0xaef == EXE FUN_00878d90>, 0, 0);   // 0x300 = F_VISIBLE|F_ENABLED, userData=0, name=0
  CtlDropListSetListMaxHeight(droplist, 150.0f);
The wrapper's msg 0x04 self-registers base FUN_006144e0 -> FrameMsgCallBase chain established -> base msg 0x09 allocs the Prop. This is NOT a frame-list item and NOT a bare-proc registration.

BUILDABLE RECIPE:
1. window = CreateNativeWindow(...) (managed root/dialog frame).
2. dropId = FrameCreate(window, 0x300, childId, FUN_00878d90 /*styled wrapper*/, 0, 0). (For plain/unstyled-but-functional, pass FUN_006144e0 base directly instead.)
3. Optionally CtlDropListSetListMaxHeight(dropId, 150.0f).
4. Set width/position yourself via FrameSetSize/FrameSetPosition on dropId (GW's dialog does this in OnFrameMsgSize; the control self-sizes only HEIGHT via msg 0x38). This also cures the 'extremely wide' problem, which was frame-list row-stretching.
5. Populate: per option SendFrameUIMessage(dropId, 0x56, &{wchar_t* TextEncode(text); void* userValue}). (0x57 is the same add with the alternate insert/sort flag.)
6. Default selection: SendFrameUIMessage(dropId, 0x61, index) — writes Prop+0x58 and forwards child listbox msg 0x68.
7. Read selection: SendFrameUIMessage(dropId, 0x5c, &out) — out = *(Prop+0x58). Count: msg 0x5a -> *(Prop+0x08). Open (lazy-builds child listbox flags 0x128 via FUN_00614230): msg 0x5f.

MESSAGE MAP (verified by EXE decompile of FUN_006144e0): 0x09 create(Prop alloc, CtlDropList.cpp), 0x04 register base, 0x01 plain paint, 0x38 size, 0x56/0x57 add {text,value}, 0x5a getCount(Prop+0x08), 0x5c getSelection(Prop+0x58), 0x61 setSelection(Prop+0x58, forwards child 0x68), 0x5f open. The child listbox is created lazily on open, NOT at create time.

RESOLVER (stable, no hardcoded catalog address): string "P:\\Code\\Engine\\Controls\\CtlDropList.cpp" -> xref -> FUN_00615670 -> its caller = base FUN_006144e0; then DATA xref to FUN_006144e0 -> FUN_00878d90 = the styled wrapper (the only site storing the base ptr, its msg-0x04 handler). Anchor on CtlDropList.cpp, NOT "UiCtlDropMenu.cpp".

### C++ fix plan

1) STOP the crash: remove "dropdown" (and likewise slider/progress/groupheader — the other multi-layer controls) from the generic single-proc frame-list-item path in AddControlItemByFrameId / ResolveNamedControlProc (include/py_ui.h ~4557/4599), or gate behind an explicit allow_multilayer flag defaulting false. Do NOT resolve via the UiCtlDropMenu.cpp assertion and do NOT reuse 0x0087f5f0.
2) Add ResolveCtlDropListWrapperProc() and ResolveCtlDropListBaseProc(): anchor on the string "P:\\Code\\Engine\\Controls\\CtlDropList.cpp" -> xref FUN_00615670 -> caller FUN_006144e0 (BASE) -> data-xref -> FUN_00878d90 (styled WRAPPER). Bake the offsets from the 06-14 EXE as fallback: base=0x006144e0, wrapper=0x00878d90.
3) Add CreateDropdownChildByFrameId(window_id, child_index): FrameCreate(window_id, 0x300, child_index, wrapperProc /*FUN_00878d90*/, nullptr, nullptr) as a DIRECT child of a managed CreateNativeWindow/dialog frame (NOT via the frame list, NOT CreateUIComponent-into-a-raw-container). Then FrameSetSizeByFrameId + FrameSetPositionByFrameId (the control self-sizes only height via msg 0x38), then optionally CtlDropListSetListMaxHeight. Provide a base-proc variant (FUN_006144e0) for a plain unstyled dropdown when styling is not wanted.
4) Populate/read helpers via SendFrameUIMessage on the dropdown frame (message IDs verified, no C-API twin needed): AddDropdownOption -> msg 0x56 with payload {wchar_t* TextEncode(text); void* value}; SetDropdownSelection -> msg 0x61 (index); GetDropdownSelection -> msg 0x5c (out=*(Prop+0x58)); GetDropdownCount -> msg 0x5a (out=*(Prop+0x08)); Open -> msg 0x5f.
5) Precondition guard: parent MUST be a real managed dialog/window frame (carries OnFrameNotify + the subclass dispatch that delivers msg 0x04 self-registration). A bare CContainerFrame parent will still fail the base's expectations. Keep the existing GW::DropdownFrame::AddOption(0x57)/old CreateDropdownFrameByFrameId CreateUIComponent body OUT of the render path.

### Open questions (needs live decompile)

Remaining items need in-client validation, not more Ghidra (creation/populate/read pipeline and both proc addresses are fully decompile-confirmed):
1) CHILD LAYOUT (the real blocker, shared root failure #1): FrameSetPosition/FrameSetSize on direct children of our custom CreateNativeWindow did NOT apply in a prior attempt (children overlapped). GW positions dialog children by handling the parent's OnFrameMsgSize/layout; we need to RE how the managed window applies child geometry (decompile CDistrictSelectionDialogFrame::OnFrameMsgSize, WASM near ram:8135xxxx, and the EXE window layout path) OR confirm a working FrameSetPosition sequence — otherwise the dropdown renders but is mispositioned/overwide.
2) Confirm a plain CreateNativeWindow root is a sufficient managed parent for the wrapper's msg-0x04 self-registration, or whether an explicit FrameNewSubclass(window, dialogSubclass) must run first.
3) In-client smoke test: create the dropdown as a direct managed child with FUN_00878d90, add 3 options, read selection — verify no crash and correct read (this is task #13). Optionally confirm the base-alone-as-item hypothesis (Angle B) does not crash, but that path is deprioritized vs the ground-truth direct-child path.

---

## Editable text control (CtlEditProc @ 0x00888aa0) — correct creation recipe, render/caret path, and text get/set

**Verdict:** likely &nbsp; **Confidence:** high

### Root cause

The historical crash / dead-and-stretched box comes from registering the wrong proc as the component callback (and from the frame-list-item path). CtlEditProc (0x00888aa0) is only the render+caret+input subclass; its switch has NO case 9 (OnFrameCreate) and NO case 4 (class vtable), so registering it as the primary component callback attaches nothing, sets no class vtable, and builds no CCtlEdit value context. A subsequent value message (0x5E/0x57/0x5A) or a GetValue read of ctx+0x48 then hits uninitialized/garbage state -> silent no-op or fault. Decompiling the real game builder FUN_0051b580 proves edit boxes are constructed by registering the OUTER procs FUN_008852e0 (full) / FUN_0087d9a0 (simple) through CreateUIComponent (FUN_0062bfc0); those outer procs are what attach CtlEditProc (msg 9), set the class vtable (msg 4 -> 0x00619c50), and expose the value interface (msg 100 -> 0x00b96960). Angle A is correct; Angle B correctly diagnosed the symptoms but chose the wrong callback (CtlEditProc via CreateUIComponent) — CreateUIComponent registers only the proc you pass, it does not itself build the CCtlEdit handler stack.

### Verified recipe

Do NOT register CtlEditProc (FUN_00888aa0 / 0x00888aa0) as the frame's component callback, and do NOT build editable text as a single-proc frame-list ITEM. Build it exactly like the game does (verified by decompiling the real GmChat builder FUN_0051b580 @ 0x0051b580):

PROC (primary component callback): the OUTER CCtlEdit proc FUN_008852e0 (0x008852e0). Verified switch: msg 4 -> installs C++ class vtable *(ctx+0xc)=LAB_00619c50 (0x00619c50, xref'd ONLY by FUN_008852e0); msg 9 (OnFrameCreate) -> FUN_0062f150(frame, FUN_00888aa0, slot 0) attaches CtlEditProc as the slot-0 RENDER/CARET subclass; msg 100(0x64) -> copies a 7-pointer value-interface table from PTR_FUN_00b96960 (0x00b96960) into the caller buffer; default -> base chain (thunk_FUN_00647170). A lighter single-line variant exists: FUN_0087d9a0 (0x0087d9a0, the chat "EditMessage" field) — msg 4 vtable FUN_00603cc0, msg 9 attaches CtlEditProc, else chains. Use FUN_008852e0 for a full get/set/maxlength/readonly edit box.

CREATE: via CreateUIComponent = FUN_0062bfc0(parent_frame, component_flags, child_index, callback_proc, extra=0, label). Real observed usage in FUN_0051b580: full edit `FUN_0062bfc0(parent, 0x892e000, 3, FUN_008852e0, 0, L"EditName")`; simple edit `FUN_0062bfc0(parent, 0x2020000, 2, FUN_0087d9a0, 0, L"EditMessage")`. Parent must be a real window/frame child (CreateNativeWindow child), NOT a frame-list item.

RENDER/CARET (the CtlEditProc subclass, msg id = param_1[1]): case 1 paint has 4 sub-ops on *param_2 — 0=background quad FUN_0062b8e0 (texture PTR_DAT_00bf4700 / PTR_DAT_00bf46fc chosen by focus/read-only via FUN_0056a410), 1=caret FUN_0062b2d0 with DAT_01081d78, 0xc=glyph/cursor FUN_0062b290 with DAT_01081d80 (own assert FUN_00487a80(0x9a)), 0xd=selection FUN_0062b2d0 with DAT_01081d7c. Also handles 0x15 (size query), 0x5f (text draw), 0x60/0x61 (interface). Everything else falls to thunk_FUN_00647170 (chain dispatcher FUN_00647170: walks handlers at ctx+0xa8, count +0xb0, index param_1[5], skips notify 9/0xb).

MATERIALS (caret cluster): DAT_01081d78 (caret) / DAT_01081d7c (selection) / DAT_01081d80 (glyph atlas) are module-static, created ONCE under `if(DAT_01081d78==0)` in CtlEditProc msg 5 (device-init broadcast) and freed in msg 6. The else branch is FUN_00487a80(0x3c) = fatal "!s_editCaretMaterial". GUARD: never send msg 5/6 yourself; only create the control in a live in-game session (a chat/edit box has already run msg 5, so materials are warm). Cold at login/char-select would null-deref. No per-instance image list.

SIZE: neither CtlEditProc nor FUN_008852e0 has a msg 0x38 self-size, so after creation call FrameSetSize (e.g. ~200 x ~20) and set explicit child position.

TEXT I/O (messages, NOT direct field pokes): the game's own accessors send UI messages via FUN_0062ef40 (0x0062ef40, asserts msg>=0x56, then FUN_00647db0+FUN_00647c80 dispatch into the frame's proc chain): SetText FUN_00604b00 -> msg 0x5E; GetText FUN_00603c40 -> msg 0x57; SetMaxLength FUN_00604aa0 -> msg 0x5A. These are the SAME messages py_ui's Get/SetEditableTextValue/MaxLength/ReadOnly helpers send. They are serviced by the CCtlEdit class vtable/value-interface that ONLY the outer-proc (FUN_008852e0) construction installs — hence they work on a properly built frame and are dead on a bare CtlEditProc frame. Post-create like the game: FUN_00604aa0(frame, maxlen) then FUN_00604b00(frame, encoded_text).

### C++ fix plan

1) Repoint the editable-text component-callback resolver from CtlEditProc to the outer proc. Today ResolveCtlEditProc()/EditableTextFrame_Callback resolves 0x00888aa0 via FindAssertion("UiCtlEditBox.cpp","!s_editCaretMaterial"). Add ResolveOuterCCtlEditProc() = 0x008852e0: resolve it as the DATA xref target that (a) is one of CtlEditProc's two data xrefs {0x008852e0, 0x0087d9a0} and (b) whose msg-9 case calls Ui_AttachCurrentHandlerSlot(frame, CtlEditProc, 0) AND whose msg-100 case emits the 7-pointer interface (0x00b96960) / msg-4 sets vtable 0x00619c50 — that uniquely identifies 0x008852e0. Cache it. (Simple fallback proc = 0x0087d9a0 if a lightweight single-line field is wanted.)
2) In CreateEditableTextFrameByFrameId (py_ui.h ~3349/3376) / UI::CreateEditableTextFrame (UIMgr.cpp ~2305), pass callback = ResolveOuterCCtlEditProc() (0x008852e0), NOT CtlEditProc, into CreateUIComponent(parent, flags, child_index, callback, nullptr, label). This is the single change that fixes both the crash and text I/O.
3) Do NOT add AddEditableTextItemToFrameListByFrameId (the single-proc item builder in ui_elements_creation_recipes.md sec.12) — structurally wrong for edit. Editable text must use the CreateUIComponent path as a CreateNativeWindow child, not a frame-list item.
4) After creation: FrameSetSizeByFrameId(id, ~200, ~20) (no msg 0x38 self-size) and set explicit child position (window child-positioning gap applies; fix separately, don't rely on list stretch).
5) Add a session guard: only create in-game (materials warm); refuse/return 0 at login/char-select. Add a comment/assert that our code must NEVER send msg 5 or 6 (msg 5 else-branch = FUN_00487a80(0x3c) fatal "!s_editCaretMaterial").
6) Keep Get/SetEditableTextValue (msg 0x5E set / GetValue), SetEditableTextMaxLength (0x5A), Is/SetEditableTextReadOnly (0x56/0x5B) unchanged — they become functional once the outer proc builds the CCtlEdit context. Initial text must be encoded (BuildStandaloneLiteralEncodedTextPayload). Model post-create after FUN_0051b580: SetMaxLength then SetText.

### Open questions (needs live decompile)

Non-blocking: (1) Exact minimal component_flags for a standalone single-line edit — the decompiled real values are chat-specific: 0x892e000 (full "EditName", FUN_008852e0) and 0x2020000 (simple "EditMessage", FUN_0087d9a0); Angle A's guessed 0x300 is wrong. Start from 0x892e000 for a full edit and trim by testing (bit meanings of 0x892e000 not yet decoded). (2) The precise handler that terminates messages 0x5E/0x57/0x5A/0x56/0x5B — confirmed they are sent (FUN_0062ef40 dispatch) and serviced on outer-proc frames, but the exact vtable slot in the CCtlEdit class object (via 0x00619c50) vs the value-interface table at 0x00b96960 was not individually decompiled; recommended: decompile the 7 functions at PTR_FUN_00b96960 (0x00b96960) and FUN_00647c80 (0x00647c80) to map each message to its accessor. (3) In-client validation still pending (task #13: rebuild DLL + run ui_elements_test) — the recipe is RE-confirmed but not yet rendered live. None block implementing the fix.

---

## ProgressBar (CtlProgress::CProgressFrame::FrameProc @ EXE 0x008812e0 / WASM ram:80f6cf82) — root-cause of the creation crash and the correct build/render/value recipe

**Verdict:** likely &nbsp; **Confidence:** high

### Root cause

WRONG-PROC RESOLUTION (Ghidra-confirmed; this is the proximate crash, and it corrects Angle A's assumption). GWCA/py_ui.h anchor the progress callback on FindAssertion("UiCtlProgress.cpp","!sm_rateArrowImageList") -> ToFunctionStart. The string 0x00b964f4 is referenced ONLY from FUN_00882530 (@0x00882551) and FUN_008828b0 (@0x00882d70) — never from the real proc 0x008812e0. FUN_00882530 decompiles as `void FUN_00882530(void)`: a ref-counted rate-arrow IMAGE-LIST loader (guards DAT_010819f8, sets DAT_010819fc=FUN_0062d790(...), assert path FUN_00487a80(0x16e)). ToFunctionStart therefore yields 0x00882530 (a void(void) loader), which GWCA registers as ProgressBar_Callback. The first lifecycle message (msg 4/5/9) then invokes a void(void) with (FrameMsgHdr*, in, out) and mismatched calling convention -> immediate crash. Compounded (for the item path) by the frame-list full-width stretch. The real proc 0x008812e0 carries no assert-message string of its own (only line-only FUN_00487a80(line) asserts), so it cannot be anchored by an assertion message — which is exactly why the current anchor lands on the loader. Angle A's "missing lifecycle / need to manually send msg 5 and install LAB_00618b70" is unnecessary: the correct proc self-drives msg 4/5/9; the only defect is that the wrong function is being registered.

### Verified recipe

REAL PROC = EXE 0x008812e0 (Ghidra-confirmed: message switch on hdr->message_id, multi-layer over FrameWithValue base &LAB_00618b70 @ 0x00618b70). Create through the typed-component path that already exists: GW::ProgressBar::Create -> py_ui.h CreateProgressBarByFrameId(parent_frame_id, component_flags=0x300, child_index, label). component_flags 0x300 = F_VISIBLE|F_ENABLED (these are FRAME create flags, NOT the paint-style bits). Do NOT create it as a frame-list ITEM (the list stretches every row to full width -> "extremely wide") and do NOT feed the raw proc into the generic single-proc item creator.

The engine drives the whole lifecycle automatically once the CORRECT proc is registered — no manual image-list or base-class setup is needed:
- msg 4 (OnComponentVtable): proc writes base handler &LAB_00618b70 into *(param_2[3]).
- msg 5 (class-init, first instance only): builds 3 class-static image lists — DAT_01081a98 (from &DAT_00b966b0) and DAT_01081abc (from &DAT_00b966dc) via FUN_0065efa0, plus rate-arrow list DAT_010819fc via FUN_00882530 (refcounted by DAT_010819f8). Asserts on lines 0x636/0x651.
- msg 9 (create): allocs the 0x28 instance ctx via FUN_0047f340("...UiCtlProgress.cpp",0x5ab), stores it at frame[2], self-sends msg 0x45 to arm the anim tick. Ctx(0x28) layout confirmed: +0x00 frameId; +0x04 overlay-text=0; +0x08 bar1 render-obj=0; +0x0c lerp-frac1=0; +0x10 color1A=0xffffffff; +0x14 color1B=0xffffffff; +0x18 bar2 render-obj=0; +0x1c lerp-frac2=0; +0x20 color2A=0xffffffff; +0x24 color2B=0xffffffff.
- default case: thunk_FUN_00647170 delegates to the base FrameWithValue layer.

After Create, size/position EXPLICITLY (FrameSetSize + FrameSetPosition) so it is not a stretched strip; case 0x38 auto-sets height = font-height(FUN_0062d0e0)+pad, so only width/x/y need to come from parent layout.

RUNTIME MESSAGES (GWCA IDs are already correct where they exist):
- Fill VALUE / MAX / PERCENT are NOT cases in 0x008812e0 (verified: proc has no 0x56/0x57/0x58/0x5a/0x5b case); they fall through default -> base FrameWithValue. Drive via the base messages: SetValue=0x58 (wparam uint), GetValue=0x56, SetMax=0x5a, GetMax=0x57, SetPercent=0x5b (0..100). SetIncrementsPerSecond (animated auto-advance, arms 0x45)=0x59 (float).
- Animated BAR COLOR (ARGB, proc-level, confirmed in decompile): msg 0x60 = bar1 color, msg 0x61 = bar2 color; payload = float-reinterpreted 0xAARRGGBB; lerps via FUN_008823d0 using reset constant _DAT_0094052c. These are NOT percent (catalog previously conflated them).
- Palette COLOR-ID (base layer): SetColorId=0x65 (0..8). SetStyle=0x64.
- TEXT: msg 0x62 = proc-level overlay text (confirmed: sets ctx+0x04, invalidates via FUN_0062bd80(frame,0x40)). Base value-text is 0x5c. Prefer 0x62 for the on-bar overlay.
- Paint = case 0x5e -> FUN_00883790, which tests style bits 0x10 (primary animated bar / DAT_01081a98), 0x20 (secondary bar / DAT_01081abc), 0x40 (draw text), 0x100 (end marker / DAT_00b966e4). For a basic filled bar the style must include 0x10 (|0x40 for text). NOTE these paint-style bits are a DIFFERENT field from the 0x300 create flags.

Teardown: destroy through the component path so msg 0xb frees ctx+0x18/ctx+0x08 then the 0x28 struct, and the last-instance msg 6 releases the 3 image lists / decrements DAT_010819f8.

### C++ fix plan

1) UIMgr.cpp InitializeTypedComponentCallbacks (~1561-1571): stop assigning ProgressBar_Callback from FindAssertion(...)->ToFunctionStart directly (that yields the loader FUN_00882530). Keep FindAssertion("UiCtlProgress.cpp","!sm_rateArrowImageList")->ToFunctionStart to LOCATE the loader FUN_00882530, then RESOLVE ITS SINGLE CALLER to reach the real proc: scan .text for the unique `call rel32` targeting FUN_00882530 (verified unique caller @0x0088159b) and ToFunctionStart(callsite,0xFFF) -> 0x008812e0; assign THAT to ProgressBar_Callback. Alternative address-free anchors inside 0x008812e0 if the call-scan is undesirable: (a) byte-signature for the msg-9 create that pushes the "UiCtlProgress.cpp"/0x5ab pair, or (b) the case-4 store `mov [reg], offset LAB_00618b70`, then ToFunctionStart. Do NOT add the Angle-A fallback of manually sending msg 5 or hand-installing LAB_00618b70 — with the correct proc registered, GW::ProgressBar::Create fires msg 4/5/9 itself.
2) py_ui.h: fix the identical defective anchor at ResolveNamedControlProc:4602 and AddControlItemByFrameId:4560 (both use {"UiCtlProgress.cpp","!sm_rateArrowImageList"}) for control=="progress" — apply the same caller-follow resolver (or share the UIMgr resolver). Route "progress" through the positioned-child creator (the existing CreateProgressBarByFrameId / GW::ProgressBar::Create), NOT CtlFrameListCreateItem, then FrameSetSize+FrameSetPosition so it is not stretched full-width.
3) GW::ProgressBar manipulators (UIMgr.cpp ~3653-3680 / py_ui.h): existing SetValue=0x58 / GetValue=0x56 / SetMax=0x5a / SetStyle=0x64 / SetColorId=0x65 IDs are correct. ADD the missing ones: GetMax=0x57, SetPercent=0x5b, SetIncrementsPerSecond=0x59 (float), overlay SetText=0x62 (encoded wchar_t*), and (optional animated) SetBar1Color=0x60 / SetBar2Color=0x61 with payload = float-reinterpreted 0xAARRGGBB. Ensure the paint style includes bit 0x10 (primary bar) via SetStyle(0x64) or the create descriptor, else the fill will not paint even though value is set.
4) Rebuild Py4GW.dll and run the in-client progress-bar test (existing task #13) to confirm visual fill + text render.

### Open questions (needs live decompile)

Low-risk optional confirmations only (core path fully decompiled): (1) Decompile base FrameWithValue proc at &LAB_00618b70/0x00618b70 (EXE base entry FUN_00618d00) to confirm it services 0x56/0x57/0x58/0x5a/0x5b/0x5c exactly as GWCA sends (WASM inlines these; EXE splits them into the base — GWCA already matches the WASM handler, so low risk). (2) 0x00884a50 is the sole CALL xref to 0x008812e0 and Ghidra reports no function there (bytes look like a jmp thunk / registration wrapper); confirm whether the game registers 0x008812e0 directly or via that trampoline, in case CreateUIComponent expects the trampoline value rather than 0x008812e0. (3) Confirm the FUN_0065efa0 texture-resource names at &DAT_00b966b0 / &DAT_00b966dc and the end-marker &DAT_00b966e4 (art assets) — cosmetic only. (4) Confirm _DAT_0094052c is the 1.0 lerp-reset constant used by msgs 0x45/0x60/0x61.

---

## Tabs control (CtlPage / CtlPageProc @ EXE 0x0061a950, WASM ram:80e078f3) — correct creation, render path, and tab add/select protocol

**Verdict:** likely &nbsp; **Confidence:** high

### Root cause

The prior "tabs" attempt failed for two independent reasons, neither of which is intrinsic to CtlPage: (1) CreateTabsFrameByFrameId routed container creation through CreateUIComponent/CreateTabsFrame (the wrong container path) instead of a plain frame-list item or direct-child FrameCreate; and (2) there was no crash-safe AddTab: the helper defaulted the page callback to 0 (null FrameProc) and passed an un-encoded caption, both of which crash. Tabs do NOT share the slider/dropdown crash class — CtlPageProc msg 0x09 is self-handled (8-byte instance alloc, active_index=-1) with no base-class delegation, so the container itself renders cold once created via a supported path. The catalog's instance layout (+0x08 tab_count/+0x0C items) is wrong; the alloc is only 8 bytes.

### Verified recipe

PROC: CtlPageProc = EXE 0x0061a950 (verified: FUN_0061a950, body 0061a950-0061ac07) / WASM ram:80e078f3. Resolve via FindAssertion("CtlPage.cpp","!IsBtnCode(pageCode)")+ToFunctionStart. It is a self-contained container/layout-manager frame, NOT a frame-list leaf item and NOT the slider/dropdown multi-layer class: msg 0x09 (create) is SELF-HANDLED (MemAlloc(8) instance; +0x00 = frame handle, +0x04 = active_index = 0xffffffff; NO base delegation). It therefore renders cold with no image-list init. CORRECT the catalog: the instance is only 8 bytes {+0x00 frame handle, +0x04 active_index}; there is no +0x08 tab_count / +0x0C items field (tab count is derived from child frames).

CONTAINER CREATION (two valid paths; msg 0x09 self-handles so neither crashes):
 - PRIMARY / crash-safe with today's helpers: create as a FRAME-LIST ITEM. window_id = CreateNativeWindow(...); frame_list_id = CreateScrollableContentByFrameId(window_id, 0); tabs_id = CtlFrameListCreateItemByFrameId(frame_list_id, flags=0x300, insert_index, CtlPageProc, BuildStandaloneLiteralEncodedTextPayload(L"")). msg 0x09 ignores that empty-text userData (harmless); 0x38 self-sizes; paint/mouse fall to base in the managed list. Use this now because our direct-child positioning is currently unsolved (in-client evidence: FrameSetPosition on direct children did not apply).
 - NATIVE / architecturally-correct target (how the game does it in CFeatBoardFrame::OnFrameCreate): FrameCreate(window_id, component_flags=0x300, child_id>=1, CtlPageProc, ctx=0, label=0) as a direct child. Prefer once direct-child positioning is solved.
 In BOTH, component_flags = 0x300. Do NOT CreateUIComponent / CreateTabsFrame (the historical CRASH path).

ADD A TAB (msg 0x56, repeat per tab i=0..n): build a 5-dword CtlPageItem {caption, flags, code, proc, ctx} = {BuildStandaloneLiteralEncodedTextPayload(L"Tab i"), 0x20000, i, contentProc, context}, then FrameMsgSend(tabs_id, 0x56, &item, &out_body_frame_id). Engine creates: page body = FrameCreate(page, flags|0x200, i, contentProc, context, 0) + FrameShow(0); tab button = FrameCreate(page, 0x20100, ~i, CtlBtn class &DAT_00000a7c (flat CtlBtnProc, cold-renderable, no image list), caption, 0), FrameSetLayer(-1); first tab auto-selects via SetActive(i,0); then FrameContentInvalidate + FrameScheduleSize.
 HARD RULES (verified): (a) code i MUST be >=0 and unique (asserted "!IsBtnCode(pageCode)"); (b) caption MUST be GW-literal-encoded (same encoder as add_text) — a raw wchar_t* becomes the button userData and CRASHES; (c) contentProc MUST be a valid self-contained FrameProc (e.g. a plain panel proc or CtlTextProc). The game always passes a real proc (FeatBoard contentProc 0xaea) and NEVER 0 — passing 0 registers a null FrameProc for the page and is unverified/unsafe; helpers must default null->a resolved plain/text proc; (d) if contentProc is a text proc, context/wparam must itself be an encoded text payload; use 0x20000 for flags to match the game (the engine ORs 0x200 in for the page regardless). Capture out_body_frame_id as the frame to populate.

SELECT / QUERY (verified from decompile):
 - Select tab: FrameMsgSend(tabs_id, 0x5d, i, 0)  (0x5d asserts i>=0 then SetActive(instance, i, 0)).
 - Active index: u32 out; FrameMsgSend(tabs_id, 0x59, 0, &out); out = *(instance+4) (0xffffffff until first tab; poll+diff to detect user clicks).
 - Body frame for tab i: FrameMsgSend(tabs_id, 0x5a, i, &out) (FrameGetChild), or reuse out_body_frame_id from 0x56.
 - Enable/disable tab: 0x58 / 0x57. index<->btncode: 0x5b. style blob: 0x5e.
 User clicks: tab button push -> parent msg 0x31 (notify 7) -> SetActive(~btnCode,1) internally; no wiring needed.

LAYOUT: CtlPage lays out the tab-button strip + active body itself on 0x37/0x38. Never FrameSetPosition the tab children and never FrameSetSize the container (fights OnFrameSizeQuery 0x38). Styled/textured tab art needs the UiCtlPageProc subclass (WASM ram:80e09c1f); the base proc gives fully functional tabs with default button art from msg 0x5e.

### C++ fix plan

1. Add ResolveCtlPageProc() mirroring ResolveCtlTextButtonProc: FindAssertion("CtlPage.cpp","!IsBtnCode(pageCode)",0,0)+ToFunctionStart(0xFFF), cache. Confirm it lands on base+0x21a950 (EXE 0x0061a950).
2. Container: add CreateTabsAsListItemByFrameId(frame_list_id, insert_index=0, flags=0x300) = CtlFrameListCreateItemByFrameId(frame_list_id, 0x300, insert_index, ResolveCtlPageProc(), BuildStandaloneLiteralEncodedTextPayload(L"")). Keep the existing generic AddControlItemByFrameId "tabs" branch (its container step is fine); the missing piece is a crash-safe AddTab. STOP exposing CreateTabsFrameByFrameId (py_ui.h:3406) as the render path (CreateUIComponent = crash).
3. Fix AddTabByFrameId (py_ui.h:3455): (a) if callback==0, default to ResolveTextLabelFrameCallback()/a resolved plain-panel proc so the page never gets a null FrameProc; (b) ENCODE the caption via BuildStandaloneLiteralEncodedTextPayload (or add a plain-text overload that always encodes); (c) if wparam/context is text for a text page proc, encode it too; (d) guard child index >= 0 before the send. Prefer sending msg 0x56 directly with a locally-built CtlPageItem{caption,flags=0x20000,code,proc,ctx} to be independent of GWCA AddTabArgs header drift (the GWCA field order {caption,flags,child,callback,wparam} is already correct — do not change it).
4. Add TabSetActiveByFrameId(page,i)=FrameMsgSend(page,0x5d,i,0); TabGetActiveByFrameId(page)=FrameMsgSend(page,0x59,0,&out); TabGetItemFrameByFrameId(page,i)=FrameMsgSend(page,0x5a,i,&out); optional 0x57/0x58 enable/disable.
5. Do NOT FrameSetSize the tabs container (CtlPage self-sizes via 0x38) and do NOT position its children. Remove any "tabs" routing that would send it through a raw single-proc leaf-item creator expecting manual layout.

### Open questions (needs live decompile)

Low-risk items to pin before shipping the SKINNED variant (functional base tabs need none of these): (1) EXE address of the styled subclass IUi::UiCtlPageProc (WASM ram:80e09c1f) — only if textured tab buttons are wanted instead of base default art; (2) formally pin FUN_0061a950 as CtlPageProc by resolving the "!IsBtnCode(pageCode)" assertion string in the EXE (the function is confirmed to exist at 0x0061a950 and matches the catalog, but the symbol name is not applied in the EXE db); (3) confirm the EXE &DAT_00000a7c tab-button class resolves to flat CtlBtnProc (0x0060f4f0) so tab buttons render cold on x86; (4) optional: decompile CCtlPage::OnFrameSizeQuery (ram:80e05a11) to confirm a CtlText page is not zero-height inside a frame-list row. All message IDs (0x56/0x59/0x5a/0x5b/0x5d/0x5e/0x31/0x57/0x58), the item struct {caption,flags,code,proc,ctx}, the 8-byte instance, and the FrameCreate flags (0x300 container, 0x20000 item, |0x200 page, 0x20100 button) are confirmed on WASM.

---

## Group header (CGroupHeaderFrame @ EXE 0x0087ddc0 / WASM ram:81192c89) — reconciled native creation, layout, message protocol, and C++ fix

**Verdict:** likely &nbsp; **Confidence:** high

### Root cause

Two independent RE defects, plus a mis-diagnosis the decompile refutes.
(1) MIS-DIAGNOSIS (Angle A): the theory that the frame-list-item path "never allocates the TCtlInstance base object -> crash" is FALSE for GroupHeader. EXE FUN_0087ddc0 allocates the 0x60-byte TCtlInstance INLINE on msg 9 (vtable 0x00b96070) then dispatches OnFrameCreate; allocation depends only on msg 9 reaching the registered proc, which the item path does deliver (proven in-client by other controls' procs running their paint/click). GroupHeader itself was never in the in-client failure set, so its item-path behavior was untested, not observed to crash. Angle B's mechanism is correct.
(2) REAL defect A - resolver anchor: current helpers (include/py_ui.h AddControlItemByFrameId ~4562 and ResolveNamedControlProc ~4604) resolve groupheader with FindAssertion("UiCtlGroupHeader.cpp","UiCtlGroupHeader.cpp",0,0) — the message arg is the FILENAME, not a real assertion expression, so ToFunctionStart can land off CGroupHeaderFrame::FrameProc. Valid anchors are assertion strings INSIDE the proc: "isOpen" (0x56 handler) or "decodedName" (0x57 handler).
(3) REAL defect B - message IDs: docs/RE/ui_controls_catalog.md (~lines 162-169) swaps 0x57/0x58. Decompile proves 0x57=GetText, 0x58=SetIsOpen.
The slider/dropdown crashes are a SEPARATE failure class (internal child listboxes / unhandled image lists) and do NOT apply to GroupHeader, whose only child needing art (the CheckOpen checkbox FUN_008867f0) self-builds its own image list on msg 5.

### Verified recipe

Create the group header as a REAL managed frame whose registered proc is the group-header FrameProc (EXE FUN_0087ddc0). The frame-list-item path is valid and preferred (it supplies the managed frame-context slot and delivers msg 9):
1. window = CreateNativeWindow(...).
2. frame_list_id = CreateScrollableContentByFrameId(window, 0) (managed parent context).
3. proc = ToFunctionStart(FindAssertion("UiCtlGroupHeader.cpp","isOpen",0,0), 0xFFF) -> CGroupHeaderFrame::FrameProc (EXE 0x0087ddc0). Use assertion expression "isOpen" (fallback "decodedName"), NOT the filename-as-message anchor currently in the code.
4. encoded = BuildStandaloneLiteralEncodedTextPayload(header_text).
5. item = CtlFrameListCreateItemByFrameId(frame_list_id, item_flags=0, insert_index, proc, encoded).

Engine does the rest automatically (DECOMPILE-CONFIRMED; do NOT replicate in C++/Python):
- msg 9 reaches FUN_0087ddc0, which INLINE allocates TCtlInstance<CGroupHeaderFrame> (vtable 0x00b96070, size 0x60), stores it at the frame-context slot, sets instance+4=frameId, then calls base dispatcher FUN_008783b0. Base case 9 invokes vtable+0x1c (OnFrameCreate = EXE 0x0087e090) then vtable+0x18.
- OnFrameCreate (0x0087e090) self-builds two children via FrameCreate = EXE FUN_0062bfc0(parentFrameId, flags, childIndex, proc, userData, wname):
   * child0 = FrameCreate(frame, 0, 0, FUN_008867f0 [checkbox proc, callback 0x0AFD], 0, L"CheckOpen") — self-manages its own image list DAT_01081d70 (built on msg 5, freed on msg 6) => no cold image-list crash.
   * child1 = FrameCreate(frame, 0xA0000, 1, FUN_00616c00 [CtlTextBtnProc, callback 0x0A56], encodedCaption, L"TxtName").
   * On child1: SetColor(0xFFFFEAB8)=FUN_0059fee0; SetHoverColor(0xFFFFF5DF)=FUN_0060a2d0; SetGrEffects(0x10)=FUN_00617790; SetDefaultTextStyle(8)=FUN_0062f4b0. If FrameTestStyles(frame,0x2000): FrameMouseEnable(child1,0,-1)=FUN_0062ede0.
   * LAYOUT: FramePlaceChildren(frame, FeatureFlagGetToggle(0x71) ? L"UiCtlGroupHeaderMobile" : L"UiCtlGroupHeader") = FUN_0062f1a0 — a NAMED layout template; never FrameSetPosition.
   * If FrameTestStyles(frame,0x1000) [non-collapsible]: hide/disable child0 (FUN_0062fcb0 + FUN_0062c9c0(child1,0)); else FrameGamepadEnable(frame,0x30,0)=FUN_0062ccd0.

Interact via UI messages to the header frameId (protocol confirmed from FUN_0087ddc0 switch; catalog had 0x57/0x58 SWAPPED):
- 0x56 GetIsOpen: child0=FrameGetChild(frame,0)=FUN_0062cfc0; *out=CtlBtnIsChecked(child0)=FUN_0060f4b0.
- 0x57 GetText: child1=FrameGetChild(frame,1); CtlTextBtnGetTextLen(FUN_006143f0)+CtlTextBtnGetText(FUN_00616bb0) into TArray<wchar_t> out.
- 0x58 SetIsOpen(bool): child0=FrameGetChild(frame,0); CtlBtnCheck(child0,value)=FUN_0060f490.
- 0x59 SetText(wchar*): child1=FrameGetChild(frame,1); CtlTextBtnSetText(child1,text)=FUN_006177b0.
Poll 0x56 each frame to detect collapse. Do NOT create children yourself, do NOT FrameSetSize/FrameSetPosition — engine self-sizes and places children.

### C++ fix plan

In C:\Users\Apo\Py4GW\include\py_ui.h:
1. FIX RESOLVER: in AddControlItemByFrameId (~line 4562) and ResolveNamedControlProc (~line 4604), change the groupheader branch from { file="UiCtlGroupHeader.cpp"; msg="UiCtlGroupHeader.cpp"; } to { file="UiCtlGroupHeader.cpp"; msg="isOpen"; } (fallback msg="decodedName"). Add a cached ResolveGroupHeaderProc() mirroring ResolveCtlTextButtonProc; it must ToFunctionStart(FindAssertion("UiCtlGroupHeader.cpp","isOpen",0,0),0xFFF) -> 0x0087ddc0.
2. ADD AddGroupHeaderItemToFrameListByFrameId(frame_list_id, header_text, insert_index=0, item_flags=0): encoded=BuildStandaloneLiteralEncodedTextPayload(header_text); item=CtlFrameListCreateItemByFrameId(frame_list_id, item_flags, insert_index, ResolveGroupHeaderProc(), encoded); return item. Do NOT send 0x5E and do NOT call FrameSetSize/FrameSetPosition — OnFrameCreate self-builds children and FramePlaceChildren positions them (manual sizing is what breaks composites / causes overlap).
3. ADD msg wrappers with CORRECT ids: GroupHeaderGetIsOpen->0x56 (&u32 out), GroupHeaderGetText->0x57 (TArray<wchar_t> out), GroupHeaderSetIsOpen->0x58 (&u32 value), GroupHeaderSetText->0x59 (pass encoded/wchar payload).
4. Do NOT add manual child creation for GroupHeader; DEPRECATE CreateControlChildByFrameId's FrameSetPosition approach for composites. If non-list composite layout is ever needed, add ResolveFramePlaceChildren()+PlaceChildrenByFrameId(frame, L"<template>") bound to EXE FUN_0062f1a0 (FramePlaceChildren) instead of FrameSetPosition.
5. DOCS: fix docs/RE/ui_controls_catalog.md GroupHeader table (0x57=GetText, 0x58=SetIsOpen); note child1=CtlTextBtnProc (callback 0x0A56 / EXE FUN_00616c00) and child0=checkbox (callback 0x0AFD / EXE FUN_008867f0, self-managed image list DAT_01081d70). Mirror the swap fix + child-proc notes into native_button_pipeline.md and ui_elements_creation_recipes.md.

### Open questions (needs live decompile)

Effectively none blocking. Resolved this pass: FrameCreate = EXE FUN_0062bfc0 (arg order parentFrameId, flags, childIndex, proc, userData, wname); FramePlaceChildren = EXE FUN_0062f1a0; layout template strings L"UiCtlGroupHeader"/L"UiCtlGroupHeaderMobile" are referenced directly in OnFrameCreate 0x0087e090; child0 checkbox proc = FUN_008867f0 (self-builds image list DAT_01081d70 on msg 5, frees on msg 6 — no cold-art crash); child1 = CtlTextBtnProc FUN_00616c00. The numeric callback codes 0x0AFD/0x0A56 are NOT needed for the C++ create path (OnFrameCreate passes proc pointers directly; the item path only needs the resolved group-header proc pointer) — they'd only matter for a future code->proc-table create path. Only truly unverified item is empirical: this exact native recipe has not yet been observed rendering in-client (GroupHeader was absent from the 2026-06-30 test set); needs an in-client run after the C++ change.
