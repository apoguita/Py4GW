# GW UI Controls - Master Catalog (Ghidra swarm, 2026-07-01)

> Produced by a 56-agent Ghidra swarm (model RE + multi-angle discovery + per-control deep RE + fixes)
> against Gw.exe build 06-14-2026 (program "/Gw.exe (06-14)") and Gw.wasm (named symbols).
> **166 distinct UI control FrameProcs discovered**; **120 deep-cataloged** (40 in §3 + 80 in §4).
> Companion docs: native_button_pipeline.md (authoritative creation recipes + master address table),
> ui_controls_catalog.md, reverse_engineering_reference.md.

## 1. UI Creation & Message-Dispatch Model (decompiler-verified)

### Model summary

DECOMPILER-VERIFIED MODEL (EXE /Gw.exe (06-14), base 0x00400000). Every UI control is a TCtlInstance<T>-style class whose sole registered FrameProc is a C++ MsgProc with signature Proc(uint* msgframe, void* payload, void* out) that switch()es on msgframe[1] = the message id. Exemplars: styled button UiCtlBtnProc FUN_00877e60 and selectable-text row CtlTextSelectable FUN_00617df0. The msgframe (first arg, the `local_20` block rebuilt inside the base-walker FUN_00647170) is a fixed 6-dword control-message record: [0]=frame handle/id, [1]=msg id, [2]=pointer to the per-frame instance-slot (case 9 stores the allocated instance at *msgframe[2]; the accessor FUN_00618aa0 returns **(msgframe+8) = that instance and asserts(0x74) if null), [3]=address of the vtable/proc-table slot into which case 4 installs the *base* class proc, [4]=per-message style/flag word (tested as (msgframe[4]&1/&2/&4) for face/style bits), [5]=proc-layer index used by FUN_00647170 to descend to the next (base) layer. CLASS INHERITANCE IS A PROC CHAIN, not a vtable of methods: each proc's `case 4` writes its parent proc into *(payload[3]) and (in the middle layers) also calls thunk_FUN_00647170 so the whole ancestry registers. Verified chain for the button: UiCtlBtnProc(0x00877e60) --case4--> CtlBtnProc/flat FUN_0060f4f0 --case4--> FUN_006123a0 (interactive base frame proc) --case4--> root proc FUN_0062c370; CtlTextSelectable(0x00617df0) --case4--> FUN_006123a0 directly (**(payload+0xc)=FUN_006123a0). At runtime any handler that does not fully consume a message falls through to `thunk_FUN_00647170(msgframe,payload,out)` (a thunk to FUN_00647170) which looks up the msgframe[5]-th entry in the frame's proc table (base at *(ctx+0xa8), count at *(ctx+0xb0)) and invokes the next lower proc with a fresh msgframe copy — this is how a derived class delegates unhandled/lifecycle messages to its base. Message SENDING into a control uses the dispatcher family FUN_0062ef40(frame,msg,payload,out) (asserts frame!=0 @0xf2e and msg>=0x56 @0xf2f, then FUN_00647db0/FUN_00647c80), plus the thinner FUN_0062ef00/FUN_0062ee80/FUN_0062efc0 senders used for internal notifications (e.g. selectable row raises 7/8/9/10 for focus/select/activate and 0x60/0x61/0x62 for draw). Style-flag reads go through FUN_0062fe20(frame,mask) (e.g. 0x40000 paint-enable gate, 0x8000 checkbox face, 0x4000 selectable) and state predicates FUN_0062e2a0 (enabled) / FUN_0062e320 (hot/highlight). Instances are heap-allocated by FUN_0047f340(assertFile,arg) with the assertion file "P:\\Code\\Engine\\Controls\\<Ctl>.cpp", and freed via FUN_005acaeb / FUN_0047f3a0 on destroy.

### Lifecycle messages

Enumerated from the two exemplars (msg id -> handler action):
case 4 = INSTALL BASE PROC (class link). UiCtlBtnProc 0x00877e60: `*(code**)param_2[3] = FUN_0060f4f0;` (wires flat-button base) then returns WITHOUT descending. CtlTextSelectable 0x00617df0: `**(undefined4**)(param_2+0xc) = FUN_006123a0;` then breaks (falls to base-walk). Middle layer FUN_0060f4f0 case4: `*(code**)param_2[3]=FUN_006123a0` + thunk_FUN_00647170. FUN_006123a0 case4: `*(code**)param_2[3]=FUN_0062c370` + thunk. So case 4 threads the whole ancestry; payload[3] (offset 0xc) is the write target slot.
case 9 = OnFrameCreate / instance alloc+init. CtlTextSelectable: asserts *(int*)param_1[2]==0 (else FUN_00487a80(0x61) "already created"); calls FUN_0047f340("P:\\Code\\Engine\\Controls\\CtlTextSelectable.cpp",0x62) to alloc; inits instance [0]=frameid,[1]=0(shown flag),[2]=1(enabled),[3]=0(text buf),[4]=0,[5]=0(len),[6]=0x80,[7]=0xffffffff,[8]=0,[9]=0xffffffff,[10]=0; stores *(param_1[2])=instance; if an initial caption was supplied copies it (FUN_0046c270 strlen, FUN_0046da80 copy) into [3]/[5]; tests style 0x4000 via FUN_0062fe20 and sets instance[8]|=0x10; sends 0x4c via FUN_0062ef00; if text present calls FUN_00632d90 to lay it out. (The button chain routes case 9 through FUN_006102b0 in FUN_0060f4f0, and FUN_006123a0 case9 registers itself via FUN_0062d6f0(*param_1,FUN_006123a0), asserting 0x108 on failure.)
case 0xb = destroy. CtlTextSelectable: reads instance=*(param_1[2]); if instance[0xc]!=0 frees text (FUN_0047f3a0); zeroes [0xc]/[0x14]/[0x10]; FUN_005acaeb(instance,0x2c) frees the 0x2c-byte struct; *(param_1[2])=0. (Flat btn 0xb frees [0x18] image + [4] buffer then FUN_005acaeb(ctx,0x2c).)
case 1 = paint. Runs only when *payload==0 (sub-pass 0 = the control's own draw pass; other values delegate). UiCtlBtnProc gates on FUN_0062fe20(frame,0x40000); selects the face bitmap PTR_DAT_00bf45xx by combining checkbox-face flag (byte@ instance+0x10 &1), disabled state, and hot state (FUN_0060f4b0/FUN_0060f4d0/FUN_0062e2a0/FUN_0062e320), then FUN_0062b8e0 blits the face and FUN_0062b3e0 the glyph/checkmark; *payload==1 sub-pass draws the imagelist icon (FUN_0062b290 with DAT_010819cc). Flat btn case1 draws a 1px-inset filled rect (FUN_0062b2d0) colored by enable/hot. Text row draws its label in case 0x60/0x61.
case 0x15 = size/scale query. Writes a 4-float extent into `out` (param_3): text row returns {1.0,0,1.0,_DAT_00943278}; styled btn copies DAT_00bf4518.. face metrics (two variants by style bit) and optionally FUN_00876690 for text-margined variant; flat btn returns 4x _DAT_0093c89c.
case 5 = class one-time INIT / shared-resource load (button only): asserts DAT_010819cc==0 (0x45), then FUN_0062d790(...) builds the shared image list and stores it in global DAT_010819cc.
case 6 = class one-time TEARDOWN (button only): FUN_0046f9b0(DAT_010819cc); DAT_010819cc=0.
Additional handled messages on the text row (each first resolves inst=FUN_00618aa0): 8 draw-compose (emits sub-draws 0x60/0x61 then FUN_0062ef40 msg 0x62); 0xc invalidate/redraw request (FUN_0062bd80 0x40, raise 7 if focused); 0x24/0x2e mouse enter/press -> raise focus/activate (FUN_0062ee80 8/9) gated by style 0x2000; 0x25 FUN_0062bd40 relayout; 0x2c hover leave; 0x38 hit-test (FUN_00618910); 0x39 relayout+FUN_0062f110; 0x3a text-commit/edit; 0x4c late-init hook; 0x56 hide (inst[1]=0, assert 0x1a5), 0x57 show (inst[1]=1, assert if already shown / not created); 0x58 get pos {inst+0x24,+0x28}; 0x59 get enabled (inst+8); 0x5a get shown (inst+4); 0x5b get text (copy inst text, empty->null term); 0x5c set indent/offset ([9]/[10]); 0x5d set enabled ptr ([2]) + raise 7; 0x5e/0x5f set text (dup+compare, FUN_00632d90 relayout, then FUN_0062bd80 0x40 + FUN_0062f110); 0x60/0x61 draw label via FUN_0062bb30 (grey 0xff808080 when disabled); 0x62 draw hot/press overlay quad (FUN_0062b2d0). Styled button also handles 0x38 tint (multiply by global color _DAT_009411d0/_DAT_0094519c per style bits), 0x5f label draw, 0x60 metrics copy. Any case not returning early falls through to thunk_FUN_00647170 to hand the message to the base proc — so lifecycle msgs (0xb destroy, 9 create, hit-test, focus) propagate down the class chain automatically.

### Creation paths

The MsgProc itself is never called directly by client code; controls are instantiated by the frame factory FUN_0062bfc0(parent,flags,child,proc,userdata,0) which creates the frame, records the proc, and returns the frame id at *(frame+0xbc). At creation the framework drives the class-init handshake by SENDING messages through this same proc: it first walks case 4 down the ancestry to populate the frame's proc-table (each layer writing its parent into payload[3]/offset 0xc and, for middle layers, calling FUN_00647170 to continue), giving an ordered proc list stored at *(ctx+0xa8) with count *(ctx+0xb0); then it sends case 9 to the top proc, which allocates the per-frame instance via FUN_0047f340("P:\\Code\\Engine\\Controls\\<Ctl>.cpp",size), inits its fields, and stores it at *(msgframe[2]) so every later message can retrieve it through FUN_00618aa0 (**(msgframe+8)). For classes with shared GPU resources (e.g. the styled button's image list) the framework also sends the one-shot class messages case 5 (build DAT_010819cc) / case 6 (free it) around first-use/last-use. Subclassing/layering is done with FrameNewSubclass 0x0062f150 which pushes an extra proc onto the proc list (e.g. the outer CCtlEdit 0x008852e0 layering its render subclass 0x00888aa0). Style flags passed at create time drive branch selection inside the procs via FUN_0062fe20(frame,mask): 0x40000 = paint-enable gate (no paint without it -> blank frame), 0x8000 = checkbox face, 0x4000 = selectable-state alloc, 0x2000 = focus/press eligibility, 0x20128 = selectable-list sel-state alloc (per model facts). Position/size is applied post-create by the anchor-6 setter FUN_0062F770; destruction routes through case 0xb (frees instance via FUN_005acaeb/FUN_0047f3a0) and the native destroyer FUN_0062c550(id). Practical creation recipe for a control: (1) FUN_0062bfc0 with the class proc + style incl. 0x40000; (2) framework auto-runs case4-chain then case9 alloc/init; (3) push text/state with the set-messages (0x5d/0x5e/0x5f etc.) via FUN_0062ef40; (4) size with FUN_0062F770. Skipping the case9 alloc (cold/partial creation) leaves *(msgframe[2])==0 so the very next FUN_00618aa0 asserts 0x74 / crashes, and omitting 0x40000 yields a live-but-blank frame.

### Instance struct & proc chaining

Per-frame instance is a small heap struct (CtlTextSelectable: 0x2c bytes, freed by FUN_005acaeb(inst,0x2c)) allocated in case 9 by FUN_0047f340(assertFile,size) and stored at *(msgframe[2]); retrieved everywhere via inst = FUN_00618aa0(msgframe) = **(msgframe+8) (asserts 0x74 if the create step never ran). CtlTextSelectable layout (dword indices): [0]=frame handle (copied from msgframe[0]); [1]=shown/visible flag (0 hidden, 1 shown; toggled by msgs 0x56/0x57, read by 0x5a); [2]=enabled pointer/flag (init 1; set by 0x5d; read by 0x59); [3]=UTF-16 text buffer ptr; [4]=0/aux; [5]=text length (chars); [6]=default color 0x80; [7]=selection/sel-length (0xffffffff = none); [8]=style flags (|0x10 when created with style 0x4000); [9]=indent/column index (0xffffffff none; set by 0x5c); [10]=indent pixel offset (float; set by 0x5c). Get-pos msg 0x58 returns {inst+0x24, inst+0x28}. The styled-button/flat-button instance is a different 0x2c struct whose fields include text buffer @+4, length @+8, image handle @+0x18, and metric floats @+0x24/+0x28 (see FUN_0060f4f0 cases 0xb/0x13/0x3a/0x4c/0x5c). BASE/DERIVED CHAINING: there is no method vtable; instead each frame owns an ordered proc list (array at ctx+0xa8, length ctx+0xb0) built by the case-4 cascade. A derived proc handles the messages it cares about and for everything else calls thunk_FUN_00647170(msgframe,payload,out); FUN_00647170 reads msgframe[5] (current layer index), finds the next non-null lower proc in that array, rebuilds a fresh 6-dword msgframe (copying [0..4], repointing [2] to the base's own instance slot at *(ctx+0xa8)+4+idx*0xc and [4] to that entry's userdata) and invokes it — so a single client-visible frame runs UiCtlBtnProc -> FUN_0060f4f0 -> FUN_006123a0 -> FUN_0062c370 in sequence for unhandled/lifecycle messages, giving classic inheritance semantics.

### Pitfalls

Cold/partial creation crash: the per-frame instance only exists after the case-9 handler runs (it allocs via FUN_0047f340 and stores at *(msgframe[2])). If you register/drive a control proc without letting the framework run case 4 (build proc chain) then case 9 (alloc+init), the first FUN_00618aa0 call dereferences a null instance slot and hits assert 0x74 (FUN_00487a80) or faults. case 9 itself asserts 0x61 if *(msgframe[2]) is already non-null, so double-create is fatal. Blank render: nothing paints unless the create-time style includes 0x40000 — UiCtlBtnProc case1 early-outs on `FUN_0062fe20(frame,0x40000)==0`, so a correctly-created frame with the paint gate cleared is live but invisible; likewise the flat/base proc only fills its rect in case1 sub-pass 0. SIZING/LAYOUT: a control has no size until case 0x15 (size query) returns extents and the anchor-6 setter FUN_0062F770 is applied; text controls additionally must run FUN_00632d90 (invoked inside case 9 and the set-text msgs 0x5e/0x5f) or the label has zero measured width; after any text/state change you must let the proc issue FUN_0062bd80(0x40)+FUN_0062f110 to re-layout or the old geometry sticks. ENCODED TEXT: captions are UTF-16 (wide) buffers duplicated with FUN_0046c270(strlen)/FUN_0046da80(copy); the code asserts 0x171 on overlapping src/dst copies, and msg 0x5b returns an empty-string-as-single-null when no text — passing a non-wide or non-owned pointer corrupts the instance. Many GW captions are the game's encoded/templated string ids resolved elsewhere, not literal text, so writing raw ASCII where an encoded id is expected renders garbage. IMAGE LISTS: the styled button's face icons live in a single lazily-built shared image list at global DAT_010819cc, created by class msg 5 (asserts 0x45 if already built) and freed by msg 6; if you drive per-instance paint (case1 sub-pass 1 / FUN_0062b290) before msg 5 has populated DAT_010819cc the icon draw reads a null list. STATE PREDICATES: disabled/hot visuals come from FUN_0062e2a0/FUN_0062e320, not from the instance flags directly, so a control can look grey (0xff808080/0xffa0a0a0 paths) purely from framework enable/hover state even when your instance fields look correct.

### Model angle 2 - additional notes

**model_summary:** CREATION MODEL (EXE 06-14), verified from Ghidra decompilation of /Gw.exe (06-14).

GW::UI::CreateUIComponent == the frame-create primitive FUN_0062bfc0(parent, flags, child, proc, userdata, p6=0) -> returns frame id. Sequence:
1. Resolve parent: parent==0 -> FUN_0064d1c0() returns the global UI root record (DAT_00c0b958 - 0x128, asserts 0x19b if root not ready); else FUN_00647db0(parent) validates the parent id against the frame table (DAT_00bef81c[id], bound DAT_00bef824; assert 0x256 if invalid).
2. Allocate the frame record: iVar2 = FUN_0047f340("P:\\Code\\Engine\\Frame\\FrApi.cpp", 0x132). A cascade FUN_00633d40 / FUN_00635230 / FUN_006370b0 / FUN_006384c0 / FUN_00639830 / FUN_0063e230 zero-inits the frame's layout / anchor / render sub-structs. Record fields: +0x84=+0x88=+0x8c=0, +0x90=0x40 (default altitude/priority 0x40).
3. FUN_00646cf0(child): builds the child-linkage node, pulls a free id from the id freelist (DAT_00bef82c/834) or grows the table (FUN_00478570), writes the record pointer into the global frame table DAT_00bef81c[id], and increments live-frame count DAT_00c0b930.
4. FUN_0064bc00(root, child, p6): initializes the per-frame message-proc VECTOR and the intrusive sibling list; the frame's public id/handle is computed as (child != 0) ? child + 0x128 : 0 and stored at record[0]/record[2]; it also splices the frame into the parent's child list.
5. *(iVar2 + 400 / 0x190) = flags  -- THE STYLE FLAGS ARE STORED HERE. Every later style test reads this word: FUN_0062fe20(frame,mask) literally returns *(FUN_00647db0(frame) + 400) & mask.
6. FUN_00647320(proc, userdata): the TYPED-COMPONENT-CALLBACK REGISTRATION (details in creation_paths). Registers the primary control proc onto the frame, one-time global class-init (msg 5) the first time a proc type is ever seen, then fires msg 4 (install base vtable) to it.
7. Tail message pump: FUN_0064dc70(4,0,0); FUN_00647fc0(2,0,0); FUN_00647c80(10,0,0) drive the initial layout/create/notify passes down the proc stack.
8. return *(iVar2 + 0xbc) = the new frame id.

DISPATCH: FUN_0062ef40(frame,msg,wparam,out) is the public SendFrameUIMessage (asserts msg>=0x56 for the public range: 0xf2e/0xf2f). It resolves the frame (FUN_00647db0) then FUN_00647c80(msg,wparam,out). FUN_00647c80 walks the frame's proc vector from the TOP layer downward (piVar2 = *frame + count*3 ints; each entry = 3 ints / 0xc bytes: [0]=proc code*, [1]=state, [2]=userdata|0x80000000; entries with proc==0 or high-bit-clear flag are skipped) and calls FUN_00647cf0 on the first live layer. msg 9 and 0xb are rejected here (asserts 0x177/0x178) because they are lifecycle-internal, driven by the create/subclass paths, not the public pump.

PROC CONTRACT: FUN_00647cf0 builds the on-stack message context the proc receives as param_1: [0]=frame id (frame[5]), [1]=msg, [2]=&instance-data-pointer slot (so *(param_1[2]) is the control's instance struct), [3]=proc userdata|flag, [4]=frame altitude (frame[0x3a]), [5]=proc layer index; wparam and out are passed through. A proc handles msg in switch(param_1[1]); unhandled cases tail-call thunk_FUN_00647170 which forwards the SAME message to the next-lower layer (the super/base call). That single mechanism implements both the class hierarchy (base vtable installed via msg 4) and FrameNewSubclass two-layer stacking.

**creation_paths:** HOW A CONTROL IS INSTANTIATED

Primary path (CreateUIComponent = FUN_0062bfc0): allocate frame record, register in global table, store flags at record+0x190, then FUN_00647320(proc,userdata) does the typed-callback registration:
- FUN_00647320 maintains a GLOBAL SORTED REGISTRY of every distinct control proc ever used: base ptr DAT_00bef83c, capacity DAT_00bef840, count DAT_00bef844. It binary-searches this array for `proc`. If absent it inserts (keeping sorted) and immediately calls (*proc)(ctx, 0, 0) with ctx[1]=5 -> the one-time CLASS-INIT message (builds shared resources like the button image list). This registry IS the "typed component callback table": procs self-register their class on first use.
- Then it appends a triple (proc, state=0, userdata) into the FRAME's OWN proc vector (frame[0]=data ptr, frame[1]=capacity, frame[2]=count; stride 0xc), growing it with FUN_00473880/FUN_004738f0.
- Then it calls (*proc)(ctx, &createParam, 0) with ctx[1]=4 and createParam=parent-frame-id (local_4c) -> msg 4 INSTALL BASE VTABLE. The proc's case 4 writes its base/instance vtable into param_2[3]; a styled proc points param_2[3] at the flat base proc, establishing the class chain.
- The param_2==0 entry to FUN_00647320 is the inverse (finalize/reorder) path that re-fires msg 9 across the vector.

STYLE FLAGS (word at frame+0x190, read via FUN_0062fe20(frame,mask)=*(frame+0x190)&mask):
- 0x300 = base container/child flags used for plain child frames (CreateUIComponent(parent,0x300,child,proc,enc,L"")). Establishes a normal interactive child; without it a bare frame renders/hit-tests wrong.
- 0x40000 = PAINT GATE for styled procs. UiCtlBtnProc case 1 and case 0x15 do nothing unless this bit is set; this is why a styled button registered without 0x40000 is invisible.
- 0x8000 = checkbox/box-face select: UiCtlBtnProc uses FUN_0062fe20(frame,0x8000) (and 0x804000) to choose the checkbox/radio 9-slice face and the glyph from image list 0x010819cc instead of a plain button face.
- 0x20000 = accepts/propagates click activation (checked in CtlBtnProc case 0x24/0x2e via FUN_0062fe20(frame,0x20000) before forwarding the label click).
- 0x20128 = selectable-list style: makes the list proc FUN_00613850 allocate per-row selection state; combines the base container bits (0x128, the same +0x128 id-bias constant seen in FUN_0064bc00) with selection bits.

FrameNewSubclass (FUN_0062f150) -- LAYERING A SECOND PROC (two-layer controls):
- FUN_0062f150(frame, proc, userdata): validates frame (FUN_00647db0, assert 0x49b if 0), allocates a NEW layer slot index via FUN_00647fa0 (returns frame's proc-count-1 after ensuring capacity), then FUN_006483b0(frame, slotIndex, proc, userdata).
- FUN_006483b0 install: if the target slot already holds a proc it sends that OLD proc msg 0xb (destroy, ctx[1]=0xb) first; writes the new proc into slot[0] and userdata|0x80000000 into slot[2]; if a create-param object is present it also sends msg 5; finally sends the NEW proc msg 9 (OnFrameCreate, ctx[1]=9, wparam=&createParam) and re-sets the 0x80000000 live bit.
- Result: the frame's proc vector now holds a STACK of procs. Dispatch (FUN_00647c80) enters at the TOP layer; each proc handles what it wants and tail-calls thunk_FUN_00647170 to forward the same message down to the next layer. This is identical to the base-vtable super-call, so "two-layer controls" (e.g. outer CCtlEdit 0x008852e0 + render subclass 0x00888aa0; base CtlSliderProc 0x00615fe0 + wrapper UiCtlSliderProc 0x0087f440; base CtlPageProc 0x0061a950 + styled UiCtlPageProc 0x00885590) are just two entries in this vector, the wrapper on top forwarding to the base.

Anchor/pos/size after create: FUN_0062F770(frame,pos,size) validates the frame then FUN_0064a470(pos,size,6) -- anchor mode is HARD-CODED to 6. Callers create then immediately FrameSetPosition to give the frame real geometry.

KEY ADDRESSES: FUN_0062bfc0 create primitive; FUN_0064d1c0 root; FUN_00647db0 id->record; FUN_0047f340 record alloc (FrApi.cpp:0x132); FUN_00646cf0 table register; FUN_0064bc00 proc-vector init (id+0x128); frame+0x190/400 flags; FUN_00647320 typed registration (registry DAT_00bef83c/840/844); FUN_0062f150 FrameNewSubclass; FUN_00647fa0 slot index; FUN_006483b0 subclass install; FUN_0062ef40 dispatcher; FUN_00647c80 vector walk; FUN_00647cf0 proc invoke; thunk_FUN_00647170 super-call; FUN_0062fe20 flag test; FUN_0062F770 FrameSetPosition (anchor 6). Procs: flat CtlBtnProc 0x0060f4f0 (case4->006123a0, case9->006102b0); styled UiCtlBtnProc 0x00877e60 (case4->0060f4f0, paint gate 0x40000, checkbox 0x8000/0x804000, imglist 0x010819cc built msg5 via 0x0062d790).

**instance_struct:** Two distinct structs matter.

FRAME RECORD (allocated by FUN_0047f340 in FUN_0062bfc0; base pointer returned by FUN_00647db0(id)):
- record[0]/record[2] = frame id/handle (id-biased by +0x128).
- +0x84/+0x88/+0x8c = 0 (layout/rect scratch), +0x90 = 0x40 default altitude.
- +0xbc = the numeric frame id returned by CreateUIComponent.
- +0x190 (decimal 400) = STYLE FLAGS word (the create `flags` param); read by FUN_0062fe20.
- proc-vector holder: record[0]=proc-array data ptr, record[1]=capacity, record[2]=count. Each proc entry = 3 dwords (0xc): [+0]=proc code*, [+4]=per-layer state (sign bit = live/skip), [+8]=userdata | 0x80000000.
- record[5] = frame id used as ctx[0]; record[0x3a] = altitude used as ctx[4]; record+0x3a region is also the create-param scratch used by FUN_006483b0/FUN_00647320.

PROC MESSAGE CONTEXT (on-stack, built by FUN_00647cf0 / FUN_006483b0 / FUN_00647320; the proc's param_1):
- [0] = frame id, [1] = msg id, [2] = &instance-pointer slot (so *(param_1[2]) = control instance struct; instance created on msg 9), [3] = userdata|0x80000000, [4] = altitude, [5] = proc layer index. wparam=param_2, out=param_3.

CONTROL INSTANCE (allocated on msg 9, e.g. flat button = 0x2c bytes via FUN_006102b0): stores state flags (bit0=checked-ish, bit2=pressed toggled with ^4, bit1 toggled by 0x57), +4=text buffer, +0x18=image handle, +0xc/+0x14/+8=render metrics. Freed on msg 0xb.

BASE/DERIVED CHAINING: two mechanisms, both using the proc vector. (1) Class inheritance: msg 4 handler writes the base proc/vtable into param_2[3]; unhandled msgs are forwarded by thunk_FUN_00647170 to that base. (2) Runtime subclassing (FrameNewSubclass): pushes another (proc,userdata) triple on top of the vector; dispatch FUN_00647c80 starts at the top layer and each layer forwards down via thunk_FUN_00647170. A single frame therefore chains derived->base and outer-subclass->inner via the same super-call thunk.

**pitfalls:** - COLD CREATION crash/blank: (a) CreateUIComponent requires a valid, already-created parent (py_ui's CreateUIComponentByFrameId guards with parent && parent->IsCreated()); FUN_00647db0 asserts (0x256) on a stale/unrealized parent id, and FUN_0064d1c0 asserts (0x19b) if the root record isn't up yet. (b) A styled proc (UiCtlBtnProc) paints and size-queries ONLY when the 0x40000 paint-gate bit is present in the create flags stored at frame+0x190 -- create it without 0x40000 and it is invisible/zero-sized even though it exists and dispatches. (c) The control INSTANCE struct is allocated by the msg-9 (OnFrameCreate) handler at *(param_1[2]); if a proc that only implements msg 9 (no msg 4 base vtable) is registered as the PRIMARY callback it never gets its base installed, and procs that expect the instance (paint/accessors) dereference a null slot -> crash. Some controls (outer CCtlEdit 0x008852e0) MUST be a direct CreateUIComponent child so their msg-9 fires, not a frame-list item.
- SIZING/LAYOUT: CreateUIComponent gives no geometry; you must call FrameSetPosition (FUN_0062F770), which forces anchor mode 6, then invalidate. Preferred size comes from msg 0x15; controls with 0x40000 report a fixed styled-face size, plain frames report the container default (+0x90=0x40 altitude, rect fields zero at create).
- ENCODED TEXT: labels/names are ENCODED wchar payloads (name_enc/label go straight to CreateUIComponent; set-text via msg 0x5b takes an encoded string). Passing raw unencoded text can crash the text pipeline; the project resolves CreateEncodedText/SetFrameText separately.
- IMAGE LISTS are shared per proc-class, built once on msg 5 and stored in a global (button list DAT_010819cc); they are torn down on msg 6. Registering the same proc many times is fine (the global registry dedups), but the class resource must exist before paint or the glyph pass draws nothing.

**lifecycle_messages:** Message id is param_1[1] in the proc context; handlers verified on flat CtlBtnProc FUN_0060f4f0 and styled UiCtlBtnProc FUN_00877e60.

- msg 4 = INSTALL BASE / CLASS VTABLE. Fired from FUN_00647320 during primary registration (local_60=4, wparam=&createParam). Handler writes the base-class proc/instance-vtable into *(code**)param_2[3]. Flat CtlBtnProc case 4: *(code**)param_2[3]=FUN_006123a0 (its instance-alloc/vtable). Styled UiCtlBtnProc FUN_00877e60 case 4: *(code**)param_2[3]=FUN_0060f4f0 -- i.e. the styled proc declares the FLAT button proc as its base, so a two-layer button chains styled -> flat.
- msg 5 = one-time CLASS REGISTER / shared-resource init. Fired ONCE per proc type the first time FUN_00647320 inserts it into the global proc registry (DAT_00bef83c). UiCtlBtnProc case 5 builds the shared checkbox/radio image list DAT_010819cc = FUN_0062d790(0x11,7,0x12,...) (asserts 0x45 if already built). msg 6 = class teardown / free that image list (FUN_0046f9b0(DAT_010819cc)).
- msg 9 = OnFrameCreate: allocate the per-frame INSTANCE struct at the slot *(param_1[2]) and asserts if already set. Fired explicitly from the subclass installer FUN_006483b0 after a proc is layered (local_1c[1]=9, wparam=&createParam), and from the frame-realize path. Flat CtlBtnProc case 9 -> FUN_006102b0 allocates+zeroes the button instance.
- msg 0xb (11) = DESTROY: fired to the OUTGOING proc before a slot is overwritten (FUN_006483b0 sends 0xb to the old proc; teardown path). CtlBtnProc case 0xb frees instance sub-buffers (image at +0x18, text at +4) and releases the 0x2c-byte instance via FUN_005acaeb.
- msg 1 = PAINT. Styled UiCtlBtnProc case 1 is GATED by FUN_0062fe20(frame,0x40000): if the 0x40000 paint-gate style bit is clear it draws nothing and thunks through; if set it picks a 9-slice face (normal/hover/pressed/disabled and checkbox vs plain) and blits via FUN_0062b8e0. wparam *param_2 selects sub-pass 0 (background) vs 1 (glyph, drawn from image list DAT_010819cc via FUN_0062b290). Flat CtlBtnProc case 1 draws a flat filled rect (FUN_0062b2d0) colored by pressed/hover/disabled state.
- msg 0x15 (21) = SIZE-QUERY / preferred metrics: writes preferred width/height into out (param_3). Styled proc case 0x15 also gated by 0x40000 and returns the styled face's fixed dimensions (DAT_00bf4518.. or checkbox DAT_00bf4528..).
- msg 0x56-0x6a = control-specific GET/SET accessors (e.g. CtlBtnProc 0x56 set-image, 0x57 toggle-enabled bit1, 0x58 get-checked (flag&1), 0x59 get-radio (flag>>2&1), 0x5b set-text, 0x5f draw-label). These are the ids the public SendFrameUIMessage FUN_0062ef40 permits (its >=0x56 assert).
- Other observed: msg 8/0x38 layout, 0x13 measure, 0x24/0x2c/0x2e mouse click/hover toggling the pressed bit (^4) then FUN_0062bd40/FUN_0062f470 to invalidate+repaint, 0x3a text-append, 0x3b flag toggle.

### Model angle 3 - additional notes

**model_summary:** ANGLE 3 — INSTANCE STRUCT, BASE/DERIVED CHAINING, and LAYOUT/SIZING (Gw.exe 06-14, image base 0x00400000; offsets relative to the frame-record base R returned by FUN_00647db0(id) / FUN_0064d080()).

FRAME-RECORD STRUCT (R): each frame is one heap record allocated by create primitive FUN_0062bfc0 via FUN_0047f340("P:\\Code\\Engine\\Frame\\FrApi.cpp",0x132). Confirmed offsets:
- R+0xa8 = proc-node array pointer (the message-handler chain).
- R+0xb0 = node count.
- R+0xbc = frame id (create returns *(R+0xbc); it is the public handle).
- R+0xc0 = layout dirty/style flags (bit 0x100 = self placement dirty, bit 0x200 = subtree/child placement dirty).
- R+0xd0 = PLACEMENT/CONSTRAINT node (0x1c-byte layout struct filled by anchor setters).
- R+0xec/0xf0/0xf4/0xf8 = RESOLVED area rect left/top/right/bottom (floats) = the frame's actual box after layout.
- R+0x84..0x90 zeroed at create (0x90=0x40); R+0x190 (dec 400) = create style flags; R+0x1c4=0.

CONSTRAINT NODE (P = R+0xd0), written by FUN_0064a470 at P+8..P+0x18: P+8=anchor flags, P+0xc=left, P+0x10=top, P+0x14=right, P+0x18=bottom (floats). Anchor bits (identical in writer FUN_0064a470 and resolver FUN_006497d0): bit2=anchor-left, bit8=anchor-right, 0x0a=stretch-horizontal, none=center-horizontal (0.5=_DAT_009407b0); bit4=anchor-top, bit0x10=anchor-bottom, 0x14=stretch-vertical, none=center-vertical. Anchor 6=(2|4)=top-left absolute: left=x, right=x+w, top=y, bottom=y+h.

PROC-NODE CHAIN (base/derived): array at R+0xa8 of 0xc-byte nodes {+0 procFn, +4 instancePtr, +8 userdata}; most-derived node on top; FrameNewSubclass 0x0062f150 pushes one. Dispatch FUN_00647cf0 (via FUN_00647c80/FUN_0062ef40) walks top-down to the first non-null proc and calls proc(ctx,wparam,out), ctx={id,msg,&node.instance,wparam,userdata,index}; a proc reads its own state via *(ctx[2]). Derived forwards to base via thunk_FUN_00647170 (FUN_00647170) which rescans from ctx[5]-1 downward to the next non-null proc and re-dispatches against that node's instance slot; msgs 9 (create) and 0xb (destroy) are NOT forwarded.

PER-CONTROL INSTANCE STRUCT: allocated on msg 9, stored into node+4. Example flat CtlBtnProc 0x0060f4f0: 0x2c bytes (freed FUN_005acaeb(inst,0x2c)); +4/+8/+0xc text buffers, +0x14 length, +0x18 image handle, +0x24 width, +0x28 height (advertised to layout via msg 0x13). Visual state lives in the instance; geometry lives in R.

SIZING PIPELINE: setter (0x0062Fxxx page) writes the R+0xd0 constraint; resolver (0x0064xxxx page) turns it into R+0xec area. FUN_0062F770 (anchor-6) and FUN_0062F7B0 (explicit anchor) both do FUN_00647db0(id)->R, LEA ECX,[R+0xd0], FUN_0064a470(pos,size,anchor). FUN_0064a470 reads the CURRENT parent area (FUN_0064d080()->parentR, rect parentR+0xec..0xf8), computes parentW/H, writes P+0xc..0x18 per anchor bits, relinks P into the global relayout dirty list (DAT_00c0b934 prev / DAT_00c0b938 tail). Resolver FUN_006497d0 reads the constraint + current parent area and produces the final {l,t,r,b} stored to R+0xec. Driver FUN_00649f30 checks R+0xc0 dirty bits, re-links R+0xd0, calls FUN_00647fc0 (sends place-self msg 0x32 to own chain, place-children msg 0x31 to child frames at R+0xa8/R+0xb0), and re-resolves. Dirty-mark FUN_0062bd80(id,flag)->FUN_00636740(4,flag); relayout kick FUN_0062f110(id)->FUN_00649f30.

**creation_paths:** Create primitive FUN_0062bfc0 @0x0062bfc0(parent,styleFlags,child,proc,userdata,0): parent==0 -> FUN_0064d1c0 (root) else FUN_00647db0(parent); alloc record via FUN_0047f340("P:\\Code\\Engine\\Frame\\FrApi.cpp",0x132); run sub-object ctors; zero R+0x84..0x8c, set R+0x90=0x40; install proc FUN_00646cf0(proc); link parent/child FUN_0064bc00; store create flags at R+0x190; fire create msgs FUN_0064dc70(4,0,0)/FUN_00647fc0(2,0,0)/FUN_00647c80(10,0,0); return frame id at R+0xbc.

Subclassing: FrameNewSubclass @0x0062f150 pushes a {proc,instance,userdata} node onto R+0xa8 so a derived proc sits above the base; msg 4 lets each layer publish its base-proc pointer and msg 9 lets each layer allocate its own instance — this is how typed helpers stack (e.g. styled UiCtlBtnProc 0x00877e60 over base CtlBtnProc 0x0060f4f0). Style flags gate behavior: paint procs test create-flag bits (button paint-gate 0x40000, checkbox-face 0x8000) before drawing; R+0xc0 bits 0x100/0x200 gate whether FUN_00649f30 re-resolves self/subtree.

Placement setters (all share FUN_00647db0(id)->R, LEA ECX,[R+0xd0], call 0x0064xxxx worker): anchor-6 FUN_0062F770 @0x0062f770 -> FUN_0064a470(pos,size,6); explicit-anchor FUN_0062F7B0 @0x0062f7b0 -> FUN_0064a470(pos,size,anchor); single-arg FUN_0062F7F0 @0x0062f7f0 -> FUN_0064a660. Layout workers: constraint writer FUN_0064a470 @0x0064a470, area resolver FUN_006497d0 @0x006497d0, current-relation/parent-area getter FUN_0064d080 @0x0064d080 (returns *ctxptr-0x128, rect at +0xec..0xf8). WASM cross-ref (named): FramePlaceChildren(uint,wchar_t const*) @ram:809a7f5e and Coord2u overload @ram:809a7b74 both funnel to IFrame::CForm::Set(frame+0x48,name) — the form/layout registration path (FrApi.c assert 0x7ca).

**instance_struct:** Two structs. (1) Shared FRAME RECORD R (one per frame): R+0xa8 proc-node-array ptr, R+0xb0 node count, R+0xbc frame id, R+0xc0 layout dirty/style flags (0x100 self-dirty, 0x200 subtree-dirty), R+0xd0 constraint node, R+0xec/0xf0/0xf4/0xf8 resolved area rect l/t/r/b, R+0x190 create style flags. Proc nodes fixed 0xc bytes {+0 procFn, +4 instancePtr, +8 userdata}. Constraint node at R+0xd0: +8 anchor flags, +0xc left, +0x10 top, +0x14 right, +0x18 bottom (floats). (2) Per-CONTROL INSTANCE struct, allocated on msg 9, pointed to by node+4, accessed only through message handlers; flat CtlBtnProc 0x0060f4f0 instance = 0x2c bytes (+4/+8/+0xc text, +0x14 length, +0x18 image handle, +0x24 width, +0x28 height). Base/derived chaining: the message context is {id, msg, &node.instance, wparam, node.userdata, node.index}; a proc reads state via *(ctx[2]) and forwards to base by thunk_FUN_00647170 (FUN_00647170), which walks R+0xa8 downward (ctx[5]-1..0) to the next non-null proc and re-dispatches with that node's instance slot; msgs 9 and 0xb are intentionally not forwarded so create/destroy execute exactly once per layer.

**pitfalls:** WHY DIRECT CHILDREN GET MIS-SIZED (from FUN_006497d0 + FUN_0064a470):
1. Position/size are stored RELATIVE to the parent's resolved area, not absolutely. Both the writer FUN_0064a470 and resolver FUN_006497d0 fetch the parent box from FUN_0064d080() (the global CURRENT-RELATION frame, rect at parentR+0xec..0xf8) — never from an explicit parent arg. Final child rect = f(anchor bits, stored margins, parentW=parentR+0xf4-parentR+0xec, parentH=parentR+0xf8-parentR+0xf0).
2. COLD/blank: if FUN_0064d080() returns 0 (no relation context on the stack — i.e. touching the frame outside a layout pass, before the parent chain is pushed), FUN_006497d0 falls back to the DEFAULT full-screen rect {0,0,_DAT_00c0b9e4,_DAT_00c0b9e8}. The child is then sized against the whole screen instead of its parent, so it renders mislocated/full-screen — the classic "control created but blank/misplaced until the UI relayouts."
3. COLLAPSE: if the parent's own area (parentR+0xec..0xf8) is not yet resolved (still 0/stale because the parent wasn't relayouted first), parentW/H=0; center mode multiplies 0.5*0, stretch mode computes width = 0 - storedRight, so the child collapses to zero/negative. If parentRight<parentLeft the resolver asserts FUN_00487a80(0x238).
4. ANCHOR SEMANTICS: bits must match intent. 6 (=2|4, top-left) gives absolute (left=x,right=x+w,top=y,bottom=y+h); stretch modes 0x0a/0x14 reinterpret stored right/bottom as insets from the parent's far edge, so reusing top-left margins under a stretch anchor yields wrong extents.
FIX/ORDER: set geometry via FUN_0062F770/0062F7B0 only after the frame is parented; mark dirty (FUN_0062bd80) and let FUN_00649f30/FUN_0062f110 run a relayout so the parent's R+0xec area is resolved FIRST (parents before children, top-down via place-children msg 0x31). ENCODED TEXT / IMAGE LISTS: controls hold text in the per-instance struct (flat button inst+4, freed at destroy) and reference shared image lists (styled button list at 0x010819cc); these live in the instance (survive base-proc chaining) and must be torn down in the msg-0xb handler (which is not forwarded) to avoid leaks. Because msg 9/0xb are not chained, each subclass layer must allocate/free its own instance; forgetting the msg-0xb free in a layered control leaks that layer's instance.

**lifecycle_messages:** Dispatch: FUN_0062ef40(frame,msg,wparam,out) @0x0062ef40 asserts msg>=0x56, routes via FUN_00647c80 @0x00647c80 -> FUN_00647cf0 @0x00647cf0, calling the top node proc with ctx={id,msg,&instance,wparam,userdata,index}. Canonical handler sample = flat CtlBtnProc FUN_0060f4f0 @0x0060f4f0:
- msg 4 (install/base): writes the class base-proc pointer (case 4: *(code**)wparam[3]=base-proc).
- msg 9 (OnFrameCreate): FUN_006102b0(id,&instanceSlot,wparam) allocates the per-instance struct into node+4; asserts if already set; NOT forwarded to base.
- msg 0xb (destroy): frees instance (image handle inst+0x18, text inst+4) then FUN_005acaeb(inst,0x2c); NOT forwarded.
- msg 1 (paint): draws using wparam rect wparam[2..5]=l,t,r,b (FUN_0062b2d0 renders the quad).
- msg 0x13 (measure/preferred): if inst+0x24/+0x28 (w/h) set, writes out[1],out[2] then chains to base — how a control advertises intrinsic size.
- msg 0x15 (size-query): writes min/preferred vector out[0..3] (flat button = zeros, no minimum).
- msg 0x31 (place-children) / msg 0x32 (place-self): emitted by FUN_00647fc0 @0x00647fc0 during relayout — 0x32 to the frame's own proc chain, 0x31 to each child (array R+0xa8, count R+0xb0); drives recursive top-down layout.
- msgs 0x56-0x5f (button get/set: color, enable bit0, state queries, text/tooltip, draw-text) handled then fall through to thunk_FUN_00647170.
Every non-terminal case ends by calling thunk_FUN_00647170 (FUN_00647170 @0x00647170) to invoke the next base proc; it rescans R+0xa8 from ctx[5]-1 downward, rebuilds ctx against that node's instance slot (R+0xa8+index*0xc+4) and userdata (+8), and calls it — short-circuiting msgs 9 and 0xb so create/destroy run once per layer. Create-time msg burst inside FUN_0062bfc0: FUN_0064dc70(4,..) @0x0064dc70 (style-bit apply), FUN_00647fc0(2,..) (place), FUN_00647c80(10,..) (msg 0xa). Frame-id validate FUN_00647db0 @0x00647db0 (asserts 0x256).

## 2. Discovered UI Control FrameProcs (166)

| Control | EXE addr | WASM addr | Role |
|---|---|---|---|
| GmCtlColorPick (GmCtlColorPickProc) | 0x004dd0a0 |  | Color picker control (hue/sat swatch). Verified switch(param_1[1]). |
| GmCtlItemImage | 0x004ddab0 |  | Inventory item image / slot icon |
| GmCtlItemImage (GmCtlItemImageProc) | 0x004dde30 |  | Inventory/equipment item image slot. Verified switch(param_1[1]). |
| CtlLayout | 0x006018e0 |  | Layout / container frame (child arrangement) |
| CtlLayout | 0x00602190 |  | Frame layout/anchor manager (FUN_00602190 switch on layout op). Layout util, not a control frame pro |
| CtlEdit | 0x006034d0 |  | Single-line text input (engine base; outer wrapper CCtlEdit 0x008852e0) |
| CtlEdit | 0x00603cc0 |  | Text input / edit box (engine base, big switch 0x603cc0-0x60495c). Outer/styled edit is UiCtlEditBox |
| CtlTextMlProc | 0x00609360 | ram:80da0629 | Multi-line markup/rich text (anchors, inline images, hyperlinks). |
| CtlTextMl | 0x006099f0 | ram:80da0629 | Multi-line / markup rich-text label (hyperlinks, inline images, anchors). Assertion confirmed in cas |
| CtlTextMl (multi-line text) | 0x0060a530 |  | Multi-line/wrapped text control; FUN_0060a530 is the main worker (switch on message var). Proc tenta |
| CtlUtils | 0x0060cf40 |  | Control utility helpers (not a registered frame proc) |
| CtlView (CtlViewProc, container) | 0x0060d410 |  | Scrollable view/container frame; switch on message, falls to base thunk_FUN_00647170. Verified. |
| CtlBtn (CtlBtnProc, flat button) | 0x0060f4f0 |  | Flat/base clickable button frame proc; switch(param_1[1]) cases incl 0x24/0x2c click, 0x57 enable, 0 |
| CtlTextMlProc (MultiLine text label) | 0x00610c40 | ram:80da0629 | Multi-line text label; case 9 allocs 0x170 model ctx (CtlText.cpp:0x18a/0x18b, style 0x100000=CTLTEX |
| CtlImageList / UiCtlImageListProc | 0x00611410 | ram:8125a117 | Image-list resource control (indexed sprite atlas); OnContentAdd 0x81259aba |
| CtlImg | 0x00611890 | ram:8092d85f | Image / icon control (texture quad). Confirmed proc entry 0x611890 references CtlImg.cpp. |
| CtlDef | 0x00612240 | ram:80d9bfb9 | Control-definition / dialog layout container (builds child controls from a CtlSpec table). Swept pro |
| FUN_006123a0 (shared base control proc) | 0x006123a0 |  | NOT in the 39-type catalog. Common ancestor control MsgProc installed as base (case 4 → FUN_0062c370 |
| CtlFrameList | 0x00612ad0 |  | Frame-list container (list of child frames). Swept proc; selectable-row variant of same .cpp is CtlF |
| CtlFrameListProc | 0x00612c80 | ram:80e805f1 | Frame-list container: arranges arbitrary child frames as a scrolling list. |
| CCtlFrameListSelectable (selectable list | 0x00613850 |  | Selectable frame-list MsgProc; case 4 base &LAB_00612ad0; case 9 allocates selection-state (CtlFrame |
| CtlDropList (CtlDropListProc, dropdown/c | 0x006144e0 |  | Dropdown/combobox; main proc 0x006144e0, open-list create FUN_00614230 -> child list proc FUN_006154 |
| CtlDropList | 0x00615670 |  | Dropdown / combobox list control. Proc entry references CtlDropList.cpp (region 0x614230-0x615af5). |
| CtlSliderProc (slider base) | 0x00615fe0 | ram:80fcc337 | Base slider; case 9 allocs CtlSlider::CInstance 0x30 (CtlSlider.cpp:0x233); SetRange 0x56, SetValue  |
| CtlTextBtnProc (text/hyperlink button) | 0x00616c00 | ram:80d9ce76 | Engine text button; case 4 installs base FUN_006123a0; SetText 0x5F, color 0x5B/0x5D. NOT null-safe  |
| CtlTextSelectable (selectable text row) | 0x00617df0 |  | Null-safe selectable text-row proc used for hyperlink rows (item flags 0xe001); notifies parent 8 on |
| CtlProgress | 0x00618c90 |  | Progress bar / progress line (engine base). .cpp region 0x618c90-0x6196f2; styled variant is UiCtlPr |
| CtlProgress (CtlProgressProc, engine pro | 0x00618d00 |  | Base progress/gauge bar. Verified switch(param_1[1]). UI styled = UiCtlProgress 0x008812e0. |
| CtlEditAutoComplete | 0x00619c80 |  | Auto-complete dropdown attached to an edit control. Verified switch(param_1[1]). |
| CtlEditAutoComplete | 0x0061a3a0 |  | Auto-complete text edit |
| CtlPageProc (tabs base) | 0x0061a950 | ram:80e078f3 | Base tab/page control; case 4 base FUN_006123a0; case 9 allocs page ctx (CtlPage.cpp:599). Layer sty |
| CtlDragModel | 0x0061b630 |  | Drag-drop model (item drag ghost) |
| CtlScroll (CtlScrollProc, scrollbar) | 0x0061b9d0 |  | Scrollbar (thumb/track/arrows); references CtlScroll.cpp directly, instance vtable PTR_FUN_00a50798. |
| Ctl3dModel (Ctl3dModelProc) | 0x0061d100 |  | 3D model preview viewport control. Verified switch(param_1[1]). |
| CtlImeCand (CtlImeCandProc) | 0x0061d870 |  | IME candidate list control (engine). Verified switch(param_1[1]). |
| CtlImeReading (CtlImeReadingProc) | 0x0061e470 |  | IME reading/composition string control. Verified switch(param_1[1]). |
| CtlList | 0x0061eee0 |  | List box (generic list, large .cpp region 0x61eee0-0x623282). |
| CtlList (CtlListProc, list box) | 0x0061f740 |  | Generic list box control; row-insert helper FUN_0061eee0, create FUN_00621ad0 (embeds a CtlScroll).  |
| UiCtlDlg | 0x00876610 |  | Styled window/dialog frame (the app's top-level window control). Swept heavily; subclass/decorator p |
| UiCtlDlg (dialog/window) | 0x00876740 |  | Dialog/window frame (title, drag, close). FUN_00876740 is the only string referencer (if-chain dispa |
| UiCtlDlgProc (dialog/window) | 0x00876880 | ram:80e58a0d | Top-level window/dialog caption frame (title '%s [%s]', pin/close hit-regions); child-fill helper 0x |
| UiCtlBtnProc (styled button) | 0x00877e60 | ram:80df1d1e | Styled/textured 9-slice button MsgProc; paint gated on style 0x40000, checkbox face 0x8000, uses s_b |
| UiCtlTip | 0x00878950 |  | Tooltip control (hover tip; often attached as a subclass, as seen in sweep). FrameProc 0x878950-0x87 |
| UiCtlAnimSelection | 0x00879090 |  | Animated selection highlight (glowing selection ring/box). Swept proc; references UiCtlAnimSelection |
| UiCtlAnimSelection | 0x00879d50 |  | Animated selection highlight/marquee overlay. Verified switch(param_1[1]). |
| UiCtlModeIcon | 0x00879f40 |  | Mode / status icon control. Swept proc; references UiCtlModeIcon.cpp. |
| UiCtlModeIcon | 0x00879f50 |  | Mode/status icon control. Verified switch(param_1[1]). |
| UiCtlDistrict | 0x0087a4a0 |  | District selector control (map district dropdown). Swept proc; UiCtlDistrict.cpp region 0x87a4a0-0x8 |
| UiCtlDistrict | 0x0087aa90 |  | District selector control |
| UiCtlDistrict (district selector) | 0x0087aff0 |  | District/instance selector dropdown (large unit; FUN_0087aff0 dispatches + registers children). Proc |
| UiCtlHint (UiCtlHintProc) | 0x0087d230 |  | Inline hint text control. Verified switch(param_1[1]). |
| CGroupHeaderFrame | 0x0087ddc0 | ram:81192c89 | Composite group header (self-builds checkbox+caption children via TCtlInstance dispatcher FUN_008783 |
| UiCtlWebLink (UiCtlWebLinkProc) | 0x0087e250 |  | Clickable web-link text (opens browser). Proc dispatches on message var (iVar2). |
| TextShy (CTextShyFrame) | 0x0087f0d0 | ram:8149a9a7 | Cosmetic hover-fade text; case 4 sets base=FUN_00610c40 (CtlTextMl); case 9 allocs (UiCtlTextShy.cpp |
| UiCtlSliderProc (slider wrapper) | 0x0087f440 |  | Textured slider paint wrapper; case 4 sets base=FUN_00615fe0 (CtlSliderProc); case 1 draws bar/thumb |
| CtlDropListProc (Dropdown/Combobox) | 0x0087f5f0 | ram:80e3c9a3 | Dropdown/combobox MsgProc; case 9 creates internal child listbox via FUN_0062bfc0(parent,0x80,...);  |
| UiCtlProgress | 0x008801a0 |  | Styled progress bar (related variant proc 0x008812e0) |
| CtlProgressProc (ProgressBar) | 0x008812e0 | ram:80f6ce9a | Progress bar MsgProc; case 4 base &LAB_00618b70; image list DAT_01081a98 (sm_rateArrowImageList) via |
| UiCtlBulletProc | 0x00884f20 | ram:8134512b | Cosmetic bullet marker; case 4 base &LAB_00611400; case 5 builds bullet image list DAT_01081d68; cas |
| CCtlEdit (outer editable text) | 0x008852e0 | ram:80dee7ef | Outer edit-box control; case 4 base &LAB_00619c50; case 9 layers render subclass FUN_00888aa0 via FU |
| UiCtlPage tab-button proc | 0x00885340 |  | Textured per-tab button proc installed by UiCtlPageProc; case 8 draws tab image, case 0x15 size-quer |
| UiCtlPageProc (styled tabs wrapper) | 0x00885590 |  | Styled page wrapper; case 4 sets base=FUN_0061a950 (CtlPageProc); case 0x5e copies styling template  |
| UiCtlHideUi (UiCtlHideUiProc) | 0x00885c30 |  | Hide-UI toggle handle. Verified switch(param_1[1]). |
| UiCtlBtnToggleProc (checkbox) | 0x00886370 | ram:816b67fd | Toggle/checkbox button; case 4 sets base=FUN_0060f4f0 (flat btn) + style 0x10000 toggle; case 9 allo |
| UiCtlUrl (UiCtlUrlProc) | 0x00886690 |  | URL hyperlink control. Verified switch(param_1[1]). |
| UiCtlBtnExpandProc | 0x008867f0 | ram:80e7b6f7 | Expand/collapse toggle button; case 4 sets base=FUN_00877e60 (styled btn) and ORs style 0x30000; exp |
| UiCtlEditBox (UiCtlEditBoxProc) | 0x00888aa0 |  | Styled edit box render/proc (this is the known edit render subclass 0x00888aa0); outer wrapper CCtlE |
| UiCtlDropMenuEntry (UiCtlDropMenuEntryPr | 0x00888ef0 |  | Single row/entry inside a drop menu. Verified switch(param_1[1]). |
| UiCtlImeCand (UiCtlImeCandProc) | 0x00889480 |  | IME candidate window (UI-styled wrapper over engine CtlImeCand). Verified switch(param_1[1]). |
| <window-subclass frame procs> | 0x008895d0 |  | NON-catalog: representative bespoke window frame proc surfaced by the sweep. case 4 installs base pr |
| GmCtlSkImage (skill image) | 0x008c0430 |  | Skill icon image control (FUN_008c0430 create/dispatch; registers children). Proc tentative; texture |
| GmCtlSkList | 0x008c2460 |  | Skill list (module base; MsgProc within 0x008c2460-0x008c5a03) |
| GmCtlSkList (GmCtlSkListProc) | 0x008c3350 |  | Skill list control. Verified switch(param_1[1]). |
| GmCtlVirtualJoystick | 0x008c5b10 |  | On-screen virtual joystick (touch/movement). Verified switch(param_1[1]). |
| GmCtlSelection (GmCtlSelectionProc) | 0x008c65b0 |  | World/target selection reticle control. Verified switch(param_1[1]). |
| GmCtlSkCard (GmCtlSkCardProc) | 0x008c6750 |  | Skill card/tooltip panel (switch on message var uVar5). Proc likely 0x008c6750. |
| GmCtlSkProgress (GmCtlSkProgressProc) | 0x008c6e70 |  | Skill recharge progress overlay. Verified switch(param_1[1]). |
| GmCtlSkStat (GmCtlSkStatProc) | 0x008c7d30 |  | Skill stat display. Verified switch(param_1[1]). |
| GmCtlBadgeList (GmCtlBadgeListProc) | 0x008c8230 |  | Badge/notification list control. Verified switch(param_1[1]). |
| GmCtlSkCapture (GmCtlSkCaptureProc) | 0x008c8d30 |  | Skill-capture (signet of capture) UI. Verified switch(param_1[1]). |
| GmCtlSkImageEffect (GmCtlSkImageEffectPr | 0x008c91a0 |  | Animated effect overlay on skill image. Verified switch(param_1[1]). |
| GmCtlSkListContext | 0x008cbf30 |  | Skill list context/state |
| GmCtlSkListGroup (GmCtlSkListGroupProc) | 0x008cd0b0 |  | Group header within a skill list. Verified switch(param_1[1]). |
| GmCtlSkListEntry (skill list entry) | 0x008cde20 |  | Single skill row/entry (FUN_008cde20 create/dispatch). Proc tentative. |
| UiCtlPlace | 0x00923850 |  | Placement / anchor helper control (MsgProc within 0x00923850-0x00923ffa) |
| UiCtlPlace (placement) | 0x009238f0 |  | Placement/anchor helper control (FUN_009238f0 switch on message var). Tentative. |
| UiCtlStat (UiCtlStatProc) | 0x00924120 |  | Statistic/attribute display control. Verified switch(param_1[1]). |
| FrameDefProc | ? | ram:809a2041 | Root frame default message proc; ultimate fallthrough for all frames (thunk_FUN_00647170 chain). |
| CtlDefDlgProc | ? | ram:80d9b11c | Default dialog/container proc (CtlDef select/enable-children helpers). |
| UiCtlBtnGlassProc | ? | ram:80e0b7ed | Glass/translucent styled button variant |
| UiCtlBtnToggle | ? |  | Toggle button (checkbox-style styled button). |
| UiCtlScrollProc | ? | ram:80e0c369 | Styled scrollbar wrapper (global style flags). |
| UiCtlEditProc | ? | ram:80e0f5ab | Styled edit wrapper over CtlEdit. |
| UiCtlLabeledEditProc | ? | ram:8106165b | Edit field paired with a caption label (UiCtlLabeledEditGetLabelSize 0x81061576) |
| UiCtlDropListProc | ? | ram:80e47ca4 | Styled dropdown wrapper over CtlDropList. |
| UiCtlListProc | ? | ram:80e47693 | Styled list wrapper over CtlList. |
| UiCtlViewProc | ? | ram:80e584cc | Styled scroll view wrapper over CtlView. |
| UiCtlTextSelectableProc | ? | ram:80e0b8d5 | Styled selectable text row wrapper. |
| UiCtlLabelTextProc | ? | ram:80fdc7f6 | Styled text label. |
| UiCtlFadeProc | ? | ram:80dffca4 | Fade/alpha-transition overlay frame |
| UiCtlBorderProc | ? | ram:80e02ef0 | Decorative border/frame around content |
| UiCtlPlaceProc | ? | ram:8100e05e | Layout placeholder frame (CCtlLayout placement). |
| DlgMsgProc | ? | ram:80e536f8 | Message-box dialog proc. |
| UiCtlProgressActionProc | ? | ram:80f84519 | Styled progress variant (action); also Mission 80f85649, Slim 80f8665e, Stat 80f87697. |
| UiCtlImeCandProc | ? | ram:80e0def8 | Styled IME candidate window wrapper; UiCtlImeReadingProc wasm 80e0e1f2. |
| GmCtlColorPickerProc | ? | ram:81143e3b | Color picker control (game-layer; the only color-picker proc in the client). |
| CursorFrameProc | ? | ram:809357df | Cursor frame proc (mouse cursor rendering frame). |
| UiCtlBtnToggleProc | ? | ram:816b67fd | Two-state toggle button (pressed/unpressed latch) |
| UiCtlBtnExpandProc | ? | ram:80e7b6f7 | Expander/collapse chevron button |
| UiCtlBtnFloatingProc | ? | ram:812ab245 | Floating action button |
| CtlText / UiCtlLabelTextProc | ? | ram:80fdc7f6 | Static text label proc (single-line) |
| CtlTextMl (multiline text) | ? |  | Multi-line rich/wrapped text control (assertion string @0x00a4e814) |
| UiCtlTextShyProc | ? | ram:8149a8bf | 'Shy' text that hides/elides when space-constrained |
| UiCtlTextHeaderProc | ? | ram:811e887d | Section text header label |
| UiCtlHeaderProc | ? | ram:8144892b | Generic header bar |
| UiCtlEditBoxProc | ? | ram:80e0e3e0 | Styled edit box wrapper (border/background around CtlEdit) |
| UiCtlProgressMissionProc | ? | ram:80f85649 | Mission progress bar skin |
| UiCtlProgressSlimProc | ? | ram:80f8665e | Slim/thin progress bar skin |
| UiCtlProgressStatProc | ? | ram:80f87697 | Stat (health/energy) progress bar skin (EUiCtlProgressStatSkin) |
| UiCtlPageItemProc | ? | ram:80e09277 | Individual page/tab item entry |
| UiCtlDlgMsgProc | ? | ram:80e586ff | Message/modal dialog proc |
| UiCtlDlgCloserProc | ? | ram:80e5e206 | Dialog close ('X') button proc |
| UiCtlTitleFrameProc | ? | ram:80f52106 | Window title-bar frame |
| UiCtlTipProc (tooltip) | ? | ram:80e09f09 | Tooltip popup frame |
| UiCtlHintProc | ? | ram:80f067f5 | Hint/help bubble frame |
| UiCtlDropMenuProc (context/drop menu) | ? | ram:8118a057 | Drop-down/context menu container (CDropMenuFrame FrameProc 0x8118a13f) |
| UiCtlDropMenuBtnProc | ? | ram:811867fd | Button that opens a drop menu (CDropMenuBtnFrame 0x811868e5) |
| UiCtlDropMenuEntryProc | ? | ram:81188229 | Single menu entry/row (CDropMenuEntryFrame 0x81188311) |
| UiCtlBulletProc | ? | ram:8134512b | Bullet/list-marker glyph control |
| UiCtlModeIconProc | ? | ram:80efd147 | Mode/state icon control |
| UiCtlUrlProc (hyperlink) | ? | ram:80e48ccd | Clickable URL/hyperlink text (EUiCtlUrl regions) |
| UiCtlWebLinkProc | ? | ram:81208aff | Web/wiki link frame (CWebLinkFrame; wiki-mission bind) |
| UiCtlHideUiProc | ? | ram:80dfc871 | Hide-UI toggle frame (show/hide whole HUD) |
| UiCtlGapProc | ? | ram:811887c5 | Spacer/gap layout element |
| UiCtlStatFrameProc | ? | ram:814b068b | Stat display frame |
| UiCtlAnimatedSelectionProc | ? | ram:810aba46 | Animated selection highlight frame |
| UiCtlDistrictSelectorProc | ? | ram:813646a5 | District/region selector control (travel dropdown) |
| UiCtlImeReadingProc | ? | ram:80e0e1f2 | IME reading/composition window |
| UiCtlInputGuideProc | ? | ram:8134178d | Input/controller guide hint frame |
| UiCtlTaskProc (quest task) | ? | ram:817b6d22 | Quest task list row control |
| GmCtlColorPick (color picker) | ? |  | Game color-picker control (assertion @0x00946734) |
| GmCtlItemImage | ? |  | Item image / inventory slot control (draws item icon + qty). Referenced from proc region ~0x4dda17-0 |
| GmCtlSkImage / GmCtlSkList (skill contro | ? |  | Skill icon image + skill list/card/progress family (GmCtlSk*.cpp) |
| GmCtlVirtualJoystick | ? |  | On-screen virtual joystick (mobile) control |
| CtlEdit (editable text field, engine) | ? |  | Low-level editable text buffer/rendering (paint helper FUN_006033a0). Frame proc not positively isol |
| CtlDragModel | ? |  | Drag-and-drop data model (small unit, FUN_0061b650). Data model helper, not a paintable frame proc. |
| CtlUtils | ? |  | Shared control utility functions; no single frame proc. |
| CtlInstance (base template) | ? |  | TCtlInstance<T> template base for all controls (OnFrameCreate alloc/assert). Not a standalone proc. |
| UiCtlInstance (base template) | ? |  | UI-layer TCtlInstance base template. Not a standalone proc. |
| GmCtlSkListContext (skill list context) | ? |  | Context/state object for skill list (FUN_008cbf30/008cc550 helpers). Frame proc not isolated. |
| GmCtlTextureCache | ? |  | Texture cache backing skill/item icons (resource manager, not a frame proc) |
| CtlLayout | ? |  | Layout container / auto-arranger. Referenced from proc region ~0x601800-0x603000 (entry not individu |
| CtlView | ? |  | Scrollable view / viewport panel. Referenced from proc region ~0x60d4d0-0x60f135. |
| CtlImageList | ? |  | Image-list resource (frame image list, used by buttons e.g. imglist 0x010819cc). Region ~0x61144c-0x |
| CtlEditAutoComplete | ? |  | Auto-complete edit box (edit + suggestion list). Region ~0x619b90-0x61a895. |
| Ctl3dModel | ? |  | 3D model preview viewport control. Region ~0x61d2bb. |
| CtlImeCand / CtlImeReading | ? |  | IME candidate window / reading strip (Asian input). Regions ~0x508a4 / CtlImeReading.cpp. |
| UiCtlHint | ? |  | Hint / help popup bubble. Referenced from proc region ~0x87d266-0x87d280. |
| UiCtlTextShy | ? |  | Shy / auto-hiding text (fades when inactive). Referenced from proc region ~0x87f111-0x87f315. |
| UiCtlDropMenuEntry | ? |  | Single dropdown-menu entry row. Referenced from proc region ~0x888f5b. |
| UiCtlBullet | ? |  | Bullet / list-marker glyph control. Region ~0x884f75. |
| UiCtlHideUi | ? |  | Hide-UI toggle control. Region ~0x885e97-0x886220. |
| UiCtlStat | ? |  | Stat / attribute display control. Referenced from region ~0x924155-0x9244a2. |
| GmCtlColorPick | ? |  | Color picker control (dye/color selection). Referenced from proc region ~0x4dd538. |
| CtlInstance (base) | ? |  | TCtlInstance<T> base template — vtable/instance host, no standalone proc |
| GmCtlSelection | ? |  | Target/agent selection ring control (assertion string 0x00b9ae55; proc unmapped) |

## 3. Deep Catalog (40 controls)

### FrameDefProc  (EXE 0x0062c370 (FUN_0062c370), confidence: high)

- **WASM:** ram:809a2041 (named FrameDefProc(FrameMsgHdr const*,void const*,void*))
- **Struct:** FrameDefProc is STATELESS - it allocates no per-instance struct (no msg-9 install). Two structs matter:

FrameMsgHdr (hdr / param_1, the standard frame message header, int[]):
 +0x00 [0] HFrame frameId (index into frame table; 0 = invalid)
 +0x04 [1] uint  msgId (dispatch key; 1 = paint)
 +0x08 [2] void* wparam / proc-context (rewritten by CallBase to proc's context ptr)
 +0x0c [3] void* lparam
 +0x10 [4] void* proc-userdata (rewritten by CallBase from proc-array [+8])
 +0x14 [5] uint  currentProcIndex (position in the subclass proc chain; CallBase decrements toward 0)

Paint sub-pass struct (param_2 for msg 1):
 +0x00 uint/ptr paintGate - caller (FUN_006123a0 case1) does `if(*param_2==0) return;` before dispatching to base, so a null here suppresses painting.
 +0x08 Rect4f frameRect {left,top,right,bottom} floats (16 bytes) - fed to FrameContentAddImage.
 +0x18 uint colorLayerIndex (0..9) - index into s_layerColor; bound-checked (>9 asserts).
 +0x1c HGrMaterial** outHandle (optional; if non-null receives the created content handle).

Frame record (resolved from id by FUN_00647000/FUN_00647db0), fields used by CallBase walker FUN_00647170:
 +0xa8 procArray base (entries 0xc bytes: [+0]=code* proc, [+4]=context ptr, [+8]=userdata)
 +0xb0 uint procCount

s_layerColor table @ DAT_00bef564: 10 x Color4b (BGRA bytes): [0]=00,00,00,FF (black) [1]=20,20,20,FF [2]=80,80,80,FF [3]=FF,FF,FF,FF (white) [4]=80,80,80,FF [5]=80,80,80,FF [6]=FF,FF,FF,FF [7]=FF,FF,FF,FF [8]=00,00,00,20 (alpha 0x20) [9]=00,00,00,20.
- **Messages:** Signature: void FrameDefProc(FrameMsgHdr* hdr /*param_1*/, void* mparam /*param_2*/, void* mparam2 /*param_3*/), __cdecl.

Dispatch key is hdr[1] = msg id. FrameDefProc explicitly handles exactly ONE message; everything else is forwarded to the base walker.

- msg == 1 (PAINT / sub-pass) -> ONLY handled message. mparam is the paint sub-pass struct (see struct_layout). Logic:
  1. bounds-assert: if (uint)*(mparam+0x18) > 9 -> ErrorAssertion FrApi.cpp line 0x455 ("add.layer < arrsize(s_layerColor)"). This is the frame's color/layer index (0..9).
  2. mat = GrBuildSolidMaterial(&s_layerColor[idx] /*DAT_00bef564 + idx*4, a Color4b*/, 0x020003e0 /*material flags*/, 0)  (FUN_00679a60) -> HGrMaterial.
  3. layerIdx = *(mparam+0x18); outMatPP = *(void**)(mparam+0x1c) (optional out-handle pointer).
  4. frameId = hdr[0]; if frameId==0 -> assert FrApi.cpp 0xd61. if layerIdx>=10 -> assert 0xd62.
  5. frame = ResolveFrame(frameId) (FUN_00647db0); copy the frame rect from (mparam+0x08) into a local Rect4f via FUN_00630590.
  6. content = FrameContentAddImage(rect, uv0={0,0}, uv1={1,1}, mat) (FUN_00641e60); if null -> assert 0xd71.
  7. FUN_0066da30(2)  -> set EFrameContentLayer = 2 (Background) on the pending content.
  8. FUN_00665000(content, 0) -> set HGrModel = null (flat quad, no model).
  9. FUN_00635470(1, &content, layerIdx, outMatPP==0) -> attach the image content into the frame's draw list at layer=layerIdx.
  10. if outMatPP != 0 -> *outMatPP = content (return the created handle).
  11. HandleClose(mat) (FUN_0046f850) releases the transient material handle. Return.

- ALL other msgs (msg != 1): tail-call FUN_00647170(hdr, param_2, param_3) = the base/CallBase frame-proc-chain walker. It: validates hdr[0] (frame id) against the frame table; skips work entirely for msg 9 (OnFrameCreate) and 0xb (destroy); resolves the frame record; then decrements the current proc index hdr[5] and invokes the next-lower non-null proc in the subclass proc array (entry stride 0xc: [+0]=fn ptr, [+4]=proc context ptr, [+8]=userdata), rewriting a fresh header {[0]=id,[1]=msg,[2]=proc-context, [4]=proc-userdata}. If hdr[5] reaches 0 with no lower proc, it returns (FrameDefProc IS the terminal fallthrough, so the chain bottoms out here). Thus msgs 4/9/0xb/0x15/0x56-0x6a etc. are NOT interpreted by FrameDefProc itself; it either draws (msg 1) or forwards.
- **Create recipe:** You normally do NOT register FrameDefProc directly as a frame's proc - it is auto-installed as the terminal base proc by the frame system and provides the default solid-color background fill. Two realistic paths:

A) Implicit (normal): Create any frame via the create primitive FUN_0062bfc0(parent, flags, child, proc, userdata, 0) (sets *(frame+0xbc)=id). During the base-vtable install (msg 4), the base-frame installer (FUN_006123a0 case 4, or styled installer FUN_00886e80 msg 4) writes FrameDefProc into the base proc slot (`*(code**)param_2[3]=FUN_0062c370`, userdata 0). From then on, any paint (msg 1) that the higher control procs pass through / CallBase down to will hit FrameDefProc and fill the frame rect with s_layerColor[colorLayerIndex]. To control the color, set the frame's colorLayerIndex (the field delivered as paint param_2+0x18) 0..9.

B) Direct colored panel: register FUN_0062c370 as the frame's own proc via FUN_0062bfc0(parent, flags, child, FUN_0062c370, userdata=0, 0). Order/warm-ups: (1) the graphics/material subsystem must be initialized so GrBuildSolidMaterial (FUN_00679a60) works; (2) the frame must have a valid non-zero id and a valid screen rect before paint (frame id 0 -> assert 0xd61); (3) sizing: use the standard anchor-6 pos/size setter FUN_0062F770 to give the frame width/height - the fill uses the frame's own rect (mparam+0x08) with UV (0,0)->(1,1), so a zero-size frame paints nothing visible. No image-list or per-instance warm-up is needed (unlike UiCtlBtnProc); the material is built transiently each paint and closed immediately.

Content layering: the fill is added at EFrameContentLayer=2 (Background) with model=null, so foreground content of child controls draws over it.
- **Gotchas:** 1. colorLayerIndex out of range: paint asserts if *(param_2+0x18) > 9 (FrApi.cpp line 0x455) and again >=10 (line 0xd62). The color index field MUST be 0..9; feeding an arbitrary/uninitialized value crashes on the first paint.
2. Null frame id: if hdr[0]==0 during paint -> assert 0xd61. The frame must be fully created (valid id in the frame table) before it receives msg 1.
3. FrameContentAddImage failure: if FUN_00641e60 returns null (e.g. render/content subsystem not ready or out of content slots) -> assert 0xd71. Do not drive paint before the graphics content system is up.
4. CallBase (FUN_00647170) validity gate: it re-validates hdr[0] against DAT_00bef824/DAT_00bef81c frame table and asserts (0x256/0x221/0x223/0x24b) if the id is stale/out-of-range or the proc index hdr[5] exceeds the frame's procCount (+0xb0). A message header with a corrupted/forged frame id or proc index crashes here. It deliberately no-ops for msg 9 and 0xb, so do not expect FrameDefProc/CallBase to run create/destroy logic.
5. Material leak vs correctness: FrameDefProc builds a material every paint and HandleClose()s it after handing ownership to the content; this is by design. Do not cache mparam+0x1c out-handle beyond the frame's life - it points at engine-owned content.
6. Paint gate: the caller checks *(param_2)!=0 before dispatching paint to the base; a null paint sub-pass pointer silently skips the fill (not a crash, but explains "no background drawn").

### CtlDefProc (CtlDef default/base control class MsgProc)  (EXE 0x006123a0, confidence: high)

- **WASM:** ram:80d9bfb9 (0x80d9bfb9) — "CtlDefProc(FrameMsgHdr const&, void const*, void*)"
- **Struct:** FrameMsgHdr (param_1, const ref; 0x18 bytes, built/copied by chain walker FUN_00647170):
 +0x00 uint frameId
 +0x04 uint msgId
 +0x08 uint wparamA  (overwritten by walker to point at current subclass userdata entry, procArray+idx*0xc+4)
 +0x0c uint lparamB
 +0x10 uint extraC   (overwritten by walker with entry userdata dword)
 +0x14 uint subclassIndex (position in proc stack; walker decrements to find next lower non-null proc)
Frame record (resolve via FUN_00647db0/FUN_00647000(frameId)):
 +0xa8 ptr -> subclass proc array (entries 0xc bytes: [0]=proc, [4]=userdata, [8]=userdata2)
 +0xb0 uint proc count
 +0xbc uint parent frameId
 +0x190 (dec 400) uint flags; bit 0x1000 = accepts-focus/click-focus
Renderer message data consumed by base paint fn FUN_0062c370:
 +0x18 uint sub-pass/layer index (must be < 10; selects material DAT_00bef564[idx])
 +0x1c ptr -> out slot receiving the created background-quad frame
- **Messages:** Signature CtlDefProc(FrameMsgHdr const& hdr, void const* wparam, void* lparam). Dispatch on hdr+0x04 (msgId), valid range 1..0x24 via jump table addr@0x612518 / byte-index@0x612530. Handled cases:
- 1 PAINT/RENDER: wparam+0x00 = sub-pass index. If 0 -> return WITHOUT forwarding (base contributes nothing on pass 0). Else forward down subclass chain (the base quad renderer FUN_0062c370, resolved via msg 4, is invoked by the paint framework, not inline).
- 4 RESOLVE_BASE_VTABLE (get base render fn): writes FUN_0062c370 (root quad renderer) into *(wparam+0x0c), then forwards. Derived control procs (CtlBtnProc 0x60f4f0, CtlTextBtnProc 0x616c00, CtlPageProc 0x61a950, CtlSliderProc 0x615fe0, CtlTextSelectable 0x617df0, etc.) first write 0x6123a0 (CtlDefProc) into that same slot in their own case 4, then forward down so CtlDef overwrites it with the deepest renderer 0x62c370. Net: slot resolves to the root paint fn.
- 9 ON_FRAME_CREATE: FUN_0062d6f0(frameId, CtlDefProc) = assert FrameHasClass(frameId, CtlDefProc); on failure asserts CtlDef.cpp line 0x108 (264). NOT forwarded (chain walker skips msg 9).
- 0x20 NAVIGATE/directional-focus: walk parents (FUN_0062d330 = record+0xbc) to nearest ancestor having CtlDefDlgProc (FUN_00612240 @0x612240, wasm CtlDefDlgProc @80d9b11c). If found and wparam+0x00==0x16 (navigate event): wparam+0x08==4 -> CtlDefSelect(frame,3,focusPred,0); wparam+0x08==0 -> CtlDefSelect(frame,2,focusPred,0). FUN_00612560 = CtlDef::CtlDefSelect @80d9b86f; focusPred = FUN_006127c0 (returns 1 and sets focus if frame flag 0x1000). Then forward.
- 0x24 MOUSE_DOWN: if wparam+0x00==0 (left button) AND frame flag 0x1000 set (FUN_0062fe20(frame,0x1000) reads record+0x190) -> set keyboard focus FUN_0062e560(frame). Then forward.
- All other msgs (2,3,5-8,0xa..0x1f,0x21..0x23) and out-of-range default: forward unchanged down subclass chain via thunk_FUN_00647170 -> FUN_00647170. Msg 0xb (destroy) has NO case here and the chain walker itself early-returns for msg 9 and 0xb, so destroy is not propagated through this helper.
Companion CtlDefDlgProc (FUN_00612240) handles the dialog side: msg 2 (activate: auto-select first focusable child via CtlDefSelect), 0xc (enable/disable propagate FUN_006126a0 -> CtlDef::EnableChildren), 0x21 (deactivate: clear focus if this frame owns it), 0x24 (mouse: focus if no bits 6 set), 9 self-register assert CtlDef.cpp:0xaf.
- **Create recipe:** Not instantiated standalone — CtlDefProc is the shared DEFAULT/base control class layered beneath essentially every control (18+ derived procs reference 0x6123a0). To stand up a frame that uses it: 1) create the frame with the create primitive FUN_0062bfc0(parent,flags,child,derivedProc,userdata,0) (id stored at frame+0xbc). 2) The derived control proc must, in its case-4 handler, write 0x6123a0 into *(msgData+0x0c) (base-vtable resolution) and the framework must register CtlDefProc as a class on the frame (FrameAddClass) so the msg-9 assertion FrameHasClass(frameId,CtlDefProc) passes. 3) Layering order: CtlDefProc is the DEEPEST base; the concrete control proc(s) are layered above via FrameNewSubclass 0x0062f150. Warm-ups: CtlDef needs NO image-list/material preload of its own (unlike styled UiCtlBtnProc); it only relies on the engine-global render-layer/material array DAT_00bef564[0..9]. Sizing: none required by CtlDef; the derived control drives anchor-6 size via 0x0062F770. 4) Set frame flag 0x1000 if the control should take keyboard/click focus (otherwise msg 0x20/0x24 focus paths no-op). Destroy via native destroyer FUN_0062c550(id).
- **Gotchas:** 1. msg 9 (OnFrameCreate) HARD-asserts if the frame does not have CtlDefProc registered as a class -> CtlDef.cpp:264 (0x108). You must add CtlDefProc as a base class before create-time messages flow. 2. Base renderer FUN_0062c370: sub-pass index (renderData+0x18) must be < 10, else assert CtlDef.cpp:0xd62; also asserts frameId!=0 (0xd61) and quad-create success FUN_00641e60 (0xd71) — a null material (FUN_00679a60 on DAT_00bef564[idx]) or exhausted quad pool crashes. 3. Click/keyboard focus only fires when frame flag 0x1000 (record+0x190) is set; controls needing focus MUST set it or msg 0x24/0x20 silently do nothing. 4. Navigation msg 0x20 is safe with no dialog ancestor (just forwards), but the underlying CtlDefSelect asserts CtlDef.cpp:0x44 if a CtlDefDlgProc ancestor claims a child it cannot resolve. 5. Chain walker (FUN_00647170) asserts on stale/invalid frame ids: frameId>=DAT_00bef824 or freed slot -> asserts 0x256/0x221/0x223/0x24b. Never re-enter any message with a destroyed frame id. 6. Msg 0xb (destroy) is NOT dispatched to a case here and is NOT forwarded by the walker (walker early-returns for msg 9 and 0xb) — do not expect CtlDefProc to run cleanup on destroy; cleanup belongs to derived procs.

### CtlDefDlgProc  (EXE 0x00612240, confidence: high)

- **WASM:** ram:80d9b11c
- **Assertion file:** P:\Code\Engine\Controls\CtlDef.cpp (string @ EXE 0x00a501c0; assert msg "FrameHasClass(frameId, CtlDefDlgProc)" @ 0x00a501e4, used only by 0x00612240 -> unique resolution)
- **Struct:** NO per-instance control struct (stateless container class; msg 9 does not allocate). Operates purely on the shared Frame object obtained by FrameGetById (FUN_00647db0). Relevant Frame offsets used: +0xa8 = ptr to class-proc array (entries 0xc bytes: {proc, ?, userdata}); +0xb0 = class-proc count; +0xbc = cached EnumChild-result child frameId (return of FUN_0062caa0); +0x190 (dec 400) = style/flags dword read by FrameHasFlag (FUN_0062fe20 &mask). Flag bits referenced: 0x20 = skip/no-enable-broadcast child; 0x1000 = focusable (used by focus predicate FUN_006127c0); 0x10 = enabled-state toggled by FrameEnableChild.
- **Messages:** FrameProc FUN_00612240(int* hdr, int wparam, void* out); hdr[0]=frameId, hdr[1]=msg. Dispatch on hdr[1]:
- msg 2 (Activate/FocusIn): if wparam!=0 and FrameKeyGetFocus (FUN_0062e4b0) is NOT a descendant of frame (FrameIsAncestorOf FUN_0062e200 == 0): FrameEnumChild(frame,1,0) (FUN_0062caa0 -> first child) then CtlDefSelect(child) (FUN_00612560) to push focus into first selectable descendant; then chain to base. If focus already inside, just break->base.
- msg 9 (OnFrameCreate): asserts self is CtlDefDlg-classed via FrameHasClass(frame,FUN_00612240) (FUN_0062d6f0); calls FUN_00487a80(0xaf) (no-return) if not. NO instance allocation, NO state init -> control is stateless.
- msg 0xc (EnableChildren broadcast): FUN_006126a0(frame,wparam) recursively walks children (EnumChild dir 1 then 5); for each child NOT carrying flag 0x20 it calls FrameEnableChild (FUN_0062c9c0 -> toggles enabled-flag 0x10 via child msg 0xc) and recurses; then chain to base.
- msg 0x21 (Deactivate/FocusOut): if wparam!=0: EnumChild(first)+CtlDefSelect with focus predicate FUN_006127c0, and if this frame currently holds keyboard focus (FrameKeyGetFocus==frame) it releases focus via FrameKeySetFocus(0) (FUN_0062e560). Does NOT chain to base (break).
- msg 0x24 (Key/Nav): reads wparam; if (*(byte*)(wparam+4) & 6)==0 -> identical to msg 2 (move focus to first descendant + base); else break (ignored).
- msg 1,3-8,0xa,0xb,0xd-0x20,0x22,0x23 and default: pass straight through to base proc FrameMsgCallBase (thunk_FUN_00647170 -> 0x00647170), which chains to the next lower class proc in the frame's class-array (frame+0xa8, count frame+0xb0, 0xc-byte entries {proc,?,userdata}).
Note: NO paint (1), NO size-query (0x15), NO get/set control msgs (0x56-0x6a) are handled -> renders nothing and exposes no control-specific properties; it is a pure container/default-dialog behavior class. Sibling proc CtlDefProc (FUN_006123a0, same CtlDef.cpp) is the per-item def proc: handles msg 4 (writes drawcb FUN_0062c370), msg 0x20 (mouse 0x16 enter/leave -> CtlDefSelect modes 2/3), msg 0x24 (auto-focus if flag 0x1000).
- **Create recipe:** This is a BASE/default-dialog container class, not a leaf widget you paint. Recipe:
1) Create the container frame with the standard primitive FUN_0062bfc0(parent, flags, childId, dispatcher, userdata, 0) (observed flags 0x100000cc, dispatcher 0x0062ef00); frame id lands at frame+0xbc.
2) Install CtlDefDlgProc (0x00612240) into that frame's class chain BEFORE it receives msg 9: done in the frame-class msg-4 (install base/vtable) handler by writing 0x00612240 into the base-class slot and registering class-flag 0x1000 (exact pattern at EXE 0x004be132 and 0x0059764c: CALL 0x0062bfc0 then MOV [vtable],0x612240), or layer it with FrameNewSubclass (0x0062f150).
3) Add real controls (buttons/edits/lists) as children; CtlDefDlg then auto-manages tab-order, focus-in/out and enable/disable broadcast across them via CtlDefSelect (FUN_00612560) which walks EnumChild(dir 1/5)+FrameGetParent(FUN_0062d330) applying a focusable(flag 0x1000) predicate.
No warm-up needed: NO image lists, NO materials, NO encoded text, NO sizing/size-query (inherits base). It draws nothing itself.
- **Gotchas:** 1) msg 9 OnFrameCreate asserts (FUN_00487a80(0xaf), no-return) unless the frame genuinely carries CtlDefDlgProc in its class chain -> you must install the class before/at creation; never post msg 9 to a frame that isn't CtlDefDlg-classed. 2) Null-frame asserts: FrameHasFlag FUN_0062fe20 asserts 0x732 and FrameEnumChild FUN_0062caa0 asserts 0xbb0 on frameId 0 -> never let a 0 child/frame id reach the enable-broadcast or select walkers. 3) FrameEnableChild FUN_0062c9c0 asserts 0x683 on null. 4) CtlDefSelect/CtlDefRecurse (FUN_00612560/FUN_00612700) recursively deref the whole child subtree via FrameGetById; running msgs 2/0x21/0x24/0xc during teardown or on a partially-built hierarchy can deref freed/absent frames. 5) It silently no-ops (chains to base) for paint, size-query and all get/set property messages -> do not expect visual output or queryable state from this class alone.

### CtlImg  (EXE 0x00611890, confidence: high)

- **WASM:** ram:8092d85f
- **Assertion file:** P:\Code\Engine\Controls\CtlImg.cpp (OnFrameCreate alloc line 0x175=373; SetImage null-guard 0xe0)
- **Struct:** Instance = 0x3c (60) bytes (freed FUN_005acaeb(inst,0x3c)); slot at *(param_1[2]).
0x00 float dispW (payload[5]; also aspect numerator)
0x04 float dispH (payload[6])
0x08 float quadX0 - SCRATCH last-painted dest quad min.x (written each paint; read by 0x56/0x57)
0x0c float quadY0
0x10 float quadX1
0x14 float quadY1
0x18 int   hTexture - FUN_0046fda0(name) handle, freed FUN_0046f850 (payload[0]); PAINT GATE
0x1c float uvMaxU (payload[1]=uvMaxPxX/texW)
0x20 float uvMaxV (payload[2]=uvMaxPxY/texH)
0x24 float uvMinU (payload[3]=uvMinPxX/texW)
0x28 float uvMinV (payload[4]=uvMinPxY/texH)
0x2c ptr   auxBuf - nullable, elem 0x34, freed FUN_0047f3a0 (msg 0x59 only)
0x30 float auxCap
0x34 float auxCount
0x38 int   reserve (init 4)
Note: 0x08-0x14 not set by OnCreate; recomputed each paint.
- **Messages:** Dispatch on param_1[1]; param_1[0]=frameId, param_1[2]=&instanceSlot, param_2=payload.
8  = OnPaint -> FUN_00611df0(frameId, inst, paintCtx). Gate: hTexture(0x18)!=0 AND (paintCtx[0] & 0x20). Reads frame style word via FUN_0062fe20; scaling from bits: (&0xe000)==0 stretch-to-size; (&0x6000)==0 aspect-fit; (&0x4000) aspect-fill/crop. Draws textured quad via FUN_0062b2d0 using quad(0x08..0x14), tex(0x18), uv(0x1c/0x20 & 0x24/0x28).
9  = OnFrameCreate -> alloc 0x3c inst, zero aux fields, reserve(0x38)=4, store to slot; FUN_0062ede0(frame,0,-1); if *param_2 (create-data)!=0 do SetImage copy then FUN_0062bd40(invalidate)+FUN_0062f110(relayout).
0xb = OnDestroy -> free hTexture(0x18), free auxBuf(0x2c), zero 0x2c/0x34/0x30, free instance FUN_005acaeb(inst,0x3c).
0x24 = relay -> FUN_0062ee80(frame,8,payload,0).
0x25 = relay -> FUN_0062ee80(frame,7,payload,0).
0x26 = relay -> FUN_0062ee80(frame,9,payload,0).
0x38 = OnMeasure -> aspect-preserving fit of native size(0x00,0x04) into max(payload[0],payload[1]); writes fitted (w,h) to *payload[2].
0x56 = MapNorm->Pixel: input normalized (payload[0]=x, payload[1]=y) into last-painted quad(0x08..0x14), y flipped (1-v); writes *payload[2]. Asserts FUN_00487a80(0x238) if quad min>max.
0x57 = MapPixel->Norm: inverse; pre-zeros output; asserts 0x238 if rect invalid; no-op if zero-area.
0x58 = SetImage -> FUN_006121b0(frame,inst,payload): free old tex, load payload[0], copy payload[1..6] to 0x1c,0x20,0x24,0x28,0x00,0x04; invalidate+relayout. Asserts FUN_00487a80(0xe0) if payload==null.
0x59 = aux buffer append/resize (elem 0x34): grows buffer at 0x2c, updates count(0x34)/cap(0x30); overlap guard asserts 0x171; invalidates.
0xa, 0xc-0x23, 0x27-0x37, 0x39-0x55, default = no-op.
- **Create recipe:** From factory FUN_0060b650(ctx, texName, pos, size2f, texDims2f, uvMinPx2f, uvMaxPx2f, parentCtx):
1) frame = FUN_0062bfc0(parentFrame=*(parentCtx+0x18), 0 flags, isChild bool, proc=0x00611890, userdata=0, 0). Sets *(frame+0xbc)=id.
2) Style: plain -> FUN_0062ede0(frame,0,0xffffffff). Nested-in-parent -> FUN_0062ede0(frame,0x11,0) + FUN_0062fbf0(frame,parentId).
3) Build 7-dword SetImage payload: [0]=texture name/handle; [1]=uvMaxPx.x/texDims.x; [2]=uvMaxPx.y/texDims.y; [3]=uvMinPx.x/texDims.x; [4]=uvMinPx.y/texDims.y; [5]=displayW; [6]=displayH.
4) FUN_0062ef40(frame,0x58,&payload,0) (SetImage; also implicit in case 9 if create-data supplied).
5) FUN_0062f770(frame,pos2f,size2f) (anchor-6 pos/size setter 0x0062F770).
Warm-up: texture atlas for payload[0] must resolve in FUN_0046fda0 BEFORE SetImage or hTexture=0 (blank). UV rect selects atlas sub-region (min/max pixels / atlas dims). Order: create -> style/parent -> SetImage -> pos/size.
- **Gotchas:** 1) PAINT GATE (silent blank): draws only if hTexture(0x18)!=0 AND (paintCtx[0]&0x20). Unloaded texture => invisible.
2) NULL SetImage payload: msg 0x58 aborts FUN_00487a80(0xe0) on null pointer; same for create-data in msg 9.
3) payload[0] passed straight to FUN_0046fda0; 0 => blank (safe), garbage non-zero => loader crash.
4) COORD-MAP BEFORE FIRST PAINT: 0x56/0x57 read scratch quad 0x08-0x14 only written during paint; pre-paint it is degenerate -> 0x56 asserts 0x238 (min>max), 0x57 asserts 0x238/no-ops. Don't map coords before first paint.
5) AUX BUFFER msg 0x59: overlap/alias guard aborts FUN_00487a80(0x171).
6) LIFETIME: instance freed as exactly 0x3c; proc frees hTexture(0x18) and auxBuf(0x2c) on destroy - texture ownership transfers to control, don't double-free.
7) Instance size fixed 0x3c.

### CtlImageList / UiCtlImageListProc  (EXE 0x00611410 (registered via JMP thunk LAB_00611400: bytes E9 0B 00 00 00 = jmp 0x00611410; callers pass &LAB_00611400 as the FrameProc), confidence: high)

- **WASM:** ram:8125a117 (IUi::UiCtlImageListProc(FrameMsgHdr const*, void const*, void*)); OnContentAdd helper ram:81259aba (IUi::OnContentAdd(UiCtlImageList*, unsigned int, FrameMsgContentAdd const*))
- **Struct:** Per-instance struct = 12 bytes (0xC), allocated in msg 9 via FUN_0047f340("P:\\Code\\Engine\\Controls\\CtlImageList.cpp",0x97) and stored at *(param_1[2]) (the frame's control-instance slot). Freed via FUN_005acaeb(inst,0xC) in msg 0xB.
  +0x00 dword  HFrame  owning frame id (= *param_1, the frame handle). Used as target for FrameContentAddImage / invalidate.
  +0x04 dword  HFrameImageList  image-list/atlas handle. Ref-counted: FUN_0046fda0 = AddRef/clone-handle (asserts if *ptr==0), FUN_0046f9b0 = Release/Close. 0 = no image bound.
  +0x08 dword  unsigned int  image index/id within the atlas. Init 0xFFFFFFFF (= none/-1).
Extents come from the image object itself (not the struct): object+0x54 = width(int->float), object+0x58 = height (read by FUN_0063de20).
- **Messages:** FrameProc FUN_00611410(param_1=FrameMsgHdr*, param_2=wparam/in, param_3=out). piVar1=param_1[2] is the instance-slot pointer; msg id = param_1[1]. Unhandled ids fall through to thunk_FUN_00647170 = FrameMsgCallBase (base class default). Handled cases:
- msg 8  (OnContentAdd / paint-time content build): inst=*piVar1; if inst[1]!=0 (handle set) AND inst[2]!=-1 (id set): builds rect {x0,y0,w=param_2[1],h=param_2[2]} and calls FUN_0062b290 -> FUN_0062b0e0 = FrameContentAddImage(frameId, &rect, handle, id, layer=5, model=0) with uv 0..1 (0x3f800000). If handle==0 or id==-1 it adds nothing (renders blank, no crash). (WASM OnContentAdd adds aspect-fit/fill scaling for scale-modes 2/3; EXE path is the simple stretch add.)
- msg 9  (OnFrameCreate): asserts FUN_00487a80(0x96) if *piVar1!=0 (already created). Allocates 0xC-byte instance; inst[0]=frameId, inst[1]=0, inst[2]=0xFFFFFFFF; FUN_0062ede0(frameId,0,0xFFFFFFFF) primes frame content. If creation content param_2 (local_8=*param_2) non-null: assert 0x54 if *content==0, else Release old inst[1], inst[1]=AddRef(*content), inst[2]=content[1] (id), FUN_0062bd80(frameId,0x20) invalidate.
- msg 0xB (OnDestroy): assert 0x9c if *piVar1==0 (double destroy). Release inst[1] (FUN_0046f9b0), free inst (FUN_005acaeb,0xC), *piVar1=0.
- msg 0x24: forward -> FUN_0062ee80(frameId, 8, param_2, 0)  (FrameContentSetProperty, sub-id 8 — content property/align).
- msg 0x25: forward -> FUN_0062ee80(frameId, 7, param_2, 0)  (sub-id 7).
- msg 0x26: forward -> FUN_0062ee80(frameId, 9, param_2, 0)  (sub-id 9). (FUN_0062ee80 asserts if frameId==0 (0xf4c) or subid<7 (0xf4d).)
- msg 0x38 (GetImageExtents): reads inst[1]=handle(+4), inst[2]=id(+8). If handle==0 OR id==-1: write {0,0} into out at param_2[2]. Else FUN_0062da90(&extents, handle) (asserts 0xa74 if handle==0, 0xa28 if lookup fails) -> FUN_0063de20 fills {width,height} floats; copies 2 dwords to *(param_2[2]).
- msg 0x56 (GetImage): assert 0x3f if param_3==0. If handle(+4)!=0: *param_3 = AddRef(handle) (FUN_0046fda0), param_3[1] = id(+8). Else *param_3=0, param_3[1]=id. NOTE: returns an AddRef'd handle — caller must Close/Release it.
- msg 0x57 (GetImageId): assert 0x4c if param_3==0. *param_3 = id(+8).
- msg 0x58 (SetImageId only): inst=*piVar1; assert 0x5f if inst[1]==0 (no image list bound). inst[2] = param_2 (new id); FUN_0062bd80(frameId,0x20) invalidate. (Changes which sprite; requires a handle already set.)
- msg 0x59 (SetImage full = FUN_006117e0): assert 0x54 if *param_2==0. Release old inst[1]; inst[1]=AddRef(*param_2); inst[2]=param_2[1] (id); FUN_0062bd80(frameId,0x20) invalidate. Public wrapper: FUN_00604a70(frameId, handle, id) sends this via FUN_0062ef40(frameId,0x59,{handle,id},0).
- default: FrameMsgCallBase (incl. msg 4 install-vtable, size-query, etc.).
- **Create recipe:** Observed in FUN_005228e0 (representative CtlImageList child creation):
1) frameId = FUN_0062bfc0(parentFrameId, flags=0x80, childKind=1, proc=&LAB_00611400 (0x00611410), userdata=0, 0). The create primitive registers the proc and drives base install (msg 4) + OnFrameCreate (msg 9), which allocates the 0xC instance and returns id at frame+0xBC.
2) FUN_0062f5a0(frameId, layerIndex)  -- set draw/z order (e.g. 0).
3) Bind image: FUN_00604a70(frameId, imageListHandle, imageId)  -- sends msg 0x59 (SetImage). Use a valid AddRef-able atlas handle (game default seen: DAT_00c01a48 with id 0xFFFFFFFF for a blank slot). To later change only the sprite, send msg 0x58 (SetImageId) AFTER a handle is bound.
4) Position/size via the standard frame anchor system (Anchor-6 pos/size setter 0x0062F770); the image content is auto-emitted at paint (msg 8) sized to the content rect.
WARM-UP REQUIRED: a real HFrameImageList handle from the sprite/atlas subsystem must exist before msg 0x58 (SetImageId) or paint will render nothing. Passing imageId 0xFFFFFFFF is a legal 'no image' state (blank, no crash). Content struct for creation/msg 0x59 is {handle, id}; its *first dword (handle) must be non-zero.
- **Gotchas:** - msg 9 double-create: assert 0x96 if instance slot already non-null. Never re-send OnFrameCreate.
- msg 0x59 / creation content: assert 0x54 (FUN_00487a80(0x54)) if the content's first dword (*param_2 = handle) is 0. Always pass a valid handle.
- msg 0x58 SetImageId with no image list bound: assert 0x5f (inst[1]==0). Must bind a handle via 0x59 first before setting a bare index.
- msg 0x56 GetImage: assert 0x3f if out ptr param_3 is null. Also LEAKS if caller ignores returned handle — it is AddRef'd, caller must Release/Close (HandleClose).
- msg 0x57 GetImageId: assert 0x4c if out ptr null.
- msg 0xB destroy: assert 0x9c on double-destroy (slot already 0).
- msg 0x38 extents on invalid handle: guarded for handle==0/id==-1 (returns {0,0}); but a non-zero-but-invalid handle asserts inside FUN_0062da90 (0xa74 / 0xa28).
- AddRef path FUN_0046fda0 asserts 0x115 if the source content ptr is null, 0x117 if *ptr (raw handle) is 0.
- Paint (msg 8) requires BOTH handle!=0 AND id!=-1 to emit content; a bound handle with id -1 is silently blank (intentional, not a bug).
- Invalidate helper FUN_0062bd80 asserts (0xea8/0xea9) if frameId or flag arg is 0 — always call with frameId and 0x20.

### CtlTextMlProc  (EXE 0x00610c40, confidence: high)

- **WASM:** ram:80da0629
- **Assertion file:** P:\Code\Engine\Controls\CtlText.cpp (asserts :0x18a model-alloc, :0x18b base-alloc; runtime fatal codes 0x24b,0x428,0xbd,0xcc,0x1dd,0x171,0x108)
- **Struct:** Instance = a CtlText "model/string" object whose pointer is stored in the frame context slot at *(param_1[2]). Two shapes share one struct; the multi-line control always uses the MODEL shape.

BASE string object (vtable PTR_FUN_00a500d4 @0x00a500d4 -> [0]=dtor 0x006108c0, [1]=0x006109b0), built by ctor FUN_00610800:
 +0x00 void** vtable
 +0x04 wchar_t* text buffer (UTF-16)
 +0x08 (unused/aux = 0)
 +0x0c int charCount (length incl. NUL slot; == capacity in chars)
 +0x10 uint flags (init 0x80)
 +0x14 int cursor/charIndex (0xFFFFFFFF == -1 = "whole string / no selection" sentinel)
 +0x18 uint colorA / value field (init 0; foreground color, byte-compared in msg 0x5a/0x57)
 +0x1c uint valueB / context ptr (font-size/extra render arg in paint; also a pointer set by msg 0x5b)

MODEL extension (vtable PTR_FUN_00a50108 @0x00a50108 -> [0]=dtor 0x00610910, [1]=paint 0x00610a90; only when frame style has 0x100000):
 +0x20 void** subObjArray (base ptr of rendered glyph/run sub-objects)
 +0x24 int subObjArrayCapacity
 +0x28 int subObjCount
 +0x2c uint flags2 (init 0x40)
 +0x30 uint colorB (init 0xFFFFFFFF; tint/shadow color applied per sub-object via FUN_006641e0, byte-compared in msg 0x59)
 ...model paint scratch up to the ~0x170-byte allocation reported for the model ctx.
Style bits (read via FUN_0062fe20(frame,mask)) mapped to text-layout format flags at paint/measure: 0x100000=CTLTEXT_STYLE_MODEL(multi-line), 0x4000->fmt bit0, 0x8000->|2, 0x10000->|8, 0x20000->|4, 0x80000->|0x10(wrap).
- **Messages:** FrameProc FUN_00610c40(param_1=msg hdr[0]=frameId,[1]=msg,[2]=&ctxSlot; param_2=in; param_3=out builder). Switch cases (decompiler shows msg ids as denormal-float bit patterns; integer value = msg id). Unhandled msgs (incl. 0x1) fall through to thunk_FUN_00647170 = default forward to base/parent.
 0x04 INSTALL_CLASSPROC: *(code**)param_2[3] = class MsgProc FUN_006123a0 (installs CtlText class dispatcher; that proc's own case 9 asserts 0x108 if subclass install fails).
 0x08 PAINT: calls model->vtable[1] (0x00610a90) = renders the text run via FUN_0062bb30 and tints each sub-object with colorB(+0x30). Guarded: only paints when count!=0 && index(+0x14)!=-1 && (paintFlags&0x40).
 0x09 ONFRAMECREATE: if style 0x100000 set -> assert :0x18a, alloc+ctor model (vtable 0x00a50108, +0x20..=0, +0x2c=0x40, +0x30=-1); else assert :0x18b, alloc base string. Store into *ctxSlot. If arg(*param_2)!=0 set initial text via FUN_00632d90. Then defaults: FUN_0062ede0(frame,0,0xffffffff), FUN_0062ccd0(frame,0,0x30), FUN_0062ef00(frame,0x4c).
 0x0b DESTROY: if model!=0 call model->vtable[0](1) (frees text buffer + sub-obj array), *ctxSlot=0.
 0x38 MEASURE/size-query: if +0x14==-1 -> if style 0x80000 unset return {0,0}, else measure via FUN_0062d0e0; writes w/h to *(param_2[2]). If +0x14>=0 -> build format flags from style, measure substring via FUN_0062fee0 using font arg +0x1c; asserts 0x24b if +0xc<=+0x14.
 0x39 REFRESH: FUN_0062bd40(frame)+FUN_0062f110(frame) (invalidate+relayout).
 0x3a ATTACH/LAYOUT: +0x14=+0x0c (index=count), bump refcount FUN_005447e0, FUN_0062bd80(frame,0x40) invalidate, relayout, post msg 7 via FUN_0062ee80(frame,7,arg,0).
 0x4c TRIM/COMMIT: if +0x14 not 0/-1 -> assert 0x428 if +0xc<+0x14, then +0xc=+0x14, +0x14=-1, reassign text FUN_00632d90.
 0x56 GET_TEXT: assert 0xbd if param_3==0; param_3[2]=0; if count!=0 bump refcount + forward, else write single NUL into builder then forward.
 0x57 GET_VALUE: assert 0xcc if param_3==0; *param_3 = colorA(+0x18); forward.
 0x58 GET_SUBTEXT: index=+0x14; if -1 write NUL; else assert 0x24b if +0xc<=+0x14, copy (count-index) chars from +4+index*2 via FUN_005447e0; forward.
 0x59 SET_COLORB(model-only): assert 0x1dd if style 0x100000 unset; byte-compare/set +0x30, re-tint every sub-object via FUN_006641e0.
 0x5a SET_COLORA: byte-compare/set +0x18; if changed FUN_0062bd80(frame,0x40) invalidate.
 0x5b SET_CTXPTR: if +0x1c!=param_2 set +0x1c=param_2 then invalidate+relayout (LAB_00611256).
 0x5c SET_TEXT(index=-1): +0x14=-1; alloc buffer for param_2 string (FUN_00467680/FUN_0046da80), assert 0x171 on source/dest alias, +0x0c=newCount, reassign FUN_00632d90.
 0x5d SET_TEXT(index=0): same as 0x5c but +0x14=0, and additionally invalidate+relayout (LAB_00611256).
- **Create recipe:** 1) Create frame with the generic primitive FUN_0062bfc0(parent, flags, child, proc=0x00610c40, userdata, 0); the returned id lands at frame+0xbc. CRITICAL: flags MUST include 0x100000 (CTLTEXT_STYLE_MODEL) so msg 9 allocates the multi-line MODEL ctx (vtable 0x00a50108). Without it you get the single-line base string object and every model-only op (notably SET_COLORB 0x59) hard-asserts.
2) Optional text-layout style bits OR'd into flags: 0x80000 (word-wrap/multi-line height), 0x8000/0x10000/0x20000/0x4000 for alignment/format (translated to DrawText-style flags at measure/paint).
3) On the create dispatch (msg 9) pass the initial UTF-16 text pointer as arg0 (*param_2); it is copied via FUN_00632d90. May be 0 for empty. Defaults are auto-applied (FUN_0062ede0/FUN_0062ccd0/FUN_0062ef00).
4) Warm-ups: NONE like the styled button — there is no image-list gate (0x010819cc) and no material/checkbox-face requirement. Only the client font/text-layout system must be live (always is in-client). Do not pre-seed any image list.
5) Sizing: prefer self-measure — send msg 0x38 to get preferred {w,h}, or just anchor and let it size. Position/size via the anchor-6 setter 0x0062F770 after create. Do not force a zero height with wrap style expecting content.
6) Populate/update: set text with msg 0x5c (index=-1, static label) or 0x5d (index=0, also relayouts); set foreground with msg 0x5a; set model tint/shadow color with msg 0x59 (MODEL frames only). Read back with 0x56 (full text), 0x58 (substring from index), 0x57 (colorA value).
7) Destroy via the native destroyer FUN_0062c550(id); msg 0xb frees the text buffer and sub-object array.
- **Gotchas:** - FATAL FUN_00487a80(0x24b): charIndex(+0x14) must be strictly < charCount(+0x0c) whenever it is not the -1 sentinel; fires in msg 0x38 (measure), 0x58 (get-subtext), and model paint 0x00610a90. Landmine: msg 0x3a sets +0x14 = +0x0c (== count), so a paint/measure while index==count asserts; use -1 for "whole string".
- FATAL 0x428 (msg 0x4c TRIM): charCount(+0xc) must be >= charIndex(+0x14).
- FATAL 0x1dd (msg 0x59 SET_COLORB): control MUST have style 0x100000 (model). Calling the colorB setter on a non-model/base text frame is an unconditional crash — the single biggest gotcha for the multi-line variant vs single-line.
- FATAL 0xbd (msg 0x56) / 0xcc (msg 0x57): the output builder param_3 must be non-NULL.
- FATAL 0x171 (msg 0x5c/0x5d and ctor FUN_00610800): the source text pointer must NOT alias/overlap the control's own internal text buffer (+0x04); passing the control's own buffer back into SetText crashes. Copy to a separate buffer first.
- FATAL 0x108 (class MsgProc FUN_006123a0 case 9): subclass install FUN_0062d6f0(frame,proc) must succeed; means the frame must be created through the proper create pipeline.
- FATAL 0xf0d (FUN_0062ef00, hit during create defaults): frame id must be non-zero/valid.
- Soft (non-fatal, returns) asserts FUN_0047f340 at CtlText.cpp:0x18a/0x18b only warn on the model-vs-base alloc path; they do not halt but indicate style/flag mismatch (frame style 0x100000 not matching expected shape).
- Paint gate: text renders only when count!=0 AND index!=-1 style path plus the +0x14 range check — keep index=-1 and rely on a non-empty run; an empty (count==0) model draws nothing (no crash).

### CtlTextMlProc  (EXE 0x006099f0, confidence: high)

- **WASM:** ram:80da0629 (CtlTextMlProc(FrameMsgHdr const&, void const*, void*))
- **Struct:** Instance size 0x170 (92 dwords), freed with FUN_005acaeb(inst,0x170). Dword indices:
[0] +0x00 coded-text buffer (wchar_t*), default 0
[1] +0x04 buffer capacity (grow bookkeeping), 0
[2] +0x08 text length in wchars incl NUL (set len+1 by SetText)
[3] +0x0c 0x80 text-buffer grow chunk
[4] +0x10 hot/selected anchor index, default 0xffffffff (-1=none); folded into len on scroll/rewidth
[5] +0x14 filter fn ptr (SetFilter); gates msg 0x56
[6] +0x18 child/self frame id (=hdr[0])
[7..] +0x1c MarkupState block (default color/font/alignment/coord cursor); passed as (inst+7) to FUN_0060a530
[8] +0x20 anchor color, default 0xff64beeb
[9] +0x24 anchor grEffects, default 0x100
[0xa] +0x28 anchor hover color, default 0xff78d2ff
[0xb] +0x2c default text color (SetColor), default 0
[0xc] +0x30 grEffects (SetGrEffects), default 0
[0xd] +0x34 0xffffffff (base color/white)
[0xf] +0x3c 0
[0x50] +0x140 anchor-param TArray data ptr, 0
[0x51] +0x144 anchor array capacity, 0
[0x52] +0x148 anchor count, 0
[0x53] +0x14c 0x20 anchor grow chunk
[0x54] +0x150 image-material TArray data ptr, 0
[0x55] +0x154 image-material capacity, 0
[0x56] +0x158 image-material count, 0
[0x57] +0x15c 0x40 grow chunk
[0x58] +0x160 image-rect/list TArray data ptr, 0
[0x59] +0x164 image-rect capacity, 0
[0x5a] +0x168 image-rect count, 0
[0x5b] +0x16c 0x40 grow chunk
FrameMsgHdr (param_1): [0]=frameId,[1]=msg,[2]=&instancePtr.
- **Messages:** FrameProc signature FUN_006099f0(uint* hdr, void* wparam, void* out); dispatch on hdr[1]=msg. hdr[0]=frame id, *(hdr[2])=instance ptr (TCtlInstance<CtlTextMl>). Cases:
- 4 (implicit/default->break): base install handled by frame core.
- 8 OnAnchorPaintPass: gated on (*(float*)wparam bit 0x40); runs Markup engine FUN_0060a530 with content callback FUN_0060bcd0 to draw/collect anchor+image glyph quads for the visible line region (wparam[1],[2]=rect). No-op if hot anchor idx [4]==-1.
- 9 OnFrameCreate: allocates instance (FUN_0047f340 \"CtlTextMl.cpp\":0x75a, size 0x170) and stores at *(hdr[2]); inits defaults (see struct); if initial coded-text (wparam!=0) calls FUN_0060c2e0 (internal SetText); FUN_0062ef00(frame,0x4c) subscribes a msg; FUN_0062ccd0(frame,0,0x30) sets frame style. Does NOT assert on pre-existing instance.
- 0xb OnDestroy: FUN_0060c1f0 + FUN_0060c7e0 free anchor-param array; frees image-material array [0x54..0x56], image-rect array [0x58..0x5a], text buffer [0]; frees instance via FUN_005acaeb(inst,0x170).
- 0x31 OnHitTest/CoordQuery: decodes wparam token pair (wparam[1],[2]); resolves point->anchor and forwards msg 8 to self (FUN_0062ee80(frame,8,...)).
- 0x37 OnFontChanged/Reflow: clears image-material array [0x56]; FUN_0062c760(child); re-runs Markup FUN_0060a530 with size callbacks FUN_0060b650/FUN_0060bf00. Guards hot-anchor idx<len (assert 0x24b).
- 0x38 GetContentSize/Measure: runs Markup measure pass (callback FUN_0060be10), writes preferred {w,h} to *(out)=wparam[2]; guards idx<len (0x24b), rect sanity (0x238).
- 0x39 Invalidate: FUN_0062bd40(frame)+FUN_0062f110(frame) (request relayout+repaint).
- 0x3a OnPaint: FUN_0060c5e0(instance, wparam) — the render/layout builder: sends child msgs 9(measure),10(begin),7(commit content) and runs Markup FUN_0060a530 with add-content callback FUN_0060bc00; honors paint gate FUN_0062fe20(child,0x4000).
- 0x4c OnScroll/Rewidth: commits pending width (wparam[1]) then FUN_00632d90(child,text,width) reparse; folds hot anchor idx into length ([2]=idx,[4]=-1); bounds assert 0x428.
- 0x56 ResetIfFiltered: if filter [5]!=0 and text present, commits idx and FUN_00632d90 reparse (bounds 0x428).
- 0x57 GetAnchorText: FUN_0060c230(frame,wparam,out,0) -> anchor display text.
- 0x58 GetAnchorTextParam: FUN_0060c230(frame,wparam,out,1) -> anchor href/param string.
- 0x59 GetText (decoded): copies visible text tail from hot-anchor offset into out buffer; idx<len assert 0x24b, overlap 0x171.
- 0x5a GetTextCoded: copies full coded/markup buffer [0] (min(len,cap)) into out; overlap 0x171.
- 0x5b SetAnchorColor: Color4b wparam -> inst+0x20 ([8]); invalidates if changed.
- 0x5c SetAnchorGrEffects: uint -> inst+0x24 ([9]); invalidate.
- 0x5d SetAnchorHoverColor: Color4b -> inst+0x28 ([0xa]); invalidate.
- 0x5e SetColor (default text color): Color4b -> inst+0x2c ([0xb]); invalidate.
- 0x5f SetFilter: stores filter fn ptr (wparam) -> inst+0x14 ([5]); no invalidate.
- 0x60 SetGrEffects: uint -> inst+0x30 ([0xc]); invalidate.
- 0x62 SetText: FUN_0060c2e0(instance, wparam=wchar_t* coded text) -> frees anchors, reallocs buffer, [2]=len+1, [4]=-1, FUN_00632d90 reparse.
- 0x63/99 SetTextWithImageList (CtlTextMlSetDefaultListImage path): FUN_0060c360(instance, {wchar_t* text, uint count, void** imgFilenames}) -> builds inline-image materials into [0x58..0x5a] array, then sets text like 0x62.
- 0x0a,0x0c-0x30,0x32-0x36,0x3b-0x4b,0x4d-0x55,0x61: explicit break (ignored/handled by base). default: return.
Confirmed wrapper->msg map from Gw.wasm: SetText 0x62, SetColor 0x5e, SetFilter 0x5f, SetGrEffects 0x60, SetAnchorGrEffects 0x5c, GetText 0x59.
- **Create recipe:** Instance struct is created by the frame core on msg 9; you do NOT malloc it. Standard create (verified in GmTradeCart.cpp FUN_0053bb10):
1) child = FUN_0062bfc0(parentFrameId, /*flags*/0x300, /*childIndex*/N, /*proc*/FUN_006099f0 /*CtlTextMlProc*/, /*userdata*/0, 0). This returns the frame id and triggers msg 9 (instance alloc + default init). Optional initial coded text can be passed as the frame create's initial-data (wparam of msg 9); if non-zero it is SetText'd immediately.
2) FUN_0062f5a0(child, 0x15) — set control size/anchor style class (0x15) as trade-cart does.
3) Populate: FrameMsgSend(child, 0x62, codedText, 0) to set markup text; optional 0x5e SetColor, 0x5b/0x5c/0x5d anchor color/effects/hover, 0x5f SetFilter, 0x60 SetGrEffects, 0x63 SetText+imagelist.
4) Reads: 0x59 GetText / 0x5a GetTextCoded / 0x57 GetAnchorText / 0x58 GetAnchorTextParam.
Warm-ups: control needs a valid font (pulled from the child frame via FUN_0062d0e0) before paint/measure produce output; image tags in markup require the app image list / file archive; inline-image-list (msg 0x63) requires valid HGrMaterial-buildable filenames. Sizing: the control self-measures via msg 0x38 (writes preferred w/h) and reflows on 0x37/0x4c; give it a width and let markup wrap. Alt composite factory FUN_00623be0 builds a scroll page that embeds CtlTextMlProc via an edit/scroll wrapper (FUN_0060d410) using flags 0x20300 — use only if you need scrollbars.
- **Gotchas:** 1) Instance-null: nearly every case dereferences *(hdr[2]) as instance without a null check — sending any get/set BEFORE msg 9 (OnFrameCreate) crashes. Always create through the frame core so msg 9 runs first.
2) Msg 0x63 SetText+imagelist (FUN_0060c360) asserts: text ptr *wparam!=0 (0x852); if count wparam[1]!=0 the image-array pointer wparam[2] must be non-null (0x853) and each entry non-null (0x85c); material build must succeed (FUN_0065efa0 else 0x194) and image file must exist (0x180). Passing count>0 with a short/NULL-terminated array is a hard crash, not a soft error.
3) GetAnchorText/GetAnchorTextParam (FUN_0060c230): out buffer must be non-null (assert 0x79d).
4) Hot-anchor index must stay < text length: guarded by assert 0x24b in cases 8,0x37,0x38,0x59 — corrupting [4] or [2] crashes.
5) Text/image realloc overlap guard asserts 0x171 (memmove overlap) if source/dest buffers alias.
6) Rect/size sanity asserts 0x238 (measure) and 0x428 (scroll/rewidth width < committed).
7) Markup parser (ConvertParamSeries FUN_00609360 and friends) has hard asserts: null out param 0x2d3, tag-param index >0xb 0x2ed, bad param-type switch 0x35f; malformed tags mostly LOG (non-fatal via FUN_0060a490) but structurally bad input can reach these. Feed well-formed coded/markup wchar_t text.
8) Paint (0x3a) and measure (0x38) need a valid font from the child frame (FUN_0062d0e0); with no font the layout is empty (not a crash) but content is invisible.
9) Text passed to SetText is treated as coded/markup and stored as-is; it is parsed lazily on paint — do not free the source buffer expecting immediate parse errors.

### CtlTextBtnProc (Engine text/hyperlink button)  (EXE 0x00616c00, confidence: high)

- **WASM:** ram:80d9ce76
- **Assertion file:** P:\Code\Engine\Controls\CtlTextBtn.cpp (referenced in case 9 as FUN_0047f340("...CtlTextBtn.cpp", 0xa9); paint/get-text asserts at lines 0x24b, 0x171, 0x428, 0xe3)
- **Struct:** Per-instance struct = 0x38 (56) bytes. Ptr stored at *(param_1[2]); base created case 9 via FUN_0047f340(file,0xa9), freed case 0xb via FUN_005acaeb(inst,0x38). Fields (offset: init@case9 -> meaning):
+0x00: state/flags dword. bit0(0x1)=pressed/active. Set on mouse/key down (0x20,0x24), cleared on up (0x22,0x2e), toggled by enable msg 0x2c, tested by 0x56. Read as **(uint**)param_1[2].
+0x04: text buffer ptr (wchar_t*), init 0. Vector triple {ptr@+4, cap@+8, count@+0xc}.
+0x08: allocated capacity in wchars, init 0. Grown in append msg 0x60 (FUN_00473880/FUN_004738f0).
+0x0c: current text length in wchars incl terminator, init 0. Set = strlen+1 on SetText.
+0x10: 0x80 default (reserved/style param; not read within this proc).
+0x14: caret / highlight-run index. init 0xffffffff (-1)=none. Must satisfy index<+0x0c or FUN_00487a80(0x24b) fires.
+0x18: normal text color RGBA, init 0xff64beeb. get=0x57, set=0x5b.
+0x1c: hover/highlight text color RGBA, init 0xff78d2ff. get=0x58, set=0x5d.
+0x20: style/format flags, init 0x100. set=0x5c (triggers relayout).
+0x24: child sub-frame id array base ptr, init 0.
+0x28: child array capacity, init 0.
+0x2c: child array count, init 0.
+0x30: 0x40 default (reserved).
+0x34: broadcast value applied to each child frame (set=0x5e via FUN_006641e0 loop).
- **Messages:** Dispatch on param_1[1]=msg; param_1[0]=frame id, param_1[2]=&instance-ptr; param_2=msg payload/out. All non-early-return paths tail-call thunk_FUN_00647170 (chain to next proc).
4  InstallBase: *(param_2[3])=FUN_006123a0 (CtlBase text-container; it in turn installs frame base FUN_0062c370). 3-level vtable chain.
8  PaintSubPass: if len(+0xc)!=0 && caret(+0x14)!=-1: pick color +0x18(normal) or +0x1c (FUN_0062e320 hover state), style +0x20, draw char-run at buf+caret*2 via FUN_0062bb30; asserts 0x24b if caret>=len. Paint gate FUN_0062fe20(frame,0x4000).
9  OnFrameCreate: alloc 0x38 inst, init defaults above, store at *(param_1[2]); if *param_2!=0 treat as initial wchar text -> layout via FUN_00632d90; FUN_0062ef00(frame,0x4c) enables commit msg; FUN_0062c2a0(frame,1).
0xb Destroy: free child-id array entries (FUN_0046f850), free arrays, free text buffer, free instance FUN_005acaeb(inst,0x38).
0x20 Down (wparam 0x14/0x15/0x69=mouse/enter/space): set pressed bit0; if flag 0x2000 present notify FUN_0062ee80(frame,7,0,0).
0x21 invalidate FUN_0062bd40.
0x22 Up (0x14/0x15/0x69) & pressed: clear bit0 -> fire click (notify 7).
0x24 Activate(param==0): set pressed bit0; if flag 0x2000, notify 7 with wparam&1.
0x25 invalidate + notify FUN_0062ee80(frame,8,param_2,0).
0x2c Enable/disable (param_2[5]&1): set/clear bit0 from param_2[4].
0x2e UpOutside: clear pressed bit0 -> notify 7.
0x38 GetCaretPixelPos: writes POINT into param_2[2]; (0,0) if no caret; asserts 0x24b if caret>=len.
0x39 Relayout: FUN_0062bd40 + FUN_0062f110.
0x3a AppendChar/text: caret=len, append param_2[1] wchar string, relayout, notify FUN_0062ee80(frame,9,...).
0x4c CommitText: truncate len to caret(+0x14), caret=-1, relayout; asserts 0x428 if caret>len.
0x56 QueryPressed: if bit0 set break; else notify 7 (deactivate).
0x57 GetColorNormal: *param_2 = +0x18. NO NULL CHECK.
0x58 GetColorHover: *param_2 = +0x1c. NO NULL CHECK.
0x59 GetText: copy wchar buf(+4)+caret*2 into *param_2 (cap param_2[1]); writes L"" if caret==-1; asserts 0x24b if caret>=len.
0x5a GetRemainingLen: *param_2 = (len - caret) - 1 (0 if caret==-1); asserts 0xe3 if param_2==null (this one IS guarded).
0x5b SetColorNormal: +0x18=*param_2, invalidate.
0x5c SetStyleFlags: +0x20=*param_2, invalidate+relayout.
0x5d SetColorHover: +0x1c=*param_2, invalidate.
0x5e SetChildParam: +0x34=*param_2, broadcast to children via FUN_006641e0.
0x5f SetText: replace buffer with *param_2 wchar string, len=strlen+1, caret=-1, relayout; asserts 0x171 on buffer overlap.
0x60 SetTextTruncated: set text capped to min(strlen, param_2[1]); grows capacity; asserts 0x171 on overlap.
- **Create recipe:** 1) Create frame via primitive FUN_0062bfc0(parent, flags, child, proc=0x00616c00, userdata, 0) -> id stored at frame+0xbc. Optionally layer with FrameNewSubclass 0x0062f150.
2) Framework auto-sends msg 4 (install 3-level vtable chain FUN_0062c370<-FUN_006123a0<-0x00616c00) then msg 9 (OnFrameCreate): pass initial label text as msg param_2[0] = wchar_t* (may be 0 for empty). Instance (0x38) is auto-allocated; asserts if already set.
3) Position/size with the anchor-6 setter FUN_0062F770 (pos/size). No fixed intrinsic size; width follows laid-out text extent (query via msg 0x38 for caret pixel pos).
4) Set/replace label later: msg 0x5f (SetText, *param_2=wchar*) or 0x60 (truncated). Colors: 0x5b normal (default 0xff64beeb), 0x5d hover (default 0xff78d2ff). Style flags: 0x5c (default 0x100).
WARM-UPS: none. Unlike UiCtlBtnProc this is a pure engine text button — it needs only a valid text/font render context (FUN_00632d90 layout, FUN_0062bb30 draw). NO image list, NO material/atlas required. Do not confuse with styled UiCtlBtnProc 0x00877e60 which needs imglist 0x010819cc + paint gate 0x40000.
CLICK WIRING: click fires as notify code 7 (FUN_0062ee80 msg 7) on mouse/space up when the frame carries flag 0x2000; notify 8 on 0x25; notify 9 on append 0x3a. Parent proc receives these via the chain.
- **Gotchas:** 1) NULL-OUT GETTERS (primary): msg 0x57 (GetColorNormal) and 0x58 (GetColorHover) do `*param_2 = field` with NO null guard -> immediate write-through-null crash if an out-ptr isn't supplied. This is exactly the selectable-list hover crash: when a text button sits inside CtlTextSelectable/selectable-list rows, hover/hit-test paths poll color getter 0x57 with a null out buffer and fault. Note the asymmetry: 0x5a explicitly asserts FUN_00487a80(0xe3) on null param_2, but 0x57/0x58 were NOT given that guard.
2) CARET/LENGTH ASSERT: paint (msg 8), GetCaretPixelPos (0x38) and GetText (0x59) all assert FUN_00487a80(0x24b) when caret index (+0x14) >= text length (+0x0c). A corrupted or externally-set caret past the buffer end aborts the client. Keep +0x14 either -1 or < +0x0c.
3) COMMIT OVERRUN: msg 0x4c asserts FUN_00487a80(0x428) if caret(+0x14) > length(+0xc).
4) BUFFER-OVERLAP ASSERT: SetText 0x5f / SetTextTruncated 0x60 / Append 0x3a assert FUN_00487a80(0x171) if the source string memory overlaps the destination copy region — never pass a pointer into the control's own buffer as the new text.
5) Paint is gated by FUN_0062fe20(frame,0x4000): if that style bit is absent the button silently never draws its highlighted run (not a crash but a blank-control gotcha).
6) Destroy (0xb) frees with fixed size 0x38 and iterates child-id array at +0x24 — corrupting +0x24/+0x2c (count) yields OOB frees on teardown.

### CtlTextSelectable (selectable text row)  (EXE 0x00617df0 (FrameProc dispatch; thunk 0x006178f0/jump 0x00617900). Outer msg-0x61 patch wrapper FUN_0061d810 forces item-flag 1 before forwarding., confidence: high)

- **WASM:** ram:80dc7597 = CtlTextSelectable::CTextSelectable::FrameProc(FrameMsgHdr const&, void const*, void*). Outer registered proc ram:80dc74af = CtlTextSelectableProc; styled variant ram:80e0b8d5 = IUi::UiCtlTextSelectableProc. Public API: SetEnumeration 80dca120, SetSelectable 80dca27b, SetTextLiteral 80dca351, GetSelected 80dc9daf, GetSelectable 80dc9c2a, GetText 80dc9f34.
- **Assertion file:** P:\Code\Engine\Controls\CtlTextSelectable.cpp (passed to allocator FUN_0047f340 in case 9). Same file the deep-catalog seed listed as "CtlFrameList.cpp" — decompile proves it is CtlTextSelectable.cpp.
- **Struct:** Instance = 0x2c bytes (11 dwords), allocated at *(param_1[2]) in case 9, freed via FUN_005acaeb(inst,0x2c) in case 0xb. param_1 is the FrameMsgHdr: param_1[0]=frameId, param_1[1]=msg, param_1[2]=&instanceSlot. Instance getter FUN_00618aa0 = **(hdr+8) (asserts 0x74 if slot is null).
Fields (dword index / byte offset):
+0x00 [0] frameId (copied from *param_1).
+0x04 [1] isSelected flag (0/1). Set by msg 0x57, cleared by 0x56, read by 0x5a. Default 0.
+0x08 [2] isSelectable flag. Default 1. Set by 0x5d, read by 0x59; gates 0x57 (assert if 0), 0x25, 0x2c.
+0x0c [3] wchar_t* text buffer (allocated by FUN_00467680/FUN_0046da80; freed in 0xb/0x5e/0x5f). 0 = no text.
+0x10 [4] secondary/hit dword (0; zeroed on destroy).
+0x14 [5] text length in wchars incl. NUL (strlen+1). 0 = empty.
+0x18 [6] default = 0x80 (base text-color/style seed passed to DrawText path).
+0x1c [7] encoded-text resolve marker: 0xffffffff = fully resolved/literal; other = index of still-unresolved encoded segment. Drives msgs 0x3a/0x4c/0x18ad0. 0x5e sets -1, 0x5f sets 0.
+0x20 [8] render flags. Gets |=0x10 at create when frame flag 0x4000 is set (clip/ellipsis). Read by 0x59-family paint.
+0x24 [9] icon/enumeration image-list index. Default 0xffffffff (= no icon). Set by 0x5c, read by 0x58; drawn in msg 8 only when != -1.
+0x28 [10] icon x-offset (float). Set by 0x5c, read by 0x58.
- **Messages:** Dispatch on param_1[1]; unhandled/fallthrough forwards to base via thunk_FUN_00647170(hdr,body,out).
case 4  InstallBase: sets **(body+0xc)=FUN_006123a0 (base CtlFrame subclass proc, which in its own case 4 chains root FUN_0062c370). Establishes the subclass layer.
case 8  ContentAdd/render pass (FrameMsgContentAdd): builds layout rects; if body flag 0x40 set and icon[9]!=-1 emits self-msg 0x61 (draw icon) via FUN_0062efc0 using image-list DAT_00a504f8; if text[5]!=0 and resolve-marker[7]!=-1 emits self-msg 0x60 (draw text); then FUN_0062ef40(frame,0x62,body,0) to paint background/highlight.
case 9  Create (FrameMsgCreate): assert 0x61 if slot already set; alloc+init instance; *body = optional initial wchar_t* label copied into buffer; sets flag 0x10 if frame flag 0x4000; FUN_0062ef00(frame,0x4c); assert 0x84 if resolve-marker[7]==0; submits text for resolution via FUN_00632d90.
case 0xb Destroy: free text buffer, zero [3]/[4]/[5], free 0x2c-byte instance, null the slot.
case 0xc Hide/relayout: FUN_0062bd80(frame,0x40); if body==0 && isSelected notify parent 7.
case 0x15 SizeQuery: assert 0x103 if out null; writes hint {x=1.0, y=0, w=1.0, h=_DAT_00943278 default row height}.
case 0x24 Mouse-down/press: if selectable && *body==0: if not selected notify parent 8 (+capture check FUN_0062e3f0); test frame flag 0x2000 then repaint (0x62).
case 0x25 Mouse-leave: if selectable, FUN_0062bd40 relayout.
case 0x2c Focus/enter: if selectable && frame flag 0x8000 && not selected, notify parent 8.
case 0x2e Mouse-move/drag: if selectable && frame flag 0x2000 && body+0x10!=0 && *body==0 notify parent 9.
case 0x38 Measure content extent: FUN_00618910 computes text/icon pixel extents into out.
case 0x39 Invalidate: FUN_0062bd80(frame,0x40)+FUN_0062f110 relayout.
case 0x3a TextResolved (FrameMsgTextResolved): if resolve-marker[7]!=0, adopt resolved encoded string (marker=len), invalidate, notify parent 10 (text activated/resolved).
case 0x4c Show/activate: if resolve-marker[7]!=0, FUN_00618ad0 re-submits text for async resolution.
case 0x56 Deselect: assert 0x1a5 if not currently selected; isSelected=0; relayout.
case 0x57 Select: assert 0x1b2 if already selected; assert 0x1b7 if not selectable; isSelected=1; relayout.
case 0x58 GetEnumeration/GetIcon: assert 0x1c4 if out null; out[0]=iconIndex[9], out[1]=iconOffset[10].
case 0x59 GetSelectable: assert 0x1ce if out null; out[0]=isSelectable[2].
case 0x5a GetSelected: assert 0x1d7 if out null; out[0]=isSelected[1].
case 0x5b GetText: assert 0x1e0 if out null; copies buffer[7..len] (or a single NUL when marker==-1) into caller TArray<wchar_t>.
case 0x5c SetEnumeration(uint idx,float off): early-out if unchanged; sets icon[9]/offset[10]; relayout (0x40 + FUN_0062f110).
case 0x5d SetSelectable(int): if changed, sets isSelectable[2], relayout; if now 0 && selected, notify parent 7.
case 0x5e SetText(wchar_t*): if null clears text; else (re)alloc buffer only if differs, resolve-marker[7]=-1, resubmit; relayout.
case 0x5f SetTextLiteral(wchar_t*): as 0x5e but resolve-marker[7]=0 (literal, still gets one resolution pass); relayout.
case 0x60/0x61 Draw text/icon primitive: FUN_0062bb30 DrawText (greys to 0xff808080 when disabled via FUN_0062e2a0).
case 0x62 Paint background/highlight: if body flag 1 && icon set, picks tint 0xff404040/0xff808080/0xff969696 by hover/enabled (FUN_0062e320), builds material FUN_00679a60(0x20003e0), fills quad FUN_0062b2d0.
Parent notification codes seen: 7 (deselected-while-hidden), 8 (click/select), 9 (drag), 10 (text resolved/activated) via FUN_0062ee80.
- **Create recipe:** 1. Create a child frame under a selectable-list parent (list proc 0x00613850, list flags 0x20128) using the frame create primitive FUN_0062bfc0(parent, childFlags, childId, proc=FUN_00617df0, userdata, 0); the returned frame stores id at frame+0xbc. Item/hyperlink flags used by the list for these rows are 0xe001; the msg-0x61 wrapper FUN_0061d810 additionally ORs item-flag 1 for the paint path.
2. childFlags: set 0x4000 to enable width-clamp + clip/ellipsis (sets render flag 0x10) and the size-clamp branch in FUN_00618910; set 0x2000 to receive drag notifies (msg 0x2e→parent 9); set 0x8000 to receive focus-enter select (msg 0x2c→parent 8). Omit all for a plain non-interactive label.
3. FrameMsgCreate (msg 9) body[0] MAY carry an initial wchar_t* label; it is deep-copied into the instance buffer. The base subclass proc FUN_006123a0 is auto-installed at msg 4 and root proc FUN_0062c370 chained under it — do not install CtlTextBtnProc; this proc IS the drop-in replacement for CtlTextBtnProc inside selectable lists.
4. After create, drive via messages (or the public wrappers): SetTextLiteral 0x5f / SetText 0x5e for label; SetSelectable 0x5d(1) to make the row clickable; SetEnumeration 0x5c(iconIndex,xoffset) for a leading icon.
5. Sizing: the control self-reports via msg 0x15 as {relX=1.0, relY=0, relW=1.0, absH=_DAT_00943278 default line height}; let the list lay it out, do not hard-size height.
Warm-ups: (a) text is resolved asynchronously — after create, msg 0x4c/0x3a pump the encoded-string resolver (FUN_00632d90), so text may render one frame late; (b) to show an icon you MUST have registered the image-list referenced by DAT_00a504f8 and pass a valid index via 0x5c, otherwise leave icon index at default -1 (no icon, no crash).
- **Gotchas:** - Instance getter FUN_00618aa0 asserts 0x74 (P:\...\CtlTextSelectable.cpp) if ANY message except 4/9 arrives before Create or after Destroy — never message a row whose slot is null.
- Double-create: msg 9 asserts 0x61 if the instance slot is already populated.
- Create-time invariant: after FUN_0062ef00(frame,0x4c) msg 9 asserts 0x84 if resolve-marker[7]==0. Do NOT SetTextLiteral(0x5f, which sets marker=0) during the create message; set literal text only after Create completes.
- Select on non-selectable: msg 0x57 asserts 0x1b7 if isSelectable[2]==0, and asserts 0x1b2 if already selected. Call SetSelectable(1) before Select, and don't double-select.
- Deselect when not selected: msg 0x56 asserts 0x1a5. Track selection state.
- Null out-pointer on every getter: msg 0x15 asserts 0x103; 0x58 asserts 0x1c4; 0x59 asserts 0x1ce; 0x5a asserts 0x1d7; 0x5b asserts 0x1e0. Always pass a valid out buffer.
- Text-buffer overlap/length guards: assert 0x171 (source/dest buffers overlap during copy in create/0x5e/0x5f), assert 0x428 (resolve-marker index > text length in create/FUN_00618ad0), assert 0x24b (resolve-marker >= length in paint msg 8 / FUN_00618910). These fire if you feed a marker index past the string — only mutate text through the 0x5e/0x5f messages, never by poking [3]/[5]/[7] directly.
- Icon draw path (msg 8 / 0x61) dereferences image-list template DAT_00a504f8; setting icon index[9] != -1 without a registered image list will fault at render. Default -1 is the safe no-icon state.
- Paint gate: background/highlight (msg 0x62) only runs when body-flag 1 is set AND icon is present; the msg-0x61 wrapper FUN_0061d810 supplies that flag. If you bypass the wrapper and drive 0x61 directly, the highlight quad won't render.

### CtlBtn (CtlBtnProc) — flat/base engine button  (EXE 0x0060f4f0 (FrameProc/MsgProc). WASM: ram:80dbe9be. Assertion file: P:\Code\Engine\Controls\CtlBtn.cpp (alloc at line 0x1da). Base-class proc layered underneath = FUN_006123a0 (installed via case 4 into *(param_2[3])); its base = FUN_0062c370. Default fall-through = thunk_FUN_00647170 (DefFrameProc)., confidence: high)

- **WASM:** ram:80dbe9be (Gw.wasm named CtlBtnProc)
- **Struct:** Per-instance struct = 0x2C bytes (11 dwords), allocated in case 9 via FUN_0047f340("CtlBtn.cpp",0x1da), freed in case 0xb via FUN_005acaeb(inst,0x2c). Pointer stored at *(param_1[2]) i.e. *puVar3. Fields:
+0x00 uint flags — bit0(0x1)=CHECKED (toggled by 0x57; read by 0x58), bit1(0x2)=alt/secondary-image active (toggled 0x3b/0x5d), bit2(0x4)=PRESSED/PUSHED (toggled 0x24/0x2c/0x2e; read by 0x59). Init 0.
+0x04 wchar_t* text buffer (heap; freed on destroy). Init 0.
+0x08 uint text buffer capacity (chars). Init 0.
+0x0c uint text length (chars, from wcslen+1). Init 0.
+0x10 uint = 0x80 default (state/alpha byte; not re-read in this proc's own cases). 
+0x14 uint = 0xFFFFFFFF default — image/atlas frame index AND text-edit caret/selection marker (set -1 by 0x5c; consumed by 0x3a/0x4c IME edit path).
+0x18 texture/image handle (loaded by 0x5b via FUN_0046fda0; freed by FUN_0046f850 on destroy; drawn in paint layout as param_2[6]).
+0x1c void* callback userdata/context (set by 0x5a).
+0x20 void* secondary/highlight image pointer (set by 0x5d; float-compared ==0.0; wired via FUN_00630080/FUN_00630040).
+0x24 float measured content width — default -1.0 (_DAT_00937edc=0xBF800000); written by paint-layout (case 8) as param_2[9].
+0x28 float measured content height — default -1.0; written by paint-layout as param_2[10].
Dispatch block param_1: [0]=frame id, [1]=msg id, [2]=ptr-to-instance-ptr (puVar3). param_2=wparam payload, param_3=out/result.
- **Messages:** switch(param_1[1]):
case 1 PAINT-BG (sub-pass *param_2==0): draws filled rounded rect (corner radius _DAT_0093c89c=4.0, style 0x20003e0). Color: pressed/checked(0x58||0x59 set)=0xFF8080FF; else enabled=0xFF808080, disabled(FUN_0062e320==0)=0xFF404040. Rect inset by +1/-1px. FUN_0062b2d0 draw, FUN_0046f850 free brush.
case 4 INSTALL base vtable: *(code**)param_2[3]=FUN_006123a0 (layers base-class proc).
case 8 PAINT-LAYOUT/measure (FUN_0060ff50): computes image(+0x18)+text(+0x0c/+0x04) placement per scale mode, draws bg image (payload bit 0x10) and image (bit 0x40, needs +0x14!=-1), writes measured w/h to +0x24/+0x28. Asserts 0x238/0x24b on bad geometry, and requires +0x14 sel index < param_2[3] count.
case 9 ONFRAMECREATE (FUN_006102b0): alloc 0x2c inst, +0x10=0x80,+0x14=-1,+0x24/+0x28=-1.0; if wparam text non-null, copy caption into buffer; apply component style flags — 0x800000/0x4000 → text-align msgs(0x14,0x69,0x15), 0x2000 → msg 9 relay. Asserts CtlBtn.cpp:0x1da.
case 0xb ONFRAMEDESTROY: free image(+0x18), free text(+0x04), zero +0x04/+0x08/+0x0c, free 0x2c struct.
case 0xc/0x21/0x25/0x36 INVALIDATE/REDRAW: FUN_0062bd40(frame).
case 0x13 GET-CONTENT-SIZE: if +0x24>0 AND +0x28>0, out param_3[1]=+0x24, param_3[2]=+0x28 then base; else fall to base (default -1 = unmeasured → no size).
case 0x15 GET-BORDER/MARGIN METRICS: param_3[0..3] all = 4.0 (_DAT_0093c89c).
case 0x20 ONSTATECHANGE/ENABLE (FUN_0060f2a0): radio-group exclusive-select + push-button toggle + redraw; walks siblings (FUN_0062caa0 type5/6) sending 0x57=uncheck to peers when style 0x80000 (radio) set; fires notify 7/8/9.
case 0x24 ONCLICK/ACTIVATE (guard *param_2==0): if togglable, XOR pressed bit(^4), invalidate, and if style 0x20000 run FUN_0060f2a0 (selection).
case 0x2c ONMOUSEDOWN/DRAG-SELECT: sets pressed per payload[4]/[5] flags (bit ^4).
case 0x2e ONMOUSEUP: clears pressed(^4), and if payload[4]!=0 & not-push(0x20000) runs selection.
case 0x38 KEY/INPUT (FUN_00610580).
case 0x39 LAYOUT-INVALIDATE: FUN_0062bd80(frame,0x50)+FUN_0062f110.
case 0x3a IME/TEXT-INSERT: inserts wchars into buffer(+0x04/+0x0c), reflows, invalidate 0x40. Asserts 0x171 on buffer overlap.
case 0x3b TOGGLE-ALT(^2 bit1): FUN_00630080 w/ +0x20; invalidate 0x40.
case 0x4c COMMIT/DESTROY-CONTENT: commits edit text using +0x14 marker, resets +0x14=-1.
case 0x56 DO-CLICK (programmatic): if pressed bit(4) clear, run FUN_0060f2a0 (simulate click/select).
case 0x57 SET-CHECKED (bit0): sets/clears checked to match (param_2!=0), invalidate+notify. Used by radio-group to uncheck peers.
case 0x58 GET-IS-CHECKED: *param_3 = (*inst & 1); then base. ASSERTS if param_3==0 (0x152).
case 0x59 GET-IS-PUSHED: *param_3 = (*inst>>2 & 1); then base. ASSERTS if param_3==0 (0x15c).
case 0x5a SET-CALLBACK-USERDATA: *(inst+0x1c)=param_2; invalidate 0x10.
case 0x5b SET-IMAGE: frees old +0x18, loads texture from payload string (FUN_0046fda0)→+0x18; invalidate.
case 0x5c SET-TEXT (internal buffer copy): resets +0x14=-1, wcslen+copy into +0x04/+0x08; ASSERTS if param_2==0 (0x196) and on buffer overlap (0x171).
case 0x5d SET-SECONDARY/HIGHLIGHT-IMAGE: toggles bit1, sets +0x20 pointer via FUN_00630080/FUN_00630040; invalidate 0x40.
case 0x5e SET-TEXT (public CtlBtnSetTextLiteral) (FUN_00610420).
case 0x5f PAINT-TEXT sub-pass: draws caption (FUN_0062bb30) with enabled(0x00232323-ish)/disabled color, honoring payload flags.
default: thunk_FUN_00647170 → base proc chain.
- **Create recipe:** CtlBtnProc is the ZERO-dependency flat engine button — no image-list global (unlike styled UiCtlBtnProc @0x00877e60 which needs 0x010819cc), so it cannot crash on a missing image store. Recipe:
1. FrameCreate primitive FUN_0062bfc0(parent, component_flags, child_index, proc=0x0060f4f0, userdata, 0). New frame id read at frame+0xbc. (GWCA: GW::UI::CreateCtlButtonFrame / CreateFlatButtonWithClick.)
   - flags: 0x40000 = typical base clickable; add 0x10000 = push/latch toggle; 0x80000 = radio-group member (exclusive select, auto-unchecks siblings via 0x57); 0x20000 = toggle-on-click drives selection path; 0x2000/0x4000/0x800000 = caption text-alignment applied at create.
   - caption can be passed as the create wparam (case 9 copies it), OR set later.
2. FrameSetSize(id, w, h) — REQUIRED. case 0x15 reports only a 4px border metric and +0x24/+0x28 start at -1.0 (unmeasured), so without an explicit size the button renders as a thin strip. Typical 100x24.
3. Set caption: SendFrameUIMessage(frame, 0x5E, wchar_t* text, 0) (public setter) — or 0x5C for the raw internal copy.
4. FrameSetPosition(id, &Coord2f{x,y}) (anchor-6 setter 0x0062F770).
5. FrameMouseEnable(id, 1, 0) — required for hover/click.
6. (Optional) click delivery: FrameNewSubclass(parent, dialogSubclassType, 0) so notify ids 7(pushed)/8(clicked)/9 dispatch to the parent OnFrameNotify. Read pushed state anytime via msg 0x59, checked via 0x58.
Warm-ups: NONE required (no image list / material). Optional image via msg 0x5B (loads its own texture). Order that matters: create → size → text → position → mouse-enable.
- **Gotchas:** 1. NULL out/in pointer asserts (hard crash via FUN_00487a80): msg 0x58 (GET checked) needs param_3!=0 (assert 0x152); msg 0x59 (GET pushed) needs param_3!=0 (0x15c); msg 0x5C (SET text) needs param_2!=0 (0x196). Always pass a valid result/text pointer.
2. Buffer-overlap assert (0x171) on 0x5C and 0x3A: the source text buffer must not alias the control's own +0x04 buffer; pass an independent string.
3. Text must be a valid NUL-terminated wide string — 0x5C/0x5E call wcslen (FUN_0046c270); a non-terminated buffer overruns/crashes.
4. Paint-layout (case 8) asserts on inconsistent image geometry (0x238, 0x24b) and requires the selection index +0x14 to be < the payload count param_2[3]; only feed a valid image (via 0x5B) and don't force image draw (payload bit 0x40) with +0x14 still = -1.
5. Lifecycle: every non-create message dereferences the instance at *(param_1[2]); the frame must have completed OnFrameCreate (case 9) before any get/set — sending 0x57/0x58/0x5E to a half-created frame is a null deref.
6. Unlike the styled UiCtlBtnProc, this proc has NO paint-gate flag (0x40000) or image-list dependency, so it is safe to paint immediately after sizing; but it draws ONLY flat color rects + optional self-loaded image — do not expect a checkbox face (that is UiCtlBtnProc's 0x8000 path).
7. Corner-radius/border constants come from globals _DAT_0093c89c(=4.0) and default size _DAT_00937edc(=-1.0); relying on the proc for a default size fails (returns unmeasured), so an explicit FrameSetSize is mandatory to avoid an invisible/thin button.

### CCtlEdit (UiCtlEditBox — outer editable text-box control)  (EXE 0x008852e0, confidence: high)

- **WASM:** ram:80dee7ef
- **Assertion file:** Outer/render layer asserts: none in outer proc itself. Base chain assertion files (P:\Code\Engine\Controls\): CtlEditAutoComplete.cpp (autocomplete base FUN_00619c80, case9 line 0x78, dup-instance 0x77), CtlEdit.cpp (core base FUN_00603cc0, case9 lines 0xf11/0xf13, dup 0xf0f, destroy 0xf1b). Render subclass FUN_00888aa0 has no .cpp string (inline UI painter).
- **Struct:** TWO instances are allocated (both reached via param_1[2] -> instance ptr; core edit reached by FUN_0061a880(frame)=**(frame+8)).

CtlEditAutoComplete instance (FUN_00619710, 0x40 bytes, freed FUN_005acaeb(_,0x40)):
 +0x00 frame/context id; +0x04 suggestion-string buf ptr; +0x08 buf capacity; +0x0c string len(chars); +0x10 =0x80; +0x14 =0; +0x18 sentinel(0xdddddddd->0x24); +0x1c self-ptr list head (*p=p); +0x20 tree/list node ((int)inst+0x1d then inst-7); +0x24 =0x20; +0x38 =0x400. (autocomplete trie/dictionary node.)

CtlEdit CORE instance (FUN_00603000; word index shown):
 +0x00 (w0)  vtable &PTR_FUN_00a4df28 (or PTR_FUN_00a4e330 when multiline 0x80000)
 +0x04 (w1)  frame id (handle)
 +0x08 (w2)  selection-anchor / caret-start
 +0x0c (w3)  selection-end / caret
 +0x1c (w7)  =0x15 (msg/type tag)
 +0x20 (w8)  focus/active flag
 +0x24 (w9)  IME-initialized flag (set 1 in 0x21)
 +0x2c (w0xb)/+0x30 (w0xc) last mouse pos (set in 0x1b)
 +0x3c (w0xf) dragging flag (set 1 in 0x37)
 +0x40 (w0x10) caret-blink timer / capture id (0x21,0x50,0x51)
 +0x44 (w0x11) pending-action flag (0x37)
 +0x4c (w0x13) =0xffff first-visible/scroll index (set by 0x5a)
 +0x50 (w0x14) echo/value word (GET 0x56, SET 0x5b)
 +0x54 (w0x15) PRIMARY wchar text buffer ptr
 +0x58 (w0x16) primary buffer capacity (chars)
 +0x5c (w0x17) primary text length (+1 terminator)
 +0x60 (w0x18) =0x80 inline SSO buffer start
 +0x64 (w0x19..,=100) SECONDARY/composition buffer ptr
 +0x68 (w0x1a) secondary buffer base/capacity
 +0x6c (w0x1b) secondary buffer length
 +0x70 (w0x1c) =0x80 secondary inline
 +0x74 (w0x1d) =0xffffffff undo/mark index
 (multiline extra: words 0x24-0x35 zeroed, +0x36=0xffffffff line-cache).
- **Messages:** The control is a 4-layer proc stack; every layer forwards unhandled msgs to thunk_FUN_00647170 (walks the subclass/base chain). msg id = param_1[1]; param_2 = in/wparam, param_3 = out.

== OUTER UiCtlEditBox proc FUN_008852e0 (create THIS) ==
 4  install base: **(param_2+0xc)=&LAB_00619c50 (JMP->FUN_00619c80 CtlEditAutoComplete).
 9  OnFrameCreate: FUN_0062f150(frame, FUN_00888aa0, 0) -> layers the RENDER subclass (does not alloc its own instance).
 100(0x64) class descriptor query: copies 7-dword template PTR_FUN_00b96960 into param_3 = {0x00885620,0x00885100,1.0f,-1.0f,0,0,100.0f} (two callback procs + scale/default-size).
 default -> forward.

== RENDER subclass FUN_00888aa0 (layered, runs FIRST) ==
 1 paint, sub-pass=*param_2: 0=bg/border quad FUN_0062b8e0 (tex PTR_DAT_00bf46fc when focused[FUN_0062e2e0]/enabled[FUN_0056a410], else 00bf4700); 1=fill quad FUN_0062b2d0 tex DAT_01081d78; 0xc=caret/cursor FUN_0062b290 tex DAT_01081d80 with blink phase FUN_006275e0/FUN_006275f0; 0xd=fill FUN_0062b2d0 tex DAT_01081d7c.
 5 one-time GLOBAL resource init: builds DAT_01081d78/d7c (FUN_00679a60 textures) + DAT_01081d80 (FUN_0062d790 material 0x11); asserts FUN_00487a80(0x3c) if DAT_01081d78 already set. Then forwards.
 6 global teardown: frees the 3 handles, zeroes them, forwards.
 0xc invalidate FUN_0062bd40 then forward.
 0x15 size-query: param_3[0..3] = default {w=_DAT_00940ee0,h=_DAT_009407b8,...}.
 0x5f draw text FUN_0062bb30 (color = enabled?white:grey via FUN_0062e2a0, base 0x505050-0x5f5f60).
 0x60 get glyph/font: *param_3=FUN_007c3bc0(0x2a); param_3[1]=FUN_00878950; forward.
 0x61 get callback vtable: param_3[0..2]={FUN_00889480,FUN_00889560,FUN_0087d5d0}; asserts 0xd0 if param_3==0.

== CtlEditAutoComplete base FUN_00619c80 (via LAB_00619c50) ==
 4  install base *(param_2[3])=FUN_00603cc0 (CtlEdit core).
 9  assert 0x77 if *(param_1[2])!=0; FUN_0047f340("...CtlEditAutoComplete.cpp",0x78); alloc instance FUN_00619710 -> store at *(param_1[2]).
 0xb destroy: unlink dropdown, free instance (FUN_005acaeb, 0x40 bytes), *(param_1[2])=0.
 0x20 key: 0x1c->FUN_0061a030(1) (next suggestion), 0x1f->FUN_0061a030(0) (prev), else forward.
 0x21 focus change: blur destroys popup child (FUN_0062cfc0/FUN_0062c550); focus opens dropdown (FUN_0062fe20 0x8000000 -> FUN_00619b70).
 0x31 char: if param_2[1]==0 && param_2[2]==7 -> FUN_0061a1a0 (feed autocomplete) then forward.
 0x32 if param_2[2]==7 -> FUN_0061a570 (clear suggestions), *param_3=0, forward.
 0x37 mouse-down: reposition suggestion popup (anchor-6 FUN_0062f770 relative to caret).
 99(0x63) FUN_0061a3a0(param_2) set autocomplete word-list/config.

== CtlEdit CORE base FUN_00603cc0 (the real edit engine) ==
 1  paint FUN_00604f70.  3  style/init FUN_00605190.
 4  install base *(param_2[3])=FUN_006123a0; VALIDATES creation flags: assert 0x763 if (flags&0x1020000)==0x1020000; 0x770 if (flags&0x902000)==0x100000; 0x778 if (flags&0x500000)==0x500000; then flags|=0x1000.
 8  -> inner vtable[+0xc](param_2).
 9  assert 0xf0f if instance set; alloc core FUN_00603000 -> *piVar2. Branch on flag 0x80000 (multiline): if set, richer init (vtable PTR_FUN_00a4e330, words 0x24-0x36 zeroed, +0x36=0xffffffff, FUN_0060ca20).
 0xa -> inner vtable[+0x10](). 
 0xb destroy: call instance vtable[0](1) dtor, *piVar2=0 (assert 0xf1b if already 0).
 0xf tab/nav query.  0x15 size-query (assert 0x8a2 if param_3==0).
 0x18/0x19 create/destroy caret timer child (slot1, FUN_0062cfc0(...,1)).
 0x1a/0x1d create scrollbar children (slots 1/2) using callback vtable from msg 0x61; forward via 0x56.
 0x1b mouse-move: store pos inst+0x30/+0x2c, relayout.
 0x1c destroy child slot2.
 0x1e SET SELECTION: inst+8=start(*param_2), inst+0xc=end(param_2[1]/param_2[2]).
 0x1f FUN_00606c30.  0x20 -> vtable[+0x14] key handler.
 0x21 SET/KILL FOCUS: large handler (caret timers +0x40, IME setup flag +0x24, scroll reset +0x8/+0xc, FUN_0062ee80 notify 8/9).
 0x24 -> vtable[+0x18].  0x2c click-within-threshold -> grab focus.
 0x2f -> vtable[+0x1c].  0x31 -> vtable[+0x20].
 0x37 mouse-down: set caret from hit-point, begin drag (inst+0x3c=1).
 0x38 hit-test: point->char index (uses buffer inst+0x64/0x6c).
 0x39 relayout (LAB_0060492c: FUN_0062bd40+FUN_0062f110 invalidate).
 0x3a APPEND/INSERT text into secondary buffer (grows inst+0x68/+0x6c/+0x70).
 0x4c commit/flush composition (FUN_00632d90).
 0x50/0x51 timer ticks (caret blink, timer id inst+0x40).
 0x56 GET (echo/value word): *param_3=*(float*)(inst+0x50); assert 0x651 if param_3==0.
 0x57 GET TEXT: FUN_0046be40(out, inst+0x54, maxlen=param_2); if flag 0x100000 trims trailing space/ctrl; assert 0x659 if out==0.
 0x58 GET caret/length adjusted for word-break; asserts 0x66a (out null) / 0x66b (buffer word0x17 null).
 0x59 FUN_006078d0.
 0x5a SET first-visible/scroll index inst+0x4c (assert 0x69a if param_2==0).
 0x5b SET word inst+0x50 (echo/password char); may trigger IME FUN_00651850.
 0x5c SET TEXT: replace primary buffer inst+0x64 (FUN_004fed50 copy); empty string frees buffer & zeroes +0x64/+0x6c/+0x68; relayout.
 0x5d FUN_00607a50.  0x5e -> vtable[+8].  0x5f default draw FUN_0062bc20.

== generic frame base FUN_006123a0 ==
 4 install base FUN_0062c370 (root CtlFrame). 9 register FUN_0062d6f0. 0x20 accelerator (key 0x16 -> FUN_00612560). 0x24 activate FUN_0062e560.
- **Create recipe:** 1. Have a parent frame id ready.
2. Create the frame with the native primitive: FUN_0062bfc0(parent, flags, child_id, proc=0x008852e0, userdata, 0) -> returns id stored at frame+0xbc. USE THE OUTER PROC 0x008852e0 (UiCtlEditBox) — NOT the render subclass 0x00888aa0 and NOT the core 0x00603cc0; those are layered/base and asserted-into automatically.
3. Choose flags carefully (core case 4 validates): must NOT set (0x1020000 all), NOT (masked 0x902000)==0x100000, NOT (0x500000 both). Engine force-ORs 0x1000. Optional bits: 0x80000 = multiline (richer instance init), 0x100000 = single-line/trim-trailing-whitespace on GET 0x57. 
4. Engine automatically sends msg 4 (builds base chain UiCtlEditBox->CtlEditAutoComplete->CtlEdit->generic->root) then msg 9 (OnFrameCreate) which allocs BOTH instances (autocomplete 0x40B + core edit). Do not resend 9.
5. WARM-UP: on the very first edit box created, render-subclass msg 5 lazily builds shared textures DAT_01081d78/d7c and material DAT_01081d80 (FUN_00679a60 / FUN_0062d790). Global one-shot; no manual step, but the material/texture subsystem must be live before first paint.
6. Size/position: anchor-6 setter FUN_0062F770(frame_id,&pos,&size); or rely on 0x15 default {_DAT_00940ee0,_DAT_009407b8}.
7. Interact via dispatcher FUN_0062ef40(frame,msg,wparam,out): SET text = 0x5c (wchar* in wparam); GET text = 0x57 (out buffer, wparam=maxlen); SET selection = 0x1e; SET scroll = 0x5a; GET length = 0x58.
8. Destroy: FUN_0062c550(id) (native destroyer) triggers msg 0xb on each layer, freeing both instances.
- **Gotchas:** - Double OnFrameCreate: sending msg 9 twice asserts — autocomplete FUN_00487a80(0x77) (instance already set), core 0xf0f/0xf13. Never manually invoke 9 after creation.
- Accessing state before create: FUN_0061a880(frame) asserts 0x8a if **(frame+8)==0 (core instance not yet allocated). Any 0x18/0x1a/0x1e/0x5x message before msg 9 dereferences a null instance.
- FLAG VALIDATION in core case 4: illegal flag combos hard-assert: (flags&0x1020000)==0x1020000 -> 0x763; (flags&0x902000)==0x100000 -> 0x770; (flags&0x500000)==0x500000 -> 0x778. Pick flags to avoid these.
- Render subclass msg 5 double-init: asserts FUN_00487a80(0x3c) if DAT_01081d78 already non-null — do not re-trigger global resource init.
- Null out-pointer on GET/size messages: 0x15 core asserts 0x8a2; 0x56 asserts 0x651; 0x57 asserts 0x659; 0x58 asserts 0x66a (out) / 0x66b (empty text buffer); render 0x61 asserts 0xd0; 0x5a set asserts 0x69a if wparam null. Always pass a valid out/param buffer.
- Encoded-text requirement: text is wchar (UTF-16); 0x5c/0x57 operate on wide strings via FUN_004fed50/FUN_0046be40. Passing a byte string corrupts length math (FUN_0046c270 counts wchars).
- Destroy ordering: case 0xb core asserts 0xf1b if instance already 0 (double free); autocomplete 0xb frees exactly 0x40 bytes — size mismatch corrupts heap. Use FUN_0062c550 rather than freeing the instance directly.
- Paint gate: the render subclass only draws when the frame is paint-eligible; texture handles (DAT_01081d78/d7c/d80) must be initialized (msg 5) before first paint or the paint quads reference null texture ids.

### CtlScroll (CCtlScroll / CCtlHorizontalScroll scrollbar)  (EXE 0x0061b9d0, confidence: high)

- **WASM:** Gw.wasm has no single MsgProc; the class is split into named per-message virtual handlers clustered at ram:80db719a-ram:80dbc2xx (CCtlScroll::~CCtlScroll 0x80db719a, OnAdvancePre 0x80db71df, OnContentAdd 0x80db75f6, OnKeyDown 0x80db843d, OnMouseDown 0x80db8890, HitTest 0x80db8c16, RepeatNotify 0x80db95e5, OnMouseMove 0x80db9a06, OnIncPos 0x80dba56d, Calc*Rect 0x80dbaca7+, accessors CtlScrollCanScroll 0x80dbb97a / GetPageSize 0x80dbbbc9 / GetRange 0x80dbbd3f / GetActiveElement 0x80dbbe15 / GetPosition 0x80dbbf8b / IncPosition 0x80dbc101 / IncPositionInstant 0x80dbc1d7). Horizontal subclass CCtlHorizontalScroll overrides the geometry vtable slots (Calc*Rect/RangeTop/RangeBottom/ThumbTop/ThumbBottom/IsAbove) at 0x80dbb315+.
- **Assertion file:** P:\Code\Engine\Controls\CtlScroll.cpp (lines seen: 0x231 anim-struct alloc, 0x4c7 horiz instance alloc, 0x4c9 vert instance alloc, 0x200/0x213/0x21c/0x225 null-out asserts, 0x252 range-order, 0x28a range-order)
- **Struct:** Instance is a heap object (~0x3c/60 bytes) allocated by the tracked allocator FUN_0047f340("CtlScroll.cpp", line). Pointer stored in the frame's control slot *(param_1[2]) (=*pfVar13). Two vtables select orientation:
  - PTR_FUN_00a50768 = CCtlScroll (VERTICAL, orientation index=1) [dtor 0061b830, cmp/IsAbove 0061c6b0 @+0x1c, RangeBottom 0061ccb0 @+0x20, transform 0061cd60 @+0x24, ThumbBottom 0061ce80 @+0x28, RangeTop/step 0061cf50 @+0x2c]
  - PTR_FUN_00a50798 = CCtlHorizontalScroll (HORIZONTAL, orientation index=0) [dtor 0061b830, +0x1c 0061c680, +0x20 0061cc30, +0x24 0061cd40, +0x28 0061ce60, +0x2c 0061cea0]
Fields (offsets):
  +0x00 vtable ptr (selects V/H geometry math)
  +0x04 activeElement / current hit region (0=none; set by HitTest+OnMouseDown; 5=thumb grabbed; cleared on mouse-up; returned by msg 0x57)
  +0x08 owning/child frame id (target of FUN_0062ee80 / FUN_0062ef40 / FUN_0062bd40 / FUN_00630080)
  +0x0c per-axis extent[0] (x); +0x10 per-axis extent[1] (y); active axis chosen by inst[+0x30] (used as inst[(orient)+3])
  +0x14 last mouse x; +0x18 last mouse y (recorded by msg 0x37)
  +0x1c thumb drag-reference value (written OnMouseDown, read OnMouseMove)
  +0x20 pageSize / visible-count (get msg 0x59, set msg 0x5f; forced >=1)
  +0x24 position (the scroll value; get 0x5a, set 0x60; changed internally by frame msg 0xb)
  +0x28 rangeMin (get/set lo of 0x5b/0x61)
  +0x2c rangeMax (get/set hi of 0x5b/0x61)
  +0x30 orientation index (int: 0=horizontal picks x, 1=vertical picks y). Default 1 (vertical ctor), 0 for horizontal (flag 0x2000).
  +0x34 smooth-scroll animation struct ptr (NULL when idle). 16-byte block (alloc @CtlScroll.cpp:0x231): {+0x00 f32 spring const=1.0 init/_DAT_0094e7b8, +0x04 f32 current pos, +0x08 f32 target pos, +0x0c f32 velocity}. Freed with FUN_005acaeb(ptr,0x10).
  +0x38 drag anchor value (set when region==5 thumb grab). NOTE position/range/page are ints stored in float-sized slots; setters read msg params as ints.
- **Messages:** Dispatch is switch(param_1[1]); param_2=in payload (floats), param_3=out. Unhandled falls through to base thunk_FUN_00647170.
  1  Paint: sub-pass id in *param_2; bg color by state (1/2->0xff606060, 4->0xffc8c8c8, 5->0xff808080) drawn via FUN_00679a60/FUN_0062b2d0.
  4  InstallBase/subclass: sets *(param_2[3]) = base proc FUN_006123a0, then chains base.
  8  OnInit/attach: FUN_0061c700(payload), then base.
  9  OnFrameCreate: FUN_0062fe20(frame,0x2000)==0 -> alloc VERTICAL CCtlScroll (vtable 00a50768, orient=1, +0x30=1); else alloc HORIZONTAL CCtlHorizontalScroll (vtable 00a50798, orient=0). Store frame id at +8; FUN_006302c0(frameid,1,0). ASSERTS if instance already present (0x4c7/0x4c9).
  0xb Destroy: virtual dtor(this,1)=delete, then base.
  0x13 Measure/size-query: derive min size from vtable range/thumb methods; write width->param_3[1], height->param_3[2].
  0x20 OnKeyDown/scroll command: *param_2 = key 0x1a..0x1f -> line/page inc/dec; emits internal setpos msg 0xb (+9 line, +7 page, sign by dir) via FUN_0062ee80.
  0x24 OnMouseDown: param_2[5]==1; free anim struct; HitTest FUN_0061c4f0 -> region in +4; if region 5 store drag anchor +0x38; invalidate FUN_0062bd40; if region 1..4 start auto-repeat FUN_00630080.
  0x2c OnMouseMove/drag: param_2[5]&1 held; if thumb-drag recompute value from cursor (FUN_0061caa0/0061cb40) else region-based; emit msg 0xb if changed.
  0x2e OnMouseUp/capture-lost: *param_2==0 -> clear +4, invalidate, FUN_00630040 release capture.
  0x37 record mouse pos -> +0x14/+0x18, chain base.
  0x38 OnLayout/arrange: query child geometry (msg 0x56 via FUN_0062ef40), set track thickness along orient (default _DAT_00945190), arrow sizing (_DAT_00944938 min).
  0x3b mouse-wheel: FUN_0061cd80 then FUN_00630080 with *param_2.
  0x45 OnAdvancePre (anim tick): spring-integrate +0x34 toward target; emit msg 0xb with rounded pos; free +0x34 when settled.
  0x57 CtlScrollGetActiveElement -> *param_3 = inst+4. ASSERT param_3!=NULL (@0x200).
  0x58 CtlScrollCanScroll -> *param_3=bool. param_2==NULL: pos(+0x24)<=min(+0x28); else (max-rangeMin+1)<=pos.
  0x59 CtlScrollGetPageSize -> *param_3 = inst+0x20. ASSERT param_3!=NULL (@0x213).
  0x5a CtlScrollGetPosition -> *param_3 = inst+0x24. ASSERT param_3!=NULL (@0x21c).
  0x5b CtlScrollGetRange -> *param_3=inst+0x28, param_3[1]=inst+0x2c. ASSERT param_3!=NULL (@0x225).
  0x5c CtlScrollIncPosition (SMOOTH): FUN_0061c920(inst,delta,1) alloc anim struct, kick msg 0x45.
  0x5d CtlScrollIncPositionInstant: FUN_0061c920(inst,delta,0) clamp+set, msg 0xb.
  0x5e SetVisibleRange/EnsureVisible: param_2=[start,end]; ASSERT start<=end (@0x252); clamp scroll so [start,end] visible; msg 0xb.
  0x5f SetPageSize: inst+0x20 = max(1,param_2); re-clamp position; invalidate FUN_0062bd80(child,0x20).
  0x60 SetPosition: inst+0x24 = clamp(param_2 into [min, max-page+1]); invalidate.
  0x61 SetRange: inst+0x28=param_2[0], inst+0x2c=param_2[1]; ASSERT min<=max (@0x28a); re-clamp page & pos; invalidate.
- **Create recipe:** 1) Create the frame with the create primitive FUN_0062bfc0(parent, flags, child, proc=0x0061b9d0, userdata, 0). For a HORIZONTAL scrollbar OR the flag 0x2000 into flags; omit it for a VERTICAL scrollbar (the create-time flag is what selects the CCtlHorizontalScroll vs CCtlScroll subclass in msg 9 -- it cannot be changed later).
2) Let the frame lifecycle drive msg 4 (installs base proc 006123a0) -> msg 8 -> msg 9 (OnFrameCreate allocates the instance and stores frame id at +8). Do NOT invoke these manually and do NOT send any get/set message before msg 9 has run.
3) Configure in this order (each setter re-clamps against the others): msg 0x61 SetRange([min,max]) -> msg 0x5f SetPageSize(visibleCount>=1) -> msg 0x60 SetPosition(pos). Pass integer-valued floats (slots are ints).
4) Sizing/warm-up: no image lists or materials required (unlike styled buttons; paint is solid fills). Give the frame cross-axis size = system scrollbar thickness (default _DAT_00945190) and main-axis = track length; msg 0x38 lays out arrows/track and msg 0x13 reports the min size. Send msg 0x38/resize once after configuring so track geometry is valid before first paint.
5) Runtime: scroll via msg 0x5d (instant) or 0x5c (animated); read state via 0x5a (pos)/0x59 (page)/0x5b (range)/0x58 (canScroll)/0x57 (active element), always with a non-NULL out pointer.
- **Gotchas:** - NULL out-pointer on getters is FATAL: msgs 0x57/0x59/0x5a/0x5b call FUN_00487a80 (no-return assert, lines 0x200/0x213/0x21c/0x225) if param_3==NULL. Always supply a valid out buffer.
- Ordered-pair asserts (no-return): msg 0x5e requires start<=end (@0x252); msg 0x61 requires rangeMin<=rangeMax (@0x28a). Passing reversed pairs kills the client.
- Double-create is FATAL: msg 9 asserts (CtlScroll.cpp:0x4c7 horizontal / 0x4c9 vertical) if the instance slot *(param_1[2]) is already set. Never re-run OnFrameCreate on a live frame; slot must be zero at create.
- Messaging before create: any get/set (0x57-0x61, 0x5c/0x5d) dereferences the instance ptr *pfVar13; if msg 9 hasn't allocated it that pointer is NULL -> crash. Only talk to the control after creation.
- Orientation is locked at create by flag 0x2000. The V/H vtable supplies the +0x1c..+0x2c geometry math (IsAbove/RangeBottom/thumb transform/ThumbBottom/RangeTop); a mismatch makes thumb/hit-test math wrong (silent misbehavior, and HitTest region drives paint state at +4).
- Smooth-scroll anim struct at +0x34 is a 16-byte heap block; it is freed on OnMouseDown, on instant-inc (0x5d), and on settle (0x45). It is also released by the dtor via msg 0xb. Do not send messages to (or free) the control after destroy, and note starting a drag mid-animation frees the in-flight anim block.
- Page size is forced >=1 (msg 0x5f); position is always clamped to [rangeMin, rangeMax-pageSize+1]. Setting range/page can silently move position. Values are ints in float slots -- pass integer-valued floats or the int reinterpretation will be garbage.

### CtlSliderProc (slider base FrameProc)  (EXE 0x00615fe0, confidence: high)

- **WASM:** ram:80fcc337
- **Assertion file:** P:\Code\Engine\Controls\CtlSlider.cpp (create assert line 0x233; SetValue range asserts 0x18a/0x18b; GetValue null-out assert 0x181; generic frame-null assert 0x732 via FUN_0062fe20)
- **Struct:** CtlSlider::CInstance = 0x30 bytes (12 dwords), allocated in case 9 (FUN_0047f340 tag CtlSlider.cpp:0x233), freed via FUN_005acaeb(inst,0x30). Instance pointer is stored at *(int*)param_1[2] (i.e. frame's control-instance slot piVar1). Fields:
+0x00 u32 flags. bit0(0x1)=thumb-drag active (grabbed the thumb, not the groove). Set in FUN_00616690 hit-thumb branch and case 0x2c drag branch; cleared on mouse-up case 0x2e.
+0x04 i32/float grabOffset = pixel offset between click point and thumb origin captured at grab (param_1[1] in FUN_00616690). Used to keep thumb under cursor during drag.
+0x08 u32 frameHandle = owner frame id (= *param_1, the dispatched frame). ALL geometry/notify helpers use this; if 0 they fatal-assert (0x732).
+0x0c i32 range.min  (set by 0x56; init from optional create struct *param_2[0]).
+0x10 i32 range.max  (set by 0x56; init from optional create struct *param_2[1]).
+0x14 float value = NORMALIZED position 0.0..1.0 (m_value). Canonical stored value; integer value is derived = min+round(value*(max-min)).
+0x18 float target = normalized auto-scroll/hover target used by FUN_00616860 (steps value toward target) and set by hover in case 0x2c non-drag branch.
+0x1c float origin.x = cached screen X of slider rect (from GetScreenRect msg 0x59, written in layout case 8).
+0x20 float origin.y = cached screen Y.
+0x24 float extent.x = cached slider width in px (rect.right-origin.x). DIVISOR in mouse->value conversion for horizontal.
+0x28 float extent.y = cached slider height in px. DIVISOR for vertical.
+0x2c u32 thumbFaceFrame = handle of lazily-created thumb/groove child face frame (0 until layout case 8 runs with style bit 0x20). Freed on destroy and re-laid-out; if 0, value-change takes the invalidate path instead of moving a face.
Style bits read off the frame (not the instance) via FUN_0062fe20(frame,mask): 0x2000=VERTICAL orientation (selects .y vs .x throughout), 0x20=build thumb face child in layout, 0x10=build groove face child, 0x1000=focusable (base proc FUN_006123a0 case 0x24).
- **Messages:** Dispatched by class MsgProc on param_1[1]=msg; param_2=payload; unrecognized msgs fall through to base thunk_FUN_00647170. piVar1=param_1[2] holds &instance.
- case 1 PAINT (sub-pass = *param_2): sub 1 => groove color 0xffc8c8c8; sub 2 => hover: 0xffc8c8c8 if FUN_0062e2a0(frame) (enabled/hot) else disabled 0xff808080. Draws the groove quad via FUN_00679a60(color)->FUN_0062b2d0(frame,rect,brush,scale,uv,w,h)->FUN_0046f850(brush free).
- case 4 INSTALL BASE: sets the frame's base-class proc slot *(param_2[3]) = FUN_006123a0 (CtlFrame base), then chains base.
- case 8 LAYOUT/ONSIZE (FUN_00615dc0): queries screen rect (msg 0x59), caches origin(+0x1c/+0x20) & extent(+0x24/+0x28); if style 0x20 (re)creates thumb face child (FUN_0062b590 out->+0x2c) and refreshes thumb pos (FUN_00616a80); if style 0x10 creates groove face child. Frees old +0x2c first.
- case 9 CREATE INSTANCE: alloc 0x30, zero-init, +0x08=frame; if *param_2 (optional init struct) non-null copy {min=[0],max=[1]} into +0x0c/+0x10; store into *piVar1. Asserts CtlSlider.cpp:0x233 on alloc-context failure.
- case 0xb DESTROY: if inst: free thumb face frame at +0x2c (FUN_0046f850) if set, then free instance FUN_005acaeb(inst,0x30). NOTE: does NOT release a pending auto-scroll timer.
- case 0x20 NAV/KEY (*param_2 subcode): 0x1c/0x1e => value += 1/(max-min) (step up); 0x1d/0x1f => value -= 1/(max-min) (step down); both via FUN_00616990(newNorm,1).
- case 0x24 MOUSE-DOWN (FUN_00616690): sends msg 7 to self, computes thumb rect from value*extent+origin; if cursor inside thumb => capture grabOffset(+0x04), set drag flag bit0, snap; else (groove) sets target(+0x18) and, if FUN_00616860 requests repeat, REGISTERS auto-scroll CTimer FUN_00630080(frame,0,interval).
- case 0x2c MOUSE-MOVE: if drag flag set => recompute normalized value from cursor using axis extent (vert uses +0x28/+0x20, horiz +0x24/+0x1c) via FUN_00616900 clamp, FUN_00616990 apply(notify); else (not dragging) => set hover target +0x18 only if payload bit0(+5 byte &1) set.
- case 0x2e MOUSE-UP (*param_2==0 left button): if not dragging => release auto-scroll timer FUN_00630040(frame,0), snap value to nearest tick; if dragging => finalize normalized value, clear drag flag bit0; then notify owner FUN_0062ee80(frame,9,finalIntValue,0) = COMMIT.
- case 0x38 MEASURE/QUERY-SIZE: get content size (0x59), clamp the cross-axis to thumb minimum (local_14), write preferred size into param_2[2] rect; axis chosen by style 0x2000.
- case 0x39 RELAYOUT: FUN_0062f110(frame) force relayout.
- case 0x3b WHEEL/REPEAT-STEP: FUN_00616860(1) step toward target; if it stepped, register repeat timer FUN_00630080(frame,0,rate).
- case 0x56 SETRANGE: +0x0c=*param_2 (min), +0x10=param_2[1] (max); invalidate FUN_0062bd80(frame,0x20)+relayout FUN_0062f110.
- case 0x57 SETVALUE(int in (int)param_2): asserts value>=min (0x18a) and value<=max (0x18b) [fatal, non-returning]; normalize (v-min)/(max-min); FUN_00616990(norm,0).
- case 0x58 GETVALUE(out int* param_2): asserts param_2!=null (0x181); *param_2 = min + round(value*(max-min)).
- case 0x59 GETCONTENTSIZE/DEFAULT-METRICS: writes default thumb metrics {DAT_00a50424, DAT_00a50428, _DAT_00a5042c} into param_2[0..2].
Outbound notifications to owner via FUN_0062ee80(frame,msgId,intValue,0): msg 8 = VALUE-CHANGED (live, emitted from FUN_00616990 when the rounded integer value actually changes); msg 9 = VALUE-COMMITTED (mouse-up).
Core apply helper FUN_00616990(inst,normFloat,notifyFlag): clamps 0..1, early-outs if unchanged, writes +0x14, moves thumb face (FUN_00616a80) if +0x2c else invalidates (FUN_0062bd80 0x20), and if notifyFlag emits msg 8 with the new integer value.
- **Create recipe:** Registered as a FrameProc; create via the generic control primitive FUN_0062bfc0(parent, flags, child, proc=0x00615fe0, userdata, 0) which returns/stores the frame id at frame+0xbc. Sequence the underlying frame dispatcher then delivers, in order: msg 4 (INSTALL base -> installs FUN_006123a0), msg 9 (CREATE -> allocates the 0x30 instance). Recommended full recipe:
1) Create the frame: FUN_0062bfc0(parent, flags, child, 0x00615fe0, userdata, 0). Flags to OR in: 0x10 (groove face), 0x20 (thumb face — REQUIRED for a visible/movable thumb; without it value changes only invalidate), optional 0x2000 (VERTICAL), 0x1000 (focusable/keyboard nav). No image list or material warm-up is required — faces are solid-color quads (FUN_0062b590/FUN_0062b2d0), unlike the styled button.
2) (Optional) Pass a {min,max} init struct as the create payload so msg 9 seeds the range; otherwise send msg 0x56 SetRange(min,max) immediately after creation. ALWAYS establish max>min before any value/interaction.
3) Position & size the frame with the anchor-6 pos/size setter FUN_0062F770 (or FrameNewSubclass/layout). Giving it a rect fires msg 8 LAYOUT which caches origin/extent and builds the thumb/groove face children. Provide a nonzero cross-axis extent (nonzero width for horizontal, height for vertical) BEFORE interaction so the mouse->value divisor (+0x24/+0x28) is nonzero.
4) Send msg 0x57 SetValue(v) with min<=v<=max (or rely on default value 0 = normalized 0).
5) Read back with msg 0x58 GetValue(&out).
For a themed slider use the styled wrapper UiCtlSliderProc 0x0087f440 (xrefs this base) layered on top; it adds textured faces but the base protocol above is unchanged.
- **Gotchas:** 1) SetValue (0x57) FATAL-ASSERTS via FUN_00487a80 (non-returning) if value<min (0x18a) or value>max (0x18b). Caller MUST clamp to [min,max] first.
2) GetValue (0x58) FATAL-ASSERTS (0x181) on a null out-pointer.
3) DEGENERATE RANGE: if max==min, normalization/step math divides by (max-min)=0 (case 0x57, 0x58, 0x20 step, FUN_00616860, FUN_00616900) => div-by-zero / inf. Always SetRange with max>min before touching value.
4) FRAME-NULL ASSERT: every geometry/style/notify helper calls FUN_0062fe20(frame,mask) which FATAL-ASSERTS (0x732) if the cached frame handle (+0x08) is 0. Do not send get/set msgs to an instance whose create (msg 9) failed.
5) AUTO-SCROLL TIMER LEAK: groove mouse-down (case 0x24 -> FUN_00616690) may REGISTER a CTimer (FUN_00630080); it is released ONLY by mouse-up case 0x2e non-drag branch (FUN_00630040). If the mouse-up is swallowed, or the frame is destroyed while the button is held, the timer LEAKS — case 0xb DESTROY frees only the +0x2c face frame, NOT the timer. Ensure a matching mouse-up (or manual FUN_00630040) before teardown.
6) ZERO-EXTENT DIVISION: mouse->value conversion (FUN_00616900) divides by extent +0x24 (horiz) or +0x28 (vert). If layout (msg 8) never ran or the rect has zero width/height, the divisor is 0 => inf value (clamp saves the stored value but drag/hover geometry is undefined). Size the frame before enabling interaction.
7) NO-FACE STATE: sending SetValue before the first layout (msg 8) leaves +0x2c==0, so FUN_00616990 takes the invalidate path (safe, no crash) but the visible thumb won't move until a layout pass builds the face frame (needs style bit 0x20).
8) PAINT ordering: case 1 dispatches on sub-pass *param_2 (1=groove, 2=thumb/hover); other sub-passes fall through — normal, not a bug, but a custom subclass must forward unknown paint passes to the base thunk.

### CtlProgressProc (UiCtlProgress / ProgressBar)  (EXE 0x008812e0, confidence: high)

- **WASM:** ram:80f6ce9a
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlProgress.cpp (confirmed literal in case 9: FUN_0047f340("P:\\Code\\Gw\\Ui\\Controls\\UiCtlProgress.cpp",0x5ab)). Class ctor-table entry at data slot 0x00884a50 (jmp thunk -> 0x008812e0).
- **Struct:** Per-instance struct = 0x28 bytes (10 dwords). Alloc in case 9 via FUN_0047f340(...,0x5ab); freed in case 0xb via FUN_005acaeb(iVar6,0x28). Instance pointer reached by FUN_008849b0(param_1) = **(param_1+8) (i.e. *(frame->userslot)); asserts (0x5bd) if null. Fields:
 +0x00 dword frameId  (= param_1[0], the owning frame id)
 +0x04 ptr  valueProvider/label-source  (set by msg 0x62; init 0; used in paint 0x40 branch only if !=0)
 +0x08 ptr  renderElemA = primary text/label render object (init 0; created lazily in paint 0x100 branch via FUN_0062b8e0; freed in destroy; color-animated by tick)
 +0x0c float blendA   (animation blend fraction for group A; init 0; reset to 1.0 by msg 0x60; decays to 0 by tick 0x45)
 +0x10 u32   fromColorA (ARGB; init 0xffffffff; captured current color on msg 0x60)
 +0x14 u32   toColorA   (ARGB target; init 0xffffffff; = *param_2 on msg 0x60)
 +0x18 ptr  renderElemB = rate-arrow image element (init 0; created lazily in paint 0x10 branch via FUN_00880730 with image list DAT_01081a98; freed in destroy; color-animated by tick)
 +0x1c float blendB   (group B blend; init 0; reset to 1.0 by msg 0x61; decays via tick)
 +0x20 u32   fromColorB (ARGB; init 0xffffffff)
 +0x24 u32   toColorB   (ARGB target; init 0xffffffff; = *param_2 on msg 0x61)
NOTE: init in case 9 sets [3]=0,[7]=0,[1]=0,[2]=0,[6]=0 and [4]=[5]=[8]=[9]=0xffffffff, [0]=frameId.
Class-level (static) globals: DAT_01081a98 = sm up/rate-arrow image list (7x0x19a, flags 0x20003e0, name &DAT_00b966b0); DAT_01081abc = sm down image list (name &DAT_00b966dc); DAT_010819fc = shared resource + DAT_010819f8 = its refcount (built by FUN_00882530 -> FUN_0062d790).
- **Messages:** Signature: FUN_008812e0(undefined4 *param_1 /*msg pkt: [0]=frameId,[1]=msg,[2]=&userslot*/, float *param_2 /*wparam/in*/, undefined4 *param_3 /*out*/). switch(param_1[1]):
 4  InstallBase: *(void**)param_2[3] = &LAB_00618b70 (jmp->0x00618d00, base CtlProgress vtable/proc). No instance needed.
 5  ClassInit (one-time): assert if DAT_01081a98!=0 (0x636) or DAT_01081abc!=0 (0x651); build up-arrow imagelist DAT_01081a98 and down-arrow imagelist DAT_01081abc via FUN_0065efa0 (size 7x0x19a, flags 0x20003e0); set uv/scale globals; call FUN_00882530 (shared rsrc DAT_010819fc, ++DAT_010819f8).
 6  ClassTeardown: free both imagelists (set to 0); assert 0x181 if DAT_010819f8==0; --DAT_010819f8; when it hits 0 free DAT_010819fc.
 9  OnFrameCreate: assert 0x5aa if userslot already set; alloc 0x28-byte instance (FUN_0047f340,0x5ab); init fields (see struct); store at *(param_1[2]); register per-frame tick via FUN_0062ef00(frameId,0x45).
 0xb OnDestroy: if instance: free renderElemB(+0x18) and renderElemA(+0x08) via FUN_0046f850; FUN_005acaeb(inst,0x28); null userslot.
 0x15 SizeQuery/margins: FUN_008849b0 (needs instance); assert 0x68a if param_3==0; writes _DAT_00943278 (=2.0f) into param_3[0..3] (l/t/r/b insets).
 0x38 MeasurePreferred: needs instance; out param_2[2][0]=width(=*param_2), out param_2[2][1]=height(=FUN_0062d0e0(frameId)+_DAT_009413c8, currently +0.0).
 0x45 Tick/Animate (self-registered in case 9): advance blendA(+0x0c) and blendB(+0x1c) toward 0 by delta *param_2 (clamped >=0); if renderElemA/B non-null recolor them via FUN_008823d0(blend,fromColor,toColor) then FUN_006641e0(elem,color). Then falls through to base (default).
 0x5e Paint: FUN_008849b0 then FUN_00883790(param_2) — draws by frame paint-flags *param_2: bit 0x10=rate-arrow image (elemB, imagelist DAT_01081a98), 0x20=second arrow (imagelist DAT_01081abc), 0x40=value text via FUN_008801a0 iff +0x04 provider!=0, 0x100=label text (elemA via FUN_0062b8e0).
 0x5f RelayoutIfFlagged: FUN_008849b0; if ((uint)param_2 & 3)!=0 -> FUN_0062bd80(frameId,0x30) (invalidate/relayout); else fall through to base.
 0x60 SetColorA (primary/text target color): needs instance; assert 0x71f if param_2==0; capture current animated color into fromColorA(+0x10), set toColorA(+0x14)=*param_2, reset blendA(+0x0c)=1.0 -> animates.
 0x61 SetColorB (rate-arrow target color): needs instance; assert 0x729 if param_2==0; same for group B (+0x1c/+0x20/+0x24).
 0x62 SetValueProvider: FUN_008849b0; if +0x04 != param_2 -> +0x04=param_2 and FUN_0062bd80(frameId,0x40) (invalidate). 
 default: forward to base class chain via FUN_00647170(frame,msg,out) (walks parent frameprocs; it itself skips msgs 9 & 0xb).
IMPORTANT CORRECTION to seed: this proc does NOT implement 0x58/0x5A/0x5B (SetValue/Max/Percent). Those are on the *consumer* GmMissionProgress control FUN_00527f90 (P:\Code\Gw\Ui\Game\GmMissionProgress.cpp), which owns a UiCtlProgress child and handles 0x56 (orientation 0/1), 0x38 (measure), 0x100000b0 (value-changed notify), plus its own 0x45 easing tick. GmMissionProgress instance = 0x1c bytes.
FUN_008823d0 = ARGB lerp(frac,colorA,colorB): frac==0 -> colorB; frac==1.0(_DAT_009407b0) -> colorA; else per-channel interpolate.
- **Create recipe:** UiCtlProgress is a child control frame whose FrameProc is 0x008812e0 (referenced through jmp thunk &LAB_00884a50). Reference creator = GmMissionProgress (FUN_00527f90 case 9):
 1. Ensure ClassInit (msg 5) has run so imagelists DAT_01081a98/DAT_01081abc and shared rsrc DAT_010819fc exist (the frame manager dispatches 5 the first time the class is used; teardown via 6 is refcounted).
 2. On parent: FUN_0062ede0(parentFrame,0,0xffffffff) (prep/anchor).
 3. Create the progress frame: id = FUN_0062bfc0(parentFrame, 0x80 /*flags*/, 0 /*childId*/, &LAB_00884a50 /*=UiCtlProgress proc*/, 0 /*userdata*/, 0). This triggers msg 9 -> instance alloc + tick registration.
 4. FUN_00604aa0(id, 0x800) to apply style bit 0x800.
 5. Drive visuals through the frame paint-flags (0x10 rate arrow A, 0x20 arrow B, 0x40 value text (also send 0x62 with a value provider), 0x100 label text) and set colors with msg 0x60 (bar/text) and 0x61 (arrows); each triggers a smooth blend animation driven by the 0x45 tick.
 6. Sizing: height auto = FUN_0062d0e0(frame)+0.0 (msg 0x38); margins/insets = 2.0f each (msg 0x15). Imagelists are 7 wide x 0x19a tall cells.
Order/warm-ups that matter: class init (5) BEFORE first paint (imagelists), and OnFrameCreate (9) BEFORE any get/set/measure/paint (they all deref instance via FUN_008849b0). Register-for-tick is automatic in case 9.
- **Gotchas:** All are FUN_00487a80(code) assert-noreturn (hard abort):
 - Instance-null deref: EVERY get/set/measure/paint (0x15,0x38,0x45,0x5e,0x5f,0x60,0x61,0x62) calls FUN_008849b0 = **(param_1+8); if OnFrameCreate(9) hasn't populated the userslot -> assert 0x5bd / crash. Never message the control before it is created.
 - Double create: msg 9 asserts 0x5aa if userslot already non-null.
 - Double class init: msg 5 asserts 0x636 (DAT_01081a98 already set) / 0x651 (DAT_01081abc already set).
 - Class refcount underflow: msg 6 asserts 0x181 if DAT_010819f8==0.
 - Null out ptr: msg 0x15 asserts 0x68a if param_3==0.
 - Null wparam: msg 0x60 asserts 0x71f, msg 0x61 asserts 0x729 if param_2==0.
 - Paint imagelist gate: FUN_00883790 uses &DAT_01081a98/&DAT_01081abc (rate-arrow imagelists) for paint-flag bits 0x10/0x20. If ClassInit(5) never ran these are 0 -> painting an arrow with a null imagelist. Also value-text (flag 0x40) is guarded (only if +0x04 provider!=0) so it is safe unset.
 - Paint internal asserts: FUN_00883790 can assert 0x171 (buffer overlap) / 0x2ef (element count overflow) on internal array growth — not caller-triggerable in normal use.
 - GmMissionProgress consumer extras: FUN_00527f90 case 9 asserts 0xd9 if *param_2==0 (needs a valid value-source pointer at create); 0x56 asserts 0x111 if orientation arg > 1.

### CtlList (CCtlList / CtlListProc)  (EXE 0x0061f740 (FrameProc/CtlListProc). Base-class proc installed on msg 4 = FUN_006123a0. Instance ctor = FUN_0061ecc0 (vtable PTR_FUN_00a509c0 @0x00a509c0; owner-draw vtable PTR_FUN_00a509cc). Column/content init = FUN_00621ad0. Row-insert = FUN_0061eee0. Create primitive = FUN_0062bfc0. Anchor size setter = 0x0062F770. Vtable dtor slot(+8)=0x0061eeb0., confidence: high)

- **WASM:** ram:80e3a1d2 = CtlListProc(FrameMsgHdr const&, void const*, void*); styled wrapper IUi::UiCtlListProc @ ram:80e47693; ctor CCtlList::CCtlList(uint) @ ram:80e288bd; OnFrameCreate @ ram:80e2a0f1. Assertion file P:\Code\Engine\Controls\CtlList.cpp.
- **Struct:** Per-instance CCtlList object. Frame stores instance ptr at *(frame_userdata_slot)= *(param_1[2]); the frame HANDLE is stored back at instance+0xB0. Byte offsets (from ctor FUN_0061ecc0 + proc usage):
+0x00 vtable (=PTR_FUN_00a509c0 base, or PTR_FUN_00a509cc owner-draw)
+0x04..+0x0F general/temp (init 0)
+0x10 float: content top/clip Y baseline (used in scroll/measure)
+0x14 int: LOCKED/disabled gate (!=0 => ignore all input msgs)
+0x2C animator/interpolator sub-object (FUN_0060ca20 init; FUN_0060cbc0/cbd0/FUN_0060cbd0 smooth-scroll on capture)  spans ~+0x2C..+0x4C
+0x50 owner-draw callback object ptr (set by msg 100; freed via FUN_0046f850)
+0x54 =1 (art/style token)
+0x58 int: TOP visible row index (scroll position)
+0x5C ptr: FIELD/ROW array base; each row record = 0x10 bytes
+0x60 int: column count/capacity mirror
+0x64 (=100) int: ROW COUNT (number of fields/rows)
+0x68 =0x10 (row grow chunk)
+0x6C reserved
+0x70 int: SELECTION / current row index (0xFFFFFFFF = none)
+0x74 int: drag-pending flag; +0x78/+0x7C = drag-start x/y
+0x80/+0x84 int: capture/track anchor point x,y
+0x88 =0xFFFFFFFF, +0x8C =0xFFFFFFFF (hot/last indices)
+0x90 int: PAGE SIZE (count of fully visible rows; recomputed by FUN_006217a0/OnFrameSize)
+0xA0 ptr: COLUMN-WIDTH float array (relative widths summing <=1.0)
+0xA4 int: column array capacity
+0xA8 int: COLUMN COUNT
+0xAC =0x40 column grow chunk
+0xB0 the owning frame handle/id
+0x24-word(=0xffffffff at ctor) drag/capture SOURCE field id (msg 0x3D sets, 0x3C/0x3F clear)
+0x28-word(byte 0xA0 region) — do not confuse; byte 0x28 used as 'needs-relayout' flag set=1 in msgs 0x39/0x57.
Row record (0x10 bytes @ +0x5C) fields include: [+0]=item-ptr list head, [+4]=cap, [+8]=col-index used, [+0xC]=grow. Item objects (allocated by FUN_0061eee0, tagged file 0x39a) offsets: +0x1C/+0x20/+0x24 rect, +0x28=0x40, +0x2C data(int), +0x30 icon, +0x34/+0x38 pair, +0x3C flags(from param_2[0]), +0x40 model id, +0x44 text buf, +0x48 cap, +0x4C len, +0x50=0x80, +0x54=0xffffffff(pending draw guard), +0x58/+0x5C/+0x60 sub-buffers.
- **Messages:** Dispatch on param_1[1]=msg; param_2=in/inout payload, param_3=out. Unhandled -> thunk_FUN_00647170 (base frame proc). Handled cases:
4  InstallBase: writes base class proc FUN_006123a0 into *(param_2[3]).
8  OnFrameSize -> FUN_006217a0: recompute page size(+0x90) & visible rows; queries child scroll via msg 0x5e.
9  OnFrameCreate: alloc instance at *(param_1[2]); asserts 0xA3A if already set; flag 0x20000 -> owner-draw vtable PTR_FUN_00a509cc else base; then FUN_00621ad0 (embed CtlScroll child + column init).
0xA OnFrameTextResolved/LanguageChanged: query msg 0x5e, FrameNewSubclass(0x0062f150) reflow.
0xB OnFrameDestroy: call vtable+8 dtor (0x0061eeb0).
0x20 OnFrameKeyDown: arrow-key nav (sub 0x1C/0x1E=down/next, 0x1D/0x1F=up/prev over +0x70), skip non-selectable rows (bit1 of item+0x2C), then FUN_00623240 select.
0x24 OnFrameMouseDown: hit-test; left-click select (FUN_0062ee80 msg 7), ctrl/extend variants (msg 9); sets drag-pending +0x74 when drag flag(4) present.
0x25 OnFrameMouseLeave(null payload): clear selection (FUN_00623390 with -1).
0x26/0x27/0x28/0x2A OnFrameTouch*: forward to FUN_00621dc0 with sub 0xD/0xE/0xF/0x10.
0x2C OnFrameMouseMove/track: if not dragging & not locked, FUN_00623390 track hover.
0x2E OnFrameMouseUp: finish drag; emit selection notify msg 0x61 (left) or 99 (right) to child.
0x2F OnFrameMouseWheel: FUN_0060ca40 delta -> scroll +/-1 (respects reverse flag 0x10000).
0x31 OnFrameScrollCmd: param_2[2] 7=lineDn 8=lineUp 9=pageDn 10=pageUp 0xB=thumb(abs), calls FUN_006231b0(topIndex).
0x37 OnFrameMouseOpSource -> FUN_00621e90.
0x38 OnFrameMouseOpTarget -> FUN_00622090.
0x39 OnFrameReset: mark dirty +0x28=1, FUN_006211b0 relayout + invalidate (0x0062f470/0x0062bd40/0x0062f110).
0x3A OnFrameContentAdd(model bind): attach HGrModel list to matching field(item+0x40==ptr); asserts 0x75C if item+0x54 already !=-1.
0x3C/0x3F OnFrameCaptureLost/End: if *param_2==capture id(+0x24) release capture, reset +0x14/+0x24, emit selection notify 0x61.
0x3D OnFrameCaptureBegin: if not locked & no active capture & payload[4]!=0, set +0x24=field, store point +0x80/+0x84, out param_3 = (payload[5]==0).
0x3E FUN_006222d0.
0x4C OnFrameContentRemove: walk rows, release model buffers, free draw models (FUN_00632d90), reset item+0x54=-1.
0x56 SetItem/redraw -> FUN_006224d0.
0x57 Clear: delete all rows (FUN_00620730), shrink col array, reset +0x70/+0x90/+0x88/+0x8C, relayout, emit sel-notify 0x61.
0x58 DeleteItem -> FUN_006226a0.
0x59 InvalidateItem: clear draw-cached bit (item+0x18 &~3) for one field or whole column; payload[0]=field(-1=all), payload[1]=col; then FUN_0062bd40 invalidate.
0x5A MoveItem -> FUN_00622930.
0x5B FindItem/GetFieldAtPoint: in payload (point or key), out payload[2]=field index, payload[3]=col (-1 if none); asserts 0x293/0x298 on OOB/null array.
0x5C GetItem/read row -> FUN_00622a90.
0x5D GetCount: *param_2 = row count(+0x64).
0x5F GetPosition: *param_2 = top index(+0x58).
0x60 GetSelection: *param_2 = selection(+0x70).
0x61 SetSelectionScroll(internal): field=*param_2 (-1=current), if <count send child msg 0xB.
0x62 FUN_00622c20.
0x63(99) SetSelectionRight(internal): like 0x61 but child msg 0x11.
0x64(100) SetOwnerDrawCallback: free old +0x50, store FUN_0046fda0(param_2) copy, invalidate.
0x65 FUN_00622e60.
0x66 ScrollTo(index): asserts 0x9DF if index>=row count; FUN_006231b0.
0x67 AttachScroll: get child scroll (FUN_0062cfc0) asserts 0x9E9 if none; FrameNewSubclass 0x0062f150.
0x68 SetSelection(index public): asserts 0x9F2 if index>=count (unless 0xFFFFFFFF); FUN_00623240.
0x69/0x6A/0x6B GenericGetSet property -> FUN_0062bc20(frame,param_2) (color/font/style props).
- **Create recipe:** 1. Create the frame with the standard control-create primitive: FUN_0062bfc0(parent, flags, child, proc=0x0061f740 CtlListProc, userdata_slot, 0). The primitive stores the child/frame id at frame+0xBC. userdata_slot must point at a zero-initialized instance-ptr cell (*(param_1[2])==0 at OnFrameCreate, else assert 0xA3A).
2. Engine sends msg 4 (install base proc) then msg 9 (OnFrameCreate): instance is allocated via FUN_0061ecc0 (base) OR, if create-flag 0x20000 set, a CCtlListOwnerDraw (vtable PTR_FUN_00a509cc). Frame handle written to instance+0xB0.
3. OnFrameCreate calls FUN_00621ad0 which: sets frame flags (FUN_0062ede0(h,0x24,0), FUN_0062ef00(h,0x4c)); EMBEDS a CtlScroll child via FUN_0062bfc0(h,0,0,FUN_0061b9d0,0,0); picks bg color by flag 0x4000; then defines COLUMNS from the FrameMsgCreate payload param_2[0]: [0]=column count, [1]=ptr to float relative-width array, [2]=ptr to per-field init records (13 dwords each, only needed for owner-draw/2000 mode). Column widths MUST each be >epsilon and the running remainder (starting 1.0) must never go negative.
4. Warm-ups / ordering: define columns exactly once at create (re-defining asserts 0x581). To be an owner-draw list set flag 0x2000 (field mode) and provide param_2[2] init array; if 0x2000 set you MUST NOT also set 0x10000, and param_2 & param_2[2] must be non-null (asserts 0x598/0x59b/0x59c). Register a draw/measure callback via msg 100 before adding rows if using owner-draw.
5. Populate: add rows via FUN_0061eee0 (item alloc) driven by list msgs (SetItem 0x56 / content msgs); each item needs text buffer (flag bit1) and/or data (flag bit2/0x4) consistent with its flag word (mismatch asserts 0x392/0x393). Bind visual models with msg 0x3A.
6. Sizing: place with anchor-6 setter 0x0062F770; page size (+0x90) auto-derives from frame height / row height on msg 8 (OnFrameSize). Set selection with msg 0x68, scroll with 0x66, query count/pos/sel with 0x5D/0x5F/0x60.
7. Destroy via native destroyer FUN_0062c550(frame_id); msg 0xB runs the vtable dtor (0x0061eeb0).
Relevant create flags: 0x20000=owner-draw subclass; 0x2000=multi-field/column (owner-draw) mode; 0x10000=reversed/RTL scroll (mutually exclusive with 0x2000 at create); 0x4000=transparent/alt background; 0x4000 also toggles bg color 0xA00 vs 0.
- **Gotchas:** All are FUN_00487a80(code) fatal asserts (file CtlList.cpp) unless noted:
- 0xA3A OnFrameCreate on a frame whose instance ptr is already set (double-create / dirty userdata cell).
- 0x57F column-def payload has count==0.
- 0x581 columns already defined (+0xA8 != 0) when re-adding column set.
- 0x587 a column width <= epsilon (must be strictly positive).
- 0x588 a column width exceeds remaining budget (running sum must stay within 1.0).
- 0x598 owner-draw(0x2000) list also has 0x10000 set — illegal combo.
- 0x59B/0x59C owner-draw create missing per-field init: param_2 null / param_2[2] null.
- 0x392/0x393 item flags claim has-icon(0x4)/has-text(0x1) but the corresponding data ptr is null.
- 0x124 / 0x24B row index >= row count (+0x64) — OOB row access (insert/measure/iterate).
- 0x12F item's column index >= column count (+0xA8).
- 0x171 memmove/array overlap guard (grow-array reallocation aliasing).
- 0x4C1 SetPosition/invalidate column index >= column count.
- 0x9DF msg 0x66 ScrollTo index >= row count.
- 0x9E9 msg 0x67 attach-scroll but no scroll child frame exists.
- 0x9F2 msg 0x68 SetSelection index >= row count (0xFFFFFFFF allowed).
- 0x293 GetFieldAtPoint field index out of bounds (also logs "Field out of bounds %s").
- 0x298 GetFieldAtPoint with null field array (+0x5C == 0).
- 0x518 OnFrameSize measure mismatch (computed content height disagrees with frame height beyond tolerance).
- 0x75C content-add re-binds a row whose item+0x54 is already != -1 (double model attach).
Non-assert gotchas: every input msg early-returns if +0x14 (locked) != 0 — a list left locked silently eats keyboard/mouse. Selection field +0x70 uses 0xFFFFFFFF sentinel for "none"; callers passing raw -1 vs 0xFFFFFFFF must match. Owner-draw callback at +0x50 is FUN_0046fda0-copied and FUN_0046f850-freed — passing a stack/temp callback that dies is a use-after-free at paint. Instance ptr lives at *(param_1[2]) (frame userdata slot), NOT param_1 itself; frame handle is re-stored at instance+0xB0 and every engine call uses that.

### CtlDropList (CtlDropListProc — dropdown / combobox)  (EXE 0x006144e0, confidence: high)

- **WASM:** not separately resolved; identity CONFIRMED by assertion string "P:\\Code\\Engine\\Controls\\CtlDropList.cpp" embedded in OnFrameCreate (FUN_00615670) and referenced by every abort in this proc. WASM-first not needed — the EXE proc self-identifies.
- **Struct:** FrameProc signature: void CtlDropListProc(int* frame /*param_1*/, void* param /*param_2*/, void* out /*param_3*/). frame[0]=frameId, frame[1]=msg, frame[2]=&instancePtr (instance = *(void**)frame[2]).

INSTANCE (heap block size 0x11C, allocated by FUN_0047f340("...CtlDropList.cpp",0x11C) in msg 9; stored at *(void**)frame[2]). Dword indices:
  [0x00] items array base ptr (growable-array of 0x20-byte item records)
  [0x04] items capacity (elements)
  [0x08] items count            <- msg 0x5A GETCOUNT returns this
  [0x0C] element size = 8 (dwords => 0x20 bytes stride); set once in create
  [0x10..0x4F] type-ahead search buffer, 0x20 wide chars (0x40 bytes)
  [0x14](0x50) type-ahead buffer length (# chars in buffer)
  [0x15](0x54) drop-list visible rows / drop height; default = _DAT_009411d8; msg 0x60 sets it
  [0x16](0x58) selected index (-1/0xffffffff = none); msg 0x5C gets, 0x61 sets, internal notify 7 & msg 0x68 sync popup
  [0x17](0x5C) comparator function pointer for sort (NULL = unsorted); msg 0x62 sets; if non-NULL FUN_00615ad0 (quicksort) runs
  [0x18](0x60) "armed/just-opened" mouse flag used by LBUTTONDOWN(0x24)/LBUTTONUP(0x2E)

ITEM record (0x20 bytes, item = base + i*0x20). Dword offsets:
  +0x00 unique item id (from global counter DAT_00c0ac34, post-incremented)
  +0x04 text char-offset / render start index (0xffffffff = no text / not rendered)
  +0x08 user value (associated payload; msg 0x5E gets, 0x63 sets, sort comparator arg2/arg4)
  +0x0C text buffer base ptr (wide chars); char* = *(item+0xC) + (item+0x04)*2
  +0x10 text buffer capacity
  +0x14 text length (chars)
  +0x1C enabled flag (0 => item disabled; FUN_00614230 sets popup-row flag bit1 when 0)

POPUP CHILD (created lazily by FUN_00614230): frame created via FUN_0062bfc0(parent,0x128,0,listproc,0,0); listproc = child-supplied 0x5B handler or default FUN_00615430; render subclass FUN_0062f150(child,FUN_00615570,0). Popup item template flags local_4c[0]=0x22, |=2 if parent flag 0x2000 set, |1 when item disabled.
- **Messages:** frame[1]=msg; unhandled cases fall through to base thunk_FUN_00647170. Denormal-float case labels decoded to ints:
 0x01 PAINT: if sub-pass *param_2==0 draws box — outer border quad color 0xff202020, inner face 0xff8080ff (enabled, from FUN_0062caa0 state) or 0xff404040 (disabled); solid quads via FUN_0062b2d0 + color handle FUN_00679a60 (NO image list needed).
 0x04 INSTALL/vtable: *(param_2[3]) = FUN_006123a0 (control-base handler) then chain base.
 0x08 DRAW SELECTED TEXT: renders current selection's text (FUN_0062efc0) using item+0x0C text base + item+0x04 offset, guarded item+0x04 < item+0x14.
 0x09 ONFRAMECREATE: FUN_00615670 — alloc instance(0x11C); parse *param_2 as double-NUL-terminated wide-string list into items (each entry = wcslen+1 stride); set [0x15]=_DAT_009411d8, [0x16]=(count?0:-1), [0x17]=0; self-send msg 0x4C; FUN_0062ccd0(frame,0x30,0) min-size.
 0x0B DESTROY: free every item text buffer, clear + free items array (FUN_005acaeb), zero [0x08]/[0x16]=-1.
 0x15 GET-PREFERRED-SIZE: out[0..3] = {0,0,_DAT_009407c8,0}.
 0x20 KEY/CHAR INPUT: FUN_00615820(frame,instance,param_2,&consumed). *param_2 key: 9/0x14/0x69 = tab/close popup; 0x1C/0x1E = down/next (open popup if closed else selected++); 0x1D/0x1F = up/prev (selected--); default = printable char appended to type-ahead buffer[0x10] (max 0x20, msg 0x5D fetches labels, prefix match via FUN_0046bda0 selects). REQUIRES out ptr param_4 non-null (assert 0x1C8). On selection change: set [0x58], invalidate, notify 7, popup msg 0x68.
 0x21 DEACTIVATE/LOSTFOCUS: if param_2==0 close popup (FUN_006154e0), invalidate (FUN_0062bd40), chain.
 0x24 LBUTTONDOWN: if popup closed set [0x60]=1(armed) & chain; if open, close & notify 9.
 0x2C child-render sync: if (param_2[5]&1) open/refresh popup, msg 0x5B (place) + 0x68 (select) to popup child.
 0x2E LBUTTONUP: read [0x60] armed; toggle popup open/close; if closing with param_2[4] set commit selection; set [0x58], notify 7, invalidate, popup 0x5B/0x68.
 0x31 CHILD NOTIFY (param_2[1]==0): sub-switch param_2[2]: 2=invalidate+relayout(FUN_0062f470); 3=notify(8)+relayout+chain; 0xB/0x11=selection chosen -> [0x58]=*(param_2[3]), invalidate, notify 7, close popup (FUN_006154e0).
 0x36 POSITION POPUP: compute rect from item metrics & [0x15] drop rows, place anchored via FUN_0062f770; asserts 0x238 if rect degenerate (min>max).
 0x37 MEASURE current-selection width -> writes into item render metric.
 0x38 BUILD/MEASURE ALL glyphs: iterate items, build render glyphs (FUN_0062fee0), accumulate max width into *param_2[2]; assert 0x24B if render idx>=cap.
 0x39 invalidate + relayout (FUN_0062f110).
 0x3A ADD-TEXT to matched item (by id *param_2): grow item text buffer, copy chars, if [0x17] comparator set re-sort (FUN_00615ad0), invalidate+relayout.
 0x3B RESET type-ahead: zero instance +0x10..+0x50 (search buffer + length).
 0x4C REBUILD: iterate items, free/rebuild render glyphs, reassign ids (self-sent at end of create).
 0x56 ADD ITEM (wparam=1): FUN_006155e0 append {id, -1, value=param_2[1], text=param_2[0]} then chain.
 0x57 ADD ITEM (wparam=0): same, uVar12=0.
 0x58 CLEAR ALL: close popup, FUN_00615520 free items, reset array, [0x16]=-1, invalidate+relayout.
 0x59 CLOSE popup child (destroy open dropdown), reset [0x08]=0/[0x16]=-1, invalidate.
 0x5A GET ITEM COUNT: *param_2 = instance[0x08].
 0x5C GET SELECTED INDEX: *param_2 = instance[0x58].
 0x5D GET ITEM TEXT: copies item[*param_2] text to buffer param_2[2] (len param_2[1]); assert 0x24B if index>=count, 0x252 if text idx overflow.
 0x5E GET ITEM VALUE: index *param_2 -> param_2[1] = item[idx]+0x08; assert 0x2FE / 0x24B on bad index.
 0x5F OPEN/SHOW popup: if closed FUN_00614230 open + FUN_0062e520/0062e560 show.
 0x60 SET DROP ROWS: instance[0x54] = *param_2; relayout (FUN_0062f470).
 0x61 SET SELECTED: index (0xffffffff => count-1); assert 0x2CF if index>=count; set [0x58], invalidate, if popup open send it 0x68.
 0x62 SET COMPARATOR (sort): instance[0x5C] = param_2; if non-NULL FUN_00615ad0 sort; chain.
 0x63 SET ITEM VALUE: index guard (assert 0x2F1/0x24B), item[idx]+0x08 = param_2[1].
 0x64 default anchor/style: FUN_0062bc20(frame,param_2) then chain.
- **Create recipe:** 1) Create the frame with the generic control-create primitive, same as all TCtlInstance controls: id = FUN_0062bfc0(parentFrame, flags, childSlot, proc=0x006144e0 /*CtlDropListProc*/, userData, 0). The returned id is written to frame+0xBC. Anchor/pos via the standard anchor-6 setter FUN_0062F770 (or msg 0x64 -> FUN_0062bc20).
2) The engine then delivers msg 9 (OnFrameCreate). param_2 for that msg MUST point to a wide-char (short) item list that is a sequence of NUL-terminated UTF-16 strings terminated by an extra empty string (double-NUL), e.g. L"Red\0Green\0Blue\0\0". Empty list => pass a pointer to a single 0 (or NULL, handled). OnFrameCreate allocates the 0x11C instance, populates items, sets drop-rows default (_DAT_009411d8), selected index = 0 if any items else -1, self-sends 0x4C to measure, and sets a min height (FUN_0062ccd0 arg 0x30).
3) NO image-list / material warm-up is required — the closed combobox box paints with solid color quads (FUN_00679a60 + FUN_0062b2d0), unlike UiCtlBtnProc which needs imglist 0x010819cc. The lazily-created popup child list (FUN_00614230) is created only on open; it paints a solid black (0xff000000) background and each row via base list render FUN_0061f740 — also no external warm-up.
4) Post-create configuration via messages: add items with 0x56/0x57 (param_2[0]=wide text, param_2[1]=value); set/query selection with 0x61/0x5C; query count with 0x5A; set visible rows with 0x60; install a sort comparator with 0x62; clear with 0x58.
5) Ordering: proc install (msg 4) and OnFrameCreate (msg 9) are driven by the engine immediately after FUN_0062bfc0; do all item/selection setup AFTER msg 9 has run (instance exists). Size: default drop height from _DAT_009411d8 (rows); closed box min height forced to 0x30 units by create. Destroy via native destroyer FUN_0062c550(id) (msg 0xB frees the instance/items).
- **Gotchas:** - msg 9 item list MUST be double-NUL-terminated UTF-16; the parse loop (FUN_00615670) walks entries by wcslen+1 with no bounds — a missing terminator overreads until it hits a stray zero.
- Opening the popup twice: FUN_00614230 aborts via FUN_00487a80(0xC7=199) if a child popup already exists (FUN_0062cfc0 must return 0 before open). Always route open through msg 0x5F/0x24 which guard this.
- Index-out-of-range hard-aborts (FUN_00487a80, no return) on: 0x5D/0x38 (0x24B), 0x5E (0x2FE/0x24B), 0x61 (0x2CF), 0x63 (0x2F1/0x24B), item text overflow (0x252). Clamp indices to [0,count) yourself; 0xffffffff is the ONLY accepted "special" (means last / none) for 0x61.
- msg 0x20 (key/char) requires the out-consumed pointer param_4 non-null else FUN_00487a80(0x1C8).
- msg 0x36 popup placement aborts 0x238 if the supplied rect is degenerate (left>right or top>bottom) — feed a valid client rect.
- msg 0x38/0x08 render index guard: item+0x04 must stay < item+0x14 (text length) or 0x24B abort.
- Sort (FUN_00615ad0) aborts 0x66 if instance[0x17] comparator is NULL when invoked — only reachable through 0x62 with a valid fn ptr / 0x3A after comparator set; do not force-call sort without setting 0x62 first.
- Type-ahead buffer is a fixed 0x20-char ring at instance+0x10; it is bounded (writes guarded by len<0x20) but stale contents persist until msg 0x3B resets it — mixing programmatic selection with stale type-ahead can mis-match; send 0x3B to clear.
- Selected index default is 0 when items exist but -1 when empty; code paths that read item[selected] must handle -1 (they check, but external callers doing item[GetSelected()] will index -1 -> crash on empty list).
- Destroy order: msg 0xB frees item text buffers then the array; do not retain raw item pointers across a 0x58 (clear) / 0xB (destroy) — they are freed (FUN_0047f3a0 / FUN_005acaeb).

### CtlPageProc  (EXE 0x0061a950, confidence: high)

- **WASM:** ram:80e078f3 (named CtlPageProc(FrameMsgHdr const&, void const*, void*); body ram:80e078f3-80e087d8)
- **Struct:** Per-instance page context = 8 bytes, allocated at case 9 by operator-new tag FUN_0047f340("P:\\Code\\Engine\\Controls\\CtlPage.cpp",599). The instance-pointer slot is param_1[2] (piVar1); the proc writes ctx ptr into *piVar1.
 ctx+0x00 (dword): owning frame handle/id = copy of *param_1 (the frame id). Used everywhere as "*(*piVar1)" to re-dispatch to self.
 ctx+0x04 (int32): selectedTabIndex, initialized 0xFFFFFFFF (= none). GetSelectedTab (0x59) returns this; SelectTab (0x5d/0x31) writes it.
No other per-instance fields. Everything else (children, flags) lives on the underlying Frame object addressed by the frame id, queried via style-flag test FUN_0062fe20(frame,bit) and child-walk FUN_0062caa0(frame,mode,cur). Child "codes": page BODY frames use code = tabIndex (>=0); tab BUTTON frames use code = ~tabIndex (negative). FUN_0062d0a0(child) returns that signed code; >=0 => body, <0 => tab button. FUN_0062cfc0(frame,code) resolves a child by code; FUN_0062e2a0(child)=child->frameId; FUN_0062e3a0(child)=is-visible/enabled test used during layout.
- **Messages:** Dispatch is switch on param_1[1]=msg; piVar1=param_1[2]=instance slot; param_2=in/msg-struct, param_3=out. Unhandled/after-handled falls through to base chain thunk_FUN_00647170.
 case 4  InstallBase: writes base sub-proc FUN_006123a0 into *(param_2+0xc) (the vtable/base-proc slot). FUN_006123a0 itself: case4 installs FUN_0062c370; case9 asserts(0x108) if FrameNewSubclass FUN_0062d6f0 fails; case0x20 hit-test/mouse routing to tab btns (msg0x16 down/up -> FUN_00612560 arms btn proc FUN_006127c0); case0x24 flag 0x1000 focus handling; case1 paint pass-through when *param_2!=0.
 case 9  OnCreate: assert(0x256) if *piVar1!=0 (double-create); alloc 8B ctx (CtlPage.cpp:599), ctx[0]=frameId, ctx[1]=0xFFFFFFFF; then base-chain. RETURNS early (already chained).
 case 0xb Destroy: assert(0x25b) if *piVar1==0; free ctx via FUN_005acaeb(ctx,8); *piVar1=0.
 case 0x31 ChildNotify: read code=*(param_2+4), event=*(param_2+8), extra=*(param_2+0xc). If code>=0 (body) -> post msg 8 to self {code,event,extra} via FUN_0062ee80(frameId,8,&{code,extra,event},0). Else if event==7 (button click) -> SelectTab index=(~code) with notify=1 (FUN_0061b520).
 case 0x37 OnArrange/Layout (FUN_0061af80): reads metrics via self-msg 0x5e, tests wrap flag 0x40000 and orientation via FUN_0061acb0; positions each tab button (FUN_0062f770 anchor set) and stretches page bodies to fill; may re-invalidate FUN_0062f110.
 case 0x38 OnMeasure/size-query (FUN_0061b2d0): reads metrics 0x5e; walks children measuring tab buttons (FUN_0062d2a0) and bodies (FUN_0062d380); writes desired {w,h} to *(param_2+8); honors flags 0x10000 (use selected-tab width) / 0x20000 (use selected-tab height) / 0x40000 (multi-row adds row height local_48).
 case 0x56 AddTab (FUN_0061ad40): in-struct param_2 = {[0]=ownerPtr(user for btn), [1]=bodyFlags, [2]=tabIndex(>=0 else assert 0x1b2/0x32), [3]=bodyProc, [4]=bodyUserdata}; out param_3=created body frame id. Creates BODY = FUN_0062bfc0(frame, bodyFlags|0x200, tabIndex, bodyProc, bodyUserdata, 0) then hides it; creates BUTTON = FUN_0062bfc0(frame, 0x20100, ~tabIndex, CtlBtnProc 0x0060f4f0, ownerPtr, 0), setval -1. If no current selection -> auto SelectTab(tabIndex).
 case 0x57 DisableTab (FUN_0061af20(code,0)): code>=0 assert 0x206; resolve button by ~code, FUN_0062c9c0(btn,0).
 case 0x58 EnableTab (FUN_0061af20(code,1)): same, arg 1.
 case 0x59 GetSelectedTab: assert(0x20f) if out null; *param_3 = ctx[1] (selected index, 0xFFFFFFFF if none).
 case 0x5a GetTabButtonFrame: assert(0x218) out null, assert(0x219) param_2<0; *param_3 = FUN_0062cfc0(frame, index) (find child by code=index -> body). 
 case 0x5b BtnCodeToIndex: assert(0x222) out null, assert(0x3a "!IsBtnCode") if param_2>=0; *param_3 = ~param_2 (decode tab index from negative button code).
 case 0x5c GetBodyFrameId: assert(0x22a) out null, assert(0x22b) param_2<0; body=FUN_0062cfc0(frame,~param_2) assert(0x22e) if not found; *param_3=FUN_0062e2a0(body).
 case 0x5d SelectTab (FUN_0061b520 with notify=0): assert(0x236) if param_2<0. Deselect old (hide body, unpress+setval -1 on old button), select new (show body, press+setval 1 on new button), relayout (FUN_0062bd40/FUN_0062f470), if flags 0x30000 invalidate, ctx[1]=new; notify variant posts msg 7.
 case 0x5e GetMetrics: copies 7 dwords from DAT_00a50680 into param_3 = {0,0,0, 1.0f, 0, 20.0f, 0} (default tab-spacing=1.0, row-height=20.0). Styled UiCtlPageProc overrides this to supply texture-derived metrics.
 default/others: chain to base via thunk_FUN_00647170.
- **Create recipe:** This is the BASE tab/page logic proc; use the styled wrapper for real tab textures. Recipe:
1) Create the tab-container frame with the STYLED proc so you get textures AND the base logic: id = FUN_0062bfc0(parentFrame, styleFlags, childCode, UiCtlPageProc 0x00885590, userdata, 0). UiCtlPageProc chains to CtlPageProc (0x0061a950) for all case 9/0xb/0x31/0x37/0x38/0x56.../0x5e logic above; it also owns the tab-button texture proc UiCtlPageProc tab-btn 0x00885340. (If you only need untextured logic you may register CtlPageProc directly, but tabs will paint via flat CtlBtnProc 0x0060f4f0 only.)
2) Set orientation/behavior style flags on the frame BEFORE AddTab: 0x2000 = allow horizontal auto-fit (row of tabs), 0x4000 = vertical/single-column layout (forces column in FUN_0061acb0), 0x40000 = multi-row wrap, 0x10000/0x20000 = size to selected tab width/height in measure, 0x1000 = focus routing (base). Orientation decision is FUN_0061acb0: 0x4000 => column; else 0x2000 with <2 tab-buttons => single; else row.
3) For each tab, send AddTab: build in-struct {ownerPtr, bodyFlags, tabIndex(0,1,2,...), bodyContentProc, bodyUserdata} and call FUN_0062ef40(frameId, 0x56, &inStruct, &outBodyFrameId). AddTab makes the tab button (code=~index, proc CtlBtnProc 0x0060f4f0) and the hidden body (code=index, your bodyProc). Index 0 auto-selects.
4) Parent your page contents under the returned body frame id (or fetch later via msg 0x5c index->bodyFrameId, or 0x5a index->body child handle).
5) Programmatically switch: FUN_0062ef40(frameId, 0x5d, tabIndex, 0) (silent) — user clicks route through case 0x31 event 7 automatically.
6) Query current tab: FUN_0062ef40(frameId, 0x59, 0, &outIndex). Enable/disable: msg 0x58/0x57 with the tab index code.
Warm-ups: none beyond a valid parent frame and (for textures) the UiCtlPageProc style layer + its atlas being loaded. Sizing: control auto-measures via msg 0x38 using metrics from msg 0x5e (default row height 20.0, spacing 1.0); override metrics by layering the styled proc. Anchor/positioning of children is done internally with FUN_0062f770 during case 0x37, so do not hand-anchor tab children.
- **Gotchas:** All crashes are engine asserts via FUN_00487a80(code), file P:\Code\Engine\Controls\CtlPage.cpp (non-returning):
 - 0x256: sending msg 9 (OnCreate) twice on the same frame — ctx already allocated (double-create). Never re-issue create.
 - 0x25b: msg 0xb (Destroy) when ctx is null (never created / already destroyed).
 - 0x20f: GetSelectedTab (0x59) with a NULL out pointer — you MUST pass a valid out dword.
 - 0x218 / 0x219: GetTabButtonFrame (0x5a) NULL out / negative index.
 - 0x222 / 0x3a: BtnCodeToIndex (0x5b) NULL out / passing a NON-button (>=0) code — "!IsBtnCode". This msg expects a negative button code only.
 - 0x22a / 0x22b / 0x22e: GetBodyFrameId (0x5c) NULL out / negative index / index has no body (tab not added yet).
 - 0x236: SelectTab (0x5d) with a negative index.
 - 0x1b2 and 0x32: AddTab (0x56) with a negative tabIndex (two guards).
 - 0x206: Enable/Disable tab (0x57/0x58) with a non-negative code (expects negative-encoded code? actually asserts if code<0 path fails) — pass the tab index; internally negates.
 - 0x108: base sub-proc (FUN_006123a0) OnCreate — FrameNewSubclass (FUN_0062d6f0) failed to install the tab-button hit proc.
Additional non-assert gotchas: (a) msg 9/0xb are engine-driven; do not call them yourself — use the frame create/destroy primitives. (b) SelectTab is a no-op if new index == current (guards duplicate notify). (c) Children are auto-arranged in case 0x37; manually anchoring tab bodies/buttons will be overwritten. (d) Tab button vs body distinction is purely the sign of the child code (index vs ~index); reusing the same numeric index for a foreign child will confuse child-walk logic. (e) Without the UiCtlPageProc style layer, msg 0x5e returns only default metrics (no texture insets), so styled tab graphics won't render.

### CtlView (CtlViewProc)  (EXE 0x0060d410, confidence: high)

- **WASM:** unresolved (not needed; assertion string "P:\\Code\\Engine\\Controls\\CtlView.cpp" is embedded in the EXE proc at case 9 line 0x105 and case 0x3d line 0x348, directly confirming identity)
- **Assertion file:** P:\Code\Engine\Controls\CtlView.cpp (lines seen: 0x104 dup-create, 0x105 alloc, 0x117 null-instance, 0x158 null-out, 0x19c/0x19d mutually-exclusive scroll flags, 0x348 drag-helper alloc, 0x3ea/0x3fa/0x412/0x480 various)
- **Struct:** Instance = 0x34 bytes (freed as 0x34 in destroy). Zero-alloc; case-9 init writes:
 +0x00 [0]: content/model pointer. Init 0x20; overwritten by msg 0x7ffffff6 (*inst=param2). Used as scroll-line-step (inst[0]) in wheel/scroll math.
 +0x04 [1]: frame id (this control's frame handle). = frame[0] at create. Passed as *(inst+4) to all FUN_0062cfc0 child lookups. LOAD-BEARING.
 +0x08 [2]: aux param/rect pointer. Init 1; set by msg 0x7ffffffa (*(inst+8)=param2).
 +0x0c [3]: style bit = frame[4] & 1.
 +0x10 [4]: (uninit by ctor; zeroed by allocator) scroll-state / offset field.
 +0x14 [5]: (uninit) scroll-state / offset field.
 +0x18 [6]: (uninit) scroll-state / offset field.
 +0x1c [7]: drag-scroll helper object pointer (0xC8/200-byte object), else 0. Allocated msg 0x3d, freed msg 0x3c and in destroy.
 +0x20 [8]: active-drag tracked id; init 0xffffffff (-1 = idle).
 +0x24 [9]: init 0 (also base of an intrusive list head used by helper +0xa4).
 +0x28 [10]: init 0.
 +0x2c [11]: viewport width; set by msg 0x7ffffff4 (*param2).
 +0x30 [12]: viewport height; set by msg 0x7ffffff4 (param2[1]).

Drag-scroll helper (0xC8 bytes, alloc line 0x348): +0x24 list node base; +0xa4 list head (=self+0x24); +0xa8..+0xb4 zeroed; +0xb8/+0xbc size (param2[2],param2[3]); +0xc0/+0xc4 zeroed.
- **Messages:** FrameProc signature FUN_0060d410(undefined4 *frame, float *param2, uint *out). msg = frame[1]; instance reached via FUN_0060f120(frame)=**(int**)(frame+8) (asserts 0x117 if null). Base fall-through is thunk_FUN_00647170 (base CtlFrame proc). Child slots via FUN_0062cfc0(frameId,idx): idx1=content frame, idx2=vertical scrollbar, idx3=horizontal scrollbar.

LOW block (msg < 0x7ffffff3):
- 0x7ffffff2 (relayout/measure): child=FUN_0062cfc0(inst[+4],1); asserts 0x117 if inst null, 0x480 if child null; FUN_0062fcb0(child,param2) then FUN_0062f470(inst[+4]); falls to base.
- 5 (PAINT): if global DAT_00c0ac30==0 it seeds view render color globals (_DAT_00c0ac1c..2c from _DAT_009407b8/_DAT_00942af4/_DAT_00940ee0/_DAT_00940ea8, alpha 1.0) then calls base and RETURNS; else just base.
- 9 (ONFRAMECREATE): allocates 0x34-byte instance (FUN_0047f340, line 0x105); asserts 0x104 if slot already set; installs it, sets scroll style, creates inner content frame FUN_0062bfc0(inst[+4],0x300,0,FUN_0060f0f0,0,0), and if param2[0]!=0 creates an inner child control from descriptor {flags,proc,userdata}.
- 0xb (DESTROY): asserts 0x117 if null; frees inst[+0x1c] drag helper (200 bytes) then inst (0x34 bytes); zeroes slot.
- 0x13 (19, HITTEST/FOCUS-QUERY): if (out[4]&1) and content child (slot3/slot2) exists, sets out[5]|=1, *out=child, forwards to base+returns; else resolves inner child control id into *out and forwards if nonzero.
- 0x2f (47, MOUSEWHEEL): converts wheel delta (FUN_0060ca40); if nonzero scrolls the vertical(3)/... scrollbar child by +/- inst[0] via FUN_005636a0.
- 0x31 (49, SCROLLCMD): sub-dispatch on param2[1]/param2[2]: line-up/line-down (+/- inst[0]), page-up/page-down (viewport height via FUN_0060f4d0), and a set-position path (FUN_0060a400 + FUN_0060f150 invalidate). param2[1]==0 branch calls FUN_0062ee80 (route to child) when param2[2]>6.
- 0x37 (55): FUN_0060e420(param2).
- 0x38 (56, MEASURE/SIZE-QUERY): resolves inner content control, computes combined min/max size into *param2[2] rect (clamps).
- 0x3c (60, END-DRAGSCROLL): if *param2==inst[+0x20] tears down drag helper: inst[+0x20]=0xffffffff, free inst[+0x1c] (200 bytes), inst[+0x1c]=0.
- 0x3d (61, BEGIN-DRAGSCROLL): if inst[+0x20]==-1 and param2[4]!=0, allocates 0xC8-byte drag helper (line 0x348), links list head (+0xa4=self+0x24), stores size (+0xb8/+0xbc = param2[2],param2[3]), sets inst[+0x1c]=helper, inst[+0x20]=*param2, out[0]=(param2[5]==0), sends 0x45 to inst[+4], forwards to base+returns.
- 0x3e (62): FUN_0060ec30(param2).
- 0x3f (63): FUN_0060ee70(param2).
- 0x45 (69): FUN_0060e210(param2).
- default: if msg==0x21 or msg>0x55, forward to inner child control's own dispatcher via FUN_0062cfc0(child,0,0)->id->FUN_0062ef40(id,msg,param2,out) then base; else just base.

HIGH block (private/internal, msg 0x7ffffff3..0x7fffffff):
- 0x7ffffff3: GET content extent, dim=3 (horizontal); via child(inst[+4],3), FUN_0060a400 if differs.
- 0x7ffffff4: SET viewport size inst[+0x2c]=param2[0], inst[+0x30]=param2[1]; decides scroll enable via FUN_006302c0(inst[+4],...) using scrollbar children 2/3 and drag state.
- 0x7ffffff5: FUN_0060f0b0(param2).
- 0x7ffffff6: SET inst[0]=param2 (content/model pointer).
- 0x7ffffff7: GET content extent, dim=2 (vertical) — shared LAB with 0x7ffffff3.
- 0x7ffffff8: RECREATE scrollbar child: destroy old child(inst[+4],1) via FUN_0062c550, recreate FUN_0062bfc0(inst[+4],(*param2)|0x300,1,param2[1],param2[2],0).
- 0x7ffffff9: LAYOUT/scroll children; asserts 0x412 if param2[0]>param2[2] or param2[1]>param2[3] (min>max rect inversion); positions vertical(2)/horizontal(3) scrollbars.
- 0x7ffffffa: SET inst[+8]=param2, invalidate FUN_0062f470(inst[+4]).
- 0x7ffffffb: GET horizontal content metrics (child idx3) into out[0..3]; asserts 0x158 if out null; forwards to base+returns; if no child jumps to LAB_0060dbda (FUN_0046dac0 then base).
- 0x7ffffffc: GET inner child control id into out[0]; asserts 0x3fa if out null; forwards+returns.
- 0x7ffffffe: GET vertical content metrics (child idx2) into out[0..3]; asserts 0x158 if out null; else LAB_0060dbda fallback; forwards+returns.
- 0x7fffffff: GET child(inst[+4],1) id into out[0]; asserts 0x3ea if out null; forwards+returns.
- **Create recipe:** 1. Create the frame with the standard primitive: FUN_0062bfc0(parentFrameId, flags|0x300, childSlot, proc=0x0060d410, userdata, 0). The 0x300 bits are OR'd in by the view for its own inner content frame and are the expected convention.
2. Scroll orientation is chosen by FRAME STYLE FLAGS (tested in msg 9 via FUN_0062fe20): horizontal pair = 0x10000 / 0x20000; vertical pair = 0x8000 / 0x40000. Pick AT MOST ONE flag from each pair (see crash gotchas). Absence of both = that axis non-scrolling.
3. The engine sends msg 9 (OnFrameCreate) which allocates the 0x34 instance, creates the inner content frame (proc FUN_0060f0f0) and the scrollbar children. Do NOT allocate the instance yourself.
4. Optional inner child control: pass param2[0] (create param block word 0) = pointer to a descriptor {word0=childFlags, word1=childProc, word2=childUserdata}; the view creates it as FUN_0062bfc0(inst[+4], childFlags|0x300, 0, childProc, childUserdata, 0). Leave NULL for an empty container.
5. Warm-up / ordering: after create, set the content/model via msg 0x7ffffff6, set viewport size via msg 0x7ffffff4 (word0=width, word1=height) so scroll enable (FUN_006302c0) is computed. Provide content extents so msg 0x7ffffff3/0x7ffffff7/0x7ffffffb/0x7ffffffe return sane rects.
6. Sizing: the anchor-6 pos/size setter (0x0062F770) sets outer geometry as with any control; the view internally lays out content+scrollbars on msg 0x7ffffff9 and clamps min/max on msg 0x38.
7. Destroy: send msg 0xb (or native destroyer FUN_0062c550 on the frame id) exactly once; it frees the drag helper then the instance.
- **Gotchas:** - DUP CREATE: msg 9 asserts (line 0x104) if the instance slot *(frame+8) is already non-null. Never deliver OnFrameCreate twice.
- NULL INSTANCE: FUN_0060f120 asserts 0x117 whenever any get/set/paint arrives before msg 9 populated the instance. Do not send any control message (0x2f,0x31,0x37,0x38,0x3c,0x3d,0x7ffffff2..0x7fffffff, or generic 0x21/>0x55) until after create.
- MUTUALLY-EXCLUSIVE SCROLL FLAGS: setting BOTH 0x10000 and 0x20000 on the frame asserts line 0x19c; setting BOTH 0x8000 and 0x40000 asserts line 0x19d. Choose one per axis.
- RECT INVERSION: msg 0x7ffffff9 (scroll layout) asserts line 0x412 if param2[0] > param2[2] OR param2[1] > param2[3] (min greater than max). Always pass min<=max extents.
- NULL OUT-PTR on getters: msg 0x7ffffffb & 0x7ffffffe assert 0x158; msg 0x7ffffffc asserts 0x3fa; msg 0x7fffffff asserts 0x3ea. Always pass a valid out buffer (>=4 dwords for the metric getters, which write out[0..3]).
- MISSING CONTENT CHILD on 0x7ffffff2 asserts 0x480 (child(inst[+4],1) must exist — only send after successful create).
- DRAG-STATE GUARD: msg 0x3d only begins a drag if inst[+0x20]==-1 and param2[4]!=0; msg 0x3c only ends it if *param2 matches inst[+0x20]. Mismatched begin/end leaks/keeps the 0xC8 helper (freed at destroy, but tracked id stays non-idle).
- PAINT GATE: msg 5 seeds render color globals only when DAT_00c0ac30==0; otherwise it just chains base — no per-instance paint crash, but the view assumes the base CtlFrame proc (thunk_FUN_00647170) is intact.
- GENERIC PASS-THROUGH: default branch (msg 0x21 or >0x55) requires an installed inner child control; with none it silently no-ops then base (no crash), but callers expecting child get/set replies get nothing.

### CtlFrameListProc (CtlFrameList — scrolling frame-list container)  (EXE 0x00612c80, confidence: high)

- **WASM:** ram:80e805f1
- **Assertion file:** P:\Code\Engine\Controls\CtlFrameList.cpp
- **Struct:** Instance struct = 0x74 bytes (allocated in case 9 via FUN_0047f340("...CtlFrameList.cpp",0x74); freed in case 0xb via FUN_005acaeb(inst,0x20)). Accessed through FUN_00613b00 = **(int**)(frameCtx+8) (the TCtlInstance<T> slot). Only offsets 0x00-0x1c are used by this proc; 0x20-0x73 are reserved/unused here.
+0x00 (idx0): owning frame handle/id (set = *param_1 at create; every op does FUN_0062caa0(inst[0],...) tree nav off it).
+0x04 (idx1): arrangeCbA  int(*)(FrameList* items, Box* box)          — set by msg 0x62.
+0x08 (idx2): arrangeCbB  int(*)(FrameList* items, Box* box, void* ud) — set by msg 0x63.
+0x0c (idx3): arrange userdata for idx2                               — set by msg 0x63.
+0x10 (idx4): measureCbA  int(*)(FrameList* items, SizeOut* out)      — set by msg 0x64.
+0x14 (idx5): measureCbB  int(*)(frame, FrameList* items, SizeOut* out, void* ud) — set by msg 0x65.
+0x18 (idx6): measure userdata for idx5                               — set by msg 0x65.
+0x1c (idx7): sort comparator  int(*)(a,b) (returns nonzero if a should precede b) — set by msg 0x66; drives insert-sort in add (0x57), bubble re-sort (0x60/0x613bf0), single re-place (0x61/0x613d30).
All callback slots + comparator start NULL (create only writes idx0,1,2,4,5,7 to 0). FrameList temp = struct{void* buf; int cap; int count; ...} built by FUN_006127f0 into locals during measure/arrange.
- **Messages:** Dispatch on param_1[1]=msg; sig FrameProc(uint* param_1{ctx: [0]=frame,[1]=msg,[2]=inst-slot-ptr}, float* param_2=in/wparam, float* param_3=out). Handled cases:
9  OnFrameCreate: alloc 0x74 instance, store frame handle at idx0, zero callbacks+comparator; ASSERT 0x73 if slot already set (double create).
0xb OnDestroy: FUN_005acaeb(inst,0x20); null the slot.
0x13 GetDefaultChild: *param_3 = first child (FUN_0062caa0(frame,1,0)) if nonzero.
0x31 HitTest/forward: if param_2[2]>6, repackage 5 floats and forward FUN_0062ee80(frame,7,...).
0x37 ARRANGE (layout pass): build child array (006127f0, filtered to visible unless flag 0x2000); if idx2 set call arrangeCbB(list,box,ud); elif idx1 set call arrangeCbA(list,box); else DEFAULT: stack children bottom-up — y starts param_2[1](height), each child measured (0062d2a0), y-=childH, FUN_0062f770(child,{0,y},{width,childH}). Frees list at 0x47f3a0.
0x38 MEASURE (preferred size): build child array; if idx5 set call measureCbB(frame,list,out,ud); elif idx4 set call measureCbA(list,out); else DEFAULT: out{param_2[2]}.w=max(childW), .h=sum(childH); then if flag 0x4000 NOT set, out.w = param_2[0] (given width). Frees list.
0x56 ClearAll: FUN_0062c760(frame) — recursively destroy all child frames / tear down subtree.
0x57 AddChild: FUN_0062bfc0(frame, param_2[0]|0x300, param_2[1], param_2[2]=proc, param_2[3]=userdata, 0) creates child; if comparator(idx7) set, insert-sort into siblings (compare vs prev(mode1)/next(mode3), FUN_0062fdb0 reorder, FUN_0062f470 invalidate); returns new child handle in *param_3. ASSERT 0x149 if create fails while comparator set.
0x58 RemoveChild: resolve handle (0062cfc0), destroy via native FUN_0062c550(id); ASSERT 0x203 if not found.
0x59 GetNeighbor: dir=param_2[0] (0=next-of param_2[1], 1=prev-of, 2=first, 3=last); writes id->param_2[2], handle->param_2[3]. ASSERT 0x212/0x218 ref missing, 0x223 bad dir.
0x5a GetVisibleNeighbor: like 0x59 but skips invisible (FUN_0062e3a0 loop). ASSERT 0x242/0x249/0x256.
0x5b ResolveChild: *param_3 = id from handle; ASSERT 0x276 out null.
0x5c GetChildRect: *param_3[0..3]={x,y,x+w,y+h}; ASSERT 0x27f out null, 0x282 child missing.
0x5d IsEmpty: *param_3 = (first child==0); ASSERT 0x29b out null.
0x5e IsChildVisible: *param_3 = IsVisible(child); ASSERT 0x2a6 out null, 0x2a9 child missing.
0x5f MoveChild: dir=param_2[1] (0=before param_2[2],1=after,2=front,3=back) via FUN_0062fdb0 + invalidate; ASSERT 0x2b3 target missing, 0x2ba/0x2c1 ref missing, 0x2cc bad dir.
0x60 ReSortAll: if comparator set, FUN_00613bf0 bubble re-sort.
0x61 ReplaceOne: re-insert one child to sorted pos (FUN_00613d30) if comparator set; ASSERT 0x2ea child missing.
0x62 SetArrangeCbA: idx1=param_2; invalidate arrange (0062f470).
0x63 SetArrangeCbB: idx2=param_2[0], idx3=param_2[1]; invalidate arrange.
0x64 SetMeasureCbA: idx4=param_2; invalidate measure (0062f110).
0x65 SetMeasureCbB: idx5=param_2[0], idx6=param_2[1]; invalidate measure.
0x66 SetComparator: idx7@+0x1c=param_2; if nonzero full re-sort (00613bf0).
0x67 SetChildVisible: resolve child, FUN_0062fcb0(child,param_2[1]); if changed and flag 0x2000 clear, invalidate measure+arrange.
Cases 0xa,0xc-0x12,0x14-0x30,0x32-0x36,0x39-0x55 and default: no-op (fall through to base dispatcher).
- **Create recipe:** 1) Create the frame with this proc registered: FUN_0062bfc0(parent, flags, childKey, proc=0x00612c80, userdata, 0). Framework then sends msg 4 (install vtable/base) and msg 9 (OnFrameCreate) which allocates the 0x74 instance and stores the frame handle at idx0. Do NOT touch the control before msg 9 fires — every get/set calls FUN_00613b00 which ASSERTs 0x86 if the instance slot is still null.
2) (Optional) configure layout: send 0x66 to install a sort comparator (enables auto-sorted insertion); send 0x62/0x63 for a custom arrange callback and/or 0x64/0x65 for a custom measure callback. Without callbacks the DEFAULT vertical bottom-up stack + max-width/sum-height measure applies.
3) Flags on the FRAME control word (read via FUN_0062fe20(frame, mask)): 0x2000 = include-hidden / manual-layout (enumeration keeps invisible children; visibility toggles via 0x67 skip relayout). 0x4000 = content-width (measure keeps max child width; when clear, measured width is overridden to the frame's given width). Children are always created with (givenFlags | 0x300).
4) Populate: msg 0x57 per item (pass child flags, key, child proc, child userdata) — returns the new child handle. Remove with 0x58, reorder with 0x5f, toggle visibility with 0x67, re-sort with 0x60/0x61, tear everything down with 0x56.
5) Sizing: the container asks children for their size via the shared measure primitive (0062d2a0) and lays them out with the anchor setter FUN_0062f770; give each child a real height or it collapses. Provide the container a width via the measure input (param_2[0]) when flag 0x4000 is clear.
- **Gotchas:** - Pre-init access: any msg except 9 routes through FUN_00613b00 -> ASSERT 0x86 if instance not created yet; double-create -> ASSERT 0x73 (case 9 guard).
- Null-out-pointer asserts: 0x5b needs param_3 (0x276), 0x5c needs param_3 (0x27f), 0x5d needs param_3 (0x29b), 0x5e needs param_3 (0x2a6). Passing NULL out crashes.
- Child-not-found asserts: 0x58->0x203, 0x5c->0x282, 0x5e->0x2a9, 0x61->0x2ea, 0x67->0x332, 0x5f->0x2b3, navigation 0x59->0x212/0x218, 0x5a->0x242/0x249. Handles must be live children of THIS frame (resolved via FUN_0062cfc0/FUN_0064ca80).
- Bad direction codes: 0x59 default->0x223, 0x5a->0x256, 0x5f->0x2cc (valid codes 0..3 only).
- Add failure: 0x57 with a comparator installed ASSERTs 0x149 if FUN_0062bfc0 returns 0 (child create failed); redundant idx7 recheck ASSERTs 0x14a.
- Sort paths require comparator: FUN_00613bf0 ASSERTs 0xa3 and FUN_00613d30 ASSERTs 0x109/0x10a if invoked with idx7 null — but the proc only reaches them after checking idx7 (0x60/0x61 guard, 0x66 sets it first), so safe if you never null idx7 mid-flight.
- Temp list buffer: measure/arrange (0x37/0x38) allocate a child-array (FUN_006127f0, ASSERT 0x91 if its out-ptr null; min capacity 0x32) and MUST free it at LAB_00612fb0 (FUN_0047f3a0) — both paths goto it; custom arrange/measure callbacks run inside this window and must not longjmp/destroy the list.
- Default arrange requires children to report nonzero height (0062d2a0) or they overlap at the same y; default measure with flag 0x4000 clear discards computed width in favor of the given width.

### CCtlFrameListSelectable (CtlFrameListSelectableProc / selectable frame-list MsgProc)  (EXE 0x00613850 (thunk/registered proc entry 0x00612b90 JMP->0x00613850); WASM CtlFrameListSelectableProc ram:80e83514, CCtlFrameListSelectable::FrameProc ram:80e835fc, confidence: high)

- **WASM:** ram:80e83514 (CtlFrameListSelectableProc) / ram:80e835fc (CCtlFrameListSelectable::FrameProc). Helpers: SetSelection ram:80e7f9e7 (EXE FUN_00613b60 @0x00613b60), VoidSelection ram:80e7feac (EXE FUN_006128a0 @0x006128a0). Assertion string "P:\\Code\\Engine\\Controls\\CtlFrameList.cpp".
- **Struct:** Per-instance selection-state struct = 0xC (12) bytes, heap-allocated in msg 9, pointer stored in the frame's control-instance slot (*(param_1[2])):
+0x00 dword ownerFrameId  (copied from *param_1 at create; used as base id for FrameGetChild/NotifyParent/Send)
+0x04 dword hasSelection  (0 = nothing selected, 1 = a row selected)
+0x08 dword selectedItemFrameId (valid only when +0x04 != 0; the child row frame id currently selected)
Relevant owner FRAME styles (frame struct +0x190, tested via FUN_0062fe20): 0x10000 = auto-select-single-child (msg 0x57); 0x8000 = auto-reselect-a-shown-neighbor on removal (FUN_00613e50, else it just clears). Create flags word (0x20128) is distinct from these style bits.
- **Messages:** Dispatch on msg=param_1[1]; param_1[2]=instance-slot ptr, param_2=in-payload, param_3=out. Accessor FUN_00613b30 = *(*(param_1[2])) and asserts 0x3f8 if instance NULL.
- 4 (install base): *(param_2[3]) = &LAB_00612ad0 (base CtlFrameList vtable/proc). No instance yet.
- 9 (OnFrameCreate): if *(param_1[2])!=0 -> assert 0x3e5 (double create). Else MemAlloc(0xc) at CtlFrameList.cpp:0x3e6, init [+0]=frameId(=*param_1), [+4]=0(hasSel), store ptr into *(param_1[2]). REQUIRED before any get/set sel.
- 0xb (destroy): if instance!=0 FUN_005acaeb(instance,0xc)=operator delete; slot=0.
- 0x31 (item notify from child rows, subcode=param_2[2], itemId=param_2[1]): subcode 7 = selected item being removed -> if hasSel && itemId==selectedId call FUN_00613e50 (reselect a shown neighbor else clear). subcode 8 = item activated/clicked -> SetSelection(itemId). else -> base.
- 0x56 (ClearSelection, internal): assert instance; FUN_006128a0 (VoidSelection: clears flag, sends 0x56 to selected row, NotifyParent code 8); then base.
- 0x57 (post child-add): calls base first; if owner style 0x10000 set AND first-child==last-child (single item, via EnumChild dir1==dir3) -> SetSelection(param_2[1]) (auto-select-single).
- 0x58 (child destroyed, param_2=destroyed frame id): if hasSel && param_2==selectedId -> FUN_00613e50 (reselect-neighbor-or-clear), then base.
- 0x67 (item shown-state change, param_2[0]=id, param_2[1]=isShown): if hasSel && id==selectedId && isShown==0 -> FUN_00613e50 (selected item hidden -> reselect/clear), then base.
- 0x68 (ClearSelection): assert instance; FUN_006128a0 (VoidSelection). No base call.
- 0x69 (GetSelection): assert instance; if param_3==0 assert 0x4ae; else param_3[0]=hasSel flag(+4), param_3[1]=selectedId(+8).
- 0x6a (SetSelection/Select): assert instance; FUN_00613b60(instance, param_2) where param_2 = target item frame id.
- default/other: forwarded to base list proc thunk_FUN_00647170.
OUTBOUND from SetSelection (FUN_00613b60): FrameMsgSend(selectedRowFrame, 0x57, 0,0)=highlight-on; FrameMsgNotifyParent(owner, 9, selectedId, 0)=code9 SELECTED. From VoidSelection (FUN_006128a0): FrameMsgSend(prevRowFrame, 0x56,0,0)=highlight-off; FrameMsgNotifyParent(owner, 8, id, 0)=code8 DESELECTED. So parent app observes selection via notify codes 9(sel)/8(desel) carrying the item frame id. Rows are CtlTextSelectable (0x00617df0) which interpret 0x56/0x57 as their unhighlight/highlight paint state.
- **Create recipe:** Verified from a real creator FUN_00619b70 (builds a selectable text list):
1) Register the row/item proc on the parent: FrameMsgSend(parent, 100/0x64, 0, procDescriptor) where the row proc = CtlTextSelectable 0x00617df0 (thunk_FUN_00617df0). This makes list items selectable text rows.
2) Create the list frame: id = FUN_0062bfc0(parent, flags, child=0, proc=&LAB_00612b90 (=0x00613850 selectable list proc), userdata, 0). Returns frame id stored at frame+0xbc. FLAGS: 0x20128 (verified @0x00619bd6 for the friends/party-style selectable list). An alternate creator (@0x0057c384) uses 0x380 with the same proc; 0x20128 is the recommended selectable config. msg 9 fires automatically on create and allocates the 0xC sel-state.
3) FUN_0062f5a0(id, 0xFFFFFFFF) — set sort/insert index = -1 (append).
4) FUN_00612c30(id, handler) — register the list's item/sort-notify handler (FUN_00617940 in the sample).
5) Populate: add each row as a child frame (selectable text row proc 0x00617df0) via the base CtlFrameList create-item path; rows must exist as real child frames of this list id.
6) Size/position via the standard anchor-6 setter FUN_0062F770 like other controls; the list lays out its child rows.
Order/warm-ups: OnFrameCreate (msg 9) MUST have run (it does, on create) before any 0x69/0x6a. To select a row via 0x6a the row must (a) already be a child of the list and (b) be shown/visible. When removing a row, first tell the list (msg 0x31 subcode 7, or 0x58) so it can move/clear selection instead of dangling.
- **Gotchas:** All are ErrorAssertion (non-returning) in CtlFrameList.cpp:
- 0x3e5: msg 9 sent when instance already allocated (double create). Never re-send OnFrameCreate.
- 0x3f8: accessor found NULL instance -> any get/set/notify (0x31/0x56/0x58/0x67/0x68/0x69/0x6a) reached the selectable proc before msg 9 or after destroy (0xb). Must create through this proc so case 9 allocates the sel-state.
- 0x428: SetSelection (0x6a) with an item id that is NOT a child of the list (FrameGetChild returned 0). Only select existing child rows.
- 0x42b: SetSelection to a child that is not shown/visible (IsShown/FUN_0062e3a0 == 0). Show the row first.
- 0x408: VoidSelection/ClearSel could not resolve the previously-selected child (FrameGetChild==0) — happens if the selected row was destroyed WITHOUT notifying the list. Route row removal through msg 0x31 sub 7 / 0x58 first.
- 0x444: reselect path (FUN_00613e50) FrameGetChild==0 for the outgoing selection — same root cause (row destroyed silently while selected).
- 0x4ae: GetSelection (0x69) called with param_3 (out ptr) == NULL. Always pass a valid 2-dword out buffer.
- Lifetime: sel-state is heap (0xc bytes); destroy (0xb) frees it and nulls the slot — any later message asserts 0x3f8. Do not cache/re-drive a destroyed list id.

### CtlImeCand (CtlImeCandProc)  (EXE 0x0061d870, confidence: high)

- **WASM:** unresolved (assertion string "P:\\Code\\Engine\\Controls\\CtlImeCand.cpp" confirms identity directly in EXE; WASM name lookup not required)
- **Struct:** Per-instance struct (TCtlInstance<CImeCand>), tracked-allocated in ONFRAMECREATE (CtlImeCand.cpp line 0x6b), freed with FUN_005acaeb(inst,0x10). Verified fields (all dword):
+0x00 ownerFrameId  — set to *frameArgs at create; used everywhere as *instance to resolve children (FUN_0062cfc0) and dispatch (FUN_0062ef40).
+0x04 pageStartCache — last IME candidate-list page-start (candidateList[4]); init 0, refreshed at end of 0x56 (instance[1]=list[4]).
+0x08 highlightIndex — currently highlighted candidate row (0..9), init -1 (0xffffffff); at end of 0x56 old!=new triggers 0x56(blur)/0x57(focus) on rows, then instance[2]=new.
+0x0c listChangeToken — last-seen candidateList[0]; init 0; if (list[0]!=instance[3]) -> FUN_0062f470 invalidate; then instance[3]=list[0].
Only these 4 dwords (0x00-0x0c) are read/written by the proc; total allocation size not recoverable from the wrapper decompiler but is >=0x10.
CANDIDATELIST arg to 0x56 (int* list, offsets in dwords): [0]=change token/count, [1]=total candidate count, [2]=attribute/style base, [3]=global selection index (-1 none), [4]=page-start index, [5]=page count A (must be <=10: list[5]+2<=0xc else assert 0xbb), [6]=page count B (list[6]+2<=0xc else assert 0xba), [8]=first candidate string ptr (subsequent strings walked via FUN_0046c270 length*2+2 stride).
- **Messages:** FrameProc signature FUN_0061d870(uint* frameArgs, byte* msgData, u32 param3). Dispatch is switch(frameArgs[1]) = message id. Unhandled/base cases fall through to base-class thunk thunk_FUN_00647170(frame,msgData,param3). Instance pointer is fetched by FUN_0061e0e0 = **(frameArgs+8) and it ASSERTS (FUN_00487a80(0x7d)) if null.

- 0x08 PAINT: gets instance; only draws when (msgData[0] & 1) (visible bit). Builds a render/material handle via FUN_00679a60(&h, 0x20003e0, 0) then FUN_0062b2d0(frameId, msgData+0x1c, mat, &scaleXY(1.0,1.0), &offset(0,0),0,0) to draw the candidate-window background quad, releases mat (FUN_0046f850), then chains to base. If bit not set, chains straight to base.
- 0x09 and 0x0c..0x55 (excluding 0x0a,0x0b,0x31,0x37,0x38): NO-OP group, forwarded to base proc.
- 0x0a (10) ONFRAMECREATE: allocates the instance (tracked alloc FUN_0047f340, CtlImeCand.cpp line 0x6b) IFF *(frameArgs[2])==0, else asserts FUN_00487a80(0x6a) (double-create). Inits instance [frameId, 0, -1, 0], stores ptr at *(frameArgs[2]). Copies the 11-dword child-template PTR_FUN_00a50874 to stack, queries existing child ids via FUN_0062ef40(frameId,0x57,0,tmpl), then creates 14 child frames with FUN_0062bfc0(frameId, flags, childIndex, childProc, 0, 0): idx0 flags0x40000 proc0x0061d7b0 (prev-page arrow, subclass flat CtlBtnProc 0x0060f4f0), idx1 flags0x40000 proc0x0061d7e0 (next-page arrow), idx2..0xb flags0x4300 proc0x0061d810 (10 candidate rows, subclass selectable-text CtlTextSelectable 0x00617df0, forces style bit|1), idx0xd flags0 proc0x0061b9d0, idx0xe flags0x90000 proc0x00610c40 (the "%u/%u" page-counter label). Then chains base.
- 0x0b (11) ONFRAMEDESTROY: if instance!=0 frees it FUN_005acaeb(inst,0x10); clears *(frameArgs[2])=0; chains base.
- 0x31 (49) INPUT/COMMAND: msgData[1]=action code (uVar1), msgData[2]=event type. uVar1 in 2..0xb with event==9 -> select candidate row (FUN_00651850(0,3,0, pageStart+(uVar1-2)) then FUN_00651850(0,2,0,0), i.e. commit). uVar1==0 event==7 -> prev-page (thunk_FUN_005f3990). uVar1==1 event==7 -> next-page (thunk_FUN_005f39a0). uVar1==0xd -> keyboard nav: (event-7) 0=down,1=up,2=page-down,3=page-up computes new sel index into instance[+4] baseline, 4=absolute (msgData[3]); applies via FUN_0060a400 + FUN_0059fea0 + FUN_00651850(0,4,0,...). Handled cases chain base; others fall through.
- 0x37 (55) MEASURE-WIDTH/LAYOUT-H: FUN_0061e0e0 (assert-if-null) then FUN_0061dca0(msgData) lays children horizontally; iterates children 2..0xb via FUN_0062cfc0/FUN_0062e3a0(visible?)/FUN_0062d2a0(measure)/FUN_0062f770(anchor-6 set). Chains base.
- 0x38 (56) MEASURE-SIZE: FUN_0061e0e0 then FUN_0061df40(msgData) accumulates child sizes into msgData[2] (out size struct), writes width/height. Chains base.
- 0x56 (86) UPDATE-FROM-IME: FUN_0061e0e0 then FUN_0061e110(instance, candidateList). Repopulates the 14 children from a Win32-CANDIDATELIST-like struct (see create recipe), sets per-row visibility/enable/text, highlight, and the "%u/%u" page label; sends 0x56/0x57 (blur/focus) to old/new highlighted row; if list token changed calls FUN_0062f470 (invalidate). Does NOT chain base (breaks after).
- default: chains base proc.
- **Create recipe:** This is an engine-internal IME composition candidate window; normally the IME subsystem instantiates it, not app UI code. To create manually:
1) Create the host frame with the native create primitive: FUN_0062bfc0(parentFrameId, flags, childId, CtlImeCandProc=0x0061d870, userData, 0). The frame must provide an instance-slot pointer at frameArgs[2] (standard TCtlInstance wiring done by the frame system).
2) Send ONFRAMECREATE msg 0x0a EXACTLY ONCE. The proc self-builds all 14 children (2 arrow buttons idx0/1, 10 candidate rows idx2-0xb, an aux frame idx0xd, and a "%u/%u" page label idx0xe) from template PTR_FUN_00a50874. Do NOT send 0x0a twice (asserts 0x6a). Order matters: no other instance-touching message (0x08 paint, 0x31 input, 0x37/0x38 measure, 0x56 update) may be delivered before 0x0a or FUN_0061e0e0 asserts 0x7d.
3) Feed candidate data via msg 0x56 with a pointer to a CANDIDATELIST-shaped struct (layout in struct_layout). Keep page counts small: list[5]+2 and list[6]+2 must each be <= 0xc (i.e. at most 10 visible candidates) or it asserts. list[3]=-1 for no selection.
4) Layout: host will emit 0x37 (horizontal) and 0x38 (size) which measure children; supply finite non-negative sizes in msgData or FUN_0061dca0 asserts 0x238. Paint happens on 0x08 with msgData[0]&1 set; requires the render/material path (FUN_00679a60 material id 0x20003e0) to be live — i.e. UI render device warmed up.
5) Navigation/selection is driven by msg 0x31 (action code in msgData[1], event in msgData[2]); rows 2..0xb + event 9 commit the candidate, action 0/1 + event 7 page prev/next.
Destroy with msg 0x0b (frees instance, clears slot) or the native destroyer FUN_0062c550(frameId).
- **Gotchas:** 1) NULL-INSTANCE ASSERT (FUN_00487a80(0x7d)): messages 0x08, 0x31, 0x37, 0x38, 0x56 all call FUN_0061e0e0 which asserts if the instance ptr (**(frameArgs+8)) is null. Never deliver these before ONFRAMECREATE (0x0a) has run. 2) DOUBLE-CREATE ASSERT (0x6a): sending 0x0a when *(frameArgs[2])!=0 aborts. 3) PAGE-SIZE ASSERTS in 0x56/FUN_0061e110: candidateList[6]+2 > 0xc -> abort 0xba; candidateList[5]+2 > 0xc -> abort 0xbb. Cap visible candidates at 10; malformed/large IME page counts crash. 4) LAYOUT NAN/NEGATIVE ASSERT (0x238) in 0x37/FUN_0061dca0 and its size math: passing NaN, negative, or non-strictly-positive width/height (the code checks 0.0<x==(x==0.0) i.e. rejects <=0 and NaN) aborts — measure inputs must be finite positive. 5) PAINT GATE: 0x08 only draws when (msgData[0] & 1); it also allocates a material (FUN_00679a60 id 0x20003e0) and draws quad from msgData+0x1c — the UI render device/material system must be initialized or the draw path faults; no image-list warm-up specific to this control, but the parent atlas must be present. 6) Child creation in 0x0a hard-depends on the 14-entry child template and child procs (0x0061d7b0/e0, 0x0061d810, 0x0061b9d0, 0x00610c40); those subclass CtlBtnProc/CtlTextSelectable so the base control registry must be installed first. 7) 0x56 does NOT forward to base (early return) — anything expecting base post-processing on update won't get it.

### CtlImeReading (CtlImeReadingProc)  (EXE 0x0061e470, confidence: high)

- **WASM:** ram:80dd15c4 (CtlImeReadingProc); styled wrapper IUi::UiCtlImeReadingProc ram:80e0e1f2 == EXE 0x00889560; dtor CtlImeReading::ImeReadingProp::~ImeReadingProp ram:80dd4c08
- **Assertion file:** P:\Code\Engine\Controls\CtlImeReading.cpp (create=line 0xb6/182; overlap guard 0x171; size-query null 0xc7)
- **Struct:** Instance size 0x154 (MemAlloc line 0xb6; freed FUN_005acaeb(inst,0x154)). Layout:
+0x00: base/header region (0x14 bytes; base CtlFrame state written by FUN_006123a0/vtable FUN_0062c370)
+0x08: uint orientation/mode (0 = vertical candidate stack, non-zero = horizontal row) [set by msg 0x56 from wparam[0]; read in paint FUN_0061e890 and measure FUN_0061ea10]
+0x0c: uint candidateCount (0..0x14; values >20 clamped to 20 in msg 0x56)
+0x10: uint highlightIndex (currently-selected candidate; painted with a highlight box)
+0x14 .. +0x153: ImeReadingProp entries[20], each 16 bytes = TArray<wchar_t,TArrayCopyBits<wchar_t>>:
    +0x00: wchar_t* data buffer (0 until allocated; empty 1-wchar string after create)
    +0x04: reserved/allocator field (0)
    +0x08: uint element count (length incl. null terminator)
    +0x0c: uint chunk/reserve capacity (init 0x80)
- **Messages:** FrameProc FUN_0061e470(FrameMsgHdr* p1, void* wparam=p2, void* out=p3); dispatch switch(p1[1]=msg). p1[0]=frame id, p1[2]=&instancePtr slot. Unhandled/fallthrough -> thunk_FUN_00647170 = FrameMsgCallBase.
- case 1 PAINT: sub-pass = *p2. p2==0 -> color 0x80000000 (semi-transparent backdrop); p2==1 -> color 0xc8c83232; else skip. If a color chosen, builds a quad via FUN_00679a60(&col,0x20003e0,0) then FrameContentAddImage FUN_0062b2d0(frameId, p2+2 rect, material, scale(1.0,1.0), pos, p2[6],p2[7]); frees material FUN_0046f850; then calls base. Draws the reading-window background only.
- case 4 INSTALL: *(code**)p2[3] = FUN_006123a0 (base CtlFrame proc, installs vtable FUN_0062c370), then base.
- case 8 RENDER CONTENT (OnRenderControl): FUN_0061e890(frameId, instance, p2) draws each candidate string. GATED: only runs if (*(byte*)p2 & 0x40)!=0. Branch on instance+8: ==0 vertical stack (y advances by text height, per-item FrameMsgSendAddText id 0x57 + highlight box FUN_0062b590 when item index==instance+0x10), !=0 horizontal (x advances). Then base.
- case 9 CREATE: instance = MemAlloc(0x154,2,file,0xb6). Zero-inits ImeReadingProp[20] at +0x14 (each {ptr=0,+4=0,count=0,cap=0x80}); second loop AdjustSizeChunked each TArray to a 1-wchar empty null-terminated string (count=1). Stores instance at *p1[2]. Falls through to base.
- case 0xb DESTROY: instance = *p1[2]; if non-null, for each of 20 ImeReadingProp: if data ptr!=0 free it (FUN_0047f3a0), null the fields (~ImeReadingProp); then MemFree FUN_005acaeb(instance,0x154). Falls to base.
- case 0x15 GET DEFAULT SIZE: if out(p3)==NULL -> assert 0xc7(199). Writes 4 dwords: out[0]=_DAT_009407b8, out[1]=_DAT_00943278, out[2]=_DAT_009407b8, out[3]=_DAT_00943278 (default extents).
- case 0x38 GET CONTENT/PREFERRED SIZE: FUN_0061ea10(frameId, instance, p2) measures via FrameGetDefaultTextHeight + FrameTextGetExtents over all candidates (branch on instance+8 for vertical vs horizontal accumulation), writes computed {w,h} to *(float**)(p2+8).
- case 0x39 RELAYOUT: FUN_0062bd40(frameId); FUN_0062f110(frameId) (FrameContentInvalidate + FrameNativeSizeChanged); falls to base.
- case 0x56 SET READING LIST (control-specific setter): iVar=instance; instance+8 = p2[0] (orientation/mode); count=p2[1] clamped to 0x14; instance+0xc=count; instance+0x10=p2[2] (highlight index); packed source base = p2[4]. For each candidate: len=wcslen(src)+1 (FUN_0046c270), AdjustSizeChunked(FUN_00467680), memcpy len*2 bytes into TArray buffer (FUN_0046da80) with overlap guard -> assert 0x171 if src overlaps dest; TArray.count(+8)=len; advance src by (wcslen*2+2). Then FrameContentInvalidate+FrameNativeSizeChanged. This is the primary way to feed IME candidate strings.
- case 0x57 ADD TEXT MSG: FrameContentAddTextMsg FUN_0062bc20(frameId, p2); then base. (content text passthrough)
- default: FrameMsgCallBase.
- **Create recipe:** Internal IME candidate/reading window (created by the IME/keyboard subsystem, IFrame::CKey::OnImeReading, not normally by user UI code). To instantiate manually:
1) Create child frame: FUN_0062bfc0(parent, flags, childId, proc, userdata, 0) -> frame+0xbc = id. proc = 0x0061e470 (bare CtlImeReading) OR 0x00889560 (styled UiCtlImeReadingProc, whose msg4 chains base 0x0061e470 and msg9 layers subclass FUN_0062f150(FUN_00879090,4)). Prefer the styled wrapper for the skinned look.
2) Order is proc-driven: on create the frame auto-receives msg 4 (INSTALL -> base vtable) then msg 9 (CREATE -> allocs 0x154 instance, pre-inits 20 empty TArray<wchar_t> slots). No image-list/material warm-up needed for text; background quad uses an inline-built material (FUN_00679a60) so no external imglist.
3) Populate: dispatch FUN_0062ef40(id, 0x56, &params, 0) with params = { [0]=orientation (0 vertical / 1 horizontal), [1]=count(<=20), [2]=highlightIndex, [3]=unused, [4]=wchar_t* to CONSECUTIVE null-terminated candidate strings }. Each string is copied into its ImeReadingProp TArray.
4) Size: query defaults with msg 0x15 (needs 4-dword out) or preferred content size via msg 0x38 (measures text). Position/size via anchor-6 setter FUN_0062F770.
5) Repaint is automatic: msg 0x56/0x39 issue FrameContentInvalidate(FUN_0062bd40)+FrameNativeSizeChanged(FUN_0062f110). Content is only drawn during msg 8 when render flag bit 0x40 is set on the render-params.
Destroy via native destroyer FUN_0062c550(id) (sends msg 0xb -> frees TArrays + instance).
- **Gotchas:** 1) msg 0x15 (GET DEFAULT SIZE): out pointer p3==NULL -> ErrorAssertion 0xc7 (199). Always pass a 4-dword out buffer.
2) msg 0x56 (SET LIST): memmove overlap guard -> ErrorAssertion 0x171 if the packed source-string region overlaps the destination TArray buffer. Supply candidate strings in a separate/independent buffer.
3) msg 0x56 silently CLAMPS count to 0x14 (20); passing >20 candidates truncates rather than erroring; also reads exactly `count` consecutive null-terminated wide strings from params[4] with NO bounds/NULL check on the source pointer -> bad params[4] or wrong count walks off into memory (garbage/crash), and params[1]==0 is allowed (empty list).
4) RENDER GATE: msg 8 draws candidates only if (render-params byte & 0x40)!=0; otherwise no text is shown (silent no-op, not a crash) -- a common 'nothing renders' pitfall.
5) msg 1 PAINT only emits a background quad for sub-pass 0 or 1; other sub-passes skip (silent).
6) Instance is fetched as *p1[2] in msgs 8/0x38/0xb/0x56 with no re-validation; sending these before msg 9 (create) dereferences an uninitialized/NULL instance slot -> crash. Respect proc-driven ordering (create primitive sends 4 then 9 first).
7) msg 9 does NOT assert-if-already-set (unlike other controls); re-sending 9 overwrites the instance pointer and leaks the previous 0x154 instance + its 20 TArray buffers.
8) Destroy path frees each TArray only when its data ptr!=0; fields are nulled by ~ImeReadingProp -- do not double-free by manually freeing entry buffers before msg 0xb.

### UiCtlBtnProc (styled 9-slice button, s_btnCheckImageList owner)  (EXE 0x00877e60, confidence: high)

- **WASM:** ram:80df1d1e
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlBtn.cpp (assert index 0x45 in msg 5 = "!s_btnCheckImageList"). NOTE the prompt's "Engine\Controls" prefix is wrong for this control; verified string at 0x00b95c0c is "Gw\Ui\Controls". Image-list creation asserts land in P:\Code\Engine\Frame\FrApi.cpp (FUN_0062d790).
- **Struct:** TWO structures.

(A) Dispatch/message packet = param_1 (undefined4*), the standard control MsgProc header:
  +0x00 [0] frame handle/id (passed to all Fr* helpers; asserts if 0)
  +0x04 [1] msg id (the switch selector)
  +0x08 [2] pointer-to-instance-holder; base reads instance = *(param_1[2])
  +0x10 [4] control style/variant flag byte. Tested bits: 0x1 = "expand/toggle" face variant (selects the PTR_DAT_00bf457c.. table branch in paint & the alt size in msg 0x15); 0x2 and 0x4 = theme-color select in msg 0x38 (0x2 -> DAT_009411d0, 0x4 -> DAT_0094519c).
  param_2 = sub-message/paint context; param_3 = out buffer.

(B) Per-instance data struct, allocated on OnFrameCreate (msg 9 -> FUN_006102b0), freed on destroy (msg 0xb) as a 0x2C-byte (44) block via FUN_005acaeb(inst,0x2c). Pointed to by *(param_1[2]):
  +0x00 state flags: bit0(0x1)=checked/"on"; bit1(0x2)=secondary toggle (msgs 0x3b,0x5d); bit2(0x4)=pressed/down (msgs 0x24,0x2c,0x2e). Getter 0x58 returns (flags&1); getter 0x59 returns ((flags>>2)&1).
  +0x04 caption text buffer ptr (freed on destroy; FUN_0047f3a0)
  +0x08 caption buffer capacity
  +0x0C caption length (grown by append msg 0x3a)
  +0x14 caret/selection index; 0xFFFFFFFF sentinel (msg 0x5c,0x4c)
  +0x18 image/texture handle (freed on destroy via FUN_0046f850; set by msg 0x5b)
  +0x1C callback/notify-target context ptr (set by msg 0x5a)
  +0x20 [inst[8]] tooltip/hyperlink object ptr (msgs 0x3b,0x5d)
  +0x24 width  (float, size hint; msg 0x13)
  +0x28 height (float, size hint; msg 0x13)

Style word lives in FRAME data (not this struct) at frameData+0x190 (offset 400); read by FUN_0062fe20(frame,mask)=frameData[0x190]&mask. Paint/size gate mask = 0x40000; checkbox-face mask = 0x8000; combined 0x804000; edit-box toggle 0x20000 (base).
- **Messages:** Dispatcher: FUN_0062ef40(frame,msg,wparam,&out). Styled proc switch on param_1[1]; anything not listed forwards to base flat CtlBtn FUN_0060f4f0 via thunk_FUN_00647170, which itself forwards unknowns to CFrame FUN_006123a0.

HANDLED DIRECTLY by styled UiCtlBtnProc (0x00877e60):
- 0x01 PAINT. Sub-pass = *param_2. 
    subpass 0 (face): only paints if style&0x40000 (PAINT GATE). Selects a 9-slice texture ptr from tables PTR_DAT_00bf4560..00bf4584 based on: instance style-byte bit0 (offset+0x10), enabled=FUN_0062e2a0, checked=0x58/pressed=0x59, style&0x804000, checkbox-face style&0x8000. Draws via FUN_0062b8e0(frame,rect,tex,&DAT_00bf4510,7,0,color=piVar3[6],alpha=piVar3[7]). If focused (FUN_0062e320) overlays a 0x20-inset highlight via FUN_0062b3e0(...,PTR_DAT_00bf455c,...,0x100000,...).
    subpass 1 (glyph): draws the shared check image-list DAT_010819cc via FUN_0062b290(frame,rect,DAT_010819cc,cellIndex,color,alpha); cellIndex chosen 0..5 from enabled/checked/pressed. USES DAT_010819cc UNCONDITIONALLY.
    other subpass: forward to base.
- 0x04 INSTALL BASE VTABLE: *(param_2[3]) = FUN_0060f4f0 (flat CtlBtn is the base class).
- 0x05 CLASS INIT (create shared check image list): asserts (UiCtlBtn.cpp idx0x45) if DAT_010819cc!=0; else DAT_010819cc = FUN_0062d790(0x11,7,0x12,{w=0x15,h=0x15},{0x80,0x20},PTR_DAT_00bf4558,6)  (11x12 cells... 0x15 sheet). Class-scope, one-time.
- 0x06 CLASS SHUTDOWN: FUN_0046f9b0(DAT_010819cc); DAT_010819cc=0.
- 0x15 SIZE QUERY: gated on style&0x40000; writes param_3[0..3] from DAT_00bf4518.. (normal) or DAT_00bf4528.. (bit0-variant); if checked/pressed appends via FUN_00876690 from DAT_00bf4538/DAT_00bf4548.
- 0x38 THEME/COLOR APPLY: calls base, then if style-byte bit1/bit2 scales float at *piVar3[2] by theme color DAT_009411d0 / DAT_0094519c (FUN_004f0cb0).
- 0x5F DRAW CAPTION TEXT: color 0xFFA0A0A0 when disabled or param_2[8]&1, else forces enabled tint; renders via FUN_0062bb30(frame,x,y,rect,font,-1,flags|0x40,color,...,6).
- 0x60 GET METRICS: copies 9 dwords from DAT_00bf44ec into param_3 (default padding/margin block).

INHERITED from base CtlBtn 0x0060f4f0 (reached via forward):
  0x04 base=CFrame FUN_006123a0; 0x08 pre-create; 0x09 OnFrameCreate=alloc 0x2C instance (FUN_006102b0, asserts if already set); 0x0B destroy (free img +0x18, free text +0x4, zero, free 0x2C); 0x0C/0x21/0x25/0x36 invalidate; 0x13 size-hint from +0x24/+0x28; 0x15 default color size; 0x20 activate/click (FUN_0060f2a0); 0x24 mouse-down: if enabled toggle pressed bit2 + invalidate; 0x2C drag/hover pressed tracking; 0x2E mouse-up: clear bit2, fire click; 0x38 FUN_00610580; 0x39 focus-in; 0x3A caption append/insert; 0x3B toggle bit1; 0x4C measure/layout text; 0x56 set default action; 0x57 toggle flags bit0; 0x58 GET checked=(flags&1); 0x59 GET pressed=((flags>>2)&1); 0x5A set notify-context ptr(+0x1C); 0x5B set image handle(+0x18); 0x5C set text(replace, caret=-1); 0x5D set tooltip/hyperlink(+0x20); 0x5E SET CAPTION (FUN_00610420); 0x5F base caption draw.
- **Create recipe:** 1. ONE-TIME CLASS WARM-UP (per process, before any styled button paints): send msg 0x05 to the class/an instance so DAT_010819cc (s_btnCheckImageList) is created. In practice the UI framework does this at control-class registration; if you create instances manually you MUST ensure msg 5 ran once, otherwise subpass-1 glyph paint feeds a null image list to FUN_0062b290. Re-sending 0x05 while non-null asserts (idx 0x45) — send exactly once.
2. CREATE the frame with the create primitive: FUN_0062bfc0(parent, flags, child, proc=0x00877e60, userdata, 0) -> returns/stores frame id at frame+0xBC. OnFrameCreate (msg 9) then allocates the 0x2C instance. (You may instead FrameNewSubclass 0x0062f150 to layer this proc over an existing flat button.)
3. SET STYLE WORD (frameData+0x190) to include 0x40000 (mandatory paint+size gate) plus optional: 0x8000 = checkbox face, 0x804000 = alt/toggle face, 0x20000 = edit-toggle behavior. Without 0x40000 the face never paints and 0x15 size query returns nothing.
4. SET the instance dispatch style-byte at packet offset +0x10: bit0 to pick the expand/toggle texture+size variant; bits 0x2/0x4 for themed color scaling.
5. POSITION/SIZE via the anchor-6 setter FUN_0062F770(frame,...), or rely on msg 0x15 preferred size (needs 0x40000).
6. CONTENT: caption via msg 0x5E; icon via msg 0x5B; tooltip via 0x5D; notify target via 0x5A.
7. STATE: checked via toggling flags bit0 (msg 0x57)/query 0x58; pressed is driven by mouse msgs 0x24/0x2E, query 0x59.
Ordering: warm-up(5) -> create(9 auto) -> style 0x40000 -> flags -> caption/image -> position. Sizing: image-list cells are 0x11x0x12; face size comes from DAT tables gated by 0x40000.
- **Gotchas:** - NULL IMAGE LIST: paint subpass 1 uses DAT_010819cc with no null-check; if msg 0x05 never ran, FUN_0062b290 receives a null s_btnCheckImageList -> bad draw/crash. Warm up first.
- DOUBLE-INIT ASSERT: sending msg 0x05 when DAT_010819cc!=0 -> FUN_00487a80(0x45) no-return assert (UiCtlBtn.cpp). Init exactly once; tear down with 0x06 before re-init.
- PAINT/SIZE GATE: without style&0x40000 the face-paint (subpass0) and size-query (0x15) silently do nothing (invisible / zero-size button). Not a crash but the #1 "nothing renders" trap.
- NULL FRAME ID: every helper (FUN_0062fe20 idx0x732, FUN_0062e2a0 idx0x6bc, FUN_0062e320 idx0x6b6) asserts-and-aborts if the frame handle (param_1[0]) is 0. Never dispatch with a dead/zero frame id.
- NULL OUT-PTR on getters: base 0x58 asserts if param_3==0 (idx0x152), 0x59 asserts if param_3==0 (idx0x15c), 0x5C asserts if source ptr==0 (idx0x196). Always pass a valid out buffer for state/text messages.
- IMAGE-LIST CREATE ASSERTS (FrApi.cpp FUN_0062d790): cell count/dims must be non-zero and sheet>=cell (idx 0xa47-0xa4b) — do not pass zeroed metrics if you replicate msg 5.
- TEXT BUFFER OVERLAP: caption insert/replace (0x3a/0x5c) assert (idx0x171) if the source string aliases the destination buffer region — don't set caption from a pointer into the control's own +0x04 buffer.
- LIFETIME: destroy (0xb) frees +0x18 image and +0x4 text then frees the 0x2C struct; issuing further get/set after destroy dereferences freed memory. The image list DAT_010819cc is class-global — do NOT free it (msg 6) while any styled button instance still lives.

### UiCtlBtnGlassProc (CGlassBtn::FrameProc)  (EXE 0x008869d0 (FrameProc body); registered proc pointer = thunk_FUN_008869d0 at 0x00886be0 (this thunk is what is stored as the frame's proc), confidence: high)

- **WASM:** ram:80e0b7ed UiCtlBtnGlassProc (wrapper) -> ram:80e0b31d CGlassBtn::FrameProc -> ram:80e0ae45 CGlassBtn::OnFrameArtAddModel
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlBtn.cpp (string at EXE 0x00b95c0c). Note: the EXE glass body FUN_008869d0 itself contains NO assert referencing this file - the assertion string is referenced only by the sibling styled UiCtlBtnProc FUN_00877e60 (same translation unit). Mapping was confirmed by data fingerprint, not the assertion.
- **Struct:** Stateless art/style subclass layer - it allocates NO per-instance struct and defines no case 9/0xb. It only reads the FrameMsgHdr (param_1[0]=frame id, param_1[1]=msg; param_1[2]=instance ptr owned by the base UiCtlBtnProc). All mutable state is queried from the base button instance via dispatch messages: IsPushed=msg 0x58 (FUN_0060f4b0), IsChecked=msg 0x59 (FUN_0060f4d0). Style/geometry are global read-only tables: DAT_00bf46b4 (size rect 10,10,10,10), _DAT_00bf46c4.. (checked grow offsets +2/-2/-2/+2), DAT_00bf46d4 (glass margins struct 32,32,8,0...). Art model handles are process-global: DAT_0094a09c=0x01021127 (normal face), DAT_0094a094=0x01021129 (checked face), DAT_00944ef8=0x01026bf5 (pushed overlay template).
- **Messages:** Dispatch on param_1[1]=msg. param_1[0]=frame id, param_2=in/sub-pass struct, param_3=out. Unhandled -> thunk_FUN_00647170 (calls installed base proc).
- case 1 PAINT (branches on *param_2 = paint sub-pass):
  * sub-pass 0 (base face): iVar=IsChecked (FUN_0060f4d0 = dispatch msg 0x59). If checked -> model handle DAT_0094a094 (=0x01021129). Else if FUN_0062e320(frame)!=0 (enabled/art-ready gate) -> model DAT_0094a09c (=0x01021127). Else RETURN drawing nothing (PAINT GATE). Adds image via FUN_0062b8e0(frame, rect=param_2+2, model, &size{0x20,0x20}, layer=7,0,0,0).
  * sub-pass 1 (pushed overlay): iVar=IsPushed (FUN_0060f4b0 = dispatch msg 0x58). If pushed -> FUN_0062b3e0(frame, param_2+2, model DAT_00944ef8(=0x01026bf5), outer{0x40,0x40}, mid{0x20,0}, inner{0x20,0x20}, 7,0,4,0). Else break -> return.
  * any other sub-pass -> thunk_FUN_00647170 (base paint).
- case 4 INSTALL BASE: *(code**)param_2[3] = FUN_00877e60 (base = styled UiCtlBtnProc); falls through to default -> base. So CGlassBtn is a SUBCLASS layered on UiCtlBtnProc, which itself chains to flat CtlBtnProc 0x0060f4f0.
- case 0x15 SIZE-QUERY: writes default rect {10,10,10,10} from DAT_00bf46b4. If IsChecked (0060f4d0) -> grow by {+2.0,-2.0,-2.0,+2.0} from _DAT_00bf46c4.. then return.
- case 0x60 GLASS-STYLE/MARGINS GET: copies 9 floats from DAT_00bf46d4 = {32.0,32.0,8.0,0,0,0,0,0,0} into out param_3 (caller MUST supply 36-byte buffer).
- default: thunk_FUN_00647170 -> base proc (styled UiCtlBtnProc -> flat CtlBtnProc). No case 9/0xb/0x38 of its own; instance alloc + state (pushed/checked/focus) all live in the base button instance.
Note IME candidate next/prev buttons subclass THIS proc again (FUN_00889260 / FUN_00889330 via thunk_FUN_008869d0), overriding msg 9 (set texture DAT_00a4f464) and msg 0x15 (own sizes DAT_00bf4704).
- **Create recipe:** 1) Create the frame with the primitive FUN_0062bfc0(parent, flags, child, PROC, userdata, 0) where PROC = the glass thunk at 0x00886be0 (thunk_FUN_008869d0). The registered proc must be the thunk, not the raw 0x008869d0 body.
2) Let the standard control lifecycle run: msg 4 (INSTALL BASE) fires and sets the base proc to styled UiCtlBtnProc FUN_00877e60; that base in turn chains to flat CtlBtnProc 0x0060f4f0 and owns the actual TCtlInstance (msg 9 alloc / msg 0xb destroy). Do NOT register this proc standalone - it has no case 9 and will have a null base if the install/create sequence is skipped.
3) Warm-ups required BEFORE first paint:
   - The base styled UiCtlBtnProc's shared image list DAT_010819cc must be built (base handles that on its msg 5 OnInit).
   - The three global glass art model handles must be registered by the UI art system: 0x01021127 (normal), 0x01021129 (checked), 0x01026bf5 (pushed overlay). These are shared globals; this proc does no lazy-init of them.
4) Sizing: query via msg 0x15 -> default 10x10 rect ({10,10,10,10}); grows 2px on each edge when checked. Glass content margins (msg 0x60) = 32/32 corner, 8 border. Face art is drawn at 32x32 (0x20), pushed overlay at 64x64 (0x40) template with 32px inner.
5) To make a labeled/IME-style variant, subclass again over the glass thunk (see FUN_00889260) using FrameNewSubclass 0x0062f150 and override msg 9/0x15 as needed.
- **Gotchas:** - PAINT GATE: case 1 sub-pass 0 returns WITHOUT drawing when the button is not checked AND FUN_0062e320(frame)==0 (art/enable gate). If you expect a visible face but the base art gate is false, nothing renders - not a crash but the usual "invisible control" trap.
- NULL BASE: default/unhandled messages forward through thunk_FUN_00647170 to the base proc installed at case 4 (FUN_00877e60). If the proc is registered without the frame-create/install path running, the base slot is null and the first unhandled message dereferences a null proc -> crash. Always create through FUN_0062bfc0 so msg 4 installs the base.
- MISSING ART MODELS: FUN_0062b8e0/FUN_0062b3e0 are called with global model handles 0x01021127/0x01021129/0x01026bf5. If the art system has not registered these (e.g. proc used outside its intended IME/glass context), the image add operates on an invalid model handle.
- msg 0x60 writes 9 dwords (36 bytes) to param_3; a short output buffer overflows.
- No own instance struct: sending msg 9/0xb/0x38 to this layer expecting per-instance behavior is wrong - those are serviced by the base UiCtlBtnProc; poking param_1[2] here assumes the base already allocated the instance.

### IUi::UiCtlBtnExpandProc  (EXE 0x008867f0, confidence: high)

- **WASM:** ram:80e7b6f7 (IUi::UiCtlBtnExpandProc(FrameMsgHdr const&, void const*, void*))
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlBtnExpand.cpp  (file-name string @0x00b96b68; asserts: FUN_00487a80(0x54) on double class-register, 0x75 on deregister-when-null. NOTE: path is "...\Gw\Ui\Controls\", NOT the "...\Engine\Controls\" default.)
- **Struct:** This is a stateless DERIVED subclass proc; it allocates NO per-instance struct of its own (no case 9/OnFrameCreate, no case 0xb/destroy — those forward to the base). All per-button state lives in the base button frame instance (created by the base chain at frame+0xbc) and is queried via helpers: FUN_0060f4b0(id)=pressed/down, FUN_0060f4d0(id)=hover/highlight, FUN_0062e320(id)=toggled/expanded state, FUN_0062e2a0(id)=enabled. The ONLY class-level state is one shared static image list: DAT_01081d70 (the expand/collapse arrow sprite sheet, 4 frames). This is distinct from the base styled-button's own checkbox-face list DAT_010819cc.
Message-arg shapes:
- FrameMsgHdr *param_1: [0]=frameId(uint), [1]=msgId(uint).
- Paint (msg1) param_2: [0]=subPass(int); [2..5]=dest rect (4 floats, passed as param_2+2); [6]=color/modulate (0x18). Only subPass 0 is honored.
- Install (msg4) param_2: [1]=ptr to frame style/flags field; [3]=ptr to base-proc vtable slot.
- SizeQuery (msg0x15) param_3(out): 4 dwords (preferred rect) all written 0.
Dispatch guard: EAX=msg-1; CMP 0x14; JA -> default. Valid handled range msg 1..0x15; byte index table @0x8869b0, target table @0x886998.
- **Messages:** Handles only 5 messages; everything else forwards to the base chain via FUN_0062ee70 (=thunk_FUN_00647170).
- msg 1 PAINT: if subPass(*param_2)==0, compute frame index cVar3 = (FUN_0062e320(id)!=0 ? 1:0) + (FUN_0060f4b0(id)!=0 ? 2:0)  => 0=collapsed/normal,1=expanded/normal,2=collapsed/pressed,3=expanded/pressed; then FUN_0062b290(id, rect=param_2+2, DAT_01081d70, cVar3, color=param_2[6], 0) draws the arrow glyph from the shared image list. On any other subPass it returns WITHOUT forwarding, so the base button face/checkbox is NEVER painted (arrow-only control, by design).
- msg 4 INSTALL: *(code**)param_2[3] = FUN_00877e60 (installs styled-button base proc); *(uint*)param_2[1] |= 0x30000 (forces style bits 0x10000|0x20000). Establishes inheritance UiCtlBtnExpand : UiCtlBtn(0x877e60) : CtlBtn(0x0060f4f0).
- msg 5 CLASS-REGISTER (load shared resource): asserts if DAT_01081d70!=0; queries UI option FUN_0049b9e0(0x71): if 0 -> imglist cell 0x20/0x10 with texture ptr @0x00b96b9c(=0x0105f3c3); if !=0 -> cell 0x1c/0x40 with texture ptr @0x00b96b94(=0x0105f381). DAT_01081d70 = FUN_0062d790(0x11,7,0x1a, sizeA, sizeB, texturePtr, 4=frameCount).
- msg 6 CLASS-DEREGISTER (free shared resource): asserts if DAT_01081d70==0; FUN_0046f850(DAT_01081d70); DAT_01081d70=0.
- msg 0x15 SIZE-QUERY: writes param_3[0..3]=0 (zero preferred size; final size comes from image/layout).
- All other msgs (2,3,7..0x14, and get/set label/color/callback in the 0x56-0x6a band) -> default forward to base. IMPORTANT CORRECTION: this proc does NOT implement any 0x57/0x58 protocol (the prior catalog note was wrong); to set label/callback/colors you send the standard button messages, which pass through to UiCtlBtnProc(0x877e60)/CtlBtnProc(0x0060f4f0).
- **Create recipe:** 1. One-time per class: send msg 5 (CLASS-REGISTER) so DAT_01081d70 (arrow image list) is built BEFORE any instance paints. Also ensure the base styled-button class list DAT_010819cc is registered (base msg 5) since base messages may reference it. Never register twice (asserts).
2. Create the frame with the standard primitive FUN_0062bfc0(parent, flags, child, proc=0x008867f0, userdata, 0). The returned frame id is stored at frame+0xbc.
3. The control self-installs on msg 4: base proc becomes 0x00877e60 and style gets |= 0x30000. No manual base wiring needed.
4. Position/size: this control returns zero from size-query, so give it an explicit rect via the anchor-6 pos/size setter FUN_0062F770 (or your layout). Natural glyph size is the image-list cell (0x20 or 0x1c px depending on UI option 0x71).
5. Toggle state: expanded/collapsed is the base button "checked/toggled" bit read by FUN_0062e320 — set it through the standard button toggle/check message (forwarded to base), not through this proc.
6. Label/click callback/colors: set via the standard button get/set messages; they forward to the base chain.
7. Teardown: destroy the frame via the native destroyer FUN_0062c550(id); at class shutdown send msg 6 exactly once to free DAT_01081d70.
Order summary: class-register(msg5) -> create frame(FUN_0062bfc0 w/ proc 0x8867f0) -> size via 0x62F770 -> set toggle/label through forwarded button msgs -> ... -> destroy(0x62c550) -> class-deregister(msg6).
- **Gotchas:** 1. NULL image list on paint: msg 1 passes DAT_01081d70 to FUN_0062b290 with NO null guard. If the class was never registered (msg 5) before first paint, DAT_01081d70==0 and the draw reads a null image list -> crash/garbage. Always class-register first.
2. Double class-register: msg 5 calls FUN_00487a80(0x54) (assert/abort) if DAT_01081d70!=0. Registering twice terminates.
3. Deregister-when-null: msg 6 calls FUN_00487a80(0x75) if DAT_01081d70==0. Sending msg 6 without a prior register, or twice, terminates.
4. Paint never forwards: on subPass!=0 (and even subPass 0) it returns without calling the base paint, so no button face/border/checkbox is ever drawn — expect an arrow glyph ONLY. Do not rely on base face rendering.
5. No get/set here: sending a 0x57/0x58 (or any 0x56-0x6a) expecting a UiCtlBtnExpand-specific handler is a no-op override; it silently forwards. There is no expand-specific get/set protocol despite the earlier note.
6. Frame index bound: cVar3 is 0..3 and the image list is created with exactly 4 frames — safe as long as the arrow texture (0x0105f3c3 / 0x0105f381) really has 4 cells; a mismatched/short atlas would read an out-of-range cell.
7. UI-option dependency: which texture/size variant is used is chosen at register time by FUN_0049b9e0(0x71); if that option flips after registration, the already-built list is stale (must deregister+register to change).

### UiCtlBtnToggle  (EXE 0x00886370 (FrameProc for the toggle button child frame). WASM: IUi::UiCtlBtnToggleProc(FrameMsgHdr const&,void const*,void*) @ ram:816b67fd. Assertion file "P:\Code\Gw\Ui\Controls\UiCtlBtnToggle.cpp" @ EXE 0x00b96a2c (referenced from case 9 at 0x008863e3). The host/wrapper control that instantiates it is FUN_0056b810 (its CtlInstance-based container, own instance 0x20 bytes, "P:\Code\Engine\Controls\CtlInstance.h")., confidence: high)

- **WASM:** ram:816b67fd
- **Struct:** Per-instance struct = 0x18 bytes (6 dwords), pointer stored at *(p1[2]):
+0x00 HFrameImageList/HGrModel handle A (dup of desc0[0]); primary/left face imagelist. Closed on destroy.
+0x04 int imageIndex A0 (desc0[1]) — single-mode UNCHECKED / two-mode-left CHECKED.
+0x08 int imageIndex A1 (desc0[2]) — single-mode CHECKED / two-mode-left UNCHECKED.
+0x0C HFrameImageList handle B (dup of desc1[0]); right face imagelist for two-image mode. Closed on destroy. May be 0.
+0x10 int imageIndex B0 (desc1[1]) — two-mode-right UNCHECKED.
+0x14 int imageIndex B1 (desc1[2]) — two-mode-right CHECKED.
Creation userdata (delivered as p2 in msg 9) = pointer to a 2-entry array of descriptor pointers {desc0*, desc1*}; each descriptor = {handleSource(dword), idx0(int), idx1(int)} (0xC bytes). desc1* may be null.
Host wrapper FUN_0056b810 instance = 0x20 bytes, vtable PTR_FUN_009404a4; holds child frameId at +0x04; shares a global image descriptor DAT_00c01b8c (built once in its case 5 via FUN_0062d790(2,7,0x12,...,&DAT_009503b0,2), freed in case 6).
- **Messages:** Proc signature FUN_00886370(FrameMsgHdr* p1, void* p2/in, void* p3/out): p1[0]=frameId, p1[1]=msg, p1[2]=&instancePtr slot. switch(p1[1]):
- case 1 PAINT: piVar2=*(p1[2]) (the 0x18 instance). Gates: if p2[0](float)==0 -> return (no paint). Image path requires p2[0]==1 AND p2[6]==4 (int compares), then style=FrameTestStyles(frame,0x1000000) via FUN_0062fe20, and (*inst!=0) AND (inst[3]!=0 OR style!=0). checked=CtlBtnIsChecked(frame) via FUN_0060f4b0. If style bit 0x1000000 SET (single-image mode): FrameContentAddImage(frame, p2+2 /*Rect4f*/, imglist=inst[0], index = checked?inst[2]:inst[1], layer=5, model=p2[7]) via FUN_0062b290. If style CLEAR (two-image split): draws left half {imglist=inst[0], idx=checked?inst[1]:inst[2]} over rect (width*0.5), then right half {imglist=inst[3], idx=checked?inst[5]:inst[4]} at offset; both layer 5, model 0.
- case 4 INSTALL/vtable: p2[1] style |= 0x10000 then &= 0xFFFBFFFF (set 0x10000, clear 0x40000 paint gate); *p2[3]=base proc FUN_0060f4f0 (flat CtlBtnProc); *p2[4]=0; *p2[5]=0. (Toggle layers on the flat CtlBtn base so CtlBtnIsChecked works.)
- case 9 ONFRAMECREATE: inst=MemAlloc(0x18) via FUN_0047f340(assert,0x57); *(p1[2])=inst. Reads descriptor: d=*p2; if d: desc0=d[0] -> inst[0]=HandleDuplicate(desc0[0]) (FUN_0046fda0, 0 if desc0[0]==0), inst[1]=desc0[1], inst[2]=desc0[2]; desc1=d[1] -> inst[3]=dup(desc1[0]), inst[4]=desc1[1], inst[5]=desc1[2]. (Second descriptor optional/null.)
- case 0xB DESTROY: inst=*(p1[2]); if inst: HandleCloseSafe(inst[0]) & HandleCloseSafe(inst[3]) (FUN_0046f9b0, null-tolerant); operator delete(inst,0x18) FUN_005acaeb.
- case 0x38 MEASURE: th=FrameGetDefaultTextHeight(frame) FUN_0062d0e0; k=th*1.5 (_DAT_00948c18); out=(float*)p2[2]; out[0]=k+k (width=3*th), out[1]=k (height=1.5*th).
- case 0x60 DEFAULT-SIZE: th=FrameGetDefaultTextHeight; k=th*1.5; p3[8]=int 1, p3[1]=k+k, p3[0]=k, p3[2]=0.0.
- default: thunk_FUN_00647170 = FrameMsgCallBase(p1,p2,p3) forwards to base (CtlBtnProc).
- **Create recipe:** Concrete instantiation (verified in FUN_0056b810 case 9 @ 0x0056b984):
1. Warm-up: build/own the image descriptor the toggle will draw. Wrapper builds a shared list DAT_00c01b8c = FUN_0062d790(2,7,0x12,&sz,&sz2,&DAT_009503b0,2) once (128x64 atlas) and reuses it. The descriptor block you pass must be {handleSource, idxUnchecked, idxChecked}.
2. Build userdata on stack: local descA = {imageListHandle, 0, 1}; localArr = {&descA, &descB-or-0}; userdata = &localArrPtr (a pointer to the {desc0*,desc1*} array).
3. Create the child frame: FUN_0062bfc0(parentFrameId, flags=0x01000300, child=0, proc=FUN_00886370, userdata, 0). Flags 0x01000300 = 0x1000000 (single-image TOGGLE style, tested in paint) | 0x200 | 0x100. This -> child frame id at frame+0xBC. Sequence of engine msgs then fires automatically: msg4 install (sets base=CtlBtnProc 0x0060f4f0, style 0x10000, clears 0x40000), msg9 create (allocs 0x18 instance, dups handles).
4. Register control messages on the frame: FUN_0062ef00(frame,0x1000012a); FUN_0062ef00(frame,0x1000011a) (host click/state notifications).
5. Sizing: let the control self-size via msg 0x38/0x60 (width=3*textHeight, height=1.5*textHeight) or override with the anchor-6 pos/size setter 0x0062F770.
6. Check state is driven through the flat CtlBtn base (CtlBtnIsChecked 0x0060f4b0); paint auto-selects checked vs unchecked image index.
Order that matters: proc must be FUN_00886370 at create so msg4/msg9 install the CtlBtn base + allocate the 0x18 instance BEFORE any paint. Provide at least desc0; provide desc1 only if you clear the 0x1000000 style for a split two-image look.
- **Gotchas:** 1) Instance-null deref: PAINT (case 1) and DESTROY (case 0xB) dereference *(p1[2]) (the 0x18 instance). If msg 9 (OnFrameCreate) never ran, this reads a garbage/null instance pointer. Always create via the proc path so msg9 allocates first.
2) Paint gate: case 1 returns early unless p2[0](float)!=0; the image branch additionally requires p2[0]==1 AND p2[6]==4 (int). Wrong paint sub-pass -> silently no draw (falls to base). The install (case 4) clears style 0x40000 and sets 0x10000 — if a subclass re-sets 0x40000 the paint gate blocks drawing.
3) Empty-image guard: image draw is skipped when inst[0]==0 (imagelist A null) OR when in two-image mode both inst[3]==0 and style 0x1000000 clear. So clearing the toggle style WITHOUT supplying desc1 => nothing renders (not a crash, but a blank control).
4) Handle lifetime: inst[0] and inst[0xC] are HandleDuplicate copies closed on destroy via null-tolerant FUN_0046f9b0 — safe if 0, but passing an already-freed/invalid handle in the descriptor will assert inside FrameContentAddImage/HandleDuplicate.
5) Image index bounds: inst[1/2/4/5] are raw frame indices into the image list; an out-of-range index makes FrameContentAddImage (FUN_0062b290) assert ("P:\...UiCtlBtnToggle.cpp" line 0x57 region).
6) CtlBtn base required: checked/unchecked selection calls CtlBtnIsChecked (0x0060f4b0); if the base proc CtlBtnProc 0x0060f4f0 is not installed (msg4 skipped), check-state is undefined.
7) Model arg: single-image mode passes model=p2[7]; if the caller's paint arg struct doesn't populate [7], you pass a stray HGrModel to AddImage.

### UiCtlHideUiProc (styled page/tab wrapper over CtlPage) — EXE label was "UiCtlPageProc", verified name is UiCtlHideUiProc  (EXE 0x00885590, confidence: high)

- **WASM:** ram:80dfc871 (IUi::UiCtlHideUiProc) -> TCtlInstance<IUi::Controls::CCtlHideUi>::MsgProc ram:80dfc959. Base CtlPageProc = FUN_0061a950 (assertion "P:\\Code\\Engine\\Controls\\CtlPage.cpp"). Wrapper TU string "P:\\Code\\Gw\\Ui\\Controls\\UiCtlHideUi.cpp" @0x00b969cc, adjacent to this proc's styling template.
- **Struct:** CtlPage instance (allocated by base case 9 at *(hdr[2]); freed as 8 bytes) — the wrapper stores NO extra fields in the EXE build:
+0x00 int  hframe        (owning frame id; = *hdr at create)
+0x04 int  selectedIndex (0xffffffff/-1 = none until a tab is selected)
Total 8 bytes (free size arg = 8). The tab/child list is held on the frame object (queried via FUN_0062caa0 / FUN_0062cfc0), not in this struct. Styling template (7 dwords) is static data, not per-instance: PTR_FUN_00b96994 @0x00b96994 (styled) and DAT_00b969b0 @0x00b969b0 (zeros/plain); base default template DAT_00a50680.
- **Messages:** FrameProc signature FUN_00885590(FrameMsgHdr* hdr, void* wparam, void* out); msg = hdr[1] (=*(hdr+4)). Falls through to thunk_FUN_00647170 (base-proc chain walker) which routes unhandled msgs to the installed base CtlPageProc FUN_0061a950.

WRAPPER-HANDLED (FUN_00885590):
- case 4 (INSTALL BASE/vtable): **(void***)(wparam+0xc) = FUN_0061a950 (CtlPageProc). Sets this class's base proc to CtlPage; CtlPage's own case 4 then sets ITS base = FUN_006123a0 (frame base). Chain: UiCtlHideUi -> CtlPage -> FrameBase.
- case 0x15 (size/inset query): zeroes out[0..3] (4 dwords) -> styled page reports zero container border/insets. Returns immediately.
- case 0x5e (GET TAB STYLING TEMPLATE): copies 7 dwords to out. wparam==0 -> PTR_FUN_00b96994 = {0x008854f0 (tab-face subclass proc), 0x00885340 (tab-button subclass proc), 8.0f, 0.0f, -2.0f, 26.0f, 0}. wparam!=0 -> DAT_00b969b0 = all zeros (plain/unstyled tabs). Returns immediately.
- default -> thunk_FUN_00647170 -> CtlPageProc.

INHERITED FROM CtlPageProc FUN_0061a950 (reached via fallthrough; full page protocol):
- case 4: base = FUN_006123a0 (frame base).
- case 9 OnFrameCreate: assert instance-slot *(hdr[2]) == 0 else err0x256; alloc 8B via FUN_0047f340(CtlPage.cpp,599); inst[0]=hframe(=*hdr), inst[1]=0xffffffff (selectedIndex=-1); store; then base create.
- case 0xb OnFrameDestroy: assert inst!=0 else err0x25b; FUN_005acaeb(inst,8) free; slot=0.
- case 0x31: tab-select/notify routing (idx>=0 -> FUN_0062ee80 select child; idx<0 & type==7 -> select by ~idx).
- case 0x37: FUN_0061af80 = LAYOUT TABS; fetches 0x5e template via FUN_0062ef40(hframe,0x5e,sel,buf), enumerates children (FUN_0062caa0), positions each via FUN_0062f770; honors frame flag 0x40000 (tab wrap/orientation) via FUN_0062fe20(frame,0x40000). Uses template floats: local_58=x-start(8.0), local_54=gap(0.0), local_4c=row height(26.0), local_50=-2.0 pad.
- case 0x38: FUN_0061b2d0 (second layout/measure pass).
- case 0x56: FUN_0061ad40 -> get current tab (writes out).
- case 0x57: FUN_0061af20(...,0) select previous tab. case 0x58: FUN_0061af20(...,1) select next.
- case 0x59: get count/current -> *out = *(inst+... ) ; assert out!=0 else err0x20f.
- case 0x5a: get tab id by index -> FUN_0062cfc0(childlist,idx); assert out!=0 (0x218) & idx>=0 (0x219).
- case 0x5b: index-from-encoded-id -> *out=~wparam; assert out!=0 (0x222) & wparam<0 (err0x3a).
- case 0x5c: get tab enabled/state -> resolve child FUN_0062cfc0(~wparam) assert found (0x22e), *out=FUN_0062e2a0(child).
- case 0x5d: select tab by index -> assert wparam>=0 (0x236); FUN_0061b520(idx,0).
- case 0x5e (base default): returns DAT_00a50680 template (overridden by wrapper above).

TAB-BUTTON SUBCLASS PROC FUN_00885340 (template[1], layered on each tab btn): case1=paint noop; case8=draw tab face bitmap via FUN_0062b8e0 (&DAT_00b96984 selected / &DAT_00b9698c unselected, 0x20x0x20) when flag bit0 set, using FUN_0060f4b0 selected-state; case0x15=report tab btn size/colors (selected vs unselected color globals); case0x5f=draw tab background via FUN_0062bb30 (enabled color 0xffffffff via FUN_0062e320, disabled 0xffa0a0a0). template[0] FUN_008854f0 is a lighter face variant (only case8 img via &DAT_00b9697c + case0x15 colors).
- **Create recipe:** Verified from real caller FUN_00889950 (a HideUi tabbed panel builder):
1) Have a parent/host frame (param_1). Optionally set frame state bits first (FUN_0062ccd0(parent,8,0)); orientation read from frame flags 0x1000/0x2000/0x40000.
2) CREATE THE STYLED PAGE FRAME:
   pageId = FUN_0062bfc0(parent, 0x40000, 1, FUN_00885590, 0, 0)
   -> parent, flags=0x40000 (styled paint-gate; same bit case0x37 layout tests), childSlot=1, proc=FUN_00885590 (UiCtlHideUiProc), userData=0, 0. Returns pageId (frame id, also *(frame+0xbc)).
   NOTE: on OnFrameCreate the base allocates the 8B CtlPage instance; do NOT double-create on the same slot.
3) ADD TABS (loop i=0..n-1): 
   tab = FUN_0061a8b0(pageId, labelEncId, tabFlags, i, tabProc, 0)
     - styled/toggle tab: tabFlags=0x20000, tabProc=FUN_00878340 (styled btn) then FUN_0060e160(tab,0,&LAB_00612ad0,0) and FUN_00612900(tab,0,0,contentProc,boolFlag) to bind the tab's content page.
     - plain tab: tabFlags=0, tabProc=contentProc directly; or FUN_0060f490(pageId,i) to drop a tab with no content.
   labelEncId MUST be an encoded string id from FUN_007c3bc0(msgId) / FUN_007c3be0(...) — never a raw char*.
4) SELECT DEFAULT TAB: FUN_0060a2d0(pageId, index); FUN_0062cfc0(pageId,1) to enable; index may come from a saved global (DAT_01081d84). Broadcast via FUN_0062f0a0 if needed.
5) LAYOUT: page auto-runs case 0x37 (FUN_0061af80) which reads the 0x5e styling template; ensure the UI atlas/face bitmaps (&DAT_00b96984 / &DAT_00b9698c / &DAT_00b9697c) are loaded so styled tab buttons can paint.
Order matters: create page -> add tabs (each with its content proc) -> select default. Sizing: styled tab row height = template float 26.0f; page container insets are ZERO (case 0x15 returns zeros), so size the page frame yourself.
- **Gotchas:** - DOUBLE-CREATE: case 9 asserts instance slot *(hdr[2])==0 (err 0x256, CtlPage.cpp:599). Creating the page twice on the same frame slot aborts.
- DOUBLE-DESTROY / destroy-before-create: case 0xb asserts instance!=0 (err 0x25b).
- NULL OUT POINTER: get-cases assert out!=0: 0x59(0x20f), 0x5a(0x218), 0x5b(0x222), 0x5c(0x22a). Always pass a valid out buffer.
- INDEX SIGN RULES: 0x5a & 0x5d require index>=0 (asserts 0x219 / 0x236); 0x5b requires wparam<0 encoded id (err 0x3a); 0x5c requires the encoded child (~wparam) to resolve or asserts 0x22e.
- PAINT GATE: styled tab buttons only paint when frame flag 0x40000 is set (also drives layout orientation in case 0x37). Without it, tabs render blank.
- IMAGE-LIST / ATLAS WARM-UP: styled tab-button faces draw &DAT_00b96984 (selected) / &DAT_00b9698c (unselected) / &DAT_00b9697c at 0x20x0x20 via FUN_0062b8e0 — the UI atlas must be loaded or the face draw reads unpopulated bitmap globals.
- ENCODED LABELS: tab labels must be encoded string ids (FUN_007c3bc0/FUN_007c3be0); passing raw char* corrupts tab text.
- ZERO INSETS: case 0x15 returns all-zero size/inset (4 dwords). Callers expecting nonzero container padding from a styled page get none — size the page frame explicitly.
- selectedIndex starts -1: querying current tab (0x56) before FUN_0060a2d0 returns "none".
- Template selector: 0x5e uses wparam as selector (0=styled template with the two subclass procs, nonzero=all-zero plain template); passing wrong selector yields unstyled tabs (no crash, but silent styling loss).

### UiCtlSliderProc (textured slider paint wrapper over CtlSliderProc)  (EXE 0x0087f440, confidence: high)

- **WASM:** Not separately resolved; EXE proc verified via base-layer assertion string "P:\\Code\\Engine\\Controls\\CtlSlider.cpp":0x233. Wrapper file is UiCtlSlider.cpp (styled layer). WASM name lookup unnecessary — EXE address is confirmed by the two-layer install (case 4 sets base = CtlSliderProc 0x00615fe0) and the CtlSlider.cpp assert in the base.
- **Assertion file:** Wrapper: P:\Code\Engine\Controls\UiCtlSlider.cpp (styled layer, no direct assert in wrapper). Base CtlSliderProc 0x00615fe0: P:\Code\Engine\Controls\CtlSlider.cpp — alloc/create assert at line 0x233 (563); runtime asserts 0x18a/0x18b (set-value out of range), 0x181 (get-value null out ptr), 0x6bc (null frame in enabled-check FUN_0062e2a0).
- **Struct:** Instance = 0x30 (48) bytes, allocated in base msg 9, pointer stored at *param_1[2]:
- +0x00 uint  flags. bit0 = "absolute/track-jump drag in progress" (set in FUN_00616690, cleared in msg 0x2e). Tested in 0x2c/0x2e.
- +0x04 int   drag pixel offset (thumb grab delta; param_1[1] in helpers).
- +0x08 uint  OWNER/target frame handle (param_1[2]); every outbound msg + FUN_0062fe20 orientation query use this.
- +0x0c int   range MIN (from create param[0] or msg 0x56).
- +0x10 int   range MAX (from create param[1] or msg 0x56). span = max-min; must be != 0 before value ops.
- +0x14 float NORMALIZED value 0.0..1.0 (the source of truth; get/set-int convert against range).
- +0x18 float cached/secondary value (written in pointer-drag mode 0x2c: base+0x18 = value; param_1[6]).
- +0x1c float thumb geometry X / width component (param_1[7]).
- +0x20 float thumb geometry Y / height component (param_1[8]).
- +0x24 float horizontal scale factor (param_1[9]).
- +0x28 float vertical scale factor (param_1[10]).
- +0x2c ptr   optional alt-render/live handle; when non-NULL FUN_00616990 calls FUN_00616a80 instead of plain invalidate; freed on destroy via FUN_0046f850.
Fields 0x1c-0x28 are populated during layout/paint (measure pass); zero at create.
- **Messages:** Slider is a TWO-LAYER proc. Wrapper UiCtlSliderProc 0x0087f440 dispatches on param_1[1]=msg; anything unhandled falls through to base CtlSliderProc 0x00615fe0 via thunk_FUN_00647170. Dispatch signature: proc(frameCtx *param_1, int *param_2 /*msg args/out*/, param_3). param_1[0]=frame handle/id, param_1[1]=msg, param_1[2]=instance-pointer slot (piVar1; instance = *piVar1).

== WRAPPER (0x0087f440) handled messages ==
- 1 PAINT (textured): sub-pass selector = *param_2. If *param_2==1 -> draw THUMB (fixed 0x20x0x10 = 32x16) via FUN_0062b8e0 using image template *(&PTR_DAT_00bf4694 - (enabled?0:4)); enabled state from FUN_0062e2a0(frame). If *param_2==2 (code: local_14=*param_2-2==0) -> draw TRACK via FUN_0062b3e0 using template *(&PTR_DAT_00bf469c - (enabled?0:4)). Any other sub-pass -> forward to base (which paints the plain fallback bar).
- 4 INSTALL-BASE/vtable: *(code**)param_2[3] = FUN_00615fe0 (installs CtlSliderProc as the base layer). This is what makes the two-layer stack work.
- 0xc (notify/invalidate): FUN_0062bd40(frame) then falls through.
- 0x59 GET-PREFERRED-SIZE: returns 3 floats {DAT_00b963a4=16.0, DAT_00b963a8=32.0, DAT_00b963ac=32.0} into param_2[0..2] (textured min/preferred size 16x32x32).
- default: forward to base.

== BASE CtlSliderProc (0x00615fe0) handled messages ==
- 1 PAINT (untextured fallback): FUN_0062b2d0 draws a solid bar, color 0xffc8c8c8 enabled / 0xff808080 disabled (case *param_2==2). Used when wrapper doesn't own the sub-pass.
- 4 INSTALL-BASE: *(code**)param_2[3] = FUN_006123a0 (generic control base-of-base).
- 8 VALUE-CHANGED (inbound): FUN_00615dc0(param_2).
- 9 ONFRAMECREATE: allocate 0x30-byte instance via FUN_0047f340(\"CtlSlider.cpp\",0x233); zero it; store owner frame handle (*param_1) at instance+0x08; if create-param *param_2!=NULL set range min=((int*)*param_2)[0]->instance+0x0c, max=((int*)*param_2)[1]->instance+0x10; write instance ptr to *piVar1.
- 0xb DESTROY: if instance+0x2c!=0 free it (FUN_0046f850); free instance (FUN_005acaeb(inst,0x30)).
- 0x20 KEY/SCROLL: arrow codes in *param_2: 0x1c/0x1e -> value += 1/(max-min); 0x1d/0x1f -> value -= 1/(max-min) (both via FUN_00616990 with notify=1).
- 0x24 POINTER-DOWN / begin-drag: FUN_00616690 — hit-tests thumb (FUN_00615d70), on hit sets drag pixel-offset instance+0x04 and flag bit0, else jumps value to click position; sends owner msg 7 (capture/begin) and may start scroll timer (FUN_00630080).
- 0x2c POINTER-MOVE while captured: recompute normalized value from pointer (horizontal/vertical via flag 0x2000 on owner) and call FUN_00616990 (notify).
- 0x2e DRAG/scroll-step: continuous thumb move; recomputes and sends owner msg 9 (FUN_0062ee80(frame,9,pos,0)); clears flag bit0.
- 0x38 MEASURE/LAYOUT: writes track pixel geometry into param_2[2] using range span (max-min) * value * _DAT_009407b0; branches on owner orientation flag 0x2000; also queries msg 0x59 on owner.
- 0x39 RELAYOUT: FUN_0062f110(frame).
- 0x3b MOUSE-WHEEL: if FUN_00616860(1) step = 1/(max-min) via FUN_00630080.
- 0x56 SET-RANGE: instance+0x0c = *param_2 (min), instance+0x10 = param_2[1] (max); invalidate (FUN_0062bd80 flag 0x20) + relayout (FUN_0062f110). MUST be sent before any value op.
- 0x57 SET-VALUE-INT: param_2 IS the int value (passed by value, cast). Asserts value>=min (else 0x18a) and value<=max (else 0x18b); normalized = (value-min)/(max-min) -> FUN_00616990(...,notify=0).
- 0x58 GET-VALUE-INT: param_2 = int* out (assert non-null else 0x181); *out = min + round((max-min)*value_float).
- 0x59 GET-PREFERRED-SIZE: returns {DAT_00a50424=4.0, DAT_00a50428=16.0, DAT_00a5042c=8.0}.

== OUTBOUND messages the slider sends to its owner frame (instance+0x08) via FUN_0062ee80(owner,msg,wparam,0) ==
- 7: begin/capture (drag start).
- 8: VALUE-CHANGED notification, wparam = new integer position (min + round(span*value)). Sent by FUN_00616990 only when notify flag set AND integer position actually changed.
- 9: drag-scroll position update.
Internal normalized setter FUN_00616990(inst, float v, notify): clamps v to [0,1], writes inst+0x14, invalidates (or FUN_00616a80 if inst+0x2c set), and fires owner msg 8 when notify!=0.
- **Create recipe:** Two-layer create (identical pattern to UiCtlPageProc/UiCtlBtnProc textured wrappers):
1. Create the frame with the primitive FUN_0062bfc0(parent, flags, child, proc, userdata, 0). Pass proc = UiCtlSliderProc 0x0087f440. Store returned id at frame+0xbc.
   - userdata (create-param) should point to an int[2] = {min, max}; the base msg 9 reads it to seed the range at +0x0c/+0x10. If you pass NULL, range defaults to {0,0} and you MUST send msg 0x56 before any value op (span 0 = divide-by-zero).
2. Framework raises msg 4 -> wrapper installs base = CtlSliderProc 0x00615fe0. Then msg 9 (OnFrameCreate) allocs the 0x30 instance. Order is automatic; do not hand-call msg 9.
3. Set/confirm range: FUN_0062ef40(frame, 0x56, &minmax, 0) where minmax is int[2]{min,max}; max must be > min.
4. Set initial value: FUN_0062ef40(frame, 0x57, value, 0) — value passed BY VALUE and must satisfy min<=value<=max.
5. Read value: int out; FUN_0062ef40(frame, 0x58, &out, 0).
Sizing / warm-ups:
- Preferred size from wrapper (msg 0x59) is 16x32(x32) textured; the raw base is 4x16(x8). The anchor-6 pos/size setter 0x0062F770 positions it. The track fixed thumb art is 32x16.
- IMAGE WARM-UP REQUIRED: textured paint dereferences image templates at 0x00b963b0/b8 (thumb enabled/disabled) and 0x00b963c0/c8 (track enabled/disabled), pointer table PTR_DAT_00bf4690..0x00bf469c. These reference the shared control image list; if the UI image list isn't initialized the FUN_0062b8e0/FUN_0062b3e0 template draws will read null art. Ensure the styled-control atlas/imglist is loaded (same prerequisite as UiCtlBtnProc's 0x010819cc) before the slider paints.
- Enabled/disabled visual auto-selected via FUN_0062e2a0(frame) which checks control flag 0x10 (disabled) — no manual toggle needed.
Destroy: use the native destroyer FUN_0062c550(id); base msg 0xb frees instance + any +0x2c handle.
- **Gotchas:** 1. RANGE-ZERO DIVIDE: if min==max (default when created with NULL userdata and no 0x56), every value conversion (0x57 normalize, 0x58, key-step 1/(max-min), layout 0x38) divides by (max-min)=0. ALWAYS send msg 0x56 with max>min before 0x57/0x58/input.
2. SET-VALUE OUT-OF-RANGE FATAL: msg 0x57 with value<min asserts FUN_00487a80(0x18a) (no-return); value>max asserts 0x18b. Clamp before sending; these are hard fatals, not soft clamps.
3. GET-VALUE NULL OUT-PTR: msg 0x58 with param_2==NULL asserts 0x181 (no-return). Always pass a valid int*.
4. NULL FRAME IN PAINT: enabled-state helper FUN_0062e2a0(*param_1) asserts 0x6bc if the frame handle is 0. The slider must be fully attached/valid before it receives paint (msg 1). Don't paint an orphaned frame.
5. IMAGE-LIST GATE: textured paint (wrapper case 1, sub-pass 1 thumb / 2 track) blindly uses templates 0x00b963b0..c8 -> shared control image list. If that atlas isn't loaded the template-draw primitives deref null art. Same warm-up requirement as the styled button family.
6. PAINT SUB-PASS GATE: wrapper only draws on sub-pass *param_2==1 (thumb) or ==2 (track); other sub-passes silently forward to base (plain bar). Not a crash, but explains "why is my slider drawn as a grey bar" if the image list is missing (base fallback color 0xffc8c8c8/0x808080).
7. INSTANCE LIFECYCLE: instance is allocated in base msg 9 and required by 0x56/0x57/0x58/0xb/paint (they deref *param_1[2] then *piVar1). Sending value/range messages before the frame's msg-9 create pass runs will deref a null instance. Let the framework complete creation first.
8. CREATE-ORDER: the wrapper's msg 4 MUST run so base=CtlSliderProc is installed before msg 9; achieved by registering proc 0x0087f440 as the frame proc (the framework sequences 4 then 9). Do not register the base 0x00615fe0 directly if you want the textured look.

### UiCtlScrollProc  (EXE 0x0087d5d0, confidence: high)

- **WASM:** ram:80e0c369
- **Struct:** The styled proc FUN_0087d5d0 is per-frame stateless: its state is GLOBAL - DAT_010819e8 bit0 (styled-enabled paint gate), DAT_010819ec (up/left arrow imagelist), DAT_010819f0 (down/right arrow imagelist), texture arrays PTR_DAT_00bf45f0/00bf45f8/00bf4628/00bf4638 and rect DATs 00bf4600/08/30/40/48, metric floats 00b95ff8..00b96004 = {16.0,16.0,8.0,-1.0}.

The base CtlScrollProc instance (allocated by FUN_0061b9d0 msg 9 @CtlScroll.cpp:0x4c7, ~0x3c bytes), pointer stored at *(param_1[2]):
+0x00 vtable = &PTR_FUN_00a50798 = {0x0061b830 dtor, 0x0061b870 getContentSize, 0x0061b8c0, 0x0061b910}
+0x04 int active/hit element (returned by msg 0x57; set in msg 0x24 via FUN_0061c4f0)
+0x08 HFrame child scrollbar frame id (target of FUN_0062ee80/FUN_0062ef40 msgs)
+0x0c,+0x10 reserved (0)
+0x14 float visual-min (set msg 0x37 from param2[0])
+0x18 float visual-max (set msg 0x37 from param2[1])
+0x1c float last drag coordinate (msg 0x24)
+0x20 int page/thumb size (Get 0x59 / Set 0x5f)
+0x24 int current position (Get 0x5a / Set 0x60)
+0x28 int range min (Get 0x5b lo / Set 0x61)
+0x2c int range max (Get 0x5b hi / Set 0x61)
+0x30 uint orientation index 0/1 (vert/horiz) - indexes rect coord array pfVar3[inst+0x30 +2]
+0x34 smooth-scroll animation handle ptr (alloc @CtlScroll.cpp:0x231, freed FUN_005acaeb; ticked msg 0x45)
+0x38 float thumb drag anchor (set when active element==5)
- **Messages:** Registered outer (styled) FrameProc = FUN_0087d5d0, dispatch on param_1[1]=msg. It is a thin theme layer over the base CtlScrollProc FUN_0061b9d0; unknown msgs chain via thunk_FUN_00647170 (FrameMsgCallBase). Gate var bVar1 = (DAT_010819e8&1)!=0 AND NOT FrameTestStyles(frame,0x8000) -> styled path; else non-styled 16px fallback.

STYLED PROC (FUN_0087d5d0) messages:
- 1 Paint: sub-dispatch on *param2 (sub-pass id). 1=up/left arrow, 2=down/right arrow: idx = FUN_006113e0(frame) (CtlScrollGetActiveElement, returns pressed element) -> draw from arrow imagelist via FUN_0062b290(frame,rect,imagelist,idx,layer,model). 3=thumb: styled FUN_0062b790 (9-slice template, rect &DAT_00bf4608 + (style0x2000?0x10:0)) / non-styled FUN_0062b3e0 (16x16 coords). 4=track/gutter: styled FUN_0062b790 (&DAT_00bf4648...) / non-styled FUN_0062b8e0. FrameTestStyles(frame,0x2000) (iVar2) selects highlighted vs normal texture set: adds +4 to the PTR_DAT arrays / +0x10 to rect DATs.
- 4 InstallBase: *(code**)param2[3] = FUN_0061b9d0 (base CtlScrollProc), then chain.
- 5 Warm-up/ThemeLoad: DAT_010819ec = FUN_0062d790(0x11,7,0x12,&DAT_00bf4680,&DAT_00bf4670,PTR_DAT_00bf4668,4) (up-arrow imagelist); DAT_010819f0 = same for down-arrow. (FUN_0062d790 = FrameImageListCreate.)
- 6 Teardown: FUN_0046f9b0(DAT_010819ec); =0; FUN_0046f9b0(DAT_010819f0); =0. (close image lists.)
- 9 OnFrameCreate: if styled: FUN_0062ede0(frame,0,5) (FrameMouseEnable) + FUN_006302c0(frame,0,0xffffffff) (FrameTouchEnable). Base (via chain) allocs the instance.
- 0x56 GetMetric/thickness: styled -> *param2=8.0(DAT_00b96000), param2[1]=-1.0(DAT_00b96004 auto); non-styled -> 16.0,16.0 (DAT_00b95ff8/ffc).
- default: chain to base.

BASE PROC (FUN_0061b9d0, actual scroll logic, dispatch on param_1[1]): 1=paint gray fallback (color by active elem 0xff606060/0xffc8c8c8/0xff808080), 4=install(sets FUN_006123a0), 8=init-notify, 9=OnFrameCreate (FrameTestStyles(frame,0x2000): !=0 -> alloc full 0x3c instance @CtlScroll.cpp:0x4c7 with vtable 0x00a50798; ==0 -> lightweight FUN_0061b7d0 @0x4c9), 0xb=destroy (vtable[0](1)), 0x13=content-size query, 0x20=key/wheel nav, 0x24=mouse-down/drag-begin, 0x2c=drag/notify, 0x2e=reset, 0x37=SetVisualRange (inst+0x14/+0x18), 0x38=layout/measure, 0x3b, 0x45=smooth-scroll anim tick, 0x57=GetActiveElement(inst+4), 0x58=CanScroll query, 0x59=GetPageSize(inst+0x20), 0x5a=GetScrollPos(inst+0x24), 0x5b=GetScrollRange(inst+0x28 min,+0x2c max), 0x5c/0x5d=line-scroll +/-, 0x5e=EnsureVisible, 0x5f=SetPageSize(inst+0x20), 0x60=SetScrollPos(inst+0x24), 0x61=SetScrollRange(inst+0x28/+0x2c).
- **Create recipe:** 1. Create the scrollbar frame with FUN_0062bfc0(parent, flags, child, proc=0x0087d5d0, userdata, 0) -> id at frame+0xbc. flags MUST include style 0x2000 (full-scrollbar) so base msg 9 takes the real-instance branch (0x4c7); without it the lightweight FUN_0061b7d0 branch runs and the get/set field layout is invalid. Do NOT set 0x8000 (forces non-styled fallback path). Orientation bit drives inst+0x30 (0=vertical,1=horizontal).
2. Warm-up: the styled arrow image lists (DAT_010819ec/DAT_010819f0) are only built on msg 5 (theme/skin load broadcast). The UI system sends 5/6 on theme (re)load; if you build a scrollbar standalone before that, send msg 5 once so imagelists exist before first paint.
3. Configure model: msg 0x61 SetRange(min,max) with min<=max, msg 0x5f SetPageSize, msg 0x60 SetScrollPos. Optionally 0x37 SetVisualRange.
4. Size/anchor: styled thickness = 8px (metric 0x56 -> 8.0, cross-axis -1.0 = auto/stretch); non-styled = 16px. Position/size via anchor-6 setter 0x0062F770.
5. Layer additional subclass procs if needed via FrameNewSubclass 0x0062f150. Destroy via native FUN_0062c550(id); base msg 0xb invokes the instance dtor (vtable[0]).
- **Gotchas:** 1. PAINT GATE / null imagelist: styled paint (msg1 sub 1/2) draws arrows from DAT_010819ec/DAT_010819f0 via FUN_0062b290; if warm-up msg 5 never ran these globals are 0 -> null-imagelist paint (blank or crash). Always ensure theme warm-up before first paint.
2. NULL out-pointer fatal: msgs 0x57/0x59/0x5a/0x5b call FUN_00487a80 (no-return abort) when param_3==NULL. Never issue GetActiveElement/GetPageSize/GetPos/GetRange with a null output buffer.
3. REVERSED RANGE assert: msg 0x5e EnsureVisible asserts FUN_00487a80(0x252) if param2[1]<param2[0]; msg 0x61 SetRange asserts FUN_00487a80(0x28a) if max<min. Pass min<=max.
4. MISSING 0x2000 STYLE: base msg 9 with style 0x2000 clear takes lightweight FUN_0061b7d0 branch (assert CtlScroll.cpp:0x4c9); later scroll get/set read a struct that is not the full 0x3c layout -> garbage/OOB.
5. ANIMATION HANDLE (inst+0x34): allocated on msg 0x24/0x45 (@CtlScroll.cpp:0x231), freed via FUN_005acaeb; only destroy through msg 0xb (dtor clears it) or risk leak/UAF.
6. STYLED vs NON-STYLED thickness divergence: style 0x8000 set OR DAT_010819e8 bit0 clear silently switches geometry from 8px to 16px (different 0x56 metric) - not a crash but causes layout overlap / mis-aligned hit-testing if callers assume one thickness.

### UiCtlEditProc (styled CtlEdit wrapper / "outer edit" installer)  (EXE 0x008852e0, confidence: high)

- **WASM:** ram:80e0f5ab
- **Assertion file:** Wrapper/styled layer: P:\Code\Engine\Controls\CtlEdit.cpp (WASM class name IUi::UiCtlEditProc). Base layer asserts on P:\Code\Engine\Controls\CtlEditAutoComplete.cpp (registered in base msg 9 via FUN_0047f340).
- **Struct:** Frame-level (TCtlInstance<CtlEdit>): frame+0xbc = frame id (set by create primitive FUN_0062bfc0). In the MsgProc FrameMsgHdr, param_1[1]=msg, param_1[2]=address of the instance-pointer slot, *(param_2+0xc)=frame proc-ptr slot (base msg4 writes LAB_00619c50 here).
Autocomplete instance (0x40 bytes, at *param_1[2], allocated by FUN_00619710 on base msg9, freed via FUN_005acaeb(inst,0x40)):
- +0x00: root vtable/proc-chain ptr (FUN_00603cc0 family)
- +0x04: heap text/work buffer ptr (freed in msg0xb if nonzero, then set 0)
- +0x08: cleared to 0 on destroy (list tail)
- +0x0c: cleared to 0 on destroy (list head)
- +0x20: autocomplete entry linked-list head (walked in msg0xb; low bit=sentinel/terminator)
Class descriptor (case 100, PTR_FUN_00b96960, 7 dwords): {0x00885620, 0x00885100, 1.0f, -1.0f, 0.0f, 0.0f, 100.0f}. Confidence on exact autocomplete offsets is medium; frame-level and descriptor are firm.
- **Messages:** This control is a 3-layer stack. FUN_008852e0 is the FrameProc you register; it installs a base proc (msg4) and layers a styled render subclass (msg9).

LAYER A - Outer installer FUN_008852e0 (=UiCtlEditProc, the proc passed to the create primitive):
- msg 4 (install base/vtable): writes base MsgProc ptr LAB_00619c50 (tail-jmp -> FUN_00619c80) into *(param_2+0xc). return.
- msg 9 (OnFrameCreate): FUN_0062f150(*param_1, FUN_00888aa0, 0) = FrameNewSubclass layering the styled render subclass 0x00888aa0. return. (Instance alloc is done by the BASE msg9, not here.)
- msg 100/0x64 (get class descriptor): copies 7 dwords from PTR_FUN_00b96960 -> param_3 = {0x00885620, 0x00885100, 1.0f, -1.0f, 0.0f, 0.0f, 100.0f}.
- default: thunk_FUN_00647170 (FrameMsgCallBase / base dispatch).

LAYER B - Styled render subclass FUN_00888aa0 (owns SHARED/global image lists DAT_01081d78/_7c/_80; numeric asserts only):
- msg 1 (paint, sub-pass = *param_2): sub0 = draw frame/border image via FUN_0062b8e0, choosing art PTR_DAT_00bf4700 vs 00bf46fc by focus/enabled (FUN_0062e2e0 hittest + FUN_0056a410); sub1 = draw fill image DAT_01081d78 (FUN_0062b2d0); sub0xc = draw caret/IME indicator DAT_01081d80 with computed x-offset (FUN_0062b290), early-returns for IME states 0 and 5; sub0xd = draw image DAT_01081d7c (FUN_0062b2d0).
- msg 5 (class OnInit): lazily builds the 3 shared image lists: DAT_01081d78=FUN_00679a60(...,0x20003e0,0), DAT_01081d7c=FUN_00679a60(&DAT_00bf46f8,0x20003e0,0), DAT_01081d80=FUN_0062d790(0x11,7,0,...,&DAT_00b96c18,0x18). ASSERT 0x3c if DAT_01081d78 already non-zero. Then base.
- msg 6 (class OnTerminate): FUN_0046f9b0 frees all 3 lists, zeros them, then base.
- msg 0xc (destroy child): FUN_0062bd40(*param_1), then base.
- msg 0x15 (measure/size-query): writes default metrics {6.0f, 3.0f, 6.0f, 3.0f} (from _DAT_00940ee0=6.0, _DAT_009407b8=3.0) into param_3.
- msg 0x5f (paint text content): FUN_0062bb30 renders text; color = enabled?default:(0x505050-0x5f5f60) via FUN_0062e2a0; param_2[10]=extra arg.
- msg 0x60: allocs FUN_007c3bc0(0x2a); param_3={obj, FUN_00878950}; then base.
- msg 0x61 (get interface/vtable): ASSERT 0xd0 if param_3 null; writes {FUN_00889480, FUN_00889560, FUN_0087d5d0}; falls through to base.
- default: base.

LAYER C - Base CtlEdit+AutoComplete proc FUN_00619c80 (via LAB_00619c50):
- msg 4: *(param_2[3]) = FUN_00603cc0 (edit-core vtable).
- msg 9 (alloc instance): ASSERT 0x77 if *param_1[2] already set; FUN_0047f340(\"...CtlEditAutoComplete.cpp\",0x78); *param_1[2]=FUN_00619710(*param_1) (autocomplete instance).
- msg 0xb (destroy): walk+destroy autocomplete entry list at inst+0x20, free buffer at inst+4, FUN_005acaeb(inst,0x40) frees the 0x40-byte instance, *param_1[2]=0.
- msg 0x20 (char/key): FUN_0061a880(get inst); scancode 0x1c(enter)->FUN_0061a030(1); 0x1f->FUN_0061a030(0); else base.
- msg 0x21 (focus): create/destroy autocomplete dropdown (FUN_0062cfc0 / FUN_0062c550, gate flag 0x8000000).
- msg 0x31 (mouse down): btn0 & pass7 -> FUN_0061a1a0, then base.
- msg 0x32 (mouse up): out param_3=0; pass7 -> FUN_0061a570, then base.
- msg 0x37 (layout): position dropdown under edit via anchor-6 setter FUN_0062f770.
- msg 99/0x63 (set rect/anchor): FUN_0061a3a0(param_2).
- default: base dispatch.

EXTERNAL PROPERTY MESSAGES (sent via FUN_0062ef40(frame,msg,wparam,lparam)):
- 0x57 GET_TEXT(out_len_ptr, out_buf): FUN_00603c40; ASSERT 0xf8c if out_buf null.
- 0x5a SET_MAX_LENGTH(n): FUN_00604aa0.
- 0x5c SET_PROMPT/ghost-text(encstr): FUN_005636a0.
- 0x5e SET_TEXT(encstr): FUN_00604b00; ASSERT 0xfb8 if null.
- 0x63 SET_RECT/anchor(rect): FUN_00619c60.
- **Create recipe:** Verbatim from the live chat/GmChat builder FUN_0051b580 (the "EditName" single-line styled edit):
1) id = FUN_0062bfc0(parent, 0x0892e000, child_id, FUN_008852e0 /*proc=0x008852e0*/, userdata=0, L"EditName");   // create; proc = UiCtlEditProc installer
2) FUN_0062f150(id, FUN_0051ce20, 0);   // OPTIONAL: layer an app key/enter handler subclass on top
3) FUN_00604aa0(id, 0x14);              // msg 0x5a: max input length = 20 chars
4) prompt = FUN_007c3bc0(0x2da);        // fetch localized ENCODED prompt string
5) FUN_005636a0(id, prompt);            // msg 0x5c: set ghost/prompt text
(sibling multi-line variant in same fn uses proc FUN_0087d9a0 with flags 0x2020000 for "EditMessage" - different control.)
FLAGS: 0x0892e000 for the styled single-line name field.
ORDER/WARM-UP: create attaches the frame to a live tree; the styled class OnInit (msg 5) builds the SHARED global image lists (DAT_01081d78/_7c/_80) lazily on the first control of this class - this must run before the first paint. There is no per-instance image-list preload; just ensure the control is mounted (not painted detached). The base msg9 auto-allocates the autocomplete instance - do not send OnFrameCreate twice.
SIZING: styled measure (msg 0x15) returns default {6.0,3.0}; real size comes from parent layout / anchor-6 setter FUN_0062F770; cap text with msg 0x5a; set/get text with 0x5e/0x57; set prompt with 0x5c.
- **Gotchas:** 1) Base msg 9 double-create: ASSERT 0x77 (FUN_00487a80) if the instance slot *param_1[2] is already populated - never fire OnFrameCreate twice on the same frame.
2) Shared image-list double-init: styled msg 5 ASSERT 0x3c if DAT_01081d78 is already non-zero. The three image lists are GLOBAL/shared across all edits; forcing a second class-init crashes. They are freed only by msg 6 (OnTerminate).
3) msg 0x61 (get interface) ASSERT 0xd0 if the out pointer param_3 is null.
4) SET_TEXT 0x5e ASSERT 0xfb8 on null string; GET_TEXT 0x57 ASSERT 0xf8c on null out buffer.
5) Paint depends on class init: paint sub-passes 1/0xc/0xd dereference DAT_01081d78/_80/_7c. If the control is painted before its class msg 5 has run (image lists still 0), the draw primitives receive null image lists -> missing art / potential deref. Keep the frame in a mounted tree so init precedes the first paint.
6) Destroy must route through base msg 0xb; skipping it leaks the 0x40-byte autocomplete instance plus its entry list (inst+0x20) and buffer (inst+4). Use the native destroyer FUN_0062c550(id) which drives the proper teardown.
7) The autocomplete dropdown is a real child frame created on focus (msg 0x21, gate flag 0x8000000) and destroyed on blur - do not manually free it; toggling focus repeatedly is the intended lifecycle.

### UiCtlEditBox (IUi::UiCtlEditBoxProc) — styled edit-box render subclass  (EXE 0x00888aa0, confidence: high)

- **WASM:** ram:80e0e3e0 (IUi::UiCtlEditBoxProc(FrameMsgHdr const&, void const*, void*))
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlEditBox.cpp (string @ EXE 0x00b96bd8; xref'd 3x inside FUN_00888aa0)
- **Struct:** The render subclass keeps NO per-instance struct — its only state is 3 MODULE-GLOBAL GPU resource handles, created once on msg 5:
- DAT_01081d78 = HGrMaterial editCaretMaterial = GrBuildSolidMaterial(FUN_00679a60, color 0xfff0f0f0, fmt 0x020003e0). Drawn as the caret (paint sub 1).
- DAT_01081d7c = HGrMaterial editSelectionMaterial = GrBuildSolidMaterial(color 0x60a096dc @DAT_00bf46f8, fmt 0x020003e0). Drawn as selection highlight (paint sub 0xd).
- DAT_01081d80 = HFrameImageList imeStatusImageList = FrameImageListCreate(FUN_0062d790, fmt 0x11, texOp 7, 0, cell{0x11,0x11}, size{0x80,0x80}, tex path @DAT_00b96c18, 0x18 frames). Drawn as IME indicator (paint sub 0xc).
Per-instance editable state (text buffer, caret pos, readonly, focus, enabled) lives on the underlying base CtlEdit instance (base vtable installed at &LAB_00619c50 by the outer CCtlEdit proc) and is read only through frame-id helpers (FrameIsKeyFocus, CtlEditGetReadOnly, FrameIsEnabled) — never by struct offset in this proc.
- **Messages:** FrameProc signature FUN_00888aa0(hdr*=param_1, in*=param_2, out*=param_3). param_1[0]=HFrame id, param_1[1]=msg. This is a RENDER SUBCLASS layered at layer 0; it holds no per-instance data and dispatches switch(param_1[1]):
- 1 PAINT/AddContent — inner switch(*param_2)=element index. param_2+2=Rect4f, param_2[6..7]=layer/model args:
   * sub 0 = border: FrameContentAddImageTemplate(FUN_0062b8e0) 9-slice, inset {0x20,0x10}, layer 7. Template = active PTR_DAT_00bf4700 when FrameIsKeyFocus(FUN_0062e2e0)!=0 AND CtlEditGetReadOnly(FUN_0056a410)==0, else normal PTR_DAT_00bf46fc.
   * sub 1 = caret: FrameContentAddImage(FUN_0062b2d0, material=DAT_01081d78 editCaretMaterial, scale{1.0,1.0}, off{0,0}).
   * sub 0xc = IME indicator: FrameContentAddImage(FUN_0062b290, imagelist=DAT_01081d80, frameIndex). Index computed from EventCliGetImeLang(FUN_006275e0)/EventCliGetImeMode(FUN_006275f0); lang!=0/5 gates it, high-word path asserts UiCtlEditBox.cpp:0x9a if lang not in {2,3}.
   * sub 0xd = selection highlight: FrameContentAddImage(material=DAT_01081d7c editSelectionMaterial, scale 1.0).
- 5 INIT/create-statics — lazily builds the 3 module-global GPU handles (see struct_layout), then FrameMsgCallBase. Asserts UiCtlEditBox.cpp:0x3c (no-return) if DAT_01081d78 already non-null (double-init guard).
- 6 DESTROY-statics — HandleCloseSafe(FUN_0046f9b0) each of the 3 globals and null them, then base.
- 0xc INVALIDATE — FrameContentInvalidate(FUN_0062bd40, frame), then base.
- 0x15 SIZE-QUERY — writes 4 floats to param_3: {6.0,3.0,6.0,3.0} (minW,minH,prefW,prefH; from _DAT_00940ee0=6.0f,_DAT_009407b8=3.0f).
- 0x5f ADD-TEXT — FrameContentAddText(FUN_0062bb30) color 0xf0f0f0ff when FrameIsEnabled(FUN_0062e2a0)!=0 else 0xa0a0a0ff; text-model array=param_2[10]; content layer 6; then base.
- 0x60 GET-MASK-CHAR — out[0]=TextEncode(FUN_007c3bc0,0x2a='*') password mask glyph, out[1]=FUN_00878950 (FrameTextParams), then base.
- 0x61 GET-CHILD-CLASS-PROCS — asserts UiCtlEditBox.cpp:0xd0 if param_3==null; writes out[0]=FUN_00889480, out[1]=FUN_00889560, out[2]=FUN_0087d5d0 (child scroll/content class procs).
- default/fallthrough — thunk_FUN_00647170 = FrameMsgCallBase.
- **Create recipe:** Do NOT install FUN_00888aa0 directly. It is layered automatically by the outer CCtlEdit proc 0x008852e0 (which handles: case 4 install base vtable &LAB_00619c50; case 9 OnFrameCreate -> FrameNewSubclass(FUN_0062f150)(frame, UiCtlEditBoxProc 0x00888aa0, layer 0); case 100 return 7-entry class-info vtable PTR_FUN_00b96960).
Order (verified in FUN_0051b580, the GmChat edit builder):
1. Create the edit frame: FUN_0062bfc0(parent, flags, childIndex, proc=0x008852e0, userdata=0, L"name"). Edit style flags observed: 0x892e000 (full edit) and 0x2020000 (message variant). This create sends msg 4 then msg 9 to CCtlEdit, which installs base vtable and layers the UiCtlEditBoxProc renderer.
2. Optionally re-subclass for app logic: FUN_0062f150(frame, appProc, 0).
3. Set max length: FUN_00604aa0(frame, maxLen) e.g. 0x14. Set text: FUN_00604b00(frame, wchar*). Readonly via CtlEditSetReadOnly. Register keyboard/hotkey capture via FUN_0062e4e0 / FUN_0062ef00 as needed.
Warm-up: the 3 global GPU resources are built lazily on the first msg 5 the frame receives (auto-sent by the frame system on activation) — no explicit warm-up call needed, but the IME imagelist source texture @DAT_00b96c18 must be loadable. Default sizing from msg 0x15 is 6x3 (min==preferred); give the frame an explicit anchor-6 rect (FUN_0062F770) for a usable field.
- **Gotchas:** 1. msg 5 is a HARD assert (FUN_00487a80(0x3c), no-return) if statics already initialized (DAT_01081d78 != 0). The init is process-global, not per-frame — never trigger a second init; only one code path may build them.
2. msg 0x61 asserts (line 0xd0, no-return) when out ptr param_3 is null — caller MUST supply a 3-pointer out buffer.
3. msg 0x60 writes 2 pointers into the out buffer; msg 0x15 writes 4 floats (>=16 bytes). Undersized/null out buffers corrupt the stack.
4. Statics are GLOBAL and freed on msg 6 (destroy) which nulls DAT_01081d78/7c/80 for ALL edit boxes. Paint sub-passes 1/0xc/0xd do NOT null-guard the material/imagelist handle, so a paint racing a teardown can feed a 0/stale HGrMaterial into FrameContentAddImage. Keep at least one edit alive or avoid tearing down statics while any edit is visible.
5. IME paint (sub 0xc): with an active CHT/CHS IME, if EventCliGetImeMode high word is set and lang is not 2 or 3, it asserts UiCtlEditBox.cpp:0x9a. Only reachable with East-Asian IME state.
6. This proc has NO instance struct — do not attempt to read/write per-instance edit state through it; all live state is on the base CtlEdit instance reached via frame-id helper calls. Treating param_1 as an instance pointer past [1] is wrong.
7. Must be reached via the CCtlEdit wrapper (0x008852e0) so the base vtable (&LAB_00619c50) is installed first; installing the renderer on a frame without the CtlEdit base yields missing text/caret behavior and helper calls (CtlEditGetReadOnly) reading an uninitialized base.

### UiCtlLabeledEditProc  (EXE 0x00879230, confidence: high)

- **WASM:** Wrapper UiCtlLabeledEditProc ram:8106165b -> dispatcher TCtlInstance<CLabeledEdit>::MsgProc ram:81061743; IUi::CLabeledEdit::CtlMsgProc ram:81060b6b; OnFrameSize ram:81060f6e; GetLabelSize ram:81061576. EXE image base 0x00400000.
- **Struct:** Per-instance struct (heap, size 0x20; operator-new tagged "P:\Code\Engine\Controls\CtlInstance.h":0xaf; freed FUN_005acaeb(inst,0x20) at destroy):
 +0x00 vtable ptr = &PTR_FUN_009404a4 (CLayout-derived; single virtual fn = 0x004a0430, invoked once at end of create as (**vtbl)(inst+0x08)).
 +0x04 owning frame handle/id (set = *param_1 in create).
 +0x08..0x1f CLayout subobject (0x18 bytes; ctor FUN_006017e0, dtor FUN_00601810).
Instance pointer is NOT in the frame directly: it lives in a slot pointed to by the FrameMsgHdr, i.e. slot = *(param_1+8) (=param_1[2]); *slot = instance. Retrieval via TCtlInstance<CLabeledEdit>::Ptr = FUN_004a0440(param_1): asserts slot!=0 (FUN_00487a80(0x2b)) and *slot!=0 (0x2c), returns *slot.
Children (created in msg 9): child index 0 = the editable text field (proc FUN_0087d9a0); child index 1 = the caption label = CtlTextMl (proc FUN_006099f0, its own instance size 0x170 from CtlTextMl.cpp).
- **Messages:** msg = FrameMsgHdr word param_1[1]; param_2 = in/wparam; param_3 = out. Handled cases:
- 9 (OnFrameCreate): assert *slot==0 (FUN_00487a80(0xae)); operator-new instance (0x20); set vtable &PTR_FUN_009404a4; CLayout ctor FUN_006017e0; store into *slot; assert Ptr==new (0xb1); inst[1]=frame; create child0 = edit via FUN_0062bfc0(frame, (create[0])|0x300, 0, FUN_0087d9a0, 0, 0); create child1 = label via FUN_0062bfc0(frame, 0x300, 1, FUN_006099f0, create[1], 0); FUN_0060a400(label,0x10) (align/flags); FUN_0062ede0(label,0,0xffffffff); virtual init call (**vtbl)(inst+8).
- 0xb (OnFrameDestroy): Ptr; CLayout dtor FUN_00601810; FUN_005acaeb(inst,0x20); *slot=0.
- 0xc (Enable/Disable): child0=FrameGetChild(frame,0); FrameEnable(child0, wparam) FUN_0062c9c0; then base FUN_00647170.
- 0x31 (49, keyboard/nav): if wparam layout matches and code in (6,0xe) -> FUN_0062ee80(childframe,code,...) else base.
- 0x37 (55, OnFrameSize/layout): default text height FUN_0062d0e0; native size of label(child1) and edit(child0) via FUN_0062d2a0; vertically center by ratio _DAT_009407b0(=0.5); place LABEL with anchor/margins flag 0x94 and EDIT with flag 0x30 (FUN_0062e8a0).
- 0x38 (56, OnGetNativeSize): combine child native sizes -> out Coord2f (width = max, includes text height).
- {1,3,7,8,0xa,0xf,0x13,0x15,0x20,0x24-0x2a,0x2c,0x2e,0x32,0x34-0x36,0x3a-0x3f,0x44-0x46,0x4b,0x4c,0x4e,0x4f,0x52}: call Ptr (validate instance) then delegate to base frame proc FUN_00647170.
- 4,5,6: no-op then base.
- default (control-specific; first validates instance, asserts 0x149/0x2c on null):
   * 0x56..0x62 (13 msgs): FrameGetChild(frame,0)=edit; FUN_0062ef40(edit,msg,wparam,out) then base -> text get/set forwarded to edit child (0x57/0x58 get text+len, 0x59 char, 0x5a copy buffer, 0x5b-0x5e set colors, 0x62 set text, etc.).
   * 0x63 (99, GetLabelSize): child1=FrameGetChild(frame,1); FrameGetNativeSize(child1) via FUN_0062d2a0 -> out Coord2f. Public helper = UiCtlLabeledEditGetLabelSize FUN_00879700 (dispatches FUN_0062ef40(frame,99,0,out)).
   * 0x64 (100, SetLabelColor): child1=FrameGetChild(frame,1); CtlTextMlSetColor(child1, wparam=Color4b) = FUN_0060a2f0 -> FUN_0062ef40(child1,0x5e,color,0).
   * anything else -> base FUN_00647170.
- **Create recipe:** Create ONE frame whose FrameProc is 0x00879230; it self-builds its edit + label children on msg 9 (do NOT create children yourself).
- Primitive path: FUN_0062bfc0(parent, flags, childId, 0x00879230 /*proc*/, userdata, 0); the engine then sends msg 9 (FrameMsgCreate) to the new frame. The create-msg param block (*param_2) must be a 2-dword array: [0] = edit-child style flags (control ORs in 0x300), [1] = caption pointer/userdata for the CtlTextMl label child.
- Warm-ups/order: (1) frame gets created -> children auto-made (child0 edit FUN_0087d9a0, child1 label CtlTextMl FUN_006099f0 seeded with create[1]); (2) set caption via the label param at create or by messaging child1; (3) push edit content by sending edit text messages 0x56-0x62 (e.g. 0x62 SetText) to the LabeledEdit frame - they auto-forward to child0.
- Sizing: automatic. Layout runs on msg 0x37 (label anchored with margins flag 0x94, edit with 0x30, vertically centered). Query combined native size with msg 0x38; query just the label size with msg 0x63 (or helper FUN_00879700). No manual anchor sizing required, but you may still drive the outer frame via the standard anchor-6 setter FUN_0062F770.
- Destroy only by sending/allowing msg 0xb (CLayout dtor + free 0x20).
- **Gotchas:** 1) Instance-slot gate: almost every message calls TCtlInstance::Ptr (FUN_004a0440) or inline checks that ABORT via FUN_00487a80(0x2b / 0x2c / 0x149) if the frame's instance slot (*(param_1+8)) is null or *slot==0. Never send control messages (0x56-0x64, incl. 0x63 GetLabelSize / 0x64 SetLabelColor) to a frame not created through msg 9 of proc 0x00879230.
2) Double-init: msg 9 asserts *slot==0 (0xae) before allocating and asserts Ptr==new (0xb1); re-creating/initializing the same frame aborts.
3) Children must exist: 0x56-0x62 do FrameGetChild(frame,0) (edit); 0x63/0x64 do FrameGetChild(frame,1) (label). Both are created only in msg 9 - a partially built frame will have missing children and forwarding to a null child misbehaves/crashes.
4) 0x63 GetLabelSize writes an 8-byte Coord2f to the caller out-pointer; pass a valid 2-float buffer (helper FUN_00879700 zero-inits [0],[1] then dispatches). Passing a too-small/garbage out-ptr corrupts the stack.
5) 0x64 SetLabelColor forwards wparam as a Color4b const& to the label; must point to a 4-byte color, and only takes effect if the frame is a real LabeledEdit (routes to child1 msg 0x5e).
6) Teardown only via msg 0xb (CLayout dtor + free size 0x20). Freeing/leaking the frame without the msg-0xb path leaks/corrupts; the label child (CtlTextMl, 0x170) has its own internal asserts (e.g. FUN_00487a80(0x24b) on out-of-range index) reachable if its buffers are driven inconsistently.

### UiCtlDropListProc  (EXE 0x00878d90, confidence: high)

- **WASM:** ram:80e47ca4
- **Assertion file:** P:\Code\Engine\Controls\CtlDropList.cpp
- **Struct:** Styled UiCtlDropListProc holds NO per-instance state. The instance struct belongs to the base CtlDropList, allocated in base msg 9 (FUN_00615670) via FUN_0047f340("...CtlDropList.cpp",0x11c) and stored at *(p1[2]). Size 0x11c (284 bytes):
- +0x00 dword0: Item[] array data ptr (TArray). Each Item = 0x20 bytes.
- +0x04 dword1: item array capacity.
- +0x08 dword2: item count (queried by msg 0x5a).
- +0x0c dword3: array grow quantum (=8).
- +0x10..+0x4f: incremental-search wchar scratch buffer (up to 0x20 wchars); cleared by msg 0x3b.
- +0x50 dword0x14: search buffer length (used by keynav FUN_00615820).
- +0x54 dword0x15: enabled/default-compare field (init _DAT_009411d8; set by msg 0x60).
- +0x58 dword0x16: SELECTED index (init (count!=0)-1 => -1 when empty; msg 0x5c get, 0x61 set).
- +0x5c dword0x17: sort comparator fn ptr (0=none; set by msg 0x62; FUN_00615ad0 asserts 0x66 if used while 0).
- +0x60 dword0x18: LButton-down/click-tracking bool (set in base msg 0x24, consumed in 0x2e).
Per-Item (0x20 bytes): +0x00 item id (global counter DAT_00c0ac34); +0x04 string index/len (0xffffffff sentinel = no string); +0x08 user value/payload (msg 0x5e/0x63); +0x0c wchar string data ptr; +0x10 string len; +0x14 string capacity (bound); +0x18.. TArray tail.
Frame-level runtime state on the frame object itself: +0x50 (frame) incremental-search len, +0x58 (frame) live selection during nav, used by FUN_00615820.
- **Messages:** UiCtlDropListProc FUN_00878d90(FrameMsgHdr* p1, void* p2, void* out) — p1[0]=frameId, p1[1]=msg. Styled wrapper is STATELESS; it overrides render/layout only and chains everything else to the base CtlDropListProc FUN_006144e0 via FrameMsgCallBase (thunk_FUN_00647170). Cases it handles:

- msg 1 PAINT (face+arrow): only when *p2==0 (paint sub-pass 0). Picks face image by state: open(FUN_00614480/CtlDropListIsOpen!=0)->PTR@0x00b95cb8; else disabled(FUN_0062e2a0/FrameIsEnabled==0)->PTR@0x00b95ca8; else normal->PTR@0x00b95cb0. Draws face via FrameContentAddImageTemplate FUN_0062b8e0(frame, rect=p2+2, faceImg, &Coord2u{128,32}@0x00bf459c, 7,0,0,0). Then if FrameIsMouseFocus (FUN_0062e320)!=0 draws the dropdown arrow overlay via FrameContentAddImage FUN_0062b3e0(frame, arrowRect, arrowIcon PTR@0x0094ff68, &size{0x20,0x20}, texCoords, EGrTexOp=0xe, flags=0x100000, layer/HGrModel=p2[6], 0). Arrow rect = content rect p2[2..5] + insets {+3,+3,-3,-3} (DAT_00bf45b4/b8/bc/c0). If not mouse-focus, returns without base call.
- msg 4 INSTALL/vtable: *(code**)p2[3] = FUN_006144e0 (registers base CtlDropListProc as the next proc in the chain), returns (no base call). Base FUN_006144e0 on its own msg 4 chains to FUN_006123a0.
- msg 0xc, 0x25 INVALIDATE: FrameContentInvalidate FUN_0062bd40(frame) then base.
- msg 0x13 GET-POSITION/popup-anchor: FrameGetPosition FUN_0062d380(frame,0,&pos,0,0); out[1]=pos.x - 36.0*g_uiScaleX(_DAT_0094bc80); out[2]=(height-9.0-11.0)*g_uiScaleY(_DAT_009407b0); then base. (constants DAT_00bf45ac=36,45a8=9,45b0=11)
- msg 0x15 SIZE-QUERY: writes fixed Rect4f into out[0..3] = {14.0, 9.0, 36.0, 11.0} (DAT_00bf45a4/a8/ac/b0). Returns (no base).
- msg 0x5b DESCRIPTOR: copies 5 dwords from PTR_FUN_00b95c94 block into out[0..4], then falls through to base call.
- msg 0x64(100) TEXT-render: color = disabled(FrameIsEnabled==0)?0xffa0a0a0 : 0xffffffff; FrameContentAddText FUN_0062bb30(frame, text=*p2, len=p2[1], rect=p2+2, flags=p2[6]|4, 0xffffffff, p2[7]|0x10, color, p2[9], p2[10], layer=6). Returns (no base).
- default: FrameMsgCallBase -> base CtlDropListProc.

Base CtlDropListProc FUN_006144e0 (delegated, integer msg ids; Ghidra shows denormal floats): 1=paint bg quads, 4=install FUN_006123a0, 8=child-paint text, 9=OnFrameCreate build (FUN_00615670 parses double-null wchar list, allocs 0x11c instance), 0xb=destroy/clear items, 0x15=size, 0x20=key/char nav (FUN_00615820: Enter/Space=0x9/0x14/0x69 open, Down=0x1c/0x1e next, Up=0x1d/0x1f prev, printable=incremental search), 0x21=mouse, 0x24=LButtonDown (tracks +0x60 flag), 0x2c=hover, 0x2e=LButtonUp (open/close popup, commit selection, msg 0x68), 0x31=focus msgs, 0x36=destroy popup, 0x37=layout popup (FUN_0062f770 anchor), 0x38=measure popup width, 0x39/0x3b=clear, 0x3a=AddItem (dedupe, assert 0x332 on dup), 0x4c=rebuild ids, 0x56/0x57=styled sub-notify, 0x58=open popup, 0x59=toggle, 0x5a=GetItemCount(*p2=cnt@+8), 0x5c=GetSelectedIndex(*p2=idx@+0x58), 0x5d=GetItemText(idx, assert 0x24b/0x252), 0x5e=GetItemValue(idx->+8), 0x5f=open, 0x60=SetEnabledFlag(+0x54), 0x61=SetSelection(+0x58/0x16, msg 0x68, assert 0x2cf OOB), 0x62=SetSortComparator(+0x5c, triggers FUN_00615ad0 sort), 0x63=SetItemValue(idx->+8, assert 0x2f1/0x2fe), 0x64=FUN_0062bc20.
- **Create recipe:** 1) Create the frame with the STYLED proc as its FrameProc: FUN_0062bfc0(parent, flags, childIndex, proc=0x00878d90, userdata, 0) -> returns frame; *(frame+0xbc)=id. The framework auto-chains via the msg-4 install handshake: UiCtlDropListProc(0x878d90) -> base CtlDropListProc(0x6144e0) -> base frame proc(0x6123a0). Do NOT register the base proc directly if you want the styled skin.
2) The base allocates the 0x11c instance on msg 9 (OnFrameCreate). Populate items EITHER by passing a double-null-terminated wchar list as the msg-9 payload (*p2 = L"Item1\0Item2\0\0"; FUN_00615670 splits on nulls and calls FUN_00632d90 per entry) OR at runtime via msg 0x3a AddItem (checks for duplicates).
3) Set selection with base msg 0x61 (payload = index; 0xffffffff selects last). Query selection via msg 0x5c, item count via 0x5a, item text via 0x5d, item value via 0x5e/0x63.
4) Optional sort: set comparator with msg 0x62 (fn ptr) — this immediately runs FUN_00615ad0 quicksort.
5) Sizing: the control self-reports fixed size via msg 0x15 = Rect4f{14,9,36,11} (glyph metrics/padding); position/popup anchor computed in msg 0x13. Use the anchor-6 setter FUN_0062F770 for explicit pos/size if overriding.
WARM-UPS: styled paint needs the UI face/atlas materials + icon textures resident — face images PTR@0x00b95ca8/b0/b8 and arrow icon PTR@0x0094ff68 (Coord2u grid {128,32}@0x00bf459c). Load the styled UI image list/materials before first paint or the face/arrow won't render. Popup list child uses the selectable-list proc (0x00613850) — its sel-state must be allocated (flags 0x20128) when the popup opens.
- **Gotchas:** - Face paint (msg 1) only runs on sub-pass *p2==0; other sub-passes fall through to base — passing garbage p2 that is non-zero silently skips the face.
- msg 0x5b writes 5 dwords (0x14 bytes) into out; msg 0x15 writes 4 dwords; msg 0x64 text path dereferences p2[0,1,6,7,9,10] — undersized out/content buffers overflow/crash.
- CtlDropListIsOpen FUN_00614480 asserts 0x4f0 on frameId==0; FrameIsEnabled FUN_0062e2a0 asserts 0x6bc on 0; FrameIsMouseFocus FUN_0062e320 asserts 0x6b6 on 0. Never dispatch to this proc with a null frame id.
- Base build FUN_00615670: overlapping src/dst string copy triggers assert 0x171 (memmove guard); keep the items source buffer disjoint from the control's storage.
- Base index ops assert: GetItemText/Value OOB -> 0x24b/0x252; SetSelection OOB -> 0x2cf; SetItemValue OOB -> 0x2f1/0x2fe; AddItem duplicate id -> 0x332.
- Sort (FUN_00615ad0, via msg 0x62) asserts 0x66 if invoked while comparator field +0x5c is 0 — always set the comparator before requesting a sort.
- Popup open (base msg 0x37) asserts 0x238 if given an inverted/degenerate rect (requires rect.left<=right && top<=bottom).
- Keyboard-nav handler FUN_00615820 asserts 0x1c8 if its out-param (handled flag) pointer is null.
- No explicit paint-gate flag (unlike UiCtlBtnProc 0x40000); but the styled face/arrow require the styled image list/materials loaded — a null/unloaded image list yields blank/garbled paint rather than a clean skip. The arrow overlay only draws under mouse focus (msg 1 early-returns otherwise), which is expected, not a bug.

### UiCtlListProc  (EXE 0x00888910 (styled UiCtlListProc wrapper); base CtlListProc = 0x0061f740. WASM ram:80e47693. Both assert "P:\Code\Engine\Controls\CtlList.cpp"., confidence: high)

- **WASM:** ram:80e47693
- **Assertion file:** P:\Code\Engine\Controls\CtlList.cpp
- **Struct:** Instance (base CtlList, pointer stored at *(param_1[2]); frame handle cached at +0xb0):
+0x14 locked/disabled flag (nonzero => skip all interaction handlers)
+0x24 active drag/capture item id (0xffffffff = none)
+0x28 dirty/relayout flag
+0x2c drag-anchor Vec2 (via FUN_0060cbd0/FUN_0060cbc0)
+0x50 user-data/context ptr (msg 100)
+0x58 scroll offset = index of top visible row
+0x5c rows/columns array base (row stride 0x10 bytes; each entry = ptr,cap,len,widths)
+0x60 column count
+0x64 item (row) count
+0x68 column-widths growable array (FUN_00473880)
+0x70 selected/current row index (0xffffffff = none)
+0x74 pending-drag flag; +0x78/+0x7c drag-start row/field
+0x80/+0x84 press-anchor point
+0x88/+0x8c range-selection anchors (reset to -1 on clear)
+0x90 visible rows per page
+0xa8 field/column count used for bounds validation
+0xb0 TFrame* handle (all FUN_0062xxxx frame calls route through this)
Row/item struct (allocated by FUN_0061eee0): +0x18 state flags (&3 cleared => needs relayout), +0x1c/0x20/0x24/0x28 rect (defaults 0,0,0,0x40), +0x2c user value (flag 0x2), +0x30 (flag 0x10), +0x34/0x38 (flag 0x40), +0x3c item flags, +0x40 HGrModel id (flag 0x20), +0x44 text buffer ptr, +0x48 text capacity, +0x4c text length, +0x50 secondary buf (0x80 cap), +0x54 temp-length marker (0xffffffff idle).
- **Messages:** TWO-LAYER control. Styled outer proc FUN_00888910 handles only presentation msgs and forwards the rest to the installed base via thunk_FUN_00647170 (FrameMsgCallBase):
STYLED (0x00888910), dispatch on param_1[1]:
- 1 (Paint): if *param_2==1 (selection sub-pass) build Rect4f from param_2[2..5] (insets _DAT_00943280/_DAT_00943288 both 0.0f; top-1.0, bottom+1.0) then FUN_004a54f0(frame,&rect,4,1,0,param_2[7]=HGrModel) = ArtContentAddSelection (highlight quad). Other sub-passes -> base.
- 4 (InstallBase): *(param_2[3]) = FUN_0061f740 (base list proc becomes the base layer).
- 0x5e (GetRowTemplate/metrics): copies 7 dwords from PTR_FUN_00b96bac into param_3 = {word0=0x0087d5d0 rowProc, +4.0,+2.0,+4.0,+2.0,+2.0,+2.0 padding/spacing}. Base msg 0xa reads this to subclass the per-row renderer child.
- 0x69/0x6a/0x6b (DrawRowText normal/disabled/selected): FUN_0062bb30(frame,*p,p[1],p+2,p[6],0xffffffff,p[7]|0x10,color,p[9],p[10],6)=FrameContentAddText layer 6; color 0x69=0xfff0f0f0 normal, 0x6a=0xffa0a0a0 disabled-grey, 0x6b=0xffffeab8 selected-gold.
- default -> FrameMsgCallBase.
BASE (FUN_0061f740), instance ptr = *(param_1[2]); full protocol:
- 4 install factory FUN_006123a0; 8 measure/layout FUN_006217a0; 9 OnFrameCreate (alloc instance; assert 0xa3a if already set; flag 0x20000 gate selects vtable PTR_FUN_00a509cc variant, else plain FUN_0061ecc0); 0xa post-create (send 0x5e, if word0!=0 create child via FUN_0062cfc0 + FrameNewSubclass FUN_0062f150 = row renderer); 0xb destroy (calls instance vtbl+8).
- Input: 0x20 key-nav (arrows 0x1c-0x1f move sel FUN_00623240); 0x24 mouse-down begin drag/select; 0x25 clear selection (FUN_00623390); 0x26/0x27/0x28/0x2a hover -> FUN_00621dc0(0xd/0xe/0xf/0x10); 0x2c mouse-move hit+select; 0x2e mouse-up finalize -> send 0x61(select) or 99(activate); 0x2f wheel-scroll FUN_006231b0; 0x31 scroll cmd (subcases 7-0xb line/page/thumb); 0x3c/0x3f end-capture commit; 0x3d begin-capture; 0x3e FUN_006222d0.
- Data get/set: 0x56 AddItem/InsertRow (FUN_006224d0->FUN_0061eee0); 0x57 ClearAll; 0x58 SetColumn (FUN_006226a0); 0x59 InvalidateRow/redraw; 0x5a FUN_00622930; 0x5b HitTest point->row(param_2[2]),field(param_2[3]); 0x5c FUN_00622a90; 0x5d GetItemCount(*param_2=+0x64); 0x5f GetScrollOffset(+0x58); 0x60 GetSelectedIndex(+0x70); 0x61 SetSelection(index, fires event 0xb); 0x62 FUN_00622c20; 99 Activate(fires event 0x11); 100 SetUserData(+0x50); 0x65 FUN_00622e60; 0x66 EnsureVisible/ScrollToRow FUN_006231b0; 0x67 SetRowSubclass (FUN_0062cfc0+FrameNewSubclass FUN_0062f150); 0x68 SetSelectionNoEvent FUN_00623240; 0x69/0x6a/0x6b default draw FUN_0062bc20; 0x37 FUN_00621e90; 0x38 FUN_00622090; 0x39 relayout/invalidate; 0x3a text-buffer commit; 0x4c rebuild all HGrModel ids.
- **Create recipe:** 1. Create the frame with the STYLED proc as its class proc: FUN_0062bfc0(parent, flags, child, proc=0x00888910, userdata, 0) -> id stored at frame+0xbc. Flags MUST include 0x20000 to get the selectable-vtable list instance (PTR_FUN_00a509cc); without it you get the plain non-selection variant.
2. Framework auto-sends msg 4 -> styled installs base list proc FUN_0061f740 as the base layer.
3. NO image-list warm-up needed (unlike UiCtlBtnProc there is no case 5/6 imglist; DAT_010819cc is button-only). The only "warm-up" is the msg 0x5e row-template query which the base fires itself during msg 0xa (creates the per-row renderer child via rowProc 0x0087d5d0 + FrameNewSubclass 0x0062f150).
4. msg 9 allocates the instance (asserts if already present).
5. Configure columns first: send 0x58 (SetColumn) to establish +0x60 column count and +0xa8 field count BEFORE adding rows.
6. Add rows with 0x56 (AddItem); pass text ptr+len and/or HGrModel per item flags.
7. Selection: 0x61/0x68 set (with/without event), 0x60 get; scroll 0x66 EnsureVisible / 0x5f get offset; hit-test 0x5b.
8. Sizing: honor 0x5e template padding {4,2,4,2} and spacing {2,2}; per-row height flows from row rect (default 0x40) and content; anchor-6 pos/size via 0x0062F770. Selection highlight and row text are emitted by the styled proc during paint sub-passes, so the frame must actually be painted (parented + visible) to render.
- **Gotchas:** Asserts route through FUN_00487a80(code) (no-return) and FUN_0047f340(file,line):
- Double-create: msg 9 asserts 0xa3a if instance slot (*puVar6) already set.
- AddItem (FUN_0061eee0): row index param_2[6] >= item count(+0x64) => assert 0x124 (and 0x24b); text/len mismatch: cap!=0 with size==0 => 0x392, ptr!=0 with len==0 => 0x393; field id >= +0xa8 => 0x12f; buffer overlap => 0x171.
- Text commit case 0x3a: asserts 0x75c if row +0x54 != 0xffffffff (double commit); overlap 0x171.
- SetRedraw case 0x59: row index >= +0xa8 => assert 0x4c1.
- HitTest case 0x5b: field out of bounds => "Field out of bounds %s" assert 0x293; null column array(+0x5c==0) => assert 0x298.
- EnsureVisible case 0x66: row >= count => assert 0x9df.
- SetRowSubclass case 0x67: child frame handle 0 => assert 0x9e9.
- SetSelectionNoEvent case 0x68: row != 0xffffffff AND >= count => assert 0x9f2.
- Paint sub-pass 1 dereferences param_2[7] as HGrModel and the row renderer needs a valid text/model; sending 0x69-0x6b text draws before columns/rows exist yields empty/garbage. All interaction handlers early-out when +0x14 (locked) is nonzero -- a "dead" list usually means +0x14 set. Must pass flag 0x20000 at create or selection state/vtable is never allocated and selection msgs silently do nothing.

### UiCtlViewProc  (EXE 0x00878340, confidence: high)

- **WASM:** ram:80e584cc
- **Struct:** Per-instance struct: 0x34 (52) bytes, allocated in base msg 9 (FUN_0047f340("...CtlView.cpp",0x105)), pointer stored at *(param_1[2]) (frame userdata slot). Fetched by FUN_0060f120 (asserts 0x117 if null). Fields (dword indices):
- +0x00 (w0): style/flags word, init 0x20; set by msg 0x7ffffff6.
- +0x04 (w1): FRAME ID of this view container (all child lookups use FUN_0062cfc0(*(inst+4), idx)); init = *param_1.
- +0x08 (w2): init 1; also holds content data ptr set by msg 0x7ffffffa.
- +0x0c (w3): create-flag bit0 = param_1[4] & 1 (vertical/auto flag).
- +0x10..+0x18 (w4..w6): reserved/0.
- +0x1c (w7): pointer to 0xC8(200)-byte DRAG/RENDER sub-object, alloc'd in msg 0x3d (FUN_0047f340 ...,0x348), freed in destroy; init 0. Sub-object fields: +0x24 list head, +0xa4 list ptr, +0xa8/+0xac/+0xb0/+0xb4 counters, +0xb8/+0xbc drag pos, +0xc0/+0xc4 aux.
- +0x20 (w8): active drag/capture id, init 0xffffffff (-1 = none).
- +0x24 (w9): init 0 (drag origin/aux).
- +0x28 (w10): init 0.
- +0x2c (w11): viewport width (msg 0x7ffffff4 *param_2).
- +0x30 (w12): viewport height (msg 0x7ffffff4 param_2[1]).
Child frames by index (FUN_0062cfc0(frameId, idx)): idx1=content/child frame, idx2=horizontal scrollbar, idx3=vertical scrollbar. Inner content clip child uses proc FUN_0060f0f0 (routes msg 0x31 scroll to FUN_0062ee80).
- **Messages:** UiCtlViewProc @0x00878340 is a THIN STYLED SUBCLASS layered over the base CtlView proc FUN_0060d410 @0x0060d410. All real behavior lives in the base; the wrapper only handles two messages and forwards everything via thunk_FUN_00647170 (FrameMsgCallBase, msg=param_1[1]):

WRAPPER (0x00878340), msg = *(param_1+4):
- msg 4 (INSTALL/OnBuildChain): writes base proc into the chain slot: **(param_2+0xc)=FUN_0060d410; then if FUN_0087d980(1) (== (DAT_010819e8 & 1)==1, the global scroll style flag) -> **(param_2+0x10)=1 (enables styled scroll rendering). Then falls through to base call.
- msg 0x7ffffffd (GET-CLASS/STYLE DESCRIPTOR): *param_3 = &PTR_FUN_00bf4588 (static styled-view descriptor: defProc 0x0087d5d0, style tables 0x0094c614/0x00b95c50/0x00b95b64/0x00b95c8c, flags 0x80 & 0x20, metric 14.0f=scrollbar width), then calls base.
- everything else: straight passthrough to base chain.

BASE CtlView proc FUN_0060d410 (the actual protocol; instance obtained via FUN_0060f120 = *(param_1[2]), which ASSERTS 0x117 if null). Cases on msg:
- 5  (STYLE/COLOR INIT): if global DAT_00c0ac30==0 seeds default view colors/scale (_DAT_00c0ac1c..2c) then forwards.
- 9  (OnFrameCreate): allocates 0x34-byte instance (assert 0x104 if already set), inits fields, validates style flags (assert 0x19c if both 0x10000+0x20000 set; assert 0x19d if both 0x8000+0x40000 set), creates inner clip/content child frame with proc FUN_0060f0f0 (flags 0x300), and if create-userdata block present creates a child from {flags|0x300, proc, userdata}.
- 0xb (OnDestroy): frees +0x1c drag sub-object (200 bytes) and the 0x34 instance; clears slot (assert 0x117 if null).
- 0x13 (HITTEST/FOCUS): returns/redirects to scrollbar child (idx3 vert, idx2 horiz) or content child.
- 0x2f (MOUSEWHEEL): FUN_0060ca40 wheel delta -> scroll vert scrollbar (idx3/2) by +/-inst[0].
- 0x31 (SCROLL COMMAND): sub-cmd in param_2[2]: line-up/line-down (+/- step), page up/down (FUN_0060f4d0 page size), set-abs (FUN_0060a400); also routed by inner proc FUN_0060f0f0.
- 0x37 FUN_0060e420 (layout/paint helper); 0x38 (MEASURE/min-size query -> clamps into param_2[2] rect); 0x3c (RELEASE CAPTURE: if *param_2==inst+0x20 drag id, clear +0x1c/+0x20); 0x3d (BEGIN DRAG: allocs 0xc8 drag/render state at +0x1c, seeds pos +0xb8/+0xbc, size, fires 0x45); 0x3e FUN_0060ec30 (drag move); 0x3f FUN_0060ee70 (drag end); 0x45 FUN_0060e210 (recompute/position scrollbars).
- default: if msg==0x21 or msg>0x55, re-dispatch to content child via FUN_0062ef40 then forward.
PRIVATE HIGH RANGE (CtlView public API, msg>=0x7ffffff2):
- 0x7ffffff2 SetContent/attach child (assert 0x480 on fail); 0x7ffffff3 scroll/get vertical (idx3); 0x7ffffff4 SetViewportSize (+0x2c=w,+0x30=h; toggles scrollbar visibility via FUN_006302c0); 0x7ffffff5 FUN_0060f0b0; 0x7ffffff6 set inst+0 word; 0x7ffffff7 scroll horizontal (idx2); 0x7ffffff8 recreate inner content frame (destroy old id, create new with *param_2 flags|0x300); 0x7ffffff9 layout scrollbars into rect (assert 0x412 if rect min>max); 0x7ffffffa set content data ptr (inst+8) + invalidate; 0x7ffffffb GET vertical scroll info -> param_3[0..3] (assert 0x158 if out null); 0x7ffffffc GET content-frame id -> param_3[0] (assert 0x3fa if null); 0x7ffffffe GET horizontal scroll info (idx2, assert 0x158); 0x7fffffff GET child/content frame id (idx1, assert 0x3ea if null).
- **Create recipe:** UiCtlViewProc is registered as a FRAME SUBCLASS PROC (function-pointer create arg), not called directly. Canonical creation (verified in FUN_005634a0 @0x005634a0, the styled-list-view builder):

  local_18.face  = has_scroll_style ? 0 : 0x8000;   // create-userdata block, 3 dwords
  local_14.proc  = &LAB_0056f2d0;                    // child content proc
  local_10.data  = 0;
  frame = FUN_0062bfc0(parent, 0x20380, 0, FUN_00878340 /*UiCtlViewProc*/, &local_18, 0);
  FUN_0062ede0(frame, 0, 1);                          // set clip/child index (optional)

Create primitive is the standard FUN_0062bfc0(parent, flags, childIdx, proc, userdata, 0) -> id at frame+0xbc.
- FLAGS: 0x20380 (= 0x20000 scroll/clip | 0x300 std child | 0x80 view). Some callers use 0xa000. Add 0x20000 (needs-scroll) / 0x18000 combos per style but NEVER combine 0x10000+0x20000 or 0x8000+0x40000 (base asserts 0x19c/0x19d in msg 9).
- USERDATA is an optional 3-dword block {childFlags, childProc, childUserdata}; base msg 9 auto-creates that content child as {childFlags|0x300, childProc, childUserdata}. Pass 0 for a bare view.
- ORDER: create fires msg 4 (wrapper installs base FUN_0060d410 into chain + reads global style flag DAT_010819e8) then msg 9 (allocates instance, builds inner content frame FUN_0060f0f0 + scrollbars). Only after msg 9 are content/scroll messages safe.
- Alternative: layer over an existing view frame with FrameNewSubclass FUN_0062f150(frame, FUN_00878340, priority).
- WARM-UP: styled path needs the global UI style/material system up (descriptor 0x00bf4588 -> proc 0x0087d5d0 references style/image tables) and DAT_010819e8 initialized; same warm-up as other Ui* styled controls (UiCtlBtn/Slider/Page). Also call FUN_005634a0-style helpers create scrollbar children (idx2 horiz / idx3 vert via FUN_0062cfc0) and issue 0x7ffffff4 SetViewportSize to size the viewport.
- SIZING: use anchor-6 setter FUN_0062F770 for the outer frame pos/size, then send 0x7ffffff4 (viewport w/h at inst+0x2c/+0x30) and 0x45 to recompute scrollbars.
- **Gotchas:** 1) msg 9 asserts 0x104 if instance already installed (*param_1[2]!=0) -> NEVER double-create / double-install UiCtlViewProc on one frame. 2) Any content/scroll message before OnFrameCreate: FUN_0060f120 asserts 0x117 on null instance -> must let msg 4 then msg 9 fire first. 3) Mutually-exclusive style bits: msg 9 asserts 0x19c if BOTH 0x10000 & 0x20000 create flags set, asserts 0x19d if BOTH 0x8000 & 0x40000 set. 4) GET messages require non-null out (param_3): 0x7ffffffb & 0x7ffffffe assert 0x158, 0x7fffffff asserts 0x3ea, 0x7ffffffc asserts 0x3fa. 5) msg 0x7ffffff9 (scrollbar layout) asserts 0x412 if rect is not normalized (x0>x1 or y0>y1). 6) msg 0x7ffffff2 asserts 0x480 if inner child create fails. 7) Wrapper msg 4 MUST run to write FUN_0060d410 into the chain slot (**(param_2+0xc)); if you register UiCtlViewProc without a proper subclass chain, the base view proc is never installed and all view logic is dead. 8) Styled descriptor 0x00bf4588 / global flag DAT_010819e8 must be initialized (UI style/material warm-up) or the styled scroll-render branch (**(param_2+0x10)=1) references uninitialized style tables. 9) Destroy frees +0x1c (200 bytes) then +0x34 instance; if the drag sub-object was manually detached this double-frees.

### UiCtlTextSelectableProc  (EXE 0x00885620, confidence: high)

- **WASM:** ram:80e0b8d5
- **Assertion file:** P:\Code\Engine\Controls\CtlTextSelectable.cpp
- **Struct:** BASE CtlTextSelectable instance = 0x2c bytes / 11 dwords (freed as 0x2c in case 0xb; reached via FUN_00618aa0 = **(FrameMsgHdr+8)). Init from case 9:
+0x00 [0]: owner frame id (HFrame) = *hdr.
+0x04 [1]: selected flag (0/1). init 0. GetSelected(0x5a), SetSelected(0x57), Clear(0x56). Styled proc reads via FUN_00617870.
+0x08 [2]: selectable flag. init 1. GetSelectable(0x59), SetSelectable(0x5d). Styled reads via FUN_00617840.
+0x0c [3]: text buffer ptr (wchar_t*). init 0.
+0x10 [4]: buffer bookkeeping. init 0.
+0x14 [5]: text length (chars incl null) = strlen+1.
+0x18 [6]: 0x80 style/max constant.
+0x1c [7]: pending-select sentinel; -1 = none (SetText sets -1, SetTextAndSelect sets 0).
+0x20 [8]: state/style flags; bit 0x10 set if frame flag 0x4000 present at create.
+0x24 [9]: extra data int A / index (init -1). SetExtraData(0x5c)/Get(0x58).
+0x28 [10]: extra data int B / paired float (init 0).
Styled wrapper FUN_00885620 holds NO own instance (stateless; reads everything through base messages/accessors).
- **Messages:** RESOLUTION: exe_addr 0x00885620 (was "?"). WASM name UiCtlTextSelectableProc @ ram:80e0b8d5 -> assertion "P:\Code\Engine\Controls\CtlTextSelectable.cpp" (single xref @ EXE 0x00a504b0 used only by the BASE proc FUN_00617df0). Matched the STYLED wrapper by logic: the WASM wrapper installs a base vtable in case 4 and reimplements paint sub-passes 0x60/0x61/0x62 with theme colors (0xffa0a0a0 disabled, 0xffffeab8 selected, 0xfff0f0f0 unselected); the only EXE fn with that exact structure/switch is FUN_00885620.

TWO-LAYER MODEL. The STYLED OUTER proc FUN_00885620 overrides only a handful of messages; everything else falls through FrameMsgCallBase (thunk_FUN_00647170) to the BASE control proc FUN_00617df0 (the real CtlTextSelectable) that it installs as the class vtable.

== STYLED WRAPPER FUN_00885620 (param_1=FrameMsgHdr, param_1[1]=msg, param_2=in, param_3=out) ==
- case 4  (install base/vtable): **(param_2+0xc) = FUN_00617df0  (installs BASE CtlTextSelectableProc as working control).
- case 0x15 (size query): writes natural size 1.0f x 1.0f (rect {1.0,0,1.0,DAT_00943278}); asserts null out in base.
- case 0x60 (paint sub-pass: primary text): color = FrameIsEnabled(FUN_0062e2a0)? (GetSelected(FUN_00617870/msg0x5a)? 0xffffeab8 : 0xfff0f0f0) : 0xffa0a0a0; FrameContentAddText FUN_0062bb30(frame, x@+0, y@+4, txt@+8, layerflags@+0x18 |4, -1, flags@+0x1c |0x10, color, +0x24, +0x28, 6).
- case 0x61 (paint sub-pass: secondary/shadow text): same color logic; FUN_0062bb30 with flags@+0x1c |0x11.
- case 0x62 (paint sub-pass: selection highlight): if (hdr flag *param_2 &0x20): hover = GetSelectable(FUN_00617840/msg0x59) && FrameIsMouseFocus(FUN_0062e320) ? 1:0; sel = GetSelected(FUN_00617870/msg0x5a); ArtContentAddSelection FUN_004a54f0(frame, rect@+0x1c, 5, sel, hover, 0). Else no-op.
- default: FrameMsgCallBase thunk_FUN_00647170 -> BASE proc.

== BASE CtlTextSelectableProc FUN_00617df0 (full protocol; instance via FUN_00618aa0 = **(hdr+8)) ==
- case 4: install own base vtable = FUN_006123a0.
- case 8 (layout/render): measures & positions text; forwards paint to children via FUN_0062efc0(0x60/0x61); dispatches self 0x62 via FUN_0062ef40.
- case 9 (OnFrameCreate): assert slot *(hdr[2])==0 else assert(0x61); alloc instance (FUN_0047f340 tagged .cpp,0x62); init struct; copy initial label into buffer; if frame flag 0x4000 -> instance[8]|=0x10; send 0x4c; assert(0x84) len sanity.
- case 0xb (destroy): free text buffer, zero, free 0x2c-byte instance (FUN_005acaeb(inst,0x2c)); clear slot.
- case 0xc (attach/enable): FrameClearFlag 0x40; if !selected notify 7.
- case 0x24/0x2c/0x2e (mouse enter/leave/hover): toggle hover flag 0x2000, notify 8/9.
- case 0x25 (mouse-left): FrameRedraw.
- case 0x38/0x39 (focus in/out).
- case 0x3a (activate/enter): commit select, notify 10.
- case 0x4c: registration hook.
- case 0x56 SetUnselected/Clear: assert currently selected(0x1a5); instance[1]=0; redraw.
- case 0x57 SetSelected: assert not-already-selected(0x1b2) AND selectable(0x1b7); instance[1]=1; redraw.
- case 0x58 GetExtraData: out[0]=inst[9](+0x24), out[1]=inst[10](+0x28); assert null(0x1c4).
- case 0x59 GetSelectable: out=inst[2](+8); assert null(0x1ce).
- case 0x5a GetSelected: out=inst[1](+4); assert null(0x1d7).
- case 0x5b GetText: copy label out; assert null(0x1e0).
- case 0x5c SetExtraData: inst[9]=in[0]; inst[10]=in[1]; redraw.
- case 0x5d SetSelectable: inst[2]=in; redraw; if now-unselectable & selected notify 7.
- case 0x5e SetText: realloc/copy buffer if changed; inst[7]=-1 (no select change); assert overlap(0x171).
- case 0x5f SetTextAndSelect: realloc/copy buffer; inst[7]=0; redraw.
- case 0x60/0x61: base paint text (FUN_0062bb30, gray 0xff808080 if disabled).
- case 0x62: base selection/tooltip art (FUN_0062b2d0).
- **Create recipe:** CREATE (styled selectable text row):
1. Create frame with the create primitive FUN_0062bfc0(parent_frame, flags, child_id, proc=FUN_00885620, userdata, label_wstr). For an UNSTYLED row pass proc=FUN_00617df0 directly. (See panel builder FUN_0088dfb0 which spawns text children with FUN_0062bfc0(parent,0,idx,FUN_00610c40,text,...) then applies color via FUN_00604aa0 — same pattern; substitute proc FUN_00885620 for a selectable.)
2. On create the frame receives msg 4 (styled proc installs base FUN_00617df0 as vtable) then msg 9 (base allocs the 0x2c instance and copies the label). Provide the label as the create text arg OR SetText afterward.
3. Optional configuration AFTER create only: SetSelectable msg 0x5d, SetText msg 0x5e, SetTextAndSelect msg 0x5f, SetExtraData msg 0x5c. Toggle selection with SetSelected 0x57 / Clear 0x56.
4. Selection state read back with GetSelected 0x5a / GetSelectable 0x59 (or accessors FUN_00617870 / FUN_00617840, both take the frame id).
SIZING: control reports natural 1x1 (case 0x15); real geometry comes from parent layout / content auto-measure (case 8) or the anchor-6 pos/size setter FUN_0062F770. Text auto-measures during case 8.
WARM-UPS: none image-list-based. Paint sub-pass 0x62 uses ArtContentAddSelection (FUN_004a54f0) which needs the theme selection material loaded; on a bare/unthemed frame the highlight is a no-op (not a crash). Ensure the frame is in a paint-enabled tree. If instance[3] (text ptr) is 0, paint renders nothing (safe) — set text before first paint if a label is wanted.
ORDER: parent -> FUN_0062bfc0(...FUN_00885620...) -> (msg4/msg9 auto) -> optional 0x5d/0x5e/0x5c/0x57 -> paint.
- **Gotchas:** 1. DOUBLE-CREATE ASSERT: base case 9 asserts FUN_00487a80(0x61) if the instance slot *(hdr[2]) is already non-null. Never send OnFrameCreate twice / never reuse a live instance slot pointer.
2. NULL-INSTANCE ASSERT (primary gate): FUN_00618aa0 asserts (line 0x74) when the instance ptr is null. ANY get/set/paint message (0x56-0x62, 0x58/0x59/0x5a/0x5b, and the styled 0x60/0x61/0x62 which call GetSelected/GetSelectable) sent BEFORE case 9 completes will crash. Control must be fully created first.
3. SetSelected (0x57) double-guard: asserts if already selected (0x1b2) AND asserts the row is selectable (0x1b7). Only call when currently unselected AND selectable, else assert.
4. Clear (0x56): asserts if the row is NOT currently selected (0x1a5). Don't clear an unselected row.
5. NULL-OUT-PARAM asserts on every getter: 0x15 needs non-null out (0x103); 0x58->0x1c4; 0x59->0x1ce; 0x5a->0x1d7; 0x5b->0x1e0. Always pass a valid out buffer.
6. TEXT-BUFFER OVERLAP assert (0x171) in SetText paths (case 9, 0x5e, 0x5f): the new source string must not alias/overlap the existing buffer region; passing an aliased/overlapping pointer trips it.
7. LENGTH-SANITY asserts (0x84 at create, 0x24b/0x428 during layout): the pending-select sentinel inst[7] must not exceed text length inst[5]; corrupting [5]/[7] via raw writes asserts.
8. Styled paint 0x62 depends on theme selection art (FUN_004a54f0/ArtContentAddSelection): missing material yields no highlight but does not crash; base 0x62 uses FUN_0062b2d0 similarly.
9. Styled wrapper is stateless — do not expect an instance struct on FUN_00885620; all state lives on the base instance reached through the frame id.

### IUi::UiCtlLabelTextProc  (EXE NOT a distinct function in Gw.exe 06-14 (inlined/refactored). WASM: ram:80fdc7f6. EXE-equivalent construction = styled CtlText base FUN_00610c40 (0x00610c40) + FrameSetDefaultTextStyle FUN_0062f4b0 (0x0062f4b0) invoked with style=3 at each creation site (concrete example: FUN_008a88c0 @ 0x008a88c0 does FrameSetDefaultTextStyle(frame+4,3) then creates FUN_00610c40 text children). Nearest surviving tiny auto-style text frame-proc in this build: FUN_00889450 @ 0x00889450 (same shape: call base FUN_00610c40, then on msg 9 set style) but style 0x11 via CtlTextSetStyle FUN_0059fee0 (msg 0x5b), not the label's style 3. Raw text base under FUN_00610c40 = CtlTextProc FUN_006123a0., confidence: medium)

- **WASM:** ram:80fdc7f6 (IUi::UiCtlLabelTextProc(FrameMsgHdr const&, void const*, void*)); referenced only from dispatch table table:00002fac (theme/registration table).
- **Assertion file:** Proc body itself has NO assertion (it never allocates). Helper assertions: FrameSetDefaultTextStyle -> P:\Code\Engine\Frame\FrApi.cpp line 0xb7f (EXE 0x00a51724). Base CtlText create -> P:\Code\Engine\Controls\CtlText.cpp lines 0x18a/0x18b (buffer/index asserts 0x171/0x24b). No P:\Code\Gw\Ui\Controls\UiCtlLabelText.cpp string exists in Gw.exe 06-14 (confirms the proc is inlined; sibling files like UiCtlTextShy.cpp DO exist).
- **Struct:** The label proc is STATELESS -- it allocates nothing and stores nothing at *(param_1[2]); there is no per-instance UiCtlLabelText struct. All state lives in the base CtlText prop allocated by the base proc FUN_00610c40 on its own msg 9. That CtlText::CProp (from FUN_00610c40 create, file CtlText.cpp lines 0x18a/0x18b) is a ~0x40-byte struct: +0x00 vtable (&PTR_FUN_00a50108), +0x08 owner/model ptr, +0x0c/+0x14 text buffer ptr + resolved length (-1 = unresolved), +0x18 color (Color4b), +0x1c text height (float), +0x20 model/list ptr, +0x28 element count, +0x30 4-byte default text-style block (compared/written by base cases 0x5f/0x60). The frame object itself carries the default text style set by FrameSetDefaultTextStyle at frame+0x194 (CText subobject) with an invalidation submsg target at frame+0xa8 (per WASM FrameSetDefaultTextStyle).
- **Messages:** Extremely thin passthrough subclass over the styled CtlText base. Dispatch is on param_1[1]=msg:
- msg 4 (INSTALL/subclass base): writes the base proc pointer into *(param_2+0xc) (EXE idiom: *(code**)param_2[3] = FUN_00610c40, exactly as UiCtlTextShyProc FUN_0087f0d0 does), then chains to base. No RTTI/instance work of its own.
- msg 9 (ONFRAMECREATE): calls FrameSetDefaultTextStyle(*param_1 /frameId/, 3) = EXE FUN_0062f4b0(id,3). This forces the frame's default text style-flags to 3. It does NOT allocate its own instance/prop; instance creation is delegated to the base CtlText proc.
- msg 5,6,7,8 and ALL OTHER messages: no special handling; forwarded verbatim to the base proc via FrameMsgCallBase (SetText/SetColor/GetText/GetCodedText, size-query 0x15, paint 1, destroy 0xb, style/text messages 0x56-0x62, etc. are all serviced by the base CtlText control FUN_00610c40 -> FUN_006123a0).
Sibling for contrast: UiCtlTextHeaderProc (ram:811e887d) is the same shape but msg9 -> FrameSetDefaultTextStyle(id,8) and additionally overrides size-query 0x15 (uses FrameGetDefaultTextHeight, tests style bit 0x20000, halves height). UiCtlLabelTextProc has NO such size override -- purely base + style 3.
- **Create recipe:** Because the 06-14 EXE has no standalone proc, build a label text frame directly:
1. Warm-up: NONE beyond the always-present text/font subsystem. Text controls need NO image list or materials (unlike styled buttons which require DAT_010819cc). No selectable-list state alloc.
2. Create the frame: id = FrameCreate FUN_0062bfc0(parent, flags, childId, FUN_00610c40, userdata, labelName). Typical label flags observed at real sites: 0x100 (plain), or 0x82000/0x84000 for interactive/anchored label rows (FUN_008a88c0). The proc arg FUN_00610c40 is the styled CtlText base (it self-installs raw CtlTextProc FUN_006123a0 on its own msg 4).
3. IMMEDIATELY force the label style: FrameSetDefaultTextStyle(id, 3) = FUN_0062f4b0(id, 3). This is precisely what UiCtlLabelTextProc automates on OnFrameCreate. (Header text = style 8; style value is a text style-flags bitfield, label=0x3.)
4. Set content: text via CtlTextSetText (base control msg), color via CtlTextSetColor, optional CtlTextSetGrEffects. Height auto-derives from FrameGetDefaultTextHeight.
5. Size/position: text auto-sizes to font; place with the anchor-6 pos/size setter FUN_0062F770, or per-frame FUN_0062f5a0. Order matters: create -> FrameSetDefaultTextStyle(3) -> SetText -> position.
If you instead register a proc, replicate the WASM proc: case 4 -> *(code**)param_2[3]=FUN_00610c40; case 9 -> FUN_0062f4b0(*param_1,3); default -> FrameMsgCallBase.
- **Gotchas:** - NO image-list / material requirement (pure text control) -- none of the styled-button image-list null crashes apply.
- Base MUST be installed: the proc forwards nearly everything via FrameMsgCallBase; if the frame is created without a valid base proc (msg 4 install skipped) the passthrough calls a null base -> crash. Always create with FUN_00610c40 (or ensure the label proc runs first).
- FrameSetDefaultTextStyle FUN_0062f4b0 asserts (FUN_00487a80(0xb7f), file P:\Code\Engine\Frame\FrApi.cpp) if frameId==0 -> never pass a 0/invalid id.
- Base CtlText create path branches on frame style bit 0x100000 (FUN_00610c40 msg 9): the 0x100000 path allocates the full prop (CtlText.cpp line 0x18a), the other path (line 0x18b) uses a lighter alloc via FUN_00610800; creating with mismatched style flags changes which prop is built.
- Text buffer writes in the base assert on overlapping copy (FUN_00487a80(0x171)) and on index-out-of-range (FUN_00487a80(0x24b)); always set text through CtlTextSetText, never poke the +0x0c buffer directly.
- Unlike TCtlInstance controls, this proc does NOT assert 'instance already set' -- it owns no instance -- so double-registration is silent but the base's own OnFrameCreate DOES assert if its prop pointer is already non-zero.

### UiCtlTip  (EXE 0x00878950, confidence: high)

- **WASM:** ram:80e09f09 (IUi::UiCtlTipProc(FrameMsgHdr const&, void const*, void*)); public API: FrameTipRegister ram:809a6c79, FrameTipSetPosition ram:809a6ffe, FrameTipUnregister ram:809a71c9, FrameTipIsRegistered ram:809a6b14
- **Struct:** FrameMsgHdr (param_1, dword array — the standard control message context):
 +0x00 [0] frame id/handle (uint) — arg to all FUN_0062b2d0/b8e0/b290/bd40/bd80 draw & invalidate calls
 +0x04 [1] message id (dispatch selector)
 +0x08 [2] pointer to per-instance payload (TCtlInstance<CTip> data)
 +0x0c [3] wparam
 +0x10 [4] frame style/flags dword; bit0 (&1) = tip active/registered gate (enables paint-icon sub-draw, hit-test, and alternate size-query height)
 +0x14 [5] subclass chain index (consumed by base thunk FUN_00647170)

Instance payload (*(param_1[2])):
 +0x00 4-byte state/value word. Read as uint in paint (top byte >>0x18 = active/alpha enable; byte[3] also selects arrow image variant); written as float by SetValue(0x7fffffff). Effectively the tip's tracked active/content value.

Frame instance object (as seen through base thunk FUN_00647170): +0xa8 = proc/handler array base (0xc-byte entries: proc ptr, +4 userdata ptr, +8 msg id), +0xb0 = handler count.

Paint ctx (param_2 float* for msg 8): [0]=paint flags(1=thumbnail,2=arrow,4=icon); [7..10]=content rect l,t,r,b; [0xb],[0xc]=icon frame-index selectors.
HitTest ctx (param_2 for msg 0x17): [0]=x,[1]=y,[2]=right,[3]=bottom,[4]=uint* result (write 2=hit).
SizeQuery out (param_3 for msg 0x15): 4 dwords (size/rect).
- **Messages:** Signature: void UiCtlTipProc(FrameMsgHdr* hdr /*param_1*/, void* body /*param_2*/, void* out /*param_3*/). Dispatch is on hdr[1]=msg. This is a SUBCLASS/decorator proc: unhandled messages fall through to thunk_FUN_00647170 (chain-to-base = walk frame's proc array at inst+0xa8, count inst+0xb0, using chain index hdr[5], skipping create(9)/destroy(0xb)). Note: create(9) and destroy(0xb) are NOT handled here — the framework allocates/frees the instance; this proc only decorates.

Handled messages:
- msg 5  = OnInit/first-use (lazy resource alloc): if global tip image list DAT_010819d0==0, create it via FUN_0062d790(0,7,0x12,dims{0x10,0x10,0x10},size=0x80,PTR_DAT_00bf4594,3) and store in DAT_010819d0; then chain to base. If DAT_010819d0!=0 on this path -> assert FUN_00487a80(0x35) (line 53) NO-RETURN. Image list is a single process-global shared by ALL tips.
- msg 6  = OnShutdown: free image list FUN_0046f9b0(DAT_010819d0); DAT_010819d0=0; chain to base.
- msg 8  = OnPaint/render content. Reads state word local_8=*(uint*)hdr[2]. Uses frame handle *hdr[0] for all draw calls. body(float*) is the paint ctx: body[0]=paint flags; body[7..10]=content rect (l,t,r,b); body[0xb],body[0xc]=icon-frame selectors; margins from _DAT_009413c8/_DAT_00937ed0/_DAT_009413d8. Three sub-draws: (a) if (paintflags&1) && (state high byte !=0): build texture from state via FUN_00679b10/FUN_0065efa0 and blit thumbnail quad FUN_0062b2d0; (b) if (paintflags&2): draw arrow/pointer image FUN_0062b8e0 choosing PTR_DAT_00bf4590 vs PTR_DAT_00bf458c by state byte3; (c) if (paintflags&4) && (frameflags[+0x10]&1): draw icon from image list FUN_0062b290(frame,rect,DAT_010819d0,frameIdx,2,0) then chain to base & return.
- msg 0x15 (21) = OnSizeQuery: writes preferred size rect (4 dwords) into out(param_3) from globals _DAT_00944e00/_DAT_00944e04; 4th dword = _DAT_00944e04, or _DAT_00945988 if frameflags[+0x10]&1. Returns without chaining.
- msg 0x17 (23) = OnHitTest: only if frameflags[+0x10]&1. body[0]=x, body[1]=y, body[2]=right, body[3]=bottom, body[4]=ptr to result dword. Computes inset rect (margins _DAT_00937ed0/_DAT_009413d8); if pointer inside, writes 2 to *(uint*)body[4] (hit = tip region). Returns without chaining.
- msg 0x2b (43) = notify: if body[1]&4, FUN_0062bd80(*hdr[0],4) (post/clear a redraw request flag). Falls through to base.
- msg 0x7fffffff (INT_MAX = SetValue sentinel): if *(float*)hdr[2] != *(float*)body, write it and invalidate FUN_0062bd40(*hdr[0]), then chain to base. (Same slot as paint's state word, written as float.)
All other msgs: pass straight to base chain proc.
- **Create recipe:** UiCtlTip is a SUBCLASS decorator, not a standalone frame — it is layered on top of a host frame's proc chain. High-count call sites (FrameTipRegister has 123 xrefs) confirm the pattern:
1. Create/have a host frame: FUN_0062bfc0(parent, flags, childId, hostProc, userdata, 0) -> id at *(frame+0xbc). (Observed flags at these sites e.g. 0x24000 / 0x5.)
2. Layer the tip proc onto it: PUSH proc=0x00878950 then FrameNewSubclass FUN_0062f150(frameId, ..., 0x00878950, tipUserdata). The high-level wrapper is FrameTipRegister(frameId, msgMask, UiCtlTipProc, userdata, payloadSize) (WASM ram:809a6c79) — this both attaches the subclass and sizes the instance payload.
3. Warm-up: the shared tip image list DAT_010819d0 is created lazily on the FIRST msg 5 (OnInit) via FUN_0062d790 (128px, 3 frames of 16x16). It is process-global and shared by every tip — do not create per-instance.
4. Position the tip: FrameTipSetPosition(frameId, a, b, Coord2f) (WASM ram:809a6ffe / EXE anchor-6 setter family 0x0062F770).
5. Set/refresh the tracked value: send msg 0x7fffffff with a float body (updates instance[0] and invalidates).
6. Teardown: FrameTipUnregister(frameId) (WASM ram:809a71c9); global image list is released on msg 6 (FUN_0046f9b0, DAT_010819d0=0).
Ordering: host frame must exist and its base create(msg 9) must have run (allocating the instance payload) BEFORE this subclass receives paint/hittest/setvalue — those all dereference hdr[2].
- **Gotchas:** 1. Double-init assert: msg 5 asserts FUN_00487a80(0x35) (UiCtlTip.cpp line 53) NO-RETURN if global image list DAT_010819d0 is already non-zero when the create branch runs. The image list is a single shared global — only one tip may own its creation; re-entrant/duplicate init crashes.
2. Null instance payload: msg 8 (paint) and msg 0x7fffffff (SetValue) dereference *(param_1[2]) (read as uint / written as float). If the subclass is attached without the base frame create(9) having allocated the instance payload, these read/write a bad pointer. Always register through FrameTipRegister with a nonzero payload size so the framework allocates it.
3. Icon-draw before image-list ready: paint sub-draw (c) (paint flag &4 with frameflags[+0x10]&1) calls FUN_0062b290(...,DAT_010819d0,...). If paint with bit2 fires before msg 5 created the list, it passes a NULL image-list handle. Ensure msg 5 has run (or gate icon paint on active flag) before enabling bit2.
4. Active-flag gating: OnHitTest (0x17), the icon paint path, and the alternate size-query height ALL require frameflags[+0x10]&1. If the frame isn't marked tip-active, hit-testing silently returns no hit (tip appears dead) — not a crash but a common 'tip not responding' trap.
5. Base-chain asserts: unhandled messages route to thunk_FUN_00647170, which asserts on a dead/invalid frame id (line 0x256/0x221), an out-of-range chain index param_1[5] (line 0x223), or a corrupt handler array (line 0x24b). Feeding this proc a message with a stale frame id or bad chain index is fatal.
6. msg 8 thumbnail path builds a transient texture (FUN_0065efa0) and frees it (FUN_0046f850) each paint — depends on state-word high byte being nonzero; a garbage/uninitialized instance word can trigger a bogus texture build.

### UiCtlHint (UiCtlHintProc)  (EXE 0x0087d230, confidence: high)

- **WASM:** ram:80f067f5 (IUi::UiCtlHintProc(FrameMsgHdr const&, void const*, void*))
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlHint.cpp (confirmed via WASM string at ram:00108503 = "../../../../Gw/Ui/Controls/UiCtlHint.cpp")
- **Struct:** This control is a STATELESS SUBCLASS DECORATOR proc. It does NOT allocate a per-instance heap struct (no case 9/OnFrameCreate handler, no *(param_1[2]) instance alloc) unlike the styled button/edit controls. All state lives in (a) the frame message header and (b) module-static shared image lists.

FrameMsgHdr received as param_1 (6 dwords, standard for this UI system):
  +0x00 param_1[0]  u32  frameId (HFrame id; *param_1)
  +0x04 param_1[1]  u32  msg id (switch selector)
  +0x08 param_1[2]  ptr  arg-a (per-msg)
  +0x0C param_1[3]  ptr  arg-b (per-msg)
  +0x10 param_1[4]  u32  frame STYLE FLAGS (the control's persistent state):
                          bit0 (0x1) = interactive / has close(x) hit-region; enables taller size-query and the case-0x17 hit-test
                          bit1 (0x2) + bit2 (0x4) = image/severity tier select (standard vs warning vs error background+icon)
  +0x14 param_1[5]  u32  subclass index (consumed by base dispatcher FUN_00647170)

Module-static SHARED image-list handles (HFrameImageList; class-level, one set for ALL hint instances):
  DAT_010819dc  s_closeStandardImgList   (assert-guarded, err 0x36)  -- WASM DAT_005a8dac
  DAT_010819e0  s_imageList              (standard hint icon)        -- WASM DAT_005a8db0
  DAT_010819e4  sm_imageList / warning   (assert-guarded, err 0x37)  -- WASM DAT_005a8db4
Background textures selected from PTR_DAT_00bf45dc / 00bf45e4 / 00bf45e8 by the same bit1/bit2 tier.

Paint arg (case 8) param_2 float/dword array of interest:
  param_2[0]  = paint pass flags (bit1=draw background, bit2=draw icon)
  param_2[7]  = start of bg destination rect (passed as param_2+7)
  param_2[9]  = frame right edge, param_2[10] = frame bottom edge (icon anchored bottom-right, 16x16, inset ~2/10 px)
  param_2[0xb],[0xc] = highlight state (==2 picks alt image frame index)
Hit-test arg (case 0x17) param_2: [0..3]=query rect, param_2[4]=ptr to output part-id (written =2 on hit).
- **Messages:** switch(param_1[1]); default -> tail-calls base proc thunk_FUN_00647170 (FrameMsgCallBase). Handled cases:

case 5  = CLASS STATIC-RESOURCE INIT (create shared image lists, sent once):
   Asserts DAT_010819dc==0 (err 0x36 s_closeStandardImgList) and DAT_010819e4==0 (err 0x37) — double-init aborts.
   Creates 3 HFrameImageList via FUN_0062d790 (FrameImageListCreate: fmt=0, texOp=7, flags=0x12, min{0x10,0x10}, max{0x20,0x10}, tex ptr, count=2):
     DAT_010819dc = tex PTR_00bf45e0 ; DAT_010819e0 = tex PTR_00bf45ec ; DAT_010819e4 = tex PTR_00bf45ec.
   Then falls through to base.
case 6  = CLASS STATIC-RESOURCE TEARDOWN: FUN_0046f9b0 (HandleCloseSafe) on all 3 lists, zeroes them, then base.
case 8  = PAINT / CONTENT BUILD:
   if (*param_2 & 2): pick bg texture by tier flags (param_1[4] bit1/bit2 -> PTR_00bf45e8/e4/dc) and FUN_0062b8e0 (FrameContentAddImageTemplate) into a 0x20x0x20 rect.
   if (*param_2 & 4) AND (param_1[4] & 1): pick icon list by tier (DAT_010819e4/e0/dc), compute bottom-right 16x16 rect from param_2[9]/[10] minus offsets (_DAT_009413c8/00944930/009413d8), frame index = (param_2[0xb]==2 || param_2[0xc]==2)?1:0, FUN_0062b290 (FrameContentAddImage).
   Does NOT call base (break falls to trailing base call anyway).
case 0x15 = SIZE-QUERY: writes 4 dwords to param_3 = preferred min/max size constants; height/width uses taller variant (_DAT_00944228) when param_1[4]&1 set (interactive), else default (_DAT_00945190). Returns without base.
case 0x17 = HIT-TEST (point -> sub-part): only if param_1[4]&1. Tests query point (param_2[0..3]) against the bottom-right close-icon rect; on hit writes *(u32*)param_2[4] = 2 (close-button part id). Returns without base.
case 0x2b = STATE-CHANGE NOTIFY: if (param_2[1] & 4): FUN_0062bd80 (FrameContentInvalidate id,4) then base — repaints when the relevant state bit changes.
(no 0x56-0x6a get/set handlers; those fall to base.)
- **Create recipe:** UiCtlHint is applied as a FrameNewSubclass DECORATOR over an existing (usually text) frame — not created as a standalone frame. Verified pattern from create site FUN_0086c190 (the char-name restriction warning icon on UiCharSelect):

1. Ensure CLASS STATIC INIT happened once: dispatch msg 5 to the proc (or rely on the class registrar) BEFORE any instance paints, so DAT_010819dc/e0/e4 are non-null. This is guarded to run exactly once (re-run without a msg-6 teardown asserts).
2. Create a base frame: FUN_0062bfc0(parent, flags=0, childId=2, baseProc=FUN_00610c40 [text/label proc], userdata=0, name=L"TxtCharRestrict").
3. (optional) name/layout the parent: FUN_0062f1a0(parent, L"UiCharSelect").
4. Layer the hint proc: FUN_0062f150 (FrameNewSubclass)(frameId, proc=0x0087d230, subclassIndex=2).
5. FUN_0062f5a0(frameId, 1) to enable the subclass.
6. Set the frame STYLE FLAGS (header dword[4]) for behavior:
     bit0 (0x1) -> interactive: reserves taller size and enables the close/dismiss hit-region + icon draw.
     bit1|bit2 -> severity tier (standard / warning / error) choosing bg texture and icon image list.
   In FUN_0086c190 these bits are driven by the field's validation state (bit set via |2 when restricted).
7. Feed text/content through the base text proc (FUN_00611320 sets the text object); the hint proc only decorates with the icon/background — it renders nothing itself if the base frame has no content.
Sizing: intrinsic. Size-query (0x15) returns a small fixed footprint (~10-12 px, taller ~26 px when interactive bit0 set); background template is 32x32, icon is 16x16 anchored bottom-right.
- **Gotchas:** 1. DOUBLE STATIC-INIT ABORT: sending msg 5 while DAT_010819dc or DAT_010819e4 are already non-null hits FUN_00487a80(0x36)/(0x37) — a non-returning assert (P:\...\UiCtlHint.cpp). Never re-run class init without first sending msg 6 (teardown) to null the handles.
2. PAINT-BEFORE-INIT / NULL IMAGE LISTS: if an instance receives msg 8 (icon path: *param_2&4 with param_1[4]&1) before the class static-init (msg 5), DAT_010819dc/e0/e4 are 0 and FrameContentAddImage (FUN_0062b290) is handed a null HFrameImageList. Warm-up: guarantee msg 5 ran once first.
3. IMAGE-LIST CREATE VALIDATION: FUN_0062d790 asserts 0xa47-0xa4b if size struct is zero-width/zero-height or max<min. The hardcoded {0x10,0x10}/{0x20,0x10} sizes satisfy this; don't feed alternate degenerate sizes.
4. NOT A STANDALONE FRAME PROC: it is a subclass layered over a base proc and always tail-calls FrameMsgCallBase. It never allocates a per-instance struct and never handles case 9/0xb — do NOT read an instance pointer from *(param_1[2]); there is none. Using it as a frame's primary proc with no underlying base means no text renders.
5. HIT-TEST OUTPUT WRITE: case 0x17 writes *(u32*)param_2[4] = 2. Only reached when param_1[4]&1; the frame system supplies param_2[4], but a hand-rolled 0x17 dispatch must pass a valid output-pointer at param_2[4] or it writes through garbage.
6. SIZE-QUERY BUFFER: case 0x15 writes 4 dwords into param_3 — caller must provide a 4-dword (Rect/Coord2f pair) buffer.
7. TIER FLAG COUPLING: bits1/2 in param_1[4] must correspond to an initialized image tier; the bg-texture and icon-list selectors are independent branches keyed on the same bits, so an inconsistent flag/list state draws the wrong or a null icon.

### CGroupHeaderFrame  (EXE 0x0087ddc0, confidence: high)

- **WASM:** ram:81192c89
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlGroupHeader.cpp (verified — literal read from data adjacent to vtable PTR_FUN_00b96070 at 0x00b96100). Instance is allocated with the site string "P:\Code\Gw\Ui\Controls\UiCtlInstance.h" (0x60 bytes) — that is the alloc/assert site, not the control's own cpp.
- **Struct:** Two structs.

(A) Message frame passed to FrameProc FUN_0087ddc0(undefined4 *param_1, int param_2, uint *param_3):
  param_1[0] (+0x00) = frame handle (the TFrame the proc is bound to)
  param_1[1] (+0x04) = message id (switch selector)
  param_1[2] (+0x08) = pointer to the instance-slot holder; *(param_1[2]) = the instance pointer.
  param_2 = wParam (int)  ; param_3 = out/lParam (uint*)
  FUN_004b4a10(param_1) = resolve instance: asserts 0x72 if *(param_1+8)==0 (slot null), 0x74 if **(param_1+8)==0 (instance null); returns **(param_1+8) = instance ptr.

(B) UiCtlInstance<CGroupHeaderFrame>, 0x60 (96) bytes, allocated via FUN_0047f340(UiCtlInstance.h,0x60) on msg 9:
  +0x00 = vtable ptr = &PTR_FUN_00b96070
  +0x04 = owning frame handle (set to param_1[0] right after alloc; read as *(instance+4) by every method/helper)
  +0x08 = puVar8[1] zero-initialized at alloc; remaining bytes to 0x60 are the generic UiCtlInstance slack — CGroupHeaderFrame keeps NO extra per-instance state here (all open/text state lives in the two child frames).

vtable PTR_FUN_00b96070 (only non-stub slots; 0x004a0430/0x00480070/0x0047f330 are the generic no-op/base stubs):
  +0x18 = 0x00480070 (base OnCreate, called after +0x1c on msg 9)
  +0x1c = 0x0087e090 (self-build ctor/init — creates the two children)
  +0x30 = 0x0087e190 (msg 0x13 handler: returns child0 checkbox in *out)
  +0x68 = 0x0087e1b0 (msg 0x31 handler: child-notification router → toggles open, hover highlight)

Child frames (created by self-build, addressed by child index via FUN_0062cfc0(frame,index)):
  index 0 = "CheckOpen"  expand/collapse checkbox (proc FUN_008867f0; base proc UiCtlBtnProc 0x00877e60, style |= 0x30000)
  index 1 = "TxtName"    caption text button (proc CtlTextBtnProc 0x00616c00, style 0xa0000)
- **Messages:** Outer FrameProc FUN_0087ddc0 switches on param_1[1]. Four control-specific msgs are handled inline and RETURN early (never reach the generic dispatcher); everything else falls through to the TCtlInstance dispatcher FUN_008783b0 (which maps engine msg → instance vtable slot).

Inline (control-specific) messages:
  0x56 GetIsOpen  → child0(checkbox); state = FUN_0060f4b0(child) [which sends btn-msg 0x58 to the button]; writes *param_3 = state. ASSERT 0x4e if param_3==NULL.
  0x57 GetText    → child1(caption). Reads param_3 as a growable wchar TArray {[0]=data ptr,[1]=size,[2]=capacity, elem=2 bytes}: len=FUN_006143f0(caption); grows array to len+1, then FUN_00616bb0(caption, data, cap) copies caption text out. ASSERT 0x57 if param_3==NULL.
  0x58 SetIsOpen  → child0(checkbox); FUN_0060f490(child, param_2) [sends btn-msg 0x57 with value param_2] sets checked/open state.
  0x59 SetText    → child1(caption); FUN_006177b0(caption, param_2) sets caption wchar text. ASSERT 0x74 if param_2==NULL (text ptr).

Fall-through to FUN_008783b0 (engine msg → vtable slot; only slots wired for this control matter):
  1  paint      → vtable+8  (base/no-op here; actual paint is per-child)
  9  create/OnFrameCreate → outer proc first allocs instance (ASSERT 0x5f if slot already set), sets vtable, stores instance, sets instance+4=frame; dispatcher then calls vtable+0x1c (0x0087e090 self-build) then vtable+0x18 (base OnCreate) with create-params at *(param_2+0x10).
  0xb destroy    → dispatcher calls vtable+0x24 (base dtor); outer proc then FUN_005acaeb(instance,8) frees it and nulls the slot. ASSERT 0x72/0x74 if slot/instance already null.
  0x13 → vtable+0x30 (0x0087e190): *out = child0 (checkbox) — "default/hit child" query.
  0x15 size-query → vtable+0x34 (base).
  0x31 → vtable+0x68 (0x0087e1b0) child-notification router. param_2 = notify record {+4=source, +8=code, +0xc=data}:
        source 0: code 8 → FUN_0062ee80(frame,7,1,0) (hover-in highlight); code 9 → FUN_0062ee80(frame,7,0,0) (hover-out).
        source 1 (checkbox): code 5 & *data==0 → FUN_0052b720(child0) (click feedback); code 9 → FUN_0062ee80(frame,8,data,0) (open-state changed → bubble to parent).
  All other cases (3,7,8,0xc,0xf,0x20,0x24…0x52) route to base-class stubs.
- **Create recipe:** The group header is a COMPOSITE that self-builds its two children on msg 9 — you create only the container.

1) Create the container frame:
   id = FUN_0062bfc0(parent, flags, childId, proc=0x0087ddc0, userdata, name=L"...")
   - proc MUST be 0x0087ddc0. childId is your own frame id.
   - userdata becomes *param_2 (first dword of create-params) and is forwarded verbatim as the caption text button's userdata (its text/label source). Pass your caption-text config/pointer here.

2) On msg 9 the self-build (0x0087e090) runs automatically and:
   - creates child0 "CheckOpen" (checkbox, proc FUN_008867f0) — the +/- expand glyph;
   - creates child1 "TxtName" (caption, proc CtlTextBtnProc 0x00616c00, style 0xa0000, userdata = your forwarded value);
   - anchors caption: FUN_0059fee0(cap,{-0x1548}), FUN_0060a2d0(cap,{-0x2a21}), FUN_00617790(cap,0x10) (align), FUN_0062f4b0(cap,8) (anchor);
   - if frame style flag 0x2000 set → FUN_0062ede0(cap,0,-1);
   - applies visual style by name via FUN_0062f1a0(frame, L"UiCtlGroupHeader"), OR L"UiCtlGroupHeaderMobile" when FUN_0049b9e0(0x71) (mobile flag) is set;
   - if frame style flag 0x1000 set: hides checkbox (FUN_0062fcb0) + FUN_0062c9c0(cap,0) (compact/no-toggle variant) and returns;
   - else FUN_0062ccd0(frame,0x30,0) → default fixed height 0x30 (48 px).

3) After create, drive it with the inline messages:
   - SetText:  send 0x59 with wParam = wchar_t* label (non-NULL).
   - SetIsOpen: send 0x58 with wParam = 0/1.
   - GetIsOpen: send 0x56 with out ptr; GetText: send 0x57 with a wchar TArray.

Warm-ups / ordering:
   - The "UiCtlGroupHeader"/"UiCtlGroupHeaderMobile" style must be registered before create or FUN_0062f1a0 has nothing to apply (children render unstyled). This is the primary material warm-up.
   - The checkbox glyph image list DAT_01081d70 is created lazily by the child proc on its own msg 5 (FUN_0062d790(0x11,7,0x1a,...) using atlas DAT_00b96b94/DAT_00b96b9c) — no manual image-list setup needed, but the atlas/textures must be loaded.
   - Do NOT manually create children with indices 0/1 — the control owns them; use 0x56–0x59 to interact.
   - Sizing: width follows anchors/parent; height is fixed 0x30 unless style 0x1000 (compact). Send all get/set only AFTER msg 9 has run.
- **Gotchas:** 1. Double-create: sending msg 9 when the instance slot is already non-null → ASSERT 0x5f (FUN_00487a80). Never re-create over a live frame id.
2. Use-before-create: any of 0x56/0x57/0x58/0x59 (via FUN_004b4a10) before msg 9 built the instance → ASSERT 0x72 (slot ptr null) or 0x74 (instance null).
3. 0x56 GetIsOpen with out param_3 == NULL → ASSERT 0x4e.
4. 0x57 GetText with param_3 (TArray) == NULL → ASSERT 0x57. param_3 must be a valid {data,size,cap} array (elem size 2 bytes); it is grown/reallocated in place — passing a bogus array corrupts the heap (guarded overlap check asserts 0x171).
5. 0x59 SetText with param_2 (text ptr) == NULL → ASSERT 0x74.
6. Destroy 0xb with slot/instance already null → ASSERT 0x72/0x74.
7. Style not registered: if L"UiCtlGroupHeader"/Mobile theme isn't loaded, self-build still runs but FUN_0062f1a0 applies nothing — no crash, but checkbox/caption render invisible/unstyled (looks like a silent failure).
8. Checkbox image-list singleton DAT_01081d70: child msg 5 asserts 0x54 if it re-inits while already set, and its free path (msg 6) asserts 0x75 if DAT_01081d70 is already 0 — only relevant if you drive the child proc directly; via normal frame lifecycle it is safe.
9. Children are addressed by index 0/1 through FUN_0062cfc0; if the self-build was short-circuited by style 0x1000 (checkbox hidden), GetIsOpen/SetIsOpen still target child0 which exists but is hidden — toggling has no visible effect.



## 4. Completion Catalog - remaining controls deep RE (2026-07-01)

Second swarm (80 agents) resolved the unmapped addresses and deep-cataloged the remaining discovered controls. 80 entries; 75 resolved to a real EXE FrameProc, 7 flagged as non-frame (base template / utility / resource manager).

### UiCtlInputGuide  (EXE 0x0047f330, confidence: medium)  [NOT a frame proc]

- **WASM:** ram:8134178d
- **Assertion file:** P:\Code\Gw\Ui\Game\GmInputGuide.cpp (EXE string @0x0094c160); base template asserts against ..\Ui\Controls\UiCtlInstance.h
- **Struct layout:**

CCtlInputGuide instance (reconstructed from EXE handlers FUN_00525090/150/290 + WASM proc; word offsets):
  +0x00  base/vtable slot (TCtlInstance base)
  +0x04  FrameID (frame handle; passed to FUN_0062cfc0 to fetch child frames 1&2, to FUN_0062f9a0/FUN_0062f7f0 for layout); WASM uses inst[1] as the invalidate target
  +0x08  ptr to render/definition buffer (FUN_00525290 writes **(inst+8) and *(*(inst+8)+4)); WASM inst[2] also read as EInputGuideContext id
  +0x0C  orientation/layout bool (0/1: horizontal vs vertical; set by FUN_00525090 when aspect test flips, triggers FUN_0062bd40 relayout)
  +0x10  InputGuideDefinition* (WASM inst[4] = result of GetInputGuideDefinition(ctx,subctx))
  +0x14  sub-context / EInputGuideContext arg2 (WASM inst[5])
Message-param block (param_2): +0x04 scalar (layout position seed), +0x10/+0x14 = size floats (w,h) used by the aspect test in FUN_00525090.
Static layout constants (.rdata): _DAT_0094c21c=90.0, _DAT_0094c220=134.0, _DAT_0094c224=175.0, scale _DAT_0094c228, origin _DAT_009453e8.

- **Message protocol:**

Two-layer dispatch (NOT the classic switch FrameProc).

TOP FRAME (child id 0x52, name L"InputGuide"): created in FUN_004e0aa0 @0x004e1036 with proc = 0x0047f330. That address is a 3-byte RET-0 stub (bytes C2 00 00; Ghidra names it guard_check_icall / the CFG nop). So the top-level "InputGuide" frame is a PASSIVE CONTAINER: its frame proc does nothing on any msg (paint/size/create/destroy all no-op). No warm-up FrameMsg calls are issued after creation except a tooltip set.

REAL CCtlInputGuide behavior = static message-handler tables in .rdata next to the GmInputGuide.cpp tag, dispatched indirectly through the instance (the WASM TCtlInstance<CCtlInputGuide>::FrameMsg pattern). Table A @0x0094c140 (8 slots, noop default = FUN_004a0430):
  [0]=FUN_00525090  measure / aspect-ratio decision (picks horizontal vs vertical layout, writes orientation bool at inst+0x0C, invalidates on change)
  [1..3]=noop
  [4]=FUN_00525150  PAINT/LAYOUT: gets child frames 1 and 2 via FUN_0062cfc0(frame,1|2), positions them via FUN_0062f9a0/FUN_0062f7f0 using orientation bool and a scale (val-_DAT_009453e8)*_DAT_0094c228
  [5]=FUN_00525290  INIT/populate render data: **(inst+8)=_DAT_0094c224; *(*(inst+8)+4)=_DAT_00940ee8
  [6..7]=noop
Table B @0x0094c210: [0]=FUN_005252c0, [1..2]=noop, then layout constants (floats 90.0, 134.0, 175.0 at 0x0094c21c/0x220/0x224).

WASM proc (semantic reference, IDs differ from EXE): msg 0x46 -> FrameContentInvalidate(inst); msg 0x47/0x48/0x49 -> read context id (inst[2]) and sub-context (inst[5]), iVar=GetInputGuideDefinition(ctx,subctx), store inst[4]=iVar, FrameContentInvalidate(inst[1]); all other msgs -> delegate to TCtlInstance<CCtlInputGuide>::FrameMsg base (handles create/alloc/free/paint/size 4/9/0xB/1/0x15).

- **Create recipe:**

Exact EXE sequence (FUN_004e0aa0 @0x004e1036), args to create primitive FUN_0062bfc0(parent,flags,child,proc,userdata,name):
  1. h = FUN_0062bfc0(gameRootFrame, flags=0, child=0x52, proc=0x0047f330 (nop stub), userdata=0, name=L"InputGuide")
  2. tip = FUN_007c3bc0(0x136d0)   ; fetch help/tooltip text resource
  3. FUN_0062fab0(h, tip)          ; attach tooltip
  No size-query, no style set, no FrameMsg warm-ups for the top frame.
To reproduce a working InputGuide you must ALSO instantiate the CCtlInputGuide child controls that carry the real handler tables (0x0094c140 / 0x0094c210) and feed a valid EInputGuideContext via the 0x47/0x48/0x49-class messages so GetInputGuideDefinition populates inst+0x10 before paint. The two child frames (indices 1 and 2 fetched by FUN_00525150) must exist or the paint handler dereferences null child handles.

- **Crash gotchas:**

- Do NOT treat 0x0047f330 as a callable frame proc: it is the CFG nop (RET 0). Calling it as a paint/size proc yields a silent no-op, not the InputGuide render; there is no case-1 paint or case-9 alloc at the top frame.
- The base TCtlInstance template (UiCtlInstance.h) asserts (ErrorAssertion) if: frame payload[2] (parent/def ptr) is null (line 0x72), or *payload is null (line 0x74), or GetInputGuideDefinition fails (~0x73). Creating the control without a resolved InputGuideDefinition/context trips these asserts.
- FUN_00525150 (paint) blindly gets child frames 1 and 2 (FUN_0062cfc0(frame, 1|2)); if those children were not created it calls FUN_00487a80(0x105) (fatal) when the returned handle is 0.
- FUN_00525290 dereferences **(inst+8): inst+0x08 must point to an allocated render buffer before this init handler runs, else null-deref.
- Orientation bool at inst+0x0C is toggled by an aspect-ratio test using live screen scale (_DAT_009407b0); feeding zero/negative size in param_2+0x10/+0x14 skews the layout branch.


### GmCtlColorPick  (EXE 0x004dd0a0, confidence: high)

- **Assertion file:** P:\Code\Gw\Ui\Game\Controls\GmCtlColorPick.cpp (class-descriptor string at 0x00946734, referenced from 0x004dd538 inside the proc). NOTE: the per-instance alloc assert in case 9 uses the generic base "P:\Code\Engine\Controls\CtlInstance.h" — normal, the instance is a base CtlInstance; the control identity comes from the descriptor blob.
- **Struct layout:**

GmCtlColorPick is a swatch-grid (color palette) container control. It owns a base CtlInstance (allocated case 9, size 0x38 = 56 bytes / 14 dwords) plus one child swatch frame per color (child proc FUN_004dccc0, instance size 0x40).

CONTAINER instance (0x38 bytes), fields as [dword_index]=+offset:
[0]  +0x00  vtable = &PTR_FUN_009404a4 (shared CtlInstance vtable)
[1]  +0x04  parent/owner frame handle (= *param_1, the frame this proc is bound to)
[2]  +0x08  (base CtlInstance bookkeeping, set by FUN_006017e0)
[8]  +0x20  selected/highlighted swatch index (init 0; -1 sentinel = none; read by msg 0x56, written by 0x57 and by FUN_004dd7e0 tail)
[9]  +0x24  swatch COUNT (= cfg[3]); loop bound for child creation and for FUN_004dd7e0
[10] +0x28  child control-class token (= FUN_0062d8b0(0x11,7,0x192,...)); target of per-swatch dispatch FUN_0062ef40(child,0x61,...)
[11] +0x2c  cfg[2] (first-swatch extra param -> local_60 when idx==0 in FUN_004dd7e0)
[12] +0x30  color transform / alpha MODE flag (= cfg[1]); 0 -> FUN_005ac620(color,0x20000000,..) premultiplied path, else FUN_005aa640(color)
[13] +0x34  COLUMNS per row (= cfg[4]); grid width used in hit-test math (case 0x37)

CONSTRUCT payload (case 9, *param_2 -> 6-dword config struct 'cfg'):
cfg[0] = pointer to color-value array (one entry per swatch)
cfg[1] = mode flag            -> +0x30
cfg[2] = first-swatch param   -> +0x2c
cfg[3] = swatch count         -> +0x24
cfg[4] = columns per row      -> +0x34
cfg[5] = initial selected idx (passed to FUN_004dd7e0 as selected index)

CHILD swatch instance (FUN_004dccc0, 0x40 bytes): [0]vtable, [1]parent, [9]+0x24 color value (=*param_2), [0xc]+0x30=_DAT_0094654c scale, [0xd]/[0xe]+0x34/+0x38 animation state, +0x3c anim velocity. Child base proc = FUN_004dd620 (installed via case 4). Child paints/animates a single swatch button (msg 0x61 sets its color; msg 0x45 runs a spring animation on hover-scale).

- **Message protocol:**

Switch on msgframe[1] (param_1[1]). Instance ptr = *(param_1[2]); dispatcher tail = thunk_FUN_00647170(frame,payload,out).

CLASS lifecycle:
- case 5  CLASS_REGISTER: registers the control class via FUN_0062d790(0x11,7,0x192,&meta,&meta2,&DESC@0x0094672c,4) and stores the global class token in DAT_00c01648. Must run once before any construct.
- case 6  CLASS_RELEASE: FUN_0046f850(DAT_00c01648).

INSTANCE lifecycle:
- case 4  INSTALL_PARENT: empty (no parent-proc override; derives directly from base template).
- case 9  CONSTRUCT: asserts (0xae) if instance already set; allocs base CtlInstance (0x38), stores it into *param_1[2]; copies cfg[]-> +0x24/+0x2c/+0x30/+0x34; creates the child class token (+0x28); loops idx 0..count-1 creating a child swatch frame each via FUN_0062bfc0(parentFrame,0,idx,FUN_004dccc0,childToken,0); then FUN_004dd7e0(cfg[0],cfg[5]) to seed colors+selection; asserts 0xb1 if the just-alloc'd instance isn't returned by FUN_004a0440.
- case 0xb DESTRUCT: reset vtable, FUN_0046f850(childToken @+0x28), FUN_00601810, free instance (FUN_005acaeb, 0x38), clear *param_1[2].

DATA get/set (control-specific, 0x56+):
- case 0x56 GET_SELECTED: *param_3 = *(inst+0x20)  (returns selected swatch index).
- case 0x57 SET_SELECTED: param_2 = new index; asserts 0x1d6 if index >= *(inst+0x24) (count); updates the child highlight (FUN_0062cfc0 -> FUN_0052b720), stores +0x20, falls through to dispatcher.
- case 0x58 SET_COLORS: FUN_004dd7e0(payload[0]=color array, payload[1]=selected index) -> rebuilds/recolors every swatch and re-highlights the selected one.

LAYOUT / INPUT / PAINT:
- case 0x31 SCROLL/SET-PROP: if payload[2]==7(float-bits) -> +0x20 = payload[1]; FUN_0062ee80(frame,7,val,0).
- case 0x37 HIT-TEST: converts a normalized (x,y) in payload into a grid cell using columns(+0x34) and count(+0x24); iterates child cells via FUN_0062cfc0/FUN_0062f770 to resolve the swatch under the point.
- case 0x38 MEASURE/PAINT: FUN_00602900 measure combine; writes measured (w,h) back to *payload[2].
- default: standard null/uninit asserts (0x149, 0x2c) then dispatcher.
- Passthrough-to-base (FUN_004a0440 then dispatcher): 1,3,7,8,10,0xc,0xf,0x13,0x15,0x20,0x24-0x2a,0x2c,0x2e,0x32,0x34-0x36,0x3a-0x3f,0x44-0x46,0x4b,0x4c,0x4e,0x4f,0x52.

CHILD swatch proc FUN_004dccc0 messages: case 4 sets style |= 0xe0000 and base proc FUN_004dd620; case 9 allocs 0x40 instance, creates an inner primitive (LAB_00879f40) with FUN_0062f5a0(.,2)/FUN_0062ede0; case 0x61 SET_COLOR (color + two extra floats -> +0x20/+0x28/+0x2c, FUN_0062bd40 invalidate); case 0x45 hover spring-scale animation; case 0x37/0x38 hit/measure; case 0xb free 0x40.

- **Create recipe:**

1. One-time class registration: ensure DAT_00c01648 is populated by sending CLASS_REGISTER (msg 5) to the proc once at UI init (the game does this during control-table setup). Without it the child class token cannot resolve.
2. Create the container frame with the standard control primitive:
   frame = FUN_0062bfc0(parentFrame, flags, childId, FUN_004dd0a0 /*proc*/, userdata, 0)
   (flags per the palette's desired layout; childId is its slot under the parent.)
3. Drive lifecycle by dispatching to the frame:
   a. msg 4 (install parent) — no-op here.
   b. msg 9 (construct) with payload -> pointer to a 6-dword cfg struct:
      cfg[0]=color array ptr, cfg[1]=mode(0=premult/alpha,1=opaque), cfg[2]=first-swatch param,
      cfg[3]=swatch count, cfg[4]=columns per row, cfg[5]=initial selected index.
      This auto-creates 'count' child swatches (FUN_004dccc0) and seeds colors.
4. Runtime:
   - Change palette contents: msg 0x58 with {colorArrayPtr, selectedIdx}.
   - Change selection programmatically: msg 0x57 with new index (< count).
   - Read current selection: msg 0x56 -> out.
5. Sizing: the control measures itself in msg 0x38 from swatch cell size (0x20x0x20 base, see FUN_004dd7e0 local_40/local_44 = 0x20) times columns(+0x34) x ceil(count/columns) rows; let the parent layout query it rather than hard-coding.
6. Teardown: msg 0xb (destruct) before freeing the frame; class token is released by msg 6 at shutdown.

- **Crash gotchas:**

- Double construct: case 9 calls FUN_00487a80(0xae) (no-return assert) if *param_1[2] is already non-null. Never send msg 9 twice to the same frame.
- Instance/frame mismatch: FUN_00487a80(0xb1) fires if FUN_004a0440(frame) does not return the freshly allocated instance — happens if the frame's instance slot was corrupted or the proc was bound to the wrong frame.
- Selection out of range: msg 0x57 asserts FUN_00487a80(0x1d6) when new index >= count(+0x24). Always clamp to [0, count-1] (or use -1 sentinel only through the color-rebuild path, not 0x57).
- Uninitialized/null instance on control-specific messages: default path asserts 0x149 (instance ptr present but *ptr==0) and 0x2c. Do not send data messages (0x56/0x57/0x58) before construct completes.
- Color-array length: FUN_004dd7e0 iterates idx 0..count-1 reading colorArray[idx] and dispatching to child idx. If the array passed to msg 0x58 (or cfg[0]) has fewer than 'count' entries you get an OOB read and mis-colored/garbage swatches; if selectedIdx >= count the highlight FUN_0060f490 targets a non-existent child.
- Class token lifetime: children are created against the token at +0x28 (from FUN_0062d8b0). Releasing DAT_00c01648 (msg 6) or destroying the container (msg 0xb, which FUN_0046f850's the token) while children still reference it will leave dangling child frames — destruct order must be children-then-container-then-class.
- Mode flag: cfg[1]/+0x30 selects two different color pipelines (FUN_005ac620 premultiplied 0x20000000 vs FUN_005aa640). Passing an unexpected value falls into the 'else' (opaque) branch silently rather than asserting — wrong-looking swatches, not a crash.


### GmCtlColorPicker (IUi::Game::CColorPick)  (EXE 0x004dd0a0, confidence: high)

- **WASM:** ram:81143e3b
- **Assertion file:** P:\Code\Gw\Ui\Game\Controls\GmCtlColorPick.cpp (EXE string @0x00946734, xref DATA @0x004dd538 in FUN_004dd0a0 case 5); WASM: ../../../../Gw/Ui/Game/Controls/GmCtlColorPick.cpp @ram:0010c09c. Instance alloc tag string: P:\Code\Engine\Controls\CtlInstance.h.
- **Struct layout:**

CColorPick instance = 0x38 bytes (freed FUN_005acaeb(inst,0x38)):
 +0x00 void** vtable = &PTR_FUN_009404a4
 +0x04 uint32 parentFrameId (root frame that owns the child swatch cells; source of FUN_0062cfc0 lookups)
 +0x08 uint32 =0 (base)
 +0x0c..0x1f base-template fields (FUN_006017e0)
 +0x20 int32 selectedIndex (-1 = none; case 0x56 get, 0x57 set)
 +0x24 uint32 cellCount (number of color cells / child frames)
 +0x28 handle childCellTemplate (FUN_0062d8b0 grid item template; freed on destroy)
 +0x2c uint32 firstCellParam (applied only to cell 0 in SetColors: local_60)
 +0x30 uint32 styleFlag (0 = solid color swatch via FUN_005ac620 mask 0x20000000; nonzero = textured cell via FUN_005aa640)
 +0x34 uint32 columns (grid width, used by layout case 0x37)

FrameMsgCreate payload struct (cp = *payload in case 9):
 [0] uint32* colors (ARGB array; -> SetColors)
 [1] uint32 -> inst+0x30 styleFlag
 [2] uint32 -> inst+0x2c firstCellParam
 [3] uint32 cellCount -> inst+0x24
 [4] uint32 columns -> inst+0x34
 [5] uint32 colorCount (-> SetColors count)

Child swatch instance (FUN_004dccc0) = 0x40 bytes: +0x00 vtable, +0x04 childRoot, +0x20 color, +0x24=0xffffffff, +0x28/+0x2c cell params (msg 0x61), +0x30/0x34/0x38/0x3c animation state, +0x48 vtable dup.

- **Message protocol:**

FrameProc FUN_004dd0a0 (WASM IUi::Game::GmCtlColorPickerProc -> TCtlInstance<IUi::Game::CColorPick>::MsgProc). switch(msgframe[1]=msg). Every path ends by chaining to the base template proc via thunk_FUN_00647170(frame,payload,out) (LAB_004dd589). Instance accessor = FUN_004a0440(frame) = **(frame+8) (asserts 0x2b/0x2c if unset).

PASS-THROUGH (call FUN_004a0440 to assert instance then chain to base): msgs 1,3,7,8,0xa,0xc,0xf,0x13,0x15,0x20,0x24-0x2a,0x2c,0x2e,0x32,0x34,0x35,0x36,0x3a-0x3f,0x44-0x46,0x4b,0x4c,0x4e,0x4f,0x52.

case 4 (install-base): empty here; base install handled by chained base proc.
case 5 (class register): DAT_00c01648 = FUN_0062d790(0x11,7,0x192,&layoutdesc,&props,&DAT_0094672c[GmCtlColorPick.cpp],4) — registers the grid-layout template. Global; done once.
case 6 (class unregister): FUN_0046f850(DAT_00c01648).
case 9 (OnFrameCreate): asserts *(msgframe[2])==0 (0xae), allocs 0x38-byte instance via FUN_0047f340("...CtlInstance.h",0xaf), vtable=&PTR_FUN_009404a4, base ctor FUN_006017e0, stores back to *(msgframe[2]). Reads FrameMsgCreate payload cp=*payload: inst.count(0x24)=cp[3], inst[0x30]=cp[1], inst[0x2c]=cp[2], inst[0x34]=cp[4]. Builds child template inst[0x28]=FUN_0062d8b0(0x11,7,0x192,...). Loops i=0..cp[3]-1 creating one child swatch frame each: FUN_0062bfc0(inst.parent(inst+4=inst[1]),0,i,FUN_004dccc0,template,0). Then SetColors: FUN_004dd7e0(cp[0], cp[5]).
case 0xb (OnFrameDestroy): frees child template FUN_0046f850(inst[0x28]), base dtor FUN_00601810, FUN_005acaeb(inst,0x38), *(msgframe[2])=0.
case 0x31 (set selected float): if payload[2]==(int)7 -> inst.selected(0x20)=payload[1]; FUN_0062ee80(child,7,val,0); chain.
case 0x37 (OnFrameSize/layout): grid row/col computation using inst.count(0x24) and inst.columns(0x34); positions child cells via FUN_0062cfc0/FUN_0062f770.
case 0x38 (measure/size-query): FUN_00602900 -> writes measured {w,h} to *(payload[2]).
case 0x56 (GET selected index): *out = *(inst+0x20).
case 0x57 (SET selected index): if idx(payload)<inst.count(0x24): child=FUN_0062cfc0(inst[1],idx); FUN_0052b720(child)[highlight]; inst.selected(0x20)=idx; chain. else assert 0x1d6.
case 0x58 (SetColors): FUN_004dd7e0(payload[0]=colors*, payload[1]=count).

Child swatch proc FUN_004dccc0 (separate 0x40-byte control, one per cell): case 4 sets style flags |=0xe0000 and paint proc FUN_004dd620; case 0x61 = set cell {color=payload[0], +0x28=payload[2], +0x2c=payload[3]} then invalidate; case 0x45 = hover/animation tick.

- **Create recipe:**

This is a game-layer COMPOSITE (a grid of child swatch cells), not a leaf paint control. Standard lifecycle:
1) One-time class registration: game sends msg 5 at UI init -> DAT_00c01648 template registered. Do not repeat.
2) Create the frame with this proc: FUN_0062bfc0(parentFrame, flags, childId, FUN_004dd0a0, userdata, 0). This installs FUN_004dd0a0 as the frame proc.
3) The UI layout system then delivers msg 4 (install base), then msg 9 (OnFrameCreate) with a FrameMsgCreate whose payload cp must be laid out as: cp[0]=ptr to uint32 ARGB color array, cp[1]=styleFlag (0 for solid swatches), cp[2]=firstCellParam (0 normally), cp[3]=cellCount, cp[4]=columns, cp[5]=colorCount (== cp[3]). case 9 allocates the instance, builds the child-cell template, spawns cp[3] child frames (proc FUN_004dccc0), and calls SetColors.
Warm-ups/ordering: instance does NOT exist until msg 9; any 0x56/0x57/0x58 before create asserts (accessor FUN_004a0440 -> FUN_00487a80(0x2b/0x2c)). After create: set colors with dispatcher FUN_0062ef40(frame,0x58,{colors,count},0); read current selection with 0x56 (out receives index); set selection with 0x57 (index must be < cellCount).
Sizing: driven by columns (cp[4]) + cellCount; cell metrics come from the registered template. Query total size with msg 0x38.
Practical Py4GW note: prefer letting the game construct it through its layout (send create via FUN_0062bfc0 + let case 9 fire) rather than hand-forging the FrameMsgCreate payload; then drive it purely via the 0x56/0x57/0x58 get/set messages through FUN_0062ef40.

- **Crash gotchas:**

- Accessor FUN_004a0440 asserts (non-returning FUN_00487a80) if frame+8 is null (0x2b) or instance ptr null (0x2c). Never send get/set (0x56-0x58, 0x31) before msg 9 has created the instance.
- case 9 asserts 0xae if the instance slot *(msgframe[2]) is already non-null (double-create). case 0xb clears it; re-create only after destroy.
- case 0x57 (set selected index) asserts 0x1d6 if index >= cellCount(inst+0x24). Always clamp to [0,count).
- case 0x57 default (non-index msg) path asserts 0x149 if payload present but *(payload)==0.
- SetColors (FUN_004dd7e0) walks inst+0x24 entries reading colors[i] from cp[0]; a colors array shorter than cellCount reads OOB. Ensure len(colors)>=cellCount, and colorCount(cp[5])==cellCount(cp[3]).
- styleFlag (inst+0x30): 0 routes to color-fill FUN_005ac620(color,0x20000000,...); nonzero routes to texture path FUN_005aa640(color) treating the 'color' value as a texture/atlas handle — passing a raw ARGB with styleFlag!=0 will misuse it as a resource id.
- Instance is exactly 0x38 bytes (freed with that literal); child swatch cells are 0x40 bytes with their own proc FUN_004dccc0 and must be destroyed via the parent's msg 0xb, not individually.
- Every case chains to base proc thunk_FUN_00647170 at exit; do not short-circuit that or base bookkeeping/paint is skipped.


### GmCtlItemImage  (EXE 0x004dde30, confidence: high)

- **WASM:** unresolved (EXE address was supplied directly; not needed). Assertion file confirms game-layer symbol.
- **Assertion file:** P:\Code\Gw\Ui\Game\Controls\GmCtlItemImage.cpp (game-layer, not Engine\Controls). Alloc line 0x116, destruct line 0x10e, class-init 0x130, class-deinit 0x142.
- **Struct layout:**

Instance = 0x10 bytes (4 dwords), allocated in case 9 via FUN_0047f340(file,line)->FUN_00480010, freed in case 0xb via FUN_005acaeb(inst,0x10). Instance pointer is reached as **(frame+8) (FUN_004df600 = **(param_1[2]) with assert 0x128 if null).
  +0x00 dword  ownerFrame     : *param_1 (owning FrameProc frame id). First arg to every draw call (FUN_00647db0 target).
  +0x04 dword  itemModel      : userdata[0]; source object the image is pulled from. MUST be non-zero (assert 0x163).
  +0x08 dword  imageResource  : copy of userdata[1] made via FUN_0046fda0 (ref-counted resource clone, e.g. HFrameImageList/texture handle). MUST be non-zero when type<3 (assert 0x165). Freed on destruct (FUN_0046f850 on inst+8, assert 0x10e if null).
  +0x0c dword  typeIndex      : userdata[2]; image-source variant 0/1/2. MUST be < 3 (assert 0x164). Selects source in FUN_004de400: 0=FUN_0083f8c0(item) flags[3], 1=FUN_005a74f0 flags[6], 2=FUN_005a7520 flags[4].
Class-static (shared by ALL slots): DAT_00c0164c = HFrameImageList resource created once in case 5 via FUN_0062d790(0x13,7,0x19a, size{0x38,0x38}, cell{0x40,0x40}, &DAT_009467e0, 1); tagged "HFrameImageList" (FrApi.cpp). Freed in case 6.

- **Message protocol:**

FrameProc(param_1=msgframe, param_2=payload); switch on param_1[1]=msg (game-layer enum, shifted vs base Ctl model):
  5  CLASS_CONSTRUCT : if DAT_00c0164c==0 create shared HFrameImageList (see struct_layout); else assert 0x130 (double-init). One-time, class scope.
  6  CLASS_DESTRUCT  : free DAT_00c0164c (FUN_0046f850), null it; assert 0x142 if already null.
  7,10,0xc..0x3a    : NO-OP (fall to break/return). Reserved message ids acknowledged but ignored.
  8  PAINT           : inst=FUN_004df600; if (*param_2 & 1) [paint sub-pass flag] draw item image via FUN_0062b290(inst[0]=frame, param_2+0xc=paint rect/anchor, DAT_00c0164c=shared image list,0,0,0) -> FUN_0062b0e0 (scale 1.0, blit region 0..9). Requires DAT_00c0164c already created (msg 5 must have run).
  9  INSTANCE_CONSTRUCT : assert *(param_1[2])==0 else 0x115; alloc 0x10; inst[0]=*param_1; init [1]=0,[2]=0,[3]=3; store inst at *(param_1[2]); read userdata puVar1=*param_2 (assert non-null 0x15c); inst[1]=puVar1[0](item, assert!=0 ->0x163), inst[2]=copy(puVar1[1]) (resource), inst[3]=puVar1[2](type); validate type<3 (0x164) & resource!=0 (0x165); then FUN_00630080(frame,0,_DAT_00942af4) blank-init.
  0xb INSTANCE_DESTRUCT : inst=*(param_1[2]); if non-null: assert inst[2](+8)!=0 (0x10e), free resource FUN_0046f850(inst+8), free struct FUN_005acaeb(inst,0x10); clear slot *(param_1[2])=0.
  0x3b(59) REFRESH/VALIDATE : inst=FUN_004df600; if (*param_2==0): avail=FUN_004de400(item=inst[1], type=inst[3], resource=inst[2]); if avail==0 -> FUN_00630080(frame,0,_DAT_00942af4) blank; else -> FUN_0062cb00(frame,1.0f,0,_DAT_00940eb8,1) set full opacity/tint + FUN_0062ee80(frame,7,0,0) set render style flag(>=7).
  default : no-op.
Instance accessor FUN_004df600(frame)= **(frame+8) (asserts 0x128). Note: there is no case 4 parent-proc install and no 0x15/0x56 here — this game-layer control uses its own contiguous msg block 5..0x3b.

- **Create recipe:**

Created lazily by the owning GmCtlItem layout pass FUN_004df120 (the sole xref to FUN_004dde30, installed at 004df5c7). Slot geometry uses FUN_004de290 rect layout; the image sub-frame is spawned ONLY when the item image is not yet resident AND no existing child frame:
  if (FUN_004de400(item=parent+0x54, type=parent+0x68, res=parent+0x28)==0 && FUN_0062cfc0(parentFrame,0)==0) {
     userdata local_18 = { item(*parent+0x54), resource(*parent+0x28), type(*parent+0x68) };  // {itemModel, imageResource, typeIndex}
     child = FUN_0062bfc0(parentFrame(parent+4), 0x80 /*flags*/, 0 /*child slot*/, FUN_004dde30 /*this proc*/, &userdata, 0);
     FUN_0062f5a0(child, 1);            // warm-up: enable/mark instance
     FUN_0062ede0(child, 0, 0xffffffff); // warm-up: set color/opacity mask (full)
  }
Ordering/warm-ups to reproduce standalone:
  1. Ensure class construct (msg 5) has run so DAT_00c0164c HFrameImageList exists.
  2. Prepare userdata = {itemModelPtr!=0, resourceDescriptorPtr(cloneable, non-null), typeIndex in 0..2}.
  3. FUN_0062bfc0(parent, flags=0x80, 0, FUN_004dde30, &userdata, 0) -> child. (This drives msg 9 INSTANCE_CONSTRUCT internally.)
  4. FUN_0062f5a0(child,1); FUN_0062ede0(child,0,0xffffffff).
  5. Send msg 0x3b to sync visibility once the item image finishes loading.
Sizing: cells are 0x40x0x40 with 0x38x0x38 inner (from the shared image list); the sub-frame inherits parent slot rect from FUN_004de290, no explicit size-query message.

- **Crash gotchas:**

- Paint (msg 8) dereferences the class-static DAT_00c0164c; if msg 5 (class construct) has not run it is 0 and the image-list blit path faults. Always class-init before any instance paints.
- Double class-init aborts (assert 0x130 via FUN_00487a80); double-free/absent resource on msg 6 aborts (0x142). FUN_00487a80 is a no-return abort, not recoverable.
- Instance construct (msg 9) asserts on a non-empty slot (0x115), null userdata (0x15c), null item (0x163), typeIndex>=3 (0x164), and null image resource for type<3 (0x165). Any violation is a hard abort.
- Instance destruct (msg 0xb) asserts if the resource handle (inst+0x08) is null (0x10e) before freeing; do not zero inst[2] before destruct.
- FUN_004df600 asserts (0x128) if the instance slot **(frame+8) is null — sending msg 8/0x3b to a frame whose msg 9 never ran aborts.
- typeIndex is bounded 0..2 in BOTH FUN_004de400 (>2 aborts 0x75) and construct; keep it in range.
- The image resource at userdata[1] is CLONED (FUN_0046fda0 -> FUN_0046fb00 + optional callback[4]); the source descriptor must be a valid {ptr, name, a, b, cb} block or the clone faults.


### UiCtlProgressMission  (EXE 0x00527f90, confidence: high)

- **WASM:** ram:80f85731 (impl) / ram:80f85649 (proc thunk)
- **Assertion file:** P:\Code\Gw\Ui\Game\GmMissionProgress.cpp (EXE string 0x0094c59c); base logic references P:\Code\Gw\Ui\Controls\UiCtlProgress.cpp (0x00b964c8)
- **Struct layout:**

Instance struct = 0x1c bytes / 7 dwords (size confirmed by free FUN_005acaeb(inst,0x1c)):
+0x00 [0] uint32  frameId          (this frame's id = *hdr)
+0x04 [1] uint32  contentHandle    (= *(userdata ptr); the progress skin/content the bar tracks; compared in 0x100000b0)
+0x08 [2] uint32  orientation      (0=horizontal, 1=vertical; set via 0x56, must be <=1)
+0x0c [3] float   springDenom      (init _DAT_0094052c; stiffness denominator in 0x45 spring math)
+0x10 [4] float   fillPos          (current animated fill fraction; spring position)
+0x14 [5] float   fillTarget       (target fill; written each advance, read by FUN_00528d70)
+0x18 [6] float   fillVel          (spring velocity accumulator)
Note: the leaf render child (proc LAB_00884a50, flags 0x80) is a separate frame, not stored in this struct; it is reached each frame via FUN_0062cfc0(frameId,0). Parent container GmMissionProgress (FUN_005282d0) has its own 0x14-byte struct and creates THIS bar (proc FUN_00527f90, flags 0x300, child idx 0) plus a text child (FUN_00528ac0, flags 0x80300, idx 1).

- **Message protocol:**

EXE FrameProc FUN_00527f90(FrameMsgHdr* hdr, void* payload). hdr[1]=msg, hdr[2]=&instanceSlot (instance = **(hdr+8), accessor FUN_00528ce0 asserts non-null=line 0x7d). payload semantics per-msg. Cases handled:
- 9 CREATE: assert slot empty (else 0x6a). Alloc instance (0x1c bytes, tracked FUN_0047f340("...GmMissionProgress.cpp", line 0x6b)). Init [0]=hdr frame id, [1]=*(*payload) content/skin handle (payload=userdata ptr; assert *payload!=0 else 0xd9), [2]=0, [3]=_DAT_0094052c (spring denom const), [4..6]=0. FUN_0062ede0(frame,0,0xffffffff) style/color init. Create leaf render child: FUN_0062bfc0(frame,0x80,0,&LAB_00884a50,0,0); FUN_00604aa0(child,0x800). FUN_00528d70() pushes initial colors. FrameMsgRegister 0x100000b0 (FUN_0062ef00). If game/mission context FUN_008480c0()==0x1d3, also FrameMsgRegister 0x45 (per-frame advance).
- 0xb DESTROY: if slot!=0 free via FUN_005acaeb(instance,0x1c); slot=0.
- 0x38 GET_PREFERRED_SIZE: instance via FUN_00528ce0. If orient[2]==0 (horizontal) clamp payload[0] to min (_DAT_00944958->_DAT_009416e8), out payload[2]={clampedW, _DAT_009407c8}; if [2]==1 (vertical) out={_DAT_009407c8, clampedH}; else assert 0x109.
- 0x45 ADVANCE(dt=*payload): only fires when registered (ctx 0x1d3). Critically-damped spring on fill: pos=[4], target=[5], vel=[6], stiffness/denom=[3]. Updates [4],[6] then FUN_00528d70() to re-emit render sub-msgs.
- 0x56 SET_ORIENTATION(payload as int, 0 or 1): assert instance (0x7d), assert value<=1 (0x111). If changed store [2], FUN_0062f110(frame) relayout.
- 0x100000b0 (content-changed custom): assert instance (0x7d); if *payload==instance[1] repaint via FUN_00528d70().
All other msgs fall through (base proc handles 4/base-install, 1/paint, 0x15/size-query via the installed base template; this subclass does not chain them explicitly). FUN_00528d70 recomputes fill from [4]/[5], resolves child via FUN_0062cfc0(frame,0), and dispatches sub-messages 0x62/0x61/0x60 (FUN_0062ef40) to the leaf paint child (fill color / border color / content) — matching WASM StartFillColorFade/StartBorderColorFade/ContentAdd.

- **Create recipe:**

Not created standalone from Python — it is a native child frame instantiated by its parent panel. To reproduce natively: FUN_0062bfc0(parentFrame, flags=0x300, childIndex=0, proc=FUN_00527f90(0x00527f90), userData=&contentPtr, 0). The proc's case 9 does the rest: allocates the 0x1c instance, requires userData non-null and *userData = a valid progress content/skin handle (else assert 0xd9), stores it at [1], creates its own leaf paint child (FUN_0062bfc0(self,0x80,0,&LAB_00884a50,0,0) + FUN_00604aa0(child,0x800)), warm-up FUN_00528d70() to seed fill colors, then FrameMsgRegister 0x100000b0 and (only if FUN_008480c0()==0x1d3) 0x45 for animation. Post-create: send 0x56 to set orientation (0/1), and drive content via the 0x100000b0 content-changed message; the spring animation self-drives on 0x45 ticks. Real callers create it through the GmMissionProgress container FUN_005282d0 (case 9), which is the normal instantiation path.

- **Crash gotchas:**

see message_protocol


### UiCtlTask (IUi::Game::Quest::CCtlTask) — Quest task-list row control  (EXE 0x0057eb70, confidence: high)

- **WASM:** ram:817b6d22
- **Assertion file:** P:\Code\Gw\Ui\Game\Quest\QuestTask.cpp (EXE string @0x00951948). Resolution: WASM ram:817b6d22=UiCtlTaskProc tail-calls CCtlTask::FrameProc(ram:817b6e0b); game source QuestTask.cpp; get_xrefs_to 0x00951948 -> FUN_0057eb70 (the switch(msg) lifecycle proc) and FUN_0057ed40 (OnFrameCreate). Registered proc POINTER is thunk 0x0057efc0 (JMP 0x0057eb70). WASM template assert file: ..\Gw\Ui\Game\Quest\..\Ui\Controls\UiCtlInstance.cpp; EXE alloc uses "P:\Code\Gw\Ui\Controls\UiCtlInstance.h".
- **Struct layout:**

Instance = 0x60 (96) bytes, allocated on msg 9:
+0x00 vtable ptr -> PTR_FUN_009518b8 (slots = FUN_004a0430)
+0x04 owning frame id (written at alloc from hdr[0])
+0x08 create context / task-entry param (FrameMsgCreate payload; WASM stores *param-1)
+0x0C current task id / challenge-code handle (compared in FrameProc to detect change before re-describe)
+0x10 task description param/index (paired with +0x0C in GetDescription(this,*+0xC,*+0x10,1))
+0x14..0x5F CCtlTask members: child frame handles (CtlTextMl text child, thumbnail child), cached description/status strings, thumbnail id, mouse/style state. Offsets >0x10 not individually confirmed (medium confidence there).

- **Message protocol:**

Registered proc = thunk 0x0057efc0 -> body FUN_0057eb70(hdr* param_1, void* in=param_2, void* out=param_3). Switches on hdr[1]=msg:
- msg 9 (ALLOC/attach instance): assert *hdr[2]==0 else FUN_00487a80(0x5f) "already set"; instance=FUN_0047f340("...UiCtlInstance.h",0x60); instance[0]=&PTR_FUN_009518b8 (vtable, slots -> FUN_004a0430), instance[1]=0; *hdr[2]=instance; instance+4 = hdr[0] (owning frame id). Falls through to base dispatch.
- default/base: if instance valid (*hdr[2]!=0) -> FUN_008783b0(hdr,in,out) = TCtlInstance<CCtlTask>::FrameMsg, routing create(4)/paint(1)/position/size/sizequery(0x15)/language/text-resolved to CCtlTask handlers via vtable. create(4) -> OnFrameCreate=FUN_0057ed40.
- msg 0xb (DESTROY/free): assert hdr[2]&*hdr[2] (0x72/0x74); FUN_005acaeb(instance,8) frees; *hdr[2]=0.
- msg 0x56 (GET, control-specific): assert; FUN_0057ef40(in) resolves/refreshes task description text.
- msg 0x57 (SET text / add-row): assert; if in(wchar*)!=null && *in!=0: h=FUN_0062cfc0(frame,1,text); FUN_0060a420(h) sets row text; else assert 0x47 "empty text".
OnFrameCreate FUN_0057ed40(instance, FrameMsgCreate* p): assert *p!=0; FUN_0062bfc0(frame,0x300,1,FUN_006099f0,0,0) creates multi-line text child (CtlTextMl, flags 0x300, order 1); style=FUN_0062fe20(frame,0x1000); if bit clear -> FUN_0062bfc0(frame,0,0,FUN_00884f20,0,0) creates thumbnail child; FUN_0057ef40(p[1]) resolves description; text=p[0]; if non-null FUN_0062cfc0+FUN_0060a420 set text then FUN_0062ccd0(frame,0,0x30) applies effects, else assert 0x47. WASM confirms: FrameMsgRegister 0x4c and 0x1000014c..0x1000015c (text-resolved/language), TextEncode(1), CtlTextMlSetGrEffects(0x10), FrameSetDefaultTextStyle(7), FrameMouseEnable, 2nd FrameCreate order 0 thumbnail, FrameSetLayer(1), FrameNewSubclass.

- **Create recipe:**

Quest-log ROW control, normally spawned by its parent list, not app code. Parents FUN_0057cd50 / FUN_0057d760 / FUN_0057d900 (QuestList/QuestEntry group) register proc 0x0057efc0 and call FUN_00612900(target, dataPtr, flags, proc=0x57efc0, userdata) which sends msg 0x57 via FUN_0062ef40(frame,0x57,&payload,&out) to add the row; flags are (bit<<12)|... (0x300-class child).
Direct instantiation: FrameCreate(parent, flags=0x300, childOrder=1, proc=0x0057efc0, userdata, 0) via FUN_0062bfc0. Framework then delivers msg 9 (ALLOC -> 0x60 instance) then msg 4 (CREATE -> OnFrameCreate FUN_0057ed40) which builds the CtlTextMl text child (proc FUN_006099f0) and optionally the thumbnail child (proc FUN_00884f20, only if style bit 0x1000 is clear). Supply FrameMsgCreate payload[0]=non-empty wchar* task text, payload[1]=task/description id. Push text later via msg 0x57, refresh via msg 0x56, destroy via msg 0xb. Warm-ups: OnFrameCreate self-registers the 0x4c/0x1000014c..15c text-resolved + language-changed notifications, so no manual subscription needed; just ensure parent frame exists and payload[1] id resolves to a valid quest task.

- **Crash gotchas:**

- msg 9 asserts FUN_00487a80(0x5f) if *hdr[2] already holds an instance: never send create/alloc twice to the same frame slot.
- Every 0x56/0x57/0xb path asserts hdr[2]!=0 (0x72) and *hdr[2]!=0 (0x74): sending get/set/destroy before the msg-9 alloc faults.
- msg 0x57 and OnFrameCreate assert 0x47 ("empty text") when wchar* text is null/empty; OnFrameCreate also asserts *payload[0]!=0. Always pass a non-empty description.
- On msg 0xb the instance is freed (FUN_005acaeb(instance,8)) and *hdr[2] cleared; later access uses a stale +0x00 vtable -> crash. Do not reuse the frame after destroy.
- Thumbnail child exists only when style bit 0x1000 is clear (FUN_0062fe20(frame,0x1000)==0); code assuming it always exists null-derefs for text-only tasks.
- FrameProc delegates paint/size to base FUN_008783b0 through the +0x00 vtable, so a zeroed/corrupted instance[0] (accessed pre-alloc) calls FUN_004a0430 with a bad this.


### CtlLayout (recursive layout/anchor solver)  (EXE 0x00602190, confidence: high)  [NOT a frame proc]

- **WASM:** ?
- **Assertion file:** P:\Code\Engine\Controls\CtlLayout.cpp (string @ 0x00a4daf0; referenced by all asserts in FUN_00602190 and wrapper FUN_00602060)
- **Struct layout:**

Owner/layout object (param_1 / `this`):
  +0x00  void** vtable            (case-2 custom-size callback: slot 0 = (**(code**)*this)(&args,gravity))
  +0x04  void*  deviceCtx         (-> FUN_00601cc0 = scale/DPI float; -> FUN_0062cfc0 = measure-handle lookup)
  +0x08  LayoutNode** nodeArray   (flat, NUL-terminated per container run)
  +0x0C  ? (unused here)
  +0x10  uint32 nodeCount         (param_1[4]; bounds all index checks)

LayoutNode (element = *(nodeArray + index*4), iVar2):
  +0x04  void*  resource          (measure handle for type 1 / callback data for type 2)
  +0x08  float  preferredW        (percent-of-parent when +0x10 bit3 set)
  +0x0C  float  preferredH
  +0x10  uint8  optionFlags       (0x01 clamp-to-available; 0x02 alt-fit path; 0x04 fixed/measured; 0x08 percent-of-parent)
  +0x14  float  insetLeft
  +0x18  float  insetTop
  +0x1C  float  insetRight
  +0x20  float  insetBottom
  +0x24  uint32 gravityFlags      (see message_protocol bit table; also read as node[9] during child validation)
  +0x28  int32  layoutType        (0=box-pack, 3=box-pack variant/strict, 1=intrinsic/measured leaf, 2=custom callback)

Args to FUN_00602190:
  param_2 uint*  ioNodeIndex  (cursor into nodeArray; in/out)
  param_3 float[4] outRect    (L,T,R,B; in=parent frame, out=solved)
  param_4 float[2] availSize  (w=[0], h=[1])
  param_5 uint   inheritedGravity (root seeds 0x100)

- **Message protocol:**

NOT a frame message protocol. FUN_00602190 is a recursive layout/measure solver: __thiscall FUN_00602190(owner *this, uint *ioNodeIndex, float outRect[4], float availSize[2], uint inheritedGravity). It does NOT switch on msgframe[1]=msg (no case 4/9/0xb/1/0x15/0x56). It switches on the per-node layoutType field node+0x28:
- case 0 / case 3 (box/stack container): calls FUN_00602a10 to size the box, subtracts insets, seeds child rect (local_5c..local_50), then WALKS forward through the sibling array recursively calling itself (FUN_00602190(&idx,&childRect,&span,mask)) until it hits a NULL terminator entry. case 3 requires each child gravity & 0x2e != 0 (else assert 0x220); case 0 requires child gravity & 0x53 != 0 (else assert 0x221).
- case 1 (intrinsic/measured leaf, e.g. text/glyph): resolves a measure handle via FUN_0062cfc0(this[1], node+4), builds a flag word local_68 from preferred size vs available and node+0x10 option bits, then FUN_0062e8a0(handle, gravity, &rect, &flags). Uses FUN_004f0cb0 to clamp/round.
- case 2 (custom callback): invokes owner vtable slot 0 (**(code**)*this)(&args, gravity) to obtain a size, then FUN_0062ec50 applies it along the resolved edge.
Edge/gravity application goes through FUN_0062ec50(anchorValuePtr, edgeSelector, &rect) and FUN_0062ec50/FUN_0062ec50 with edge selectors 4=left,8=right,1=top,0x10=bottom. Gravity mask (local_8 = node+0x24 combined with inherited param_5) bits: 0x01 pin-left/top, 0x02 center-on-axis, 0x04 pin-right, 0x08 stretch/fill, 0x10 pin-bottom, 0x20/0x40 apply H/V margin, 0x80 (sign bit) reverse-anchor pass, 0x100 selects vertical axis. Scale/DPI factor comes from FUN_00601cc0(this[1]) (local_14); if 0 the anchor pass is skipped. Returns updated *ioNodeIndex (advanced past the consumed subtree) and the solved outRect[4]=(L,T,R,B). Public entry is the wrapper FUN_00602060(frameLayoutObj, float rect[4]) which requires the node array to be non-empty and NUL-terminated and seeds recursion with gravity 0x100.

- **Create recipe:**

N/A - not a creatable control and not a FrameProc. CtlLayout is an internal geometry solver, not registered/instantiated via the FUN_0062bfc0 primitive create path and never installed as a frame proc. It is driven by a frame's layout pass: build a LayoutNode array (as described) on the owner object, then call the public wrapper FUN_00602060(owner, float rect[4]) which validates the array (non-empty, NUL-terminated, count matches) and invokes FUN_00602190 recursively with gravity 0x100. Related CtlLayout helpers in the same module: FUN_00601cc0 (scale/DPI), FUN_00602a10 (box measure), FUN_00602900/FUN_00602f50 (node setup/validation), FUN_0062ec50 (edge apply), FUN_0062e8a0 (leaf measure apply), FUN_0062cfc0 (measure-handle lookup).

- **Crash gotchas:**

Function is assert-heavy; every failure calls FUN_00487a80(lineNo) with CtlLayout.cpp and does NOT return (aborts the client):
- ioNodeIndex (param_2) NULL -> assert 0x193; outRect (param_3) NULL -> assert 0x194.
- nodeIndex >= owner.nodeCount at entry -> assert 0x24b; recursion advancing past count -> assert 0x228.
- optionFlags bit3 (0x08, percent) set with negative preferredW/H -> assert 0x1a4.
- Any produced rectangle inverted (right<left OR bottom<top) -> assert 0x50 (mid-solve), 0x238 (child span), 0x26d (final result).
- case 3 child whose gravityFlags & 0x2e == 0 -> assert 0x220; case 0 child whose gravityFlags & 0x53 == 0 -> assert 0x221.
- Wrapper FUN_00602060: layout obj with count!=0 but null array ptr -> 0x166; recursion did not consume exactly count-1 -> 0x16e; final array slot not NUL terminator -> 0x171; zero count where >0 required -> 0x2ef.
Practical gotchas for callers: nodeArray MUST be NUL-terminated and its length MUST equal nodeCount; gravity bits must be internally consistent with layoutType (box variants demand specific bits); scale from FUN_00601cc0 returning 0 silently skips the entire anchor/margin pass. Deep/self-referential node arrays recurse unbounded-in-practice (bounded only by count) — a cyclic/miscounted array trips 0x228 rather than looping forever.


### CtlEdit  (EXE 0x00603cc0, confidence: high)

- **WASM:** ? (unresolved; matched via assertion string "P:\\Code\\Engine\\Controls\\CtlEdit.cpp" embedded directly in the EXE FrameProc case 9)
- **Assertion file:** P:\Code\Engine\Controls\CtlEdit.cpp
- **Struct layout:**

Instance (built by FUN_00603000; byte offsets, dword idx in [] ):
+0x00 [0]  vtable ptr (PTR_FUN_00a4df28 plain / PTR_FUN_00a4e330 extended)
+0x04 [1]  owning frame handle (passed to all FUN_0062xxxx frame calls)
+0x08 [2]  caret / scroll-anchor A (set by msg 0x1e; save/restore on focus)
+0x0c [3]  caret / scroll-anchor B
+0x10 [4]  0 (child-notify id compared in msg 0x50 as piVar2[0x10]? -> +0x40)
+0x1c [7]  0x15  (control type/class tag)
+0x20 [8]  focus-active flag region
+0x24 [9]  IME-init flag (msg 0x21)
+0x2c [0xb] cached mouse Y (msg 0x1b payload[1])
+0x30 [0xc] cached mouse X (msg 0x1b payload[0])
+0x3c [0xf] drag/select-active flag (set by msg 0x37)
+0x40 [0x10] capture/timer id (msg 0x21/0x50/0x51)
+0x44 [0x11] flag
+0x4c [0x13] 0xffff  (max-length / limit; set by msg 0x5a)
+0x50 [0x14] float value (msg 0x56 get / 0x5b set)
+0x54 [0x15] TEXT BUFFER ptr (wchar*)  <-- primary text
+0x58 [0x16] text buffer capacity (wchars)
+0x5c [0x17] text length+? (len used by msg 0x58; seeded to 1)
+0x60 [0x18] 0x80  (initial capacity seed)
+0x64 [0x19] COMPOSITION/pending buffer ptr (msg 0x3a/0x4c/0x5c)
+0x68 [0x1a] comp buffer capacity
+0x6c [0x1b] comp buffer length
+0x70 [0x1c] 0x80 seed
+0x74 [0x1d] undo/save-length sentinel (0xffffffff)
+0x78 [0x1e] secondary run/tab int[] ptr (msg 0x59 / FUN_006078d0)
+0x7c [0x1f] run array capacity
+0x80 [0x20] run array count
+0x84 [0x21] 0x40 seed for run array
+0x88 [0x22] cached pt X (msg 0x2c/0x37)
+0x8c [0x23] cached pt Y
Extended variant continues (idx 0x24..0x37 zeroed, [0x36]=+0xD8=0xffffffff) -> ~0xE0 bytes.
Base-template proc FUN_006123a0 (installed at msg 4) is itself a frame proc that chains to FUN_0062c370.

- **Message protocol:**

FUN_00603cc0(frame*, payload*, out*) switches on msg=param_1[1]. Instance = *(int*)param_1[2] (piVar2 holds &instance). Every path ends by tail-calling the base proc thunk_FUN_00647170(frame,payload,out).

LIFECYCLE / TEMPLATE:
- 4  INSTALL BASE PROC: writes *(payload[3]) = FUN_006123a0 (the CtlEdit base-template proc, which itself installs FUN_0062c370 as ITS base -> 3-level chain CtlEdit->FUN_006123a0->FUN_0062c370). ORs style |= 0x1000. ASSERTS on illegal style masks (see gotchas).
- 9  CREATE: assert(instance==0) else 0xf0f. Reads style bit 0x80000 via FUN_0062fe20(frame,0x80000). If CLEAR -> plain instance built by FUN_00603000 (~0x88 bytes, vtable PTR_FUN_00a4df28). If SET -> extended instance FUN_0047f340("CtlEdit.cpp",0xf11) with vtable PTR_FUN_00a4e330, dwords 0x24..0x37 zeroed, [0x36]=-1, +FUN_0060ca20(_DAT_0094519c,1). Stores into *piVar2.
- 0xb DESTROY: assert(instance!=0) else 0xf1b; call instance->vtable[0](1); *piVar2=0.
- 0x15 MEASURE/size query: assert(out!=0) 0x8a2; fills out[0..3] with default metrics from _DAT_0093c89c.
- 0xf  enable/hittest: if payload[1]==1 && FUN_00607cc0() -> *out = 1 (bool).

VTABLE FORWARDERS (call instance->vtable[slot]): 8->[+0xc], 0xa->[+0x10], 0x20->[+0x14], 0x24->[+0x18], 0x2f->[+0x1c], 0x31->[+0x20], 0x5e->[+0x8].

LAYOUT / GEOMETRY: 0x1b set pos cache (+0x30=payload[0] x, +0x2c=payload[1] y) then relayout(LAB_0060492c: FUN_0062bd40+FUN_0062f110). 0x1e set caret/scroll (+0x08,+0x0c) then relayout. 0x39 relayout. 0x3 FUN_00605190 (layout/measure). 0x1f FUN_00606c30. 0x38 point<->caret mapping via FUN_0062fee0 / FUN_0062d0e0.

CHILD/SCROLL PARTS via FUN_0062cfc0(*(instance+4)+?, N): 0x18/0x19/0x1a use part 1; 0x1c/0x1d use part 2; forwards 0x56/0x61 to the sub-control (FUN_0062ef40).

INPUT: 0x37 mouse-down/begin-select (FUN_0062d2a0 hit->caret, FUN_00604d30, sets +0x3c=1). 0x2c mouse-move/click-in-radius (compares dist^2 vs _DAT_00a4e418, +0x22/+0x23 = last pt) -> FUN_00604ed0. 0x21 FOCUS: payload==0 => focus LOST (release capture/IME, restore +0x0c=+0x08, notify frame msg 9); else focus GAINED (FUN_00608b10, IME setup, notify frame msg 8, calls FUN_00607cc0). 0x50 child/timer notify (piVar2[0x10]==payload[0]) -> vtable[+8], notify parent msg 7. 0x51 capture/timer lost (+0x40==payload[0]).

TEXT API (the important ones):
- 0x57 GET TEXT: assert(out!=0) 0x659; FUN_0046be40(out, *(inst+0x54) buffer, payload) copies text; if style 0x100000 set, trims one trailing whitespace/ctrl char.
- 0x58 GET TEXT LENGTH: assert(out!=0) 0x66a, assert(inst[0x17]!=0) 0x66b; *out = (*(inst+0x5c) length)-1, minus 1 more if last char is trailing space (style 0x100000).
- 0x5c SET TEXT: sets +0x74=0xffffffff (clear undo); if payload!=0 && *(short)payload!=0: FUN_0062ef00(frame,0x4c), FUN_004fed50 copy into +0x64 buffer (len+1), FUN_00632d90 relayout; else clear buffers (+0x64,+0x6c,+0x68 = 0).
- 0x3a APPEND/INSERT text into +0x64 composition buffer (grow via FUN_00473880, memmove-guard 0x171).
- 0x4c COMMIT composition (+0x74 sentinel restore, FUN_00632d90).
- 0x56 GET float value: assert(out!=0) 0x651; *out = *(float*)(inst+0x50).
- 0x5b SET float value: +0x50=payload; re-notify IME (FUN_00651850(0,6,..)) if focused; relayout.
- 0x5a SET MAX/limit: assert(payload!=0) 0x69a; +0x4c=payload; if current len(+0x5c) exceeds, FUN_00608080(1,1)+relayout.
- 0x59 SET run/tab array into secondary int[] at +0x78/+0x7c/+0x80 (FUN_006078d0).
- 0x5d FUN_00607a50. 0x5f FUN_0062bc20 (base fallthrough). 1 PAINT (FUN_00604f70).

PAINT (msg 1 -> FUN_00604f70): selects an ARGB fill from sub-state payload[0] (0=normal: 0xff464646 or disabled 0xff555555 depending on FUN_0062e2e0/+0x50; 1=0xfff0f0f0; 5..0xb and 0xd various highlight/selection colors) and, if non-transparent, draws a quad via FUN_0062b2d0 over rect payload[2..5] with textures payload[6],payload[7].

- **Create recipe:**

CtlEdit is an engine-base template control (leaf of the CtlEdit->FUN_006123a0->FUN_0062c370 proc chain). Instantiate exactly like other engine controls:

1) Create the frame with the create primitive:
   FUN_0062bfc0(parent_frame, style_flags, child_id, proc=FUN_00603cc0, userdata, 0)
   The dispatcher first delivers msg 4 to FUN_00603cc0 (installs base proc FUN_006123a0 into payload[3], forces style |= 0x1000), then msg 9 to allocate the instance.

2) Choose the variant via style bit 0x80000: CLEAR = plain single-line edit (~0x88-byte instance, vtable PTR_FUN_00a4df28); SET = extended/rich variant (~0xE0-byte instance, vtable PTR_FUN_00a4e330). Style bit 0x100000 = "trim trailing space" mode affecting GetText/GetLength.

3) Drive it through the frame dispatcher FUN_0062ef40(frame, msg, wparam, out):
   - Set text:      msg 0x5c, wparam = ptr to wide (UTF-16) NUL-terminated string.
   - Get text:      msg 0x57, out = caller wchar buffer.
   - Get length:    msg 0x58, out = &int.
   - Set max len:   msg 0x5a, wparam = limit (>0).
   - Get/Set value: msg 0x56 (out=&float) / 0x5b (wparam=float bits).
   - Position/size: managed by parent layout via msgs 0x1b/0x1e/0x15.
   No manual warm-up needed beyond create; FUN_00603000 seeds the text buffer (+0x54/+0x58/+0x5c) with a 1-char NUL so length/get calls are safe immediately after msg 9.

- **Crash gotchas:**

FUN_00487a80(code) is a NO-RETURN assert/abort. Triggers:
- msg 4 style validation (fatal at create): (style & 0x1020000)==0x1020000 -> 0x763; (style & 0x902000)==0x100000 -> 0x770 (i.e. 0x100000 requires companion bit in 0x902000); (style & 0x500000)==0x500000 -> 0x778. Do NOT combine those flag sets.
- msg 9 double-create: instance already non-null -> 0xf0f.
- msg 0xb destroy-before-create: instance null -> 0xf1b.
- Null out-pointer: msg 0x15 -> 0x8a2; 0x56 -> 0x651; 0x57 -> 0x659; 0x58 -> 0x66a.
- msg 0x58 GetLength before text buffer seeded (inst[0x17]==0) -> 0x66b (safe after normal create since FUN_00603000 seeds len=1).
- msg 0x5a with wparam==0 -> 0x69a.
- Buffer grow/memmove overlap guard (FUN_00473880 paths in 0x3a/0x5c/0x59 and in FUN_00603000/FUN_006078d0) -> 0x171 if src/dst ranges overlap; index-bounds guards -> 0x428, 0x171, 0x24b.
Also: msg 0x21 focus handler touches IME/global DAT_00c0aa38 focus owner and issues frame notifications (8/9) — must be delivered on a live, parented frame or the downstream FUN_0062f0d0/FUN_005e7480 calls operate on a stale frame handle (+0x04). Text is UTF-16 throughout (buffers are wchar*, sizes *2); passing a byte string corrupts length math.


### CtlView  (EXE 0x0060d410, confidence: high)

- **WASM:** unresolved (EXE-side FrameProc resolved from assertion string; WASM symbol not needed for this task)
- **Assertion file:** P:\Code\Engine\Controls\CtlView.cpp  (string @ 0x00a4ff40 in /Gw.exe (06-14); xref'd 14x inside FUN_0060d410, allocator line 0x105 for the instance and 0x348 for the inertia animator)
- **Struct layout:**

CtlView instance = 0x34 bytes (13 dwords), allocated in case 9 via FUN_0047f340("CtlView.cpp",0x105) [0x105 = source line, not size]; freed in case 0xb via FUN_005acaeb(inst,0x34). Instance pointer stored at *(msgframe[2]); accessor FUN_0060f120 = **(msgframe+8) = *(msgframe[2]).

+0x00 (idx0)  dword  typeTag/flags, initialized to 0x20. Also SET by msg 0x7ffffff6 to param_2 (content/bounds pointer). Read as scroll step base in msg 0x2f/0x31 (FUN_005636a0 uses *inst).
+0x04 (idx1)  ptr    control frame handle = msgframe[0]. Used everywhere: FUN_0062cfc0(*(inst+4),slot) to fetch child sub-frames.
+0x08 (idx2)  ptr    client/viewport bounds pointer (float rect), init 1; SET by msg 0x7ffffffa (=param_2) then FUN_0062f470 invalidate.
+0x0c (idx3)  dword  style bit = creation_flags(msgframe[4]) & 1.
+0x10 (idx4)  ---    part of alloc, not explicitly initialized in case 9 (allocator-zeroed).
+0x14 (idx5)  ---    "
+0x18 (idx6)  ---    "
+0x1c (idx7)  ptr    inertia/swipe animator sub-object, init 0. Allocated in msg 0x3d via FUN_0047f340("CtlView.cpp",0x348) (~0xc8/200 bytes; fields +0xa4 self-list head, +0xa8/+0xac/+0xb0/+0xb4 list, +0xb8/+0xbc start pos, +0xc0/+0xc4 zero). Freed in 0xb and 0x3c via FUN_005acaeb(*(inst+0x1c),200).
+0x20 (idx8)  dword  active swipe/animation id, init 0xffffffff (-1 = none). Matched in 0x3c, set in 0x3d, tested in 0x7ffffff4.
+0x24 (idx9)  dword  scroll X accumulator, init 0 (reset in 0x3d).
+0x28 (idx10) dword  scroll Y accumulator, init 0 (reset in 0x3d).
+0x2c (idx11) float  swipe delta/velocity X, init 0; SET *(inst+0x2c)=*param_2 in msg 0x7ffffff4.
+0x30 (idx12) float  swipe delta/velocity Y, init 0; SET *(inst+0x30)=param_2[1] in msg 0x7ffffff4.

Child sub-frame slots via FUN_0062cfc0(*(inst+4),N): 0=content-area frame, 1=inner scroll child (proc FUN_0060f0f0), 2=horizontal scrollbar, 3=vertical scrollbar.

- **Message protocol:**

FrameProc FUN_0060d410(msgframe, payload/param_2, out/param_3); msg = msgframe[1]. Non-handled/unknown -> thunk_FUN_00647170 (base-class proc chain forwarder, confirmed FUN_00647170: walks class proc table, skips msg 9 & 0xb).

CONTROL-SPECIFIC (positive msg):
 0x05 PAINT: if global DAT_00c0ac30==0 seed default draw-style block (_DAT_00c0ac18=1.0f, ..1c color, ..2c=1) then forward-to-base (thunk_FUN_00647170) which renders.
 0x09 CREATE: assert *(msgframe[2])==0 else fatal 0x104; alloc 0x34 inst; inst[1]=frame; inst[0]=0x20; inst[3]=flags&1; FUN_0060ca20(_DAT_0094519c,1); validate scroll styles (see gotchas 0x19c/0x19d); create inner scroll child FUN_0062bfc0(frame,0x300,0,FUN_0060f0f0,0,0); FUN_0062fc30 + FUN_0062ede0(child,0,-1); if param_2[0]!=0 build nested child from descriptor {style,proc,userdata}: FUN_0062cfc0(frame,0)->FUN_0062c760->FUN_0062bfc0(slot,desc[0]|0x300,0,desc[1],desc[2],0).
 0x0b DESTROY: assert inst!=0 (0x117); free animator (+0x1c,200) and inst (0x34); *(msgframe[2])=0.
 0x13 HITTEST/route: if flags bit & scrollbar child (slot3 then slot2) hits, set out[5]|=1,out[0]=childhit, forward base; else route to content child (slot0's grandchild).
 0x2f MOUSEWHEEL: delta=FUN_0060ca40(*param_2); step=±inst[0]; scroll V scrollbar (slot3||slot2) via FUN_005636a0.
 0x31 SCROLL-CMD: subcmd switch on param_2[1..2]: line-up/down (±inst[0]), page (view size - step), set-abs via FUN_005636a0 / FUN_0060a400; param_2[1]==0 & param_2[2]>6 -> FUN_0062ee80 forward.
 0x37 -> FUN_0060e420(param_2) (layout helper).
 0x38 MEASURE: query content child min/max, clamp param_2 rect [(*param_2..+4) vs computed].
 0x3c SWIPE-END: if *param_2==inst[+0x20] active-id, free animator(+0x1c), inst[+0x20]=-1.
 0x3d SWIPE-BEGIN: if inst[+0x20]==-1 && param_2[4]!=0: alloc animator(line0x348) at +0x1c, init its list/pos fields, inst[+0x20]=*param_2, record start (+0x24/+0x28=0, +0xb8/+0xbc from param_2[2..3]), out[0]=(param_2[5]==0), FUN_0062ef00(frame,0x45), forward base.
 0x3e -> FUN_0060ec30(param_2) (swipe update). 0x3f -> FUN_0060ee70. 0x45 -> FUN_0060e210 (inertia tick).
 0x21 or >0x55: assert inst!=0 (0x117); fetch content grandchild proc, FUN_0062ef40(child,msg,param_2,param_3), then forward base (delegates unknown/user messages into content child).

GET/SET (msg as signed sentinel 0x7ffffff2..0x7fffffff):
 0x7ffffff2: refresh scrollbar (slot1 child), FUN_0062cfc0(child+4,1) else fatal 0x480, FUN_0062fcb0, FUN_0062f470 invalidate.
 0x7ffffff3: SET V scroll pos (slot3) -> FUN_0060a400 + FUN_0060f150 relayout.
 0x7ffffff4: swipe-sample: inst[+0x2c]=*param_2, inst[+0x30]=param_2[1]; enable/disable capture FUN_006302c0(frame,cap,rel) based on active-id & scrollbar hittest (slots 2/3, FUN_0062e3a0).
 0x7ffffff5: -> FUN_0060f0b0(param_2).
 0x7ffffff6: SET inst[0]=param_2 (content/bounds pointer).
 0x7ffffff7: SET H scroll pos (slot2) -> FUN_0060a400 + relayout.
 0x7ffffff8: (re)create inner scroll child: destroy slot1 (FUN_0062c550) then FUN_0062bfc0(frame,style|0x300,1,param_2[1],param_2[2],0).
 0x7ffffff9: SET viewport rect / position both scrollbars (slots 2 & 3) via FUN_0060a2f0; asserts 0x412 if rect inverted.
 0x7ffffffa: SET client bounds inst[+8]=param_2; FUN_0062f470 invalidate.
 0x7ffffffb: GET V-scroll info (slot3): out[0]=pos(FUN_0060f4d0), out[1..2]=range(FUN_0061b9b0), out[3]=page(FUN_0059fea0); null out -> fatal 0x158; forward base.
 0x7ffffffc: GET content child handle (slot0) -> out[0]; null out -> fatal 0x3fa; forward base.
 0x7ffffffe: GET H-scroll info (slot2) -> out[0..3]; else FUN_0046dac0 fallback; forward base.
 0x7fffffff: GET inner scroll child (slot1) -> out[0]; null out -> fatal 0x3ea; forward base.

- **Create recipe:**

CtlView is a real paintable derived control (class registered through the control system; base paint/layout handled by parent proc chain via FUN_00647170). To instantiate:

1. Create the control frame with class FrameProc=0x0060d410 as a child of the target parent, i.e. the engine sends msg 0x09 to this proc with:
   - msgframe[0] = frame handle (filled by creator FUN_0062bfc0(parent, style, child, proc, userdata, 0))
   - msgframe[2] = &storage (storage must be 0 pre-create, else fatal 0x104)
   - msgframe[4] = creation flags; bit0 -> inst[+0x0c] style latch.
   - param_2[0] = OPTIONAL pointer to a nested-content descriptor {style, childProc, userdata}; 0 for none.
2. Style word: base 0x20; children are always OR'd with 0x300. Scrollbar behavior is encoded in the FRAME style read via FUN_0062fe20: vertical = 0x10000 (always) XOR 0x20000 (auto) — pick AT MOST ONE; horizontal = 0x8000 (always) XOR 0x40000 (auto) — pick AT MOST ONE. Setting both of a pair is fatal.
3. Warm-ups after create (optional, in any order): 0x7ffffffa to bind client-bounds float rect; 0x7ffffff9 to set viewport rect and seat scrollbars; 0x7ffffff8 to (re)install the inner scroll child with your own proc/userdata; 0x7ffffff3 / 0x7ffffff7 to set initial V/H scroll positions.
4. Content: either pass the descriptor in step 1 (param_2[0]) or later fetch slots with the GET messages (0x7ffffffc content child, 0x7fffffff inner child) and populate.
5. Sizing: send 0x38 (MEASURE) to have the view compute/clamp content min-max, and rely on base paint (msg 0x05) which seeds the draw-style block. Scrolling driven by 0x2f (wheel), 0x31 (scrollbar command), 0x3d/0x3e/0x3c/0x45 (touch swipe + inertia).
6. Teardown: msg 0x0b frees animator + instance and nulls storage.

- **Crash gotchas:**

FUN_00487a80(code) is the no-return fatal assert. Observed triggers in CtlView:
 - 0x104: msg 0x09 (CREATE) when *(msgframe[2]) already non-zero -> double-create.
 - 0x117: any message that dereferences the instance (0x13,0x2f,0x31,0x37,0x38,0x3c,0x3d,0x3e,0x3f,0x45, 0x21/>0x55, 0x0b, all 0x7ffff* getters/setters) when instance is NULL -> message sent before CREATE or after DESTROY (use-after-free).
 - 0x19c: both vertical scroll styles set (frame style has 0x10000 AND 0x20000).
 - 0x19d: both horizontal scroll styles set (frame style has 0x8000 AND 0x40000).
 - 0x480: msg 0x7ffffff2 when scrollbar slot-1 child (FUN_0062cfc0(child+4,1)) is missing.
 - 0x412: msg 0x7ffffff9 with an inverted/empty viewport rect (*param_2 > param_2[2] or param_2[1] > param_2[3]).
 - 0x158: msg 0x7ffffffb or 0x7ffffffe (V/H scroll info GET) with param_3 (out) == NULL.
 - 0x3fa: msg 0x7ffffffc (content child GET) with param_3 == NULL.
 - 0x3ea: msg 0x7fffffff (inner child GET) with param_3 == NULL.
Other hazards: the inertia animator at inst+0x1c (alloc'd on 0x3d, ~200 bytes) is only freed on msg 0x0b or on matching 0x3c (id at inst+0x20); starting a swipe (0x3d) without ending it (0x3c) before an unrelated realloc leaks/overwrites it. Base-proc forwarder FUN_00647170 deliberately does NOT forward msg 9 or 0xb to parents, so create/destroy are terminal at this level — do not expect base classes to see them.


### CtlBtn  (EXE 0x0060f4f0, confidence: high)

- **WASM:** unresolved (WASM symbol not needed; identity fixed by "P:\Code\Engine\Controls\CtlBtn.cpp" assertion string in the case-9 allocator FUN_006102b0)
- **Assertion file:** P:\Code\Engine\Controls\CtlBtn.cpp
- **Struct layout:**

CtlBtn instance = *(msgframe[2]); allocated 0x1da (474) bytes via FUN_0047f340("...CtlBtn.cpp",0x1da). Verified fields (rest of the 0x1da block is base/parent Ctl state managed by FUN_006123a0/FUN_0062c370):
+0x00 uint  flags/state word. bit0(&1)=HIGHLIGHT/hover (returned by msg 0x58; set/cleared by msg 0x57 and by click helper FUN_0060f2a0), bit1(&2)=PRESSED/down (toggled by msg 0x3b/0x5d), bit2(&4)=CHECKED/pushed-selected (returned by msg 0x59; toggled by 0x24/0x2c/0x2e/0x56). NOT initialized by create (relies on FUN_0047f340 zero-fill).
+0x04 wchar_t* label text buffer (set by 0x5c/appended by 0x3a; freed on destroy). init 0.
+0x08 uint    label buffer capacity in chars. init 0.
+0x0c uint    label length in chars. init 0.
+0x10 uint    text/render style flags. init 0x80.
+0x14 int     cached layout/glyph-run id (or selected-glyph index); init 0xffffffff, reset to -1 on label change; consumed by 0x4c/0x38.
+0x18 char*/wchar_t* icon or texture name string, duplicated via FUN_0046fda0 by msg 0x5b, freed on destroy.
+0x1c void*   userdata/notify context, set by msg 0x5a.
+0x20 float   press animation value (set by msg 0x5d, read by icon-measure FUN_0060ff50).
+0x24 float   preferred/content width  (init _DAT_00937edc; used by size-query msg 0x13).
+0x28 float   preferred/content height (init _DAT_00937edc; used by size-query msg 0x13).

- **Message protocol:**

Dispatched as FrameProc(msgframe,payload,out); switch on msgframe[1]=msg. frame handle = msgframe[0], instance ptr = *(msgframe[2]), payload = arg2, out = arg3. Unhandled/fallthrough forwards to parent via thunk_FUN_00647170. Cases:
0x01 PAINT face: only when *payload==0; draws bg quad from payload rect [2..5]+/-1 with tex/uv, color = disabled 0xFF404040 / enabled 0xFF808080 / hovered-or-focused 0xFF8080FF (probes own state via self-msg 0x58 highlight & 0x59 checked). FUN_0062b2d0.
0x04 INSTALL PARENT PROC: *(payload[3]) = FUN_006123a0 (parent chain -> FUN_0062c370 base template).
0x08 ICON/CONTENT MEASURE+EMIT: FUN_0060ff50; positions icon (payload[6]=tex,[7]=frame), emits label paint via self-msg 0x5f, writes measured w/h back to payload[9],[10].
0x09 CREATE/ALLOC: FUN_006102b0 allocs 0x1da CtlBtn.cpp instance, stores at *(msgframe[2]); seeds label from payload, then warms up: FUN_0062ccd0(frame,0x39,0), FUN_0062ef00(frame,0x4c), and applies focus/tab style via bits 0x800000/0x4000/0x2000.
0x0b DESTROY: frees +0x18 icon str, frees +0x04 text buf, zeroes +0x04/+0x08/+0x0c, frees object (FUN_005acaeb).
0x0c,0x21,0x25,0x36 INVALIDATE/redraw: FUN_0062bd40.
0x13 QUERY PREFERRED SIZE: if +0x24>0 and +0x28>0, out[1]=+0x24, out[2]=+0x28 then forward; else fall through.
0x15 QUERY DEFAULT/MIN SIZE: out[0..3] = _DAT_0093c89c.
0x20 ACTIVATE/CLICK route: FUN_0060f2a0 (notify parent, radio-group siblings clear via 0x57).
0x24 PRIMARY CLICK/SELECT: toggles checked bit2 when selectable (FUN_0062e2a0) then FUN_0060f2a0 if style 0x20000.
0x2c POINTER w/ BUTTON STATE: toggle checked bit2 driven by payload[4]/[5]/[4]&1.
0x2e RELEASE: clears pressed, fires click FUN_0060f2a0 when not style 0x20000.
0x38 LABEL MEASURE/LAYOUT: FUN_00610580.
0x39 FOCUS/ENABLE CHANGE: FUN_0062bd80(frame,0x50)+FUN_0062f110 (restyle/relayout).
0x3a APPEND TEXT: grows label at +0x04/+0x0c, restyle 0x40.
0x3b SET PRESSED: *inst ^= 2, FUN_00630080 anim(+0x20), restyle 0x40.
0x4c COMMIT/RENDER TEXT run using +0x0c/+0x14/+0x08.
0x56 SET CHECKED: if bit2 not already set, FUN_0060f2a0.
0x57 SET ENABLED/HIGHLIGHT: *inst bit0 = (payload!=NULL), invalidate+restyle.
0x58 GET HIGHLIGHT: assert(out!=NULL,0x152); *out = *inst & 1; forward.
0x59 GET CHECKED: assert(out!=NULL,0x15c); *out = (*inst>>2)&1; forward.
0x5a SET USERDATA/NOTIFY CTX: *(inst+0x1c)=payload; restyle 0x10.
0x5b SET ICON STRING: free old +0x18, +0x18 = FUN_0046fda0(payload) dup; restyle 0x10+relayout.
0x5c SET LABEL TEXT: assert(payload!=NULL,0x196); reset +0x14=-1, replace +0x04 buffer, copy string, relayout (FUN_00632d90).
0x5d SET PRESSED w/ ANIM value: toggles bit1, stores anim at +0x20 via FUN_00630080/FUN_00630040.
0x5e SETTER: FUN_00610420.
0x5f PAINT LABEL: FUN_0062bb30 with text color chosen by enabled(FUN_0062e2a0)/checked(FUN_0062e320) state.
default: forward to parent FUN_006123a0.

- **Create recipe:**

1) Create the primitive frame with THIS proc: FUN_0062bfc0(parent, styleFlags, childId, proc=FUN_0060f4f0, userdata, 0). The frame system auto-sends msg 4 (parent-proc install -> FUN_006123a0 -> FUN_0062c370) then msg 9 (alloc 0x1da CtlBtn instance stored at *(msgframe[2])). The msg-9 handler self-warms 0x39 and 0x4c and applies focus/tab style bits 0x800000 (tab-stop group), 0x4000 (tab-stop), 0x2000, so no manual warm-up needed.
2) Style bits that matter (read via FUN_0062fe20(frame,mask)): 0x20000 = "click routes to parent on down" behavior for 0x24/0x2e; 0x90000/0x40000/0x100000/0x80000/0x10000 gate icon layout & radio-group propagation in FUN_0060ff50/FUN_0060f2a0; 0x600000 field selects label size scale (_DAT_009407b8/_DAT_00a500d0/_DAT_00940ee0).
3) Set label: dispatch msg 0x5c with payload=wchar_t* (non-NULL). Append with 0x3a.
4) Set icon/texture name: msg 0x5b with payload=string.
5) Set preferred size: write instance +0x24 (w) and +0x28 (h) as floats (both >0) so msg 0x13 reports them; otherwise 0x15 returns global default _DAT_0093c89c.
6) Hook notify context via 0x5a; enable/disable-highlight via 0x57 (payload!=NULL sets, NULL clears); set checked via 0x56; press visual via 0x3b/0x5d.
7) Query state: msg 0x58 -> highlight bit, msg 0x59 -> checked bit (both need a valid out buffer).

- **Crash gotchas:**

- msg 0x58 asserts FUN_00487a80(0x152) and 0x59 asserts (0x15c) when out (param_3) is NULL — always pass a 4-byte out buffer to state getters.
- msg 0x5c (set label) asserts (0x196) when payload string is NULL.
- msg 9 double-create: FUN_0047f340 asserts if the instance slot at *(msgframe[2]) is already populated — never send create twice.
- Label writes 0x5c / append 0x3a assert (0x171) on source/dest buffer OVERLAP (aliasing the control's own +0x04 buffer as the source string).
- 0x4c and label-measure 0x38 assert (0x24b) when the glyph/label index (+0x14) >= count (+0xc/+0x18 field) — do not feed a stale +0x14 after buffer shrink; 0x5c resets it to -1.
- Icon measure FUN_0060ff50 asserts (0x238) if computed rect is inverted (min>max), and computes with _DAT_009407b0 scale — feeding a zero/NaN icon frame can produce a degenerate rect.
- Instance +0x00 flags rely on zero-init from the allocator; if the alloc path is bypassed the state bits are garbage (paint reads highlight/checked immediately).


### CtlImageList  (EXE 0x00611410, confidence: high)

- **WASM:** unresolved (mapped via assertion string P:\Code\Engine\Controls\CtlImageList.cpp @ EXE 0x00a50144)
- **Assertion file:** P:\Code\Engine\Controls\CtlImageList.cpp (EXE string @ 0x00a50144; class tag "HFrameImageList" @ 0x00a51978)
- **Struct layout:**

HFrameImageList instance = 12 bytes (0xc), allocated in case 9 via FUN_0047f340("...CtlImageList.cpp", 0x97) and freed in case 0xb via FUN_005acaeb(inst, 0xc). The 0x97 is the source LINE arg, NOT the size -- the authoritative size is the free size 0xc (only 3 dwords are ever touched). Layout:
  +0x00 dword frameHandle   -- = msgframe[0] (the owning frame); target of FUN_0062ede0/FUN_0062bd80/FUN_0062b290
  +0x04 dword imageResource -- refcounted image/atlas handle; 0 = none. AddRef=FUN_0046fda0, Release=FUN_0046f9b0
  +0x08 int   imageIndex    -- index into the image; 0xffffffff (-1) = none
Instance pointer slot = *(msgframe[2]) (piVar1 = param_1[2]; instance stored at *piVar1).

- **Message protocol:**

FrameProc FUN_00611410(msgframe=param_1, payload=param_2, out=param_3); dispatches switch(msgframe[1]=msg); every branch tail-calls the base default proc thunk_FUN_00647170. inst = *(int*)msgframe[2]; fields via inst[0..2].
- case 0x08 DRAW/BLIT: if imageResource(+4)!=0 AND imageIndex(+8)!=-1: builds rect{0,0, payload[1], payload[2]} and blits via FUN_0062b290(frame, &rect, imageResource, imageIndex, 5, 0), then base. This is the render path (control is drawn on explicit msg 8, it does NOT hook the normal paint msg 1).
- case 0x09 CREATE: assert *slot==0 (line 0x96); alloc 12B (HFrameImageList); [0]=frame,[4]=0,[8]=-1; store at *slot; FUN_0062ede0(frame,0,0xffffffff) (clear style). If payload[0]!=0 (initial spec {handle,index}): assert *spec!=0 (0x54); Release(old img); [4]=AddRef(spec[0]); [8]=spec[1]; FUN_0062bd80(frame,0x20) (invalidate).
- case 0x0b DESTROY: assert *slot!=0 (0x9c); Release(imageResource); free 12B; *slot=0.
- case 0x24: relay FUN_0062ee80(frame, 8, payload, 0) (forward sub-msg 8 to owning frame subsystem).
- case 0x25: relay FUN_0062ee80(frame, 7, payload, 0).
- case 0x26: relay FUN_0062ee80(frame, 9, payload, 0).
- case 0x38 GET IMAGE SIZE: if no image ([4]==0 || [8]==-1): write {0,0} to *(payload[2]). Else FUN_0062da90(&sz, imageResource) then write {w,h} to *(payload[2]).
- case 0x56 GET IMAGE (out {handle,index}): assert out!=0 (0x3f); if [4]!=0: *out=AddRef([4]); out[1]=[8]. else *out=0; out[1]=[8].
- case 0x57 GET INDEX: assert out!=0 (0x4c); *out = imageIndex(+8).
- case 0x58 SET INDEX: assert imageResource[4]!=0 (0x5f, image must already be set); [8]=payload; FUN_0062bd80(frame,0x20) invalidate.
- case 0x59 SET IMAGE {handle,index}: FUN_006117e0(inst,payload): assert payload[0]!=0 (0x54); Release([4]); [4]=AddRef(payload[0]); [8]=payload[1]; FUN_0062bd80(frame,0x20) invalidate.
- default: base proc only.

- **Create recipe:**

Created as a CHILD frame whose proc is the CtlImageList trampoline. Trampoline LAB_00611400 = `E9 0B 00 00 00` (jmp +0xb -> FUN_00611410); always pass &LAB_00611400 (0x00611400) as the proc, not 0x611410.
Reference create (from owner FUN_005146c0 case 9): 
  child = FUN_0062bfc0(parentFrame, flags=0, childOrder=0, proc=&LAB_00611400, userdata, 0);
  FUN_0062fcb0(child, 0);   // style/order warm-up
Sequence:
  1. FUN_0062bfc0(parent, 0, order, &LAB_00611400, userdataPtr_or_0, 0) -> emits msg 9 (CREATE); alloc + style-clear happen there.
  2. Optionally pass an initial image spec pointer {handle,index} as payload[0] at create; else send msg 0x59 afterward to set the image, then msg 0x58 to change index.
  3. Query natural size with msg 0x38 (returns image w,h into out). Parent owns positioning/sizing; there is no self-size (0x15) handler.
  4. Draw by sending msg 0x08 with payload[1]=dest w, payload[2]=dest h.
Warm-ups actually observed: FUN_0062ede0(frame,0,-1) (clear style, internal to create) and FUN_0062bd80(frame,0x20) (invalidate, internal to every image/index set).

- **Crash gotchas:**

All guards below call FUN_00487a80(code) which is a NO-RETURN assert (hard crash):
- msg 9 into an already-populated slot: assert *slot==0 (0x96). Never send CREATE twice.
- msg 9 with a spec whose handle is 0: assert *spec!=0 (0x54).
- msg 0xb DESTROY when *slot==0 (never created / double destroy): assert (0x9c).
- msg 0x58 SET INDEX before any image is set (imageResource==0): assert (0x5f). Set the image (0x59) first.
- msg 0x59 / FUN_006117e0 with a null image handle (payload[0]==0): assert (0x54).
- msg 0x56 with null out ptr: assert (0x3f); msg 0x57 with null out ptr: assert (0x4c).
- FUN_0047f340 second arg (0x97) is a SOURCE LINE, not the size -- do not treat the instance as 151 bytes; it is 12 bytes (free size 0xc). Only [0],[4],[8] are valid.
- imageResource is refcounted: every SET releases the previous handle and AddRefs the new one; DESTROY releases. Bypassing the frame proc to poke [4] directly leaks/underflows the image refcount.


### CtlImg  (EXE 0x00611890, confidence: high)

- **WASM:** ram:8092d85f
- **Assertion file:** P:\Code\Engine\Controls\CtlImg.cpp
- **Struct layout:**

CtlImg instance = 0x3C (60) bytes (alloc'd in case 9 via FUN_0047f340("...CtlImg.cpp",0x175=line373); freed in case 0xb via FUN_005acaeb(inst,0x3c)). Field map (dword index / byte offset):
[0]  0x00 float naturalWidth   (<- init[5])   used by paint & measure(0x38)
[1]  0x04 float naturalHeight  (<- init[6])
[2]  0x08 float quadX0 } transient LOCAL draw-rect, WRITTEN each paint (case 8),
[3]  0x0C float quadY0 } also READ by hit/coord msgs 0x56/0x57. NOT persistent geometry.
[4]  0x10 float quadX1 }
[5]  0x14 float quadY1 }
[6]  0x18 texture-resource handle (<- FUN_0046fda0(init[0]); 0 => nothing drawn)
[7]  0x1C float uvB.u  (<- init[1])  passed to draw as UV-corner-B ptr (inst+7)
[8]  0x20 float uvB.v  (<- init[2])
[9]  0x24 float uvA.u  (<- init[3])  passed to draw as UV-corner-A ptr (inst+9)
[10] 0x28 float uvA.v  (<- init[4])
[11] 0x2C anim/frame buffer ptr (dynamic array of 0x34-byte entries; NULL default)
[12] 0x30 float bufCapacity (0 default)
[13] 0x34 float bufCount    (0 default)
[14] 0x38 int   growIncrement (=4 default, set in case 9)

INIT payload struct (7 dwords, 0x1C bytes): delivered as *payload[0] in case 9, or payload directly in case 0x58.
 init[0]=ptr to image-descriptor (FUN_0046fda0 reads desc[0..4]={imageId,?,?,?,loadCallback}); may be 0
 init[1..2]=UV corner B (u,v) -> 0x1C/0x20 ; init[3..4]=UV corner A (u,v) -> 0x24/0x28
 init[5..6]=natural width/height -> 0x00/0x04

- **Message protocol:**

FrameProc(param_1=msgframe, param_2=payload). msg=param_1[1]; inst-slot piVar1=param_1[2] (**+8 => instance); frame handle=*param_1. NOTE: CtlImg uses PAINT=8 (not 1) and has NO case 4 parent-install; unhandled msgs 0x0A,0x0C-0x23,0x27-0x37,0x39-0x55 fall through to no-op return.
 8   PAINT: FUN_00611df0(frame,inst,ctx). Draws textured quad only if inst[6](tex)!=0 AND (ctx.byte0 & 0x20). Reads style FUN_0062fe20(frame,-1); style bits 0xE000 select fit mode (0=stretch-to-rect writing quad 0..w/0..h; else aspect-fit using masks 0x6000/0x4000 for center/anchor). Recomputes 0x08-0x14 quad, then FUN_0062b2d0(frame, inst+2 pos, inst[6] tex, inst+7 uvB, inst+9 uvA, 5, &tmp) -> FUN_00611830 -> free tmp.
 9   CREATE/INIT: alloc 0x3C, zero 0x2C/0x30/0x34, set 0x38=4, store into *piVar1; FUN_0062ede0(frame,0,0xffffffff) (style init); if payload init ptr!=0 acquire texture from *init via FUN_0046fda0 and copy init[1..6]; FUN_0062bd40(invalidate layout)+FUN_0062f110(repaint).
 0xB DESTROY: free tex(0x18) via FUN_0046f850; free anim buf(0x2C) via FUN_0047f3a0; zero 0x2C/0x30/0x34; free instance FUN_005acaeb(inst,0x3c).
 0x24 forward: FUN_0062ee80(frame,8,payload,0)   (re-dispatch paint)
 0x25 forward: FUN_0062ee80(frame,7,payload,0)
 0x26 forward: FUN_0062ee80(frame,9,payload,0)
 0x38 MEASURE (aspect-fit): in payload[0]=maxW, payload[1]=maxH, payload[2]=out ptr; scales natural (0x00,0x04) to fit within (maxW,maxH) preserving ratio, writes out[0]=w,out[1]=h.
 0x56 UV->local: payload[0]=u,[1]=v,[2]=out; maps normalized into current draw-rect 0x08-0x14: out.x=u*(x1-x0)+x0, out.y=(1-v)*(y1-y0)+y0. Asserts FUN_00487a80(0x238) if x0>x1 or y0>y1.
 0x57 local->UV: inverse; out=(0,0) then out.u=(px-x0)/(x1-x0), out.v=1-(py-y0)/(y1-y0). Asserts 0x238 if rect inverted; no-op if zero-size.
 0x58 SET-IMAGE (runtime): FUN_006121b0(frame,inst,init) — free old tex, acquire new from *init, copy init[1..6], invalidate+repaint. Asserts FUN_00487a80(0xE0) if inst NULL.
 0x59 SET/RESIZE ANIM FRAMES: grows 0x2C buffer (0x34-byte entries) toward requested count payload[0]; realloc via FUN_004738f0, updates capacity 0x30/count 0x34; asserts FUN_00487a80(0x171) on aliasing/overlap during grow.

- **Create recipe:**

Concrete pattern (from creator FUN_0060b650):
 1. frame = FUN_0062bfc0(parentFrame, 0 /*flags*/, isChild /*0 or 1*/, FUN_00611890 /*proc*/, 0 /*userdata*/, 0).
 2. Style: FUN_0062ede0(frame, 0, 0xffffffff) for a standalone image; for an embedded child use FUN_0062ede0(frame, 0x11, 0) then FUN_0062fbf0(frame, hostData). Set fit-mode bits (0xE000 group) here if non-stretch scaling wanted.
 3. Set the image with a 7-dword init struct via the dispatcher: FUN_0062ef40(frame, 0x58, &init, 0), where
      init[0]=ptr to a valid image descriptor (descriptor[0]=imageId must be nonzero; or pass 0 for empty),
      init[1..2]=UV corner B (u1,v1 normalized = pxBR/texSize),
      init[3..4]=UV corner A (u0,v0 normalized = pxTL/texSize),
      init[5]=naturalWidth, init[6]=naturalHeight (floats).
    (Equivalently msg 0x58 can be re-sent any time to swap the image.)
 4. Position/parent layout: FUN_0062f770(frame, layoutParent, rect).
 Warm-ups handled internally by case 9/0x58: FUN_0062bd40 (invalidate) + FUN_0062f110 (repaint). Sizing/measurement: send 0x38 to get aspect-fit dims. Draw only occurs once texture (0x18) is set and frame paint-flag (ctx&0x20) is on.

- **Crash gotchas:**

1. Coord msgs 0x56/0x57 read the TRANSIENT draw-rect at 0x08-0x14 which is only written during a paint (case 8). Calling them before the control has painted at least once reads stale/zero rect and either asserts FUN_00487a80(0x238) (inverted rect) or yields garbage. Never call 0x56/0x57 on an unpainted/hidden CtlImg.
2. Image descriptor validation: FUN_0046fda0 asserts 0x115 if init[0] descriptor ptr expected-but-NULL, and 0x117 if descriptor[0] (imageId)==0. Pass init[0]=0 to intentionally create an empty image; otherwise ensure descriptor[0] is a valid nonzero image id.
3. Anim-frame grow (0x59) asserts 0x171 (FUN_00487a80) if the new/old buffers alias/overlap during realloc-copy; don't feed it an aliased source.
4. SetImage (0x58) asserts 0xE0 if the instance pointer is NULL (message sent to a frame whose CtlImg instance wasn't created via case 9 first).
5. Struct size is fixed at 0x3C; the destroy path frees exactly 0x3c (FUN_005acaeb(inst,0x3c)) and frees tex(0x18) then anim buf(0x2C) - double-free if you also free those externally.
6. This proc has NO case-4 base/parent installer and PAINT is msg 8 (not the generic msg 1); do not assume the generic template message numbering.


### CtlDef (CtlDefProc)  (EXE 0x00612240, confidence: high)

- **WASM:** ram:80d9bfb9
- **Assertion file:** P:\Code\Engine\Controls\CtlDef.cpp (string @ 0x00a501c0, xref from 0x00612275 inside the proc)
- **Struct layout:**

CtlDef is a NON-allocating layout/definition frame proc: it installs no per-instance heap struct (its case 9 does not call FUN_0047f340 like leaf controls do). It only reads the shared frame node + the FrameMsgHdr.

FrameMsgHdr (param_1, treated as int*):
  +0x00 int   frameId        (frame handle / index into global frame table DAT_00bef81c, count DAT_00bef824)
  +0x04 int   msg            (switch selector = param_1[1])
  +0x08 void* wparam/payload (param_2 in dispatch; case 0x24 reads *(byte*)(payload+4) style-like flags & 6)
  +0x0c int   lparam
  +0x10 int   extra
  +0x14 uint  procStackIndex (param_1[5]; base-forward uses it to select the next proc below this one)

Frame node (resolved from frame table by base-forward FUN_00647170):
  +0xa8 proc-stack array base (entries 0xc bytes each: [0]=code* proc, [+4]=field, [+8]=userdata)
  +0xb0 uint proc-stack count (bounds-checked; asserts on overflow)
  +0xbc associated child/instance handle (returned by tree-nav FUN_0062caa0 and current-def accessor FUN_0062e4b0)

Style flags read via FUN_0062fe20(frame,mask):
  mask 0x1000 -> child element is selectable/activatable (child proc FUN_006127c0 sets it as "current" via FUN_0062e560)
  mask 0x0020 -> child is skipped by the msg 0x0c teardown broadcast
  mask 0x0006 -> if set, msg 0x24 does NOT run the layout/child build

Global "current definition" state: FUN_0063ef80 backing store; FUN_0062e4b0 reads current->+0xbc; FUN_0062e560 sets current (0=clear); FUN_0062e200 tests frame-vs-current relationship (FUN_0064d210).

- **Message protocol:**

Switch on msg = param_1[1]. Actively handled cases (everything else, incl. 0/1-paint/0xb-free, falls through to base proc thunk_FUN_00647170):

case 0x02 (activate/build): if payload!=0 and this frame is NOT already the current def (FUN_0062e200==0): create a child selectable element via FUN_0062caa0(frame,1,0,0,FUN_006127c0,0), run layout/tab-order traversal FUN_00612560(child), then forward to base.
case 0x09 (attach/register): FUN_0062d6f0(frame,FUN_00612240) registers the frame handle (FUN_00647db0) and attaches the proc/data (FUN_00647e00); asserts 0xaf/0x48e if frame==0. NO instance allocation. NOT forwarded to base.
case 0x0c (teardown/hide broadcast): FUN_006126a0 recursively walks children (nav 1=first child, 5=next sibling); for each child with style bit 0x20 clear, calls FUN_0062c9c0(child,payload) and recurses; then forward to base.
case 0x21 (deactivate): create the child selectable + init (FUN_00612560); if this frame IS the current def, clear current via FUN_0062e560(0).
case 0x24 (conditional build): if (*(byte*)(payload+4) & 6)==0, behave like case 0x02 (build child + layout); else forward to base.
cases 0x03-0x08, 0x0a, 0x0b, 0x0d-0x20, 0x22, 0x23 and default: pure pass-through to base proc thunk_FUN_00647170(hdr,wparam,out).

Base forward (FUN_00647170) walks the frame's proc-stack (frame+0xa8, count frame+0xb0) using procStackIndex (hdr[5]) to invoke the next-lower proc, rebuilding a fresh header (copies hdr[0..4], sets [2]=proc-entry addr, [4]=entry userdata). It explicitly REFUSES to forward msg 9 and msg 0xb to base.

- **Create recipe:**

CtlDef is a base/layout definition proc, not a leaf paintable widget; you "create" it by installing FUN_00612240 as a frame's proc, not by allocating an instance.
1. Create/obtain a frame and push CtlDefProc (0x00612240) onto its proc-stack via the frame-create/attach primitive FUN_0062caa0(parent, flags, child, ..., proc=FUN_00612240, userdata). (FUN_0062caa0 doubles as tree-nav when called with 3 args, returning child handle at node+0xbc.)
2. Send msg 0x09 (attach) with a valid non-null frameId + data pointer so FUN_0062d6f0 registers it (null frame -> assert 0x48e/0xaf).
3. Drive layout by sending msg 0x02 (or msg 0x24 with (payload+4)&6==0) with a non-null payload; CtlDef spawns a selectable child element (proc FUN_006127c0, activation style bit 0x1000) and runs the tab-order/layout traversal FUN_00612560. Child selectable becomes "current def" when clicked (style 0x1000 -> FUN_0062e560).
4. Use msg 0x21 to deactivate (clears current if it was this def) and msg 0x0c to broadcast teardown/hide to visible (style&0x20==0) children recursively.
No paint pass, no size-query, no per-instance struct are implemented here — those are provided by the underlying base proc reached through thunk_FUN_00647170.

- **Crash gotchas:**

- msg 0x09 on a null frame -> assert 0x48e (FUN_0062d6f0) / 0xaf (FUN_00612240). Never send attach before the frame handle is valid.
- FUN_0062caa0 asserts 0xbb0 if the frame arg is 0 (any create/nav call). FUN_0062e200 asserts 0xbcf if frame==0 (msg 0x02 relationship test).
- FUN_00612560 layout recursion asserts 0x44 if a child create fails mid-traversal.
- Base forward thunk_FUN_00647170 requires the frame be live in the global table (DAT_00bef81c within DAT_00bef824) and procStackIndex (hdr[5]) < proc count (frame+0xb0); otherwise asserts 0x256/0x221/0x223/0x24b. Passing a stale/out-of-range header index crashes here.
- Base proc will NOT forward msg 9 or 0xb: alloc/attach (9) and free (0xb) must be fully serviced by the control's own proc chain; delegating them to base is a silent no-op that leaks/asserts elsewhere.
- CtlDef has no case 1 (paint) and no case 0x15 (size query); relying on CtlDefProc alone to paint/size a frame yields nothing — it must sit above a paint-capable base proc in the stack.
- msg 0x24 gates on (payload+4)&6; a null or short payload here dereferences (payload+4) unconditionally -> ensure payload points to a struct with a valid flags byte at +4.


### CtlFrameList  (EXE 0x00612ad0, confidence: high)

- **WASM:** ram:00107f27 (assertion-file string; proc symbol not exported by name)
- **Assertion file:** P:\Code\Engine\Controls\CtlFrameList.cpp (EXE); ../../../../Engine/Controls/CtlFrameList.cpp (WASM ram:00107f27)
- **Struct layout:**

CtlFrameList instance = 0x74 bytes, allocated in case 9 via FUN_0047f340("P:\\Code\\Engine\\Controls\\CtlFrameList.cpp", 0x74). Accessor = FUN_00613b00(msgframe) = **(msgframe+8) (asserts 0x86 if null). Fields touched by this proc (first 0x20 bytes; remaining 0x54 reserved/unused here):
+0x00 (dw0) HFRAME  owner/host frame handle (= *param_1 at alloc). Every op passes *instance to the generic frame API (FUN_0062caa0 tree-nav, FUN_0062fe20 style-read, FUN_0062bfc0 create).
+0x04 (dw1) fn      layout callback A: (items*, param2) -> void. Set via msg 0x62. Init 0.
+0x08 (dw2) fn      layout callback B: (items*, param2, userdata@+0x0c) -> void. Set via msg 0x63. Takes priority over dw1. Init 0.
+0x0c (dw3) void*   userdata for dw2. Set via msg 0x63.
+0x10 (dw4) fn      measure callback A: (items*, param2) -> void. Set via msg 0x64. Init 0.
+0x14 (dw5) fn      measure callback B: (frame, items*, param2, userdata@+0x18) -> void. Set via msg 0x65. Priority over dw4. Init 0.
+0x18 (dw6) void*   userdata for dw5. Set via msg 0x65.
+0x1c (dw7) fn      comparator/sort predicate: (frameA, frameB) -> int(nonzero if A precedes B). Set via msg 0x66. Drives sorted-insert (0x57), reposition (0x61), full re-sort (0x60). Init 0 (=unsorted). Also read as (instance+0x1c) in msgs 0x60/0x66.
+0x20..0x73 reserved/uninitialized (not referenced by FUN_00612c80).
"items*" is a scratch dynamic array built by FUN_006127f0(&arr, style2000flag): enumerates children (FUN_0062caa0 rel 1=first,5=next) into a heap buffer (freed with FUN_0047f3a0 after layout/measure). Layout is: array[0]=data*, array[1]=count. Style bit 0x2000 = include hidden items; style 0x4000 = list supplies its own width (default measure sets width = param2[0]).

- **Message protocol:**

FrameProc(param_1=msgframe, param_2=payload/in, param_3=out). Dispatches on msgframe[1]=msg. NO case 1 (paint) and NO case 4 (install-base): this is a non-painting layout/model container control, not a template.
LIFECYCLE:
 0x09 ALLOC: assert 0x73 if slot already set; alloc 0x74, init dw0=frame, dw1/2/4/5/7=0.
 0x0b FREE: FUN_005acaeb(instance,0x20); slot=0.
 0x0a,0x0c-0x30,0x32-0x36,0x39-0x55: no-op (break to return).
LAYOUT/QUERY:
 0x13 (19) SIZE/CONTENT-QUERY: *param_3 = first-child handle (FUN_0062caa0(frame,1,0)) if nonzero.
 0x31 (49) if payload count>6: FUN_0062ee80(frame,7,&rect,0) forward rect (scroll/place).
 0x37 (55) ARRANGE children: collect items (respect style 0x2000); if dw2 -> dw2(items,param2,dw3); elif dw1 -> dw1(items,param2); else default = stack each child vertically (FUN_0062f770 places each, decreasing remaining height by item height). Frees items.
 0x38 (56) MEASURE children: collect items; if dw5 -> dw5(frame,items,param2,dw6); elif dw4 -> dw4(items,param2); else default = accumulate: width=max(child widths), height=sum(child heights) into size-out param_2[2]; if style 0x4000 unset, width forced to param2[0]. Frees items.
ITEM OPS (get/set 0x56+):
 0x56 (86) CLEAR ALL: FUN_0062c760(frame) destroy all children.
 0x57 (87) ADD/INSERT: payload {flags, childId, itemProc, userdata}; child = FUN_0062bfc0(frame, flags|0x300, childId, itemProc, userdata, 0); if comparator dw7 set, walk siblings (rel 1/3) and reorder to sorted slot (FUN_0062fdb0/FUN_0062f470) or append (FUN_00613d30); *param_3 = new child handle. Asserts 0x149/0x14a on null child/comparator race.
 0x58 (88) REMOVE by id: FUN_0062cfc0(frame,id) then FUN_0062c550(child); assert 0x203 if not found.
 0x59 (89) GET item by relation: selector param_2[0] (int 0/1/2/3): 0=>rel5 from ref param_2[1] (asserts 0x212 if ref missing), 1=>rel6 (asserts 0x218), 2=>rel1 (first child), 3=>rel3 (last child); default asserts 0x223. Writes handle->*param_2[2], id (FUN_0062d0a0)->*param_2[3].
 0x5a (90) GET next VISIBLE: like 0x59 but loops skipping !visible (FUN_0062e3a0). Asserts 0x242/0x249/0x256.
 0x5b (91) FIND FRAME by id -> *param_3 (=CtlFrameListGetItemFrameId). Assert 0x276 if param_3 null.
 0x5c (92) GET item screen rect -> param_3[0..3]=(x,y,x+w,y+h). Assert 0x27f null-out / 0x282 not-found.
 0x5d (93) IS-EMPTY -> *param_3 = (first child==0). Assert 0x29b null-out.
 0x5e (94) GET item visibility -> *param_3 = FUN_0062e3a0(child). Assert 0x2a6 null-out / 0x2a9 not-found.
 0x5f (95) REORDER item relative to another: payload {itemId, mode(0/1 before/after or 2/3), refId}; FUN_0062fdb0 + FUN_0062f470. Asserts 0x2b3/699/0x2c1/0x2cc.
 0x60 (96) RE-SORT ALL: if dw7 set, FUN_00613bf0 (full comparator sort).
 0x61 (97) REPOSITION one item after change: find by id (assert 0x2ea); if dw7 set, FUN_00613d30 re-slot.
 0x62 (98) SET layout-cb dw1; if changed, FUN_0062f470 (invalidate layout).
 0x63 (99) SET layout-cb pair dw2=fn,dw3=userdata; if changed, FUN_0062f470.
 0x64 (100) SET measure-cb dw4; if changed, FUN_0062f110 (invalidate measure).
 0x65 (101) SET measure-cb pair dw5=fn,dw6=userdata; if changed, FUN_0062f110.
 0x66 (102) SET comparator dw7; if nonzero, FUN_00613bf0 re-sort.
 0x67 (103) SET item visibility by id: payload {id, visible}; FUN_0062fcb0; if not style 0x2000 and visibility actually changed, FUN_0062f110+FUN_0062f470. Assert 0x332 if id not found.
Note: 0x59/0x5a/0x5f selectors are integer 0/1/2/3 that the decompiler shows as float bit-patterns (0.0/1.4e-45/2.8e-45/4.2e-45).

- **Create recipe:**

CtlFrameList is a layout/list container mixin attached to a host frame; it paints nothing itself and arranges/tracks child frames.
1) Create the host frame with this proc: FUN_0062bfc0(parentFrame, flags|0x300, childId, proc=0x00612ad0, userdata, 0). The frame system auto-sends msg 9 which allocs the 0x74 instance (dw0=frame). Do not send msg 9 yourself (double-init asserts 0x73).
2) (Optional, do FIRST if you want ordering) install comparator: send 0x66 with your (frameA,frameB)->int predicate. Subsequent 0x57 adds auto-insert in sorted order.
3) (Optional) install custom measure/layout: 0x64/0x65 for measure callback (measure children -> size), 0x62/0x63 for arrange callback (position children). If omitted, default = vertical stack (arrange) + sum-height/max-width (measure); default width follows parent width unless style bit 0x4000 is set.
4) Populate: for each item send 0x57 with {flags, childItemFrameId, childItemProc, childUserdata}; capture returned handle from out-param. Each item is itself a real child frame with its own proc.
5) Manipulate at runtime: 0x5b/GetItemFrameId(id)->frame, 0x58 remove(id), 0x67 setVisible(id,bool), 0x59/0x5a iterate, 0x5c getRect, 0x5d isEmpty, 0x56 clear, 0x60 re-sort.
Style flags read via FUN_0062fe20(frame,mask): 0x2000=iterate hidden items too, 0x4000=list controls its own width (skip parent-width override), 0x10000=used by subclass FUN_00613850 for scroll-to-bottom on add.
Sizing: no explicit size-set message here; the list sizes to content via the measure pass (0x38). Host frame position/size come from the standard frame API. Warm-ups: none beyond msg 9 auto-init; callbacks are optional (defaults work).
Higher-level game usage goes through subclass FUN_00613850 (parent=0x00612ad0), which adds selection/notify msgs 0x68 (clear-selection-notify), 0x69 (get selection id/frame), 0x6a (select item) and overrides 0x31/0x56/0x57/0x58/0x67 to fire selection/scroll events.

- **Crash gotchas:**

- Any get/set/layout message before msg 9 (instance null) => FUN_00613b00 asserts 0x86. Never touch a frame-list before its ALLOC.
- Re-sending msg 9 to an already-allocated slot asserts 0x73 (case 9 guard).
- 0x57 ADD with a comparator installed: asserts 0x149 if FUN_0062bfc0 returns null (bad childId/proc/parent) and 0x14a if dw7 comparator becomes null mid-insert. Verify create args before adding.
- 0x58 REMOVE / 0x5c rect / 0x5e visibility / 0x61 reposition / 0x67 setVisible all assert (0x203/0x282/0x2a9/0x2ea/0x332) when the id is not an existing child. Guard with 0x5b/0x5d first.
- Out-param (param_3) NULL asserts on 0x5b(0x276), 0x5c(0x27f), 0x5d(0x29b), 0x5e(0x2a6), and 0x69 on subclass(0x4ae). Always pass a valid out buffer.
- 0x59/0x5a/0x5f selector out of range 0..3 => assert 0x223 / 0x256 / 0x2cc; ref-frame not found for selectors 0/1 => assert 0x212/0x218 (0x242/0x249 on visible variant). Selectors are integers, not floats.
- FUN_006127f0 (used by 0x37/0x38 collect) asserts 0x91 if its output array pointer is null; it heap-allocs items and they MUST reach the FUN_0047f3a0 free path (both layout branches goto LAB_00612fb0) — do not early-return between collect and free.
- FUN_0062caa0 (tree nav) asserts 0xbb0 if frame handle is 0, so a stale/destroyed host frame crashes any op.
- Default measure overwrites width with parent width unless style 0x4000 is set; forgetting the flag makes custom-width layouts snap back.
- This proc has no paint (case 1) and no base-install (case 4): it is a container/model, not a visual template — pairing it as if it were a standalone paintable control (expecting it to draw) yields an invisible frame.


### CtlProgress  (EXE 0x00618d00, confidence: high)

- **WASM:** ? (resolved via embedded assertion string P:\Code\Engine\Controls\CtlProgress.cpp; WASM symbol not separately mapped)
- **Assertion file:** P:\Code\Engine\Controls\CtlProgress.cpp
- **Struct layout:**

CtlProgress instance = 52 bytes / 0x34 (freed as size 0x34 in case 0xb; the literal 100 passed to FUN_0047f340("...CtlProgress.cpp",100) is the __LINE__/alloc tag, NOT the struct size). Accessed via FUN_006196e0(msgframe) = **(msgframe+8) (asserts 0x76 if null). Layout by dword index [n] / byte off:
[0] 0x00  frame handle (parent GmFrame*, = *msgframe at construct)
[1] 0x04  uint value            (current progress; default 0)
[2] 0x08  uint max              (default 100/0x64)
[3] 0x0c  float rate/target     (animation target-rate; set by 0x59, consumed by 0x45 tick; also read as "has animation" in 0x45/paint)
[4] 0x10  float accumulator     (fractional sub-unit carry for animated fill; reset to 0 on 0x59)
[5] 0x14  wchar_t* custom-text buffer   (heap; set by 0x5c; freed in case 0xb via FUN_0047f3a0)
[6] 0x18  (0 / buffer sibling slot for [5])
[7] 0x1c  int custom-text length (wchar count; also "custom text present" flag)
[8] 0x20  uint flags/color = 0x80 default
[9] 0x24  wchar_t* formatted-text buffer (heap; built during paint "%u / %u" or "%u%%"; freed in case 0xb)
[10]0x28  (0 / buffer sibling slot for [9])
[11]0x2c  int formatted-text capacity (wchar count; grown to 0x40 on demand in paint)
[12]0x30  uint flags/color = 0x80 default

- **Message protocol:**

FrameProc(msgframe* p1, payload* p2, out* p3) switches on p1[1]=msg. Base proc = FUN_006123a0 (generic interactive-control base). Dispatcher = FUN_0062ef40(frame,msg,arg,out); style read = FUN_0062fe20(frame,mask). Cases:
 4  INSTALL BASE PROC: *(p2[3]) = FUN_006123a0 (parent/template proc).
 8  PAINT/RENDER: reads style FUN_0062fe20(frame,-1); if style&0x6000: bit 0x2000 -> format L"%u%%" = value*100/max, else bit 0x4000 -> format L"%u / %u" = value,max (grows fmt buffer[11] to 0x40). Copies geometry rect from p2[0,3..10], value=[1],max=[2] into a paint struct, then FUN_0062ef40(frame,0x5e,&paintbuf,0). (This control paints on msg 8, not msg 1.)
 9  CONSTRUCT: if slot *(p1[2])==0 alloc via FUN_0047f340("...CtlProgress.cpp",100); init value=0,max=100,flags[8]=[12]=0x80, all ptrs 0; store into *(p1[2]); FUN_0062ede0(frame,0,-1); post-init FUN_0062ef00(frame,0x4c). Else assert FUN_00487a80(99) (double-construct).
 0xb FREE/DESTRUCT: frees text buffers at +0x24 and +0x14 (FUN_0047f3a0), zeroes them, FUN_005acaeb(inst,0x34).
 0x38(56) SIZE/METRICS QUERY: *(p2[2])=*p2; out[1]=FUN_0062d0e0(frame)*_DAT_00948c18 (font-height scaled height).
 0x39(57) REFRESH/RELAYOUT: FUN_0062ef40(frame,0x5f, style&0x6000?7:3); FUN_0062ef40(frame,0x5f,4); FUN_0062f110(frame).
 0x3a(58) SET FMT-BUFFER CAPACITY: alloc buffer sized from p2[1] (+1)*2 bytes, aliasing-assert 0x171, store capacity in [11], FUN_0062ef40(frame,0x5f,4,0).
 0x45(69) TICK/ANIMATE: if rate[3]!=0 advance value[1] toward max using accumulator[4] and dt=*p2; steps value up (if [3]>0, toward max) or down; on reaching 0 or max, clears rate and FUN_0062ee80(frame,7,0,0); repaint via FUN_006194d0.
 0x4c(76) POST-CREATE INIT: if custom-text len[7]!=0 -> FUN_00632d90(frame,textbuf[5],0).
 0x56(86) GET VALUE: if p3 -> *p3 = *(inst+4); else assert 0x13e.
 0x57(87) GET MAX:   if p3 -> *p3 = *(inst+8); else assert 0x147.
 0x58(88) SET VALUE: inst[1]=p2; if changed, refresh FUN_0062ef40(frame,0x5f, style&0x6000?7:3).
 0x59(89) SET RATE/TARGET (float): p2!=0 (else assert 0x15b); inst[3]=*p2, inst[4]=0, FUN_0062ef00(frame,0x45) (kick animation).
 0x5a(90) SET MAX: inst[2]=p2; if changed -> refresh.
 0x5b(91) SET PERCENT (int 0..100): value = max*pct/100; if changed -> refresh.
 0x5c(92) SET CUSTOM TEXT (wchar*): asserts 0x185 if style&0x6000 (auto-formatted bars reject custom text); NULL clears (len[7]=0,cap[11]=0,refresh); else dup string into buffer[5], aliasing-assert 0x171, set len[7], FUN_00632d90.
 0x5d(93) HITTEST/POINT: FUN_0062bc20(frame,p2).
 0x5e(94) PAINT DELEGATE: FUN_00619500(paintbuf) (actual draw of the gauge fill/label).
 0x5f(95) INVALIDATE/STYLE-REDRAW: translate flags ((arg&3)->0x10, (arg&4)->0x40) then FUN_0062bd80(frame,flags).
 default: chain to base via thunk_FUN_00647170(p1,p2,p3).

- **Create recipe:**

1) Create the primitive frame with FUN_0062bfc0(parent, flags, child, proc=0x00618d00, userdata, 0). The dispatch machinery sends msg 4 (base proc FUN_006123a0 installed), then msg 9 (construct: value=0, max=100, flags 0x80/0x80), then msg 0x4c post-init automatically. Do NOT hand-alloc the instance — the proc owns it.
2) Configure via dispatcher FUN_0062ef40(frame,msg,arg,out):
   - Set range:   0x5a (max)     then 0x58 (value)   -- or single-shot 0x5b (percent 0..100).
   - Read back:   0x56 (value)/0x57 (max) with non-null out ptr.
   - Animated fill: 0x59 with float* target-rate to smoothly drive value toward max over ticks (0x45 fires on FUN_0062ef00(frame,0x45) kicks).
   - Auto-label style: set frame style bit 0x2000 => "value%%" or 0x4000 => "value / max" (via FUN_0062fe20 mask; label auto-rendered in paint). For a manual caption instead, leave 0x6000 clear and send 0x5c with a wchar_t*.
3) Layout/paint driven by host: msg 8 builds label + geometry and delegates to 0x5e/FUN_00619500. Send 0x39/0x5f to force relayout/redraw after style changes.
Sizing: query preferred height with 0x38 (font-height * _DAT_00948c18). Width comes from parent-assigned rect (p2[0,3..10]).

- **Crash gotchas:**

- Double-construct: sending msg 9 when *(p1[2]) already set -> assert FUN_00487a80(99). Let the framework construct once.
- Use-before-construct: every get/set routes through FUN_006196e0 which asserts 0x76 if instance is null. Frame must be fully created first.
- 0x56/0x57 GET require a non-null out pointer or they assert (0x13e / 0x147).
- 0x59 SET-RATE asserts 0x15b if the float* arg is null.
- 0x5c SET-CUSTOM-TEXT asserts 0x185 if the frame carries auto-format style bits 0x6000 (0x2000/0x4000) -- custom text and auto "%u/%u"/"%u%%" formatting are mutually exclusive.
- Buffer aliasing: 0x3a and 0x5c assert 0x171 (FUN_00487a80) if the source string overlaps the control's own buffer -- pass an independent string.
- 0x5b percent uses integer math max*pct/100; pct>100 overflows past max (no clamp on the multiply path). Range/max should be set (0x5a) before percent.
- 0x45 tick divides progress by rate/max internally; a zero max ([2]) can cause div-by-zero in the label path ("%u%%" uses value*100/max) -- never leave max at 0.
- Text buffers at inst+0x14 and inst+0x24 are heap-owned and freed in case 0xb; do not retain external pointers to them after destruct.


### CtlEditAutoComplete  (EXE 0x00619c80, confidence: high)

- **WASM:** unknown (WASM symbol CtlEditAutoComplete; EXE already given, not re-derived)
- **Assertion file:** P:\Code\Engine\Controls\CtlEditAutoComplete.cpp
- **Struct layout:**

Instance = 0x78 bytes, allocated in case 9 via FUN_0047f340("...CtlEditAutoComplete.cpp",0x78), constructed by FUN_00619710(this, frameId). It is a CtlEdit-derived object (parent proc FUN_00603cc0) that adds an autocomplete candidate hash-set. Layout (dword indices from constructor):
 +0x00 [0]  frameId  (the owning frame handle; *param_1 of every message = this frame)
 +0x04 [1]  wchar_t* curTextBuf  (current edit text, UTF-16; grown by FUN_004738f0; freed in dtor)
 +0x08 [2]  u32 bufCapacityChars
 +0x0C [3]  u32 textLenChars  (+1 for NUL; constructor terminates *(buf+len*2)=0)
 +0x10 [4]  u32 heapTag = 0x80  (allocator context passed as &field[4])
 +0x14 [5]  u32 entrySeqId = 0  (incremented per inserted candidate in FUN_0061a3a0)
 +0x18 [6]  u32 hashHeader  (init 0xDDDDDDDD then 0x24 = intrusive-hashtable magic/stride)
 +0x1C [7]  node sentinel (self-pointer *this+0x1c = this+0x1c; intrusive list/tree head)
 +0x20 [8]  entry-list root  (low-bit-tagged; walked to free children in dtor and enumerate in FUN_0061a3a0/FUN_00619b70)
 +0x24 [9]  u32 keyFieldOff = 0x20  (offset of hash key inside each entry node)
 +0x28 [10] entry** bucketArray = 0  (bucket = field[10] + (mask & hash)*0xC)
 +0x2C [0xb] 0
 +0x30 [0xc] u32 bucketCount = 0
 +0x34 [0xd] u32 hashMask = 0
 +0x38 [0xe] u32 maxEntries = 0x400
 +0x3C [0xf] u32 selectedFlag = 0  (cached highlight/selection state written by FUN_0061a3a0)
Candidate entry nodes are allocated separately by FUN_00619930 (assert tag 0x2CC): +0x04 wchar_t* text, +0x08 payload/user, +0x18 flag(local_8), +0x1C seqId(field[5] snapshot), +0x20 hash key, +0x28 next.

- **Message protocol:**

FrameProc FUN_00619c80(msgframe, payload, out); switches on msgframe[1] = msg. Instance fetched via FUN_0061a880 (= **(msgframe+8); asserts 0x8a if instance==0). Unhandled msgs tail-call parent CtlEdit proc via thunk_FUN_00647170.
 case 0x04 InstallBaseProc: *(payload[3]) = FUN_00603cc0 (parent = CtlEdit). Paint(1) and size-query(0x15) are NOT overridden -> inherited from CtlEdit.
 case 0x09 Create: assert(*(payload[2])==0) else FUN_00487a80(0x77); alloc 0x78; *(payload[2]) = FUN_00619710(frame).
 case 0x0B Destroy: walk child frames at +0x20 calling proc(1); FUN_00473ad0() (free hashtable); free curTextBuf(+4) via FUN_0047f3a0; zero [1..3]; FUN_005acaeb(this,0x40); *(payload[2])=0.
 case 0x20 KeyNav: if payload[0]==0x1c -> FUN_0061a030(1) (advance/next match); if payload[0]==0x1f -> FUN_0061a030(0) (previous match); else -> base.
 case 0x21 FocusChange: if payload==NULL (lost focus) -> find dropdown child FUN_0062cfc0 and destroy FUN_0062c550; else (gained) if style bit 0x8000000 set (FUN_0062fe20) -> open dropdown FUN_00619b70; then base.
 case 0x31 TextEdit(insert): FUN_0061a880; if payload[1]==0 && payload[2]==7 -> FUN_0061a1a0(payload[0],payload[3]) (incrementally add/refresh a completion), then base; else base.
 case 0x32 TextEdit(reset/replace): *out=0; if payload[2]==7 -> FUN_0061a570() (rebuild candidate list + choose best prefix match, auto-open/close dropdown), then base; else base.
 case 0x37 Layout/Position: compute dropdown popup rect relative to edit (FUN_0062d380/FUN_0062bf10/FUN_0062ef40 pass 100), clamp height vs _DAT_00937ec8, and reposition child list via FUN_0062f770; then base.
 case 0x63 (99) SetCandidates: FUN_0061a3a0(payload) bulk-loads a NUL-separated UTF-16 string block (iterates strings from payload[0], count/end via payload[2]) into the hashtable, each via FUN_00619930 + FUN_004740c0.
 default: base proc.

- **Create recipe:**

This is a CtlEdit subclass, not a standalone widget; create it exactly like a CtlEdit but with proc = 0x00619c80 (or the JMP thunk 0x00619c50).
 1. Ensure the destination instance slot *(payload[2]) is zeroed before msg 9 (framework guarantees this on a fresh frame; a reused slot triggers assert 0x77).
 2. Create the frame via the primitive FUN_0062bfc0(parent, flags, child, proc=0x00619c80, userdata, 0). Set the autocomplete-on-focus style bit 0x8000000 in flags/style so focus (msg 0x21) opens the dropdown; the dropdown list child itself is created internally with flags 0x20128 (FUN_00619b70).
 3. The framework auto-sends msg 4 (installs base CtlEdit proc 0x00603cc0) and msg 9 (allocates+constructs the 0x78 instance). Do not dispatch any other message before msg 9 completes.
 4. Populate the completion set with msg 0x63 (99): payload[0] = pointer to a block of consecutive NUL-terminated UTF-16 strings, payload[2] = length/end so the loop stops (terminated at buf+len). Must be sent only after construction (hashtable exists). Respect max 0x400 entries (field[0xe]).
 5. Runtime behavior is driven by CtlEdit forwarding: typing generates msg 0x31/0x32 subtype 7 which refresh matches; arrow keys generate msg 0x20 with 0x1c (next) / 0x1f (prev) to move the highlighted candidate; focus loss (msg 0x21 NULL) closes the popup. No manual paint/size handling needed — inherited from CtlEdit.

- **Crash gotchas:**

- Double-create: msg 9 asserts FUN_00487a80(0x77) if *(payload[2]) is already non-zero; instance slot must be pre-zeroed.
- Premature dispatch: FUN_0061a880 asserts 0x8a when **(frame+8)==0, so any of msgs 0x20/0x21/0x31/0x32/0x37/0x63 sent before msg 9 constructs the instance will assert. Always create first.
- Double-open dropdown: FUN_00619b70 asserts 0x99 if a dropdown child already exists (FUN_0062cfc0 != 0). It guards focus-gain, but manually forcing open while the popup is up will trip it.
- Alignment: constructor asserts 0xa0 if (this+0x1c) is not 4-byte aligned and 0xe9 if odd; the 0x78 block must come from the aligned control heap (do not place on an unaligned buffer).
- Candidate integrity: FUN_0061a570 asserts 0x24b if a candidate buffer is unexpectedly empty; FUN_0061a3a0 asserts 0x252 if (hashMask & hash) >= bucketCount (bucket overflow). Feed only valid NUL-terminated UTF-16 strings via msg 0x63 after construction; stay within maxEntries 0x400.
- Buffer-overlap guard: growth paths assert 0x171 if the reallocated text/candidate buffer overlaps the old one (memmove alias). Don't hand it aliased/overlapping storage.


### CtlDragModel  (EXE 0x0061b630, confidence: high)  [NOT a frame proc]

- **WASM:** ?
- **Assertion file:** P:\Code\Engine\Controls\CtlDragModel.cpp
- **Struct layout:**

Instance object allocated in case 9 via tagged allocator FUN_0047f340(\"...CtlDragModel.cpp\", size=0x73 => 115 bytes). This proc only touches offset 0; the rest is opaque state consumed by the drag-overlay renderer (FUN_006378b0/FUN_0064a470).

struct CtlDragModel {            // size 0x73 (115) bytes
  /* 0x00 */ void* draggedHandle; // ref-counted resource-handle wrapper (item/model being dragged);
                                   //   set via FUN_0046fda0(addref) / cleared via FUN_0046f850(release)
  /* 0x04..0x72 */ opaque;         // model-internal ghost/render state, not manipulated by this proc
};

Message-frame view used by the proc:
  msgframe[1] = msg (switch selector)
  msgframe[2] = payload*  -> payload[0] = instance ptr (*(msgframe[2]))
  msgframe[0] = frame handle (passed to FUN_0062ba80 / FUN_0062ede0 / FUN_0062bd40)
  param_2     = message body: body[0] = source handle-wrapper to clone (cases 9 & 0x56); &0x20 flag (case 8)

Create-time payload (from FUN_00531240 case 0x2c): a 5-slot local struct { [0]=handle, [1]=0, [2]=0.0, [3..4]=pos } passed as param_3 to FUN_006378b0.

- **Message protocol:**

FrameProc-shaped switch on msgframe[1]=msg; payload = *(msgframe[2]); param_2 = message body. Instance ptr lives at payload[0] (i.e. *(msgframe[2])). Only 4 cases — NO paint(1), NO base-install(4), NO size-query(0x15):

- case 8 (DRAG_TICK / render-request): if instance[0]!=0 AND (param_2[0] & 0x20)!=0 -> FUN_0062ba80(frame, 1, instance[0], 4) which calls FUN_00647db0(frame)+FUN_00635470(1, handle, 4, 0) to enqueue a paint of the drag ghost. No-op otherwise. The 0x20 bit is the same drag-overlay flag OR'd in at FUN_006378b0 (flags|0x20).

- case 9 (CREATE): instance = FUN_0047f340(\"P:\\Code\\Engine\\Controls\\CtlDragModel.cpp\", 0x73) -> stored into payload[0]. Reset draw state: FUN_0062ede0(frame,0,0xffffffff). Read body payload = *(int**)param_2; if body!=NULL: free any existing instance[0] via FUN_0046f850, then if body[0]!=0 addref/clone it via FUN_0046fda0(body[0]) into instance[0] and FUN_0062bd40(frame) (redraw); else instance[0]=0 + redraw.

- case 0xb (DESTROY): if instance[0]!=0 release via FUN_0046f850(instance[0]); then FUN_005acaeb(instance, 4) frees the instance object.

- case 0x56 (SET_MODEL): instance = payload[0]; asserts FUN_00487a80(0x46) if instance==NULL (create must have run first). Release old instance[0] (FUN_0046f850), then if param_2[0]!=0 addref via FUN_0046fda0(param_2[0]) into instance[0] + FUN_0062bd40(frame) redraw; else instance[0]=0 + redraw.

Semantics: instance[0] is a ref-counted resource HANDLE-WRAPPER pointer (the item/model being dragged). FUN_0046fda0 = addref/clone (asserts 0x115 if wrapper NULL, 0x117 if wrapper[0] NULL). FUN_0046f850 = release (atomic dec; runs finalizer at refcount 1->0).

- **Create recipe:**

This is a drag-drop MODEL, not a standalone visual frame — you create it by starting a drag via the drag-overlay system, not by FUN_0062bfc0.

Observed live recipe (GmStartMenu item-drag start, FUN_00531240 case 0x2c):
1. Obtain a ref-counted handle to the thing being dragged, e.g. h = FUN_0062cfc0(uictx, 0, 0x61, &attrs, &handleOut) which fills handleOut with an addref'd wrapper.
2. Build payload struct on stack: p[0]=handleOut; p[1]=0; p[2]=0.0f; plus start-pos floats.
3. Install the drag model: FUN_0062c210(flags, FUN_0061b630 /*proc*/, &payload, &sizeVec, &startPosVec)  -> tail-calls FUN_006378b0(flags, proc, &payload, sizeVec, startPosVec).
   - FUN_006378b0 guards: requires proc!=0 AND DAT_00c0aef8==0 (no drag already active); otherwise assert 0x272.
   - It creates the overlay frame via FUN_0064d1c0(flags|0x20, 0xfffffffe, proc, &payload, 0), stores the drag object in singleton DAT_00c0aef8, records start pos in _DAT_00c0ae28/2c, and lays out the ghost (FUN_00670340/FUN_0064a470). The dispatcher then sends msg 9 to FUN_0061b630, which allocs the 0x73 instance and addref-clones payload[0].
4. Release your caller-side ref after install: FUN_0046f850(handleOut) (the model has taken its own ref).
Warm-ups: none beyond a valid, addref'd handle wrapper and an idle drag system. To swap the ghost's model mid-drag, send msg 0x56 with body[0]=new handle. Msg 8 (with &0x20 set) drives per-frame ghost repaint. Teardown (msg 0xb) releases the handle and frees the instance; the overlay singleton DAT_00c0aef8 is torn down by the drag system.

- **Crash gotchas:**

- SET_MODEL before CREATE: msg 0x56 asserts FUN_00487a80(0x46) if the instance (payload[0]) is NULL — you must have sent msg 9 first.
- Invalid handle on clone: cases 9/0x56 call FUN_0046fda0 which asserts 0x115 if the handle wrapper is NULL and 0x117 if wrapper[0] (the underlying resource) is NULL. body[0] must be a fully-initialized, addref'd handle wrapper (5-int layout: [0]=resource, [1..3]=meta, [4]=optional post-clone callback).
- Only one drag at a time: FUN_006378b0 asserts 0x272 if DAT_00c0aef8 is already set (drag in progress) or the proc pointer is 0. Never start a second drag model without tearing down the first.
- Refcount underflow: FUN_0046f850 asserts 0x54 if the resource refcount is already 0 — do not release the same handle twice (the model owns its clone; free your own ref exactly once).
- FUN_0062ba80 (case 8 paint enqueue) asserts 0xe0d if frame==0 and 0xe0f if the pass index (4) is >=10 — pass a valid frame; pass index is fixed at 4 here.
- Case 9 always frees a pre-existing instance[0] before overwriting, so re-sending msg 9 is safe w.r.t. the handle but will leak/re-tag a new 0x73 instance unless the previous instance was destroyed via 0xb.


### Ctl3dModel  (EXE 0x0061d100, confidence: high)

- **WASM:** ram:81401b1e (Ctl3DModelProc) / ram:81400ce3 (CCtl3DModel::CtlMsgProc)
- **Assertion file:** P:\Code\Engine\Controls\Ctl3dModel.cpp (EXE 0x00a5084c, xref'd from FUN_0061d100 at 0x0061d2bb/0x0061d2d5). Instance alloc tag: P:\Code\Engine\Controls\CtlInstance.h (case 9). WASM: ../../../../Engine/Controls/Ctl3dModel.cpp (ram:0010bd51), symbol ICtl3DModel::CCtl3DModel.
- **Struct layout:**

CCtl3DModel instance, 0x54 bytes, allocated in case 9 via FUN_0047f340("CtlInstance.h",0xaf), freed via FUN_005acaeb(inst,0x54). Word index in [] :
+0x00 [0]  vtable ptr = &PTR_FUN_009404a4 (CCtl3DModel vtable)
+0x04 [1]  parent frame id (= *frame[0]); FUN_00602020(id) + FUN_0062ef00(id,0x35) on create
+0x08 [2]  embedded sub-object, initialized by (**vtable)(inst+2) (ctor FUN_006017e0), spans ~+0x08..+0x1c
+0x20 [8]  Coord3f eye/camera position .x  (msg 0x56 SetEyePosition)
+0x24 [9]  eye .y
+0x28 [10] eye .z
+0x2c [0xb] Coord3f look-at/target position .x (msg 0x5b)
+0x30 [0xc] target .y
+0x34 [0xd] target .z
+0x38 [0xe] light/rotation object handle (built in msg 0x57 via FUN_00676500; render asserts non-null 0xec); freed FUN_0046f850
+0x3c [0xf] light rig handle (FUN_00676d10(1)); freed FUN_0046f850
+0x40 [0x10] HModel handle (ModelCreate result, msg 0x59; render asserts non-null 0xeb); closed via HandleClose/FUN_0046f850
+0x44 [0x11] TArray<HGrModel*> data ptr (ModelAnimate output); freed via FUN_0047f3a0
+0x48 [0x12] TArray count
+0x4c [0x13] TArray capacity/count (assert index<count 0x24b uses this; **(+0x44)=first model elem)
+0x50 [0x14] init constant 0x40 (state/flags)

- **Message protocol:**

FrameProc switches on frame[1]=msg (param_1=frame hdr, param_2=payload, param_3=out). Instance = *(frame[2]); default path asserts if slot null (0x2c) or slot->[0]==0 (0x149).
- Deferred-to-base (FUN_004a0440 + thunk_FUN_00647170): 1(paint),3,7,8,10,0xc,0xf,0x13,0x15(size-query),0x20,0x24-0x2a,0x2c,0x2e,0x31,0x32,0x34,0x36,0x3a-0x3f,0x44-0x46,0x4b,0x4c,0x4e,0x4f,0x52, and 4/5/6.
- 0x04/0x05/0x06: base template hooks -> thunk to base proc.
- 0x09 CREATE: assert slot==0 (else 0xae); alloc 0x54 inst; set vtable, parent=*frame[0], +0x50=0x40; store *(frame[2])=inst; FUN_00602020(parent); FUN_0062ef00(parent,0x35) registers custom render; call sub-obj init.
- 0x0b DESTROY: free +0x38/+0x3c/+0x40, free TArray +0x44, dtor, free 0x54, null slot.
- 0x35 RENDER (OnFrameRender, custom paint pass registered at create): assert +0x40 model!=0 (0xeb) and +0x38 light!=0 (0xec); FUN_0077d260 draw prep, camera FUN_0066dec0(1, eye@+0x20, target@+0x2c, &look), transform FUN_00630320, draw model list, restore Gr state.
- 0x37 OnCtlLayout: reads rect payload[2..5] -> FUN_00602060.
- 0x38 measure/hit: thunk base, FUN_00602900 -> writes size to payload[2].
- 0x56 SetEyePosition(Coord3f): payload[0..2] -> +0x20/+0x24/+0x28.
- 0x57 SetLight(Coord3f pos payload[0..2], Color3b payload[3], float payload[?], Color3b, float): builds light objs +0x3c=FUN_00676d10(1), +0x38=FUN_00676500(...); ONLY if an intensity (local_c/local_10) is nonzero, else no light created.
- 0x58: no-op.
- 0x59 SetModelFile(wchar_t* payload[0]): CreateModel -> HandleClose old +0x40, ModelCreate(name,&coord,0x32,0)->+0x40, ModelAnimate(model,0.0,&TArray@+0x44,0), GrModelSetWorldTransform(first elem,0).
- 0x5a SetSequence(uint payload[1], uint payload[0]): ModelSetSequence(model@+0x40, payload[1], payload[0]).
- 0x5b SetTargetPosition(Coord3f payload[0..2]): -> +0x2c/+0x30/+0x34.
Public WASM senders: Ctl3DModelSetEyePosition(0x56), Ctl3DModelSetLight(0x57), Ctl3DModelSetModelFile(0x59), Ctl3DModelSetSequence(0x5a).

- **Create recipe:**

1) Create the frame primitive with FUN_0062bfc0(parent, flags, child, proc=0x0061d100, userdata, 0). The proc self-allocates its 0x54-byte instance on msg 0x09 and self-registers the custom render pass 0x35 via FUN_0062ef00(parent,0x35) — no manual instance alloc.
2) Warm-ups (send via dispatcher FUN_0062ef40(frame,msg,payload,out)) BEFORE the control is allowed to render:
   a. 0x59 SetModelFile(wchar_t* path) to load an HModel (fills +0x40 and the +0x44 model array). REQUIRED.
   b. 0x57 SetLight(pos,color,intensity,...) with nonzero intensity to build the light (+0x38). REQUIRED.
   c. 0x56 SetEyePosition(eye Coord3f) and 0x5b SetTargetPosition(target Coord3f) to frame the camera.
   d. Optional 0x5a SetSequence(seqA,seqB) for animation.
3) Layout/sizing via 0x37 (rect payload[2..5]); size-query 0x15 defers to base. The control paints only during the registered 0x35 pass, not the generic 0x01 paint (which is deferred to base).

- **Crash gotchas:**

- Render 0x35 hard-asserts (FUN_00487a80, no-return -> crash) if +0x40 model handle is 0 (assert 0xeb) OR +0x38 light is 0 (assert 0xec). You MUST send 0x59 (SetModelFile) AND 0x57 (SetLight with nonzero intensity) before the first render; sending only one crashes.
- 0x57 SetLight silently creates NO light object when both intensity floats are zero -> +0x38 stays null -> next 0x35 render asserts 0xec.
- 0x59 CreateModel asserts index<count (0x24b) if the loaded model produces an empty HGrModel array (bad/missing model file) -> crash. Validate the model file exists.
- 0x09 CREATE asserts 0xae if the instance slot *(frame[2]) is already non-zero (double-create on same frame).
- Sending any instance msg (0x56/0x57/0x59/0x5a/0x5b/0x35/0x37/0x38) before 0x09 create: default path derefs *(frame[2]); asserts 0x149 (slot null) or 0x2c (slot->[0]==0). Never dispatch setters before the frame is created.
- 0x0b DESTROY frees +0x38/+0x3c/+0x40 and the +0x44 TArray; re-dispatching after destroy is unsafe (slot is nulled but frame still routes).


### CtlImeCand  (EXE 0x0061d870, confidence: high)

- **Assertion file:** P:\Code\Engine\Controls\CtlImeCand.cpp (EXE string @0x00a508a4; game-layer UiCtlImeCand.cpp @0x00b96caf has no EXE xref)
- **Struct layout:**

Instance (heap, FUN_0047f340 size 0x6b = 107 bytes; only leading 16 bytes structured, rest scratch/reserved):
+0x00 uint32 frameHandle    // CtlFrame id of this control (used as inst[0] for all child dispatch)
+0x04 int32  topIndex       // cached data-model base/scroll index (= model[4]); page top
+0x08 int32  highlightCell  // currently highlighted candidate cell index, -1 = none (init 0xFFFFFFFF)
+0x0C uint32 modelVersion   // cached *dataModel ptr to detect list change (init 0), triggers FUN_0062f470 relayout on change
+0x10..0x6a  reserved/scratch (uninitialized by CREATE)

Child spec table PTR_FUN_00a50874 (11 entries copied to stack, consumed by 0x57 template + FUN_0062bfc0):
[0]=0x0061d7b0 prevPageButton proc (on create msg9 sets skin FUN_0060fe60 &DAT_00a4f464)
[1]=0x0061d7e0 nextPageButton proc
[2]=0x0061d810 candidateCell proc (10x; intercepts msg 0x61 to OR style bit0=selectable/hot, else base button FUN_00617df0)
[3]=0x0061b9d0 readingString/composition label proc
[4]=0x00610c40 pageCounter label proc
[5..10]=floats: 2.0, 0.0, 6.0, 16.0, 60.0, 24.0  (cell paddings/spacing/min metrics)

- **Message protocol:**

FrameProc FUN_0061d870(frame, msgframe/payload=param_2, out=param_3) switch(frame[1]=msg); unhandled -> thunk_FUN_00647170 (base container proc). Note: this control uses msg 0x0A (not 0x09) for create.
- 0x08 PAINT-BG: if(*payload&1) build sprite quad (FUN_00679a60 tex 0x20003e0) and draw via FUN_0062b2d0(instance[0], payload+0x1c, tex, 1x1 uv), release tex FUN_0046f850, then base. Background render sub-pass.
- 0x0A CREATE: if instance slot (*(frame[2]))==0 -> alloc FUN_0047f340("...CtlImeCand.cpp",0x6b); init [+0]=frame handle(*frame), [+4]=0, [+8]=0xffffffff, [+C]=0; store ptr into *(frame[2]); copy 11-entry PTR_FUN_00a50874 spec table to stack; FUN_0062ef40(inst[0],0x57,0,spec) install child template; then spawn 15 children via FUN_0062bfc0(inst[0],flags,childIdx,proc,0,0). If slot already set -> assert FUN_00487a80(0x6a). Ends via base.
- 0x0B DESTROY: if slot!=0 FUN_005acaeb(slot,0x10) free; *(frame[2])=0; base.
- 0x31 INPUT/NAV: wparam=*(payload+4), sub=*(payload+8). w==0&&sub==7 -> FUN_005f3990; w==1&&sub==7 -> FUN_005f39a0; 2<=w<=0xb && sub==9 -> commit candidate: FUN_00651850(0,3,0, topIndex+(w-2)) then FUN_00651850(0,2,0,0); w==0xd -> arrow/page nav (sub-7 in 0..4) computes new index then FUN_0060a400(model,idx)+FUN_0059fea0+FUN_00651850(0,4,..). Selection/scroll/commit handler.
- 0x37 MEASURE-WIDTH: FUN_0061dca0 horizontal layout/measure of child cells; base.
- 0x38 MEASURE-HEIGHT/AUTOSIZE: FUN_0061df40 vertical layout; base.
- 0x56 REFRESH/UPDATE: FUN_0061e110 rebuild — re-installs 0x57 template, sets each of 10 cells visible/enabled from payload[5]=visibleCount, payload[6]=totalCount, text payload[8], flags payload[2]; drives prev/next buttons (child 0/1) and page counter child 0xe with L"%u/%u"; recomputes highlighted cell, sends 0x56/0x57 hover msgs to old/new cell; writes inst[+8]=highlight, inst[+4]=topIndex, inst[+C]=model ptr.
- 0x09, 0x0C-0x30, 0x32-0x36, 0x39-0x55: explicit no-op passthrough to base.
- default: base proc.
Instance accessor FUN_0061e0e0(frame) = **(frame+8); asserts 0x7d if null.

- **Create recipe:**

Not user-instantiable in isolation — spawned by the IME text-input engine as a child of the active edit field. To reproduce the pipeline:
1. Parent creates it: FUN_0062bfc0(parentFrame, flags, childId, &FUN_0061d870 (0x0061d870), userdata, 0).
2. Dispatch CREATE: FUN_0062ef40(childFrame, 0x0A, 0, payload) -> allocates instance, installs the 0x57 child template automatically, and spawns all 15 sub-frames (2 page buttons + 10 candidate cells @flags 0x4300 + reading label @flags 0 + page counter @flags 0x90000; buttons @flags 0x40000). No manual child creation needed — the FrameProc does it.
3. Feed candidate data + refresh: build payload with [2]=styleFlags, [3]=selectedGlobalIdx(-1 none), [5]=visibleCount(<=10), [6]=totalCount(<=10), [8]=text, then FUN_0062ef40(childFrame, 0x56, 0, payload) to populate/repaint.
4. Sizing: send 0x37 (width) / 0x38 (height) to autosize before showing.
5. Navigation/commit driven by 0x31 messages (arrows=w0xd, digit-pick=w2..0xb sub9, page prev/next=w0/1 sub7).
Warm-ups: CREATE (0x0A) MUST precede any 0x31/0x37/0x38/0x56 (those call FUN_0061e0e0 which asserts on null instance).

- **Crash gotchas:**

- Double CREATE: sending 0x0A when instance slot already set -> assert FUN_00487a80(0x6a). Only create once per frame.
- Premature message: any of 0x31/0x37/0x38/0x56 before 0x0A -> FUN_0061e0e0 assert 0x7d (null instance deref).
- 0x56 REFRESH bounds: FUN_0061e110 asserts 0xba if payload[6]+2 > 0xC (totalCount>10) and 0xbb if payload[5]+2 > 0xC (visibleCount>10). Candidate cells are hard-limited to 10 — never pass more.
- Layout 0x37 (FUN_0061dca0) asserts 0x238 on non-positive / NaN width or height inputs; always feed valid positive extents.
- 0x31 commit path calls FUN_0060a400/FUN_00651850 against the live data-model index — desync between payload topIndex and model index can post a wrong selection; keep inst[+4] in sync via 0x56 first.
- Candidate cell proc (0x0061d810) only special-cases msg 0x61 when *(frame+4)==0x61; anything else forwards to base button proc, so custom per-cell messages below 0x61 are ignored (fall through).


### UiCtlImeReading  (EXE 0x0061e470, confidence: high)

- **WASM:** ram:80e0e1f2
- **Assertion file:** P:\Code\Engine\Controls\CtlImeReading.cpp (EXE string @ 0x00a50994; xref'd only from FUN_0061e470 case 9)
- **Struct layout:**

Instance size = 0x154 bytes (authoritative: freed via FUN_005acaeb(inst,0x154) in case 0xb). Alloc via FUN_0047f340("...CtlImeReading.cpp",0xb6) in case 9 (0xb6 = alloc tag/line, NOT the size).

Header (0x00..0x14):
  +0x00  dword   (reserved / init 0 region owned by base header before array)
  +0x04  dword   (reserved)
  +0x08  int     display mode / orientation flag  (set from payload[0] in case 0x56; case 8 layout branches on ==0 => vertical stack, !=0 => horizontal row)
  +0x0C  uint    candidate count  (clamped to max 0x14=20 in case 0x56)
  +0x10  uint    highlighted/selected candidate index (from payload[2]; case 8 draws selection box when loop index == this)

Candidate array: 20 (0x14) fixed slots, 16 bytes each, starting at +0x14, ending exactly at 0x154.
  Each slot (wchar string object):
    +0x00  wchar_t*  text buffer pointer
    +0x04  dword     (0 / secondary)
    +0x08  uint      length (char count)
    +0x0C  uint      capacity  (initialized to 0x80 = 128 in case 9)
  case 9 init loop 1: zero ptr/len, set capacity=0x80 for all 20 slots.
  case 9 init loop 2: FUN_00467680(len+1,len) reserves each buffer and writes null terminator, len++ (empty seeded strings).
  case 0xb: per-slot FUN_0047f3a0() frees any allocated buffer, zeroes slot, then frees whole 0x154 struct.

- **Message protocol:**

FrameProc FUN_0061e470(msgframe* param_1, payload* param_2, out param_3); switches on param_1[1]=msg. Instance = *(int*)param_1[2]. Unhandled msgs -> base thunk_FUN_00647170 (chains to base template FUN_006123a0, which case4-installs root proc FUN_0062c370).

 case 1  PAINT: sub-pass = *payload. If *payload==0 background fill (color 0x80000000), ==1 highlight fill (ARGB 0xC8C83232 via FUN_00679a60 texture + FUN_0062b2d0 quad + FUN_0046f850 release), then chain base paint. Returns early with no draw if *payload not in {0,1}.
 case 4  INSTALL BASE: *(code**)payload[3] = FUN_006123a0 (parent/base proc), then chain base.
 case 8  MEASURE/LAYOUT (FUN_0061e890): gated by payload flag bit 0x40. For each of count candidates computes glyph extents (FUN_0062fee0/0x57 measure) and positions them; inst+8==0 => vertical stacking (advance Y by _DAT_009413c8), !=0 => horizontal row (advance X by _DAT_00943280); draws selection rect (FUN_0062b590) on the slot equal to inst+0x10.
 case 9  CREATE: alloc 0x154 instance, seed 20 empty wchar slots (cap 0x80), store at *(int*)param_1[2]; asserts if slot reuse fails.
 case 0xb DESTROY: free each candidate buffer + free 0x154 struct.
 case 0x15 SIZE-QUERY: asserts payload nonzero (FUN_00487a80(199)); fills out[0]=_DAT_009407b8, out[1]=out[3]=_DAT_00943278, out[2]=default (control's natural size).
 case 0x38 (FUN_0061ea10): secondary paint/hit-test pass, then chain base.
 case 0x39: FUN_0062bd40(frame) relayout + FUN_0062f110(frame) invalidate/refresh.
 case 0x56 SET READING DATA (primary API): inst+8 = payload[0] (mode); count = min(payload[1],0x14) -> inst+0xC; inst+0x10 = payload[2] (selection idx); payload[4] = packed source blob of consecutive wide strings -> copied into the count slots (FUN_0046c270 length, FUN_00467680 reserve, FUN_0046da80 copy, advance src by len*2+2). Ends with FUN_0062bd40 relayout + FUN_0062f110 invalidate.
 case 0x57 GLYPH/CHILD PAINT (FUN_0062bc20): per-glyph child paint callback pass-through, then chain base.
 default: chain base template.

- **Create recipe:**

This is an internal IME composition/reading (phonetic candidate) window normally spawned by the IME manager, not a user control. To instantiate via the primitives:
1. Create the frame: FUN_0062bfc0(parent, flags, child, FrameProc=FUN_0061e470, userdata, 0). Use a top-most/overlay style flag set (it paints its own translucent background 0x80000000 and highlight 0xC8C83232) parented to the text-input frame that owns the composition.
2. Warm-ups auto-run through the frame lifecycle: msg 4 (install base FUN_006123a0) then msg 9 (alloc 0x154 instance, seed 20 empty candidate slots). Do not send msg 9 yourself twice (double-init assert).
3. Size negotiation: engine sends msg 0x15; it reports natural size from globals (_DAT_009407b8/_DAT_00943278). Provide a valid out buffer.
4. Populate: send msg 0x56 with payload {[0]=mode/orientation, [1]=candidate count (<=20), [2]=selected index, [4]=pointer to a packed run of null-terminated wide strings}. This copies strings, relayouts (FUN_0062bd40) and invalidates (FUN_0062f110).
5. Layout/paint happen automatically on the next frame (msg 8 measure gated by payload bit 0x40, msg 1 paint sub-passes 0 then 1, msg 0x57 per-glyph).
6. Tear down with the standard frame destroy path (msg 0xb) to free candidate buffers and the struct.
Reference control chain: FUN_0061e470 (this) -> base template FUN_006123a0 -> root frame proc FUN_0062c370.

- **Crash gotchas:**

- case 0x15 asserts (FUN_00487a80(199), no-return) if the out payload pointer is NULL — always pass a valid >=4-dword out buffer for size queries.
- case 0x56 clamps count to 20; but the source blob payload[4] MUST contain at least 'count' contiguous null-terminated wide strings — it walks src forward by (len*2+2) per entry with no bounds check, so a short/malformed blob over-reads game memory.
- case 0x56 range-checks the copy (FUN_00487a80(0x171) no-return) if the destination buffer overlaps the source region — never point payload[4] into the instance's own candidate buffers.
- case 9 asserts on double-init (allocator FUN_0047f340 aborts if the slot at param_1[2] is already set) — send create exactly once per frame.
- PAINT (case 1) silently no-ops for any sub-pass other than 0/1; don't expect custom sub-passes to render.
- Struct free size is 0x154; the 0xb6 constant passed to FUN_0047f340 is an alloc tag/line id, not a byte size — do not use it for sizing.


### CtlList  (EXE 0x0061f740, confidence: high)

- **WASM:** ?
- **Assertion file:** P:\Code\Engine\Controls\CtlList.cpp
- **Struct layout:**

CtlList instance (allocated in case 9 via FUN_0047f340("CtlList.cpp",0xa3e) then constructed by ctor FUN_0061ecc0). Instance ptr is stored at *(uint*)payload[2] (i.e. *puVar6 where puVar6 = param_1[2]). All offsets below are byte offsets confirmed against ctor (FUN_0061ecc0) + every switch case.

Total footprint spans at least 0xB4 bytes (last accessed field +0xB0).

+0x00  vtable ptr (&PTR_FUN_00a509c0; style-0x20000 variant boxes an inner &PTR_FUN_00a509cc object). dtor called via *(vt+8) in case 0xb.
+0x04  int = 0 (ctor param_1[1])
+0x08  int = 0
+0x0c  int = 0
+0x10  int = 0
+0x14  int  interaction/disabled gate. When !=0 nearly all input cases (0x20,0x24,0x2c,0x2f,0x31,0x3c/0x3f,0x3d) short-circuit. Set/cleared during drag capture (see +0x24 group).
+0x18  int = 0
+0x1c  int = 0
+0x20  int = 0
+0x24  int = -1 (ctor)  drag-capture source id (case 0x3d sets = *param_2; 0x3c/0x3f clears to -1)
+0x28  int = 0  "dirty"/needs-relayout flag; set to 1 in many mutators (case 0x39,0x57,0x3d cleared, FUN_006224d0 sets 1)
+0x2c  point/rect blob (2 dwords) drag-anchor; FUN_0060cbc0 reset, FUN_0060cbd0 store (cases 0x3c/0x3d), FUN_0060ca20 init in ctor
+0x50  int = 0  user-data / context object (case 0x64 replaces via FUN_0046fda0, frees old via FUN_0046f850)
+0x54  int = 1 (ctor)
+0x58  int = 0  top/scroll row index (getter case 0x5f returns it; scroll math cases 0x2f/0x31/0x5b use it)
+0x5c  ptr = 0  base pointer of the field/cell array (each cell 0x10 bytes; used in 0x5b hit-test, 0x4c reset, FUN_006224d0)
+0x60  uint = 0  capacity of the row-index buffer at +0x68 (grown via FUN_00473880)
+0x64  int = 0  item/row COUNT (getter case 0x5d returns it; bounds checks in 0x66/0x68/0x20)
+0x68  buffer/handle (ctor sets adjacent field 0x1a=0x10 chunk); FUN_0061f420 rebuilds
+0x6c  int = 0
+0x70  int = -1 (ctor)  SELECTED / focused row index (getter case 0x60; set via FUN_00623240 in 0x20/0x68; commit in 0x2e)
+0x74  int = 0  drag-pending flag (case 0x24 sets 1 with start point at +0x78/+0x7c; case 0x2e consumes/clears)
+0x78  int  drag-start X (case 0x24)
+0x7c  int  drag-start Y (case 0x24)
+0x80  int  press-anchor X (case 0x3d / 0x3c compare)
+0x84  int  press-anchor Y
+0x88  int = -1  last-hover cell col (reset in FUN_006224d0 / case 0x57)
+0x8c  int = -1  last-hover cell row
+0x90  int = 0  page size / visible-rows count (used in 0x31 page scroll, 0x5b bounds)
+0xa0  int = 0
+0xa4  int = 0
+0xa8  uint = 0  number of COLUMNS/fields (loop count in FUN_006224d0; guard `<2` in 0x59)
+0xac  int = 0x40 (ctor)  default flags/height chunk
+0xb0  ptr = param_2 (ctor)  the child RENDER FRAME handle — every draw/scroll op dispatches here via FUN_0062ef40 / FUN_0062ee80 / FUN_0062cfc0 (style read FUN_0062fe20 targets it too)

- **Message protocol:**

FrameProc signature: void CtlList_Proc(undefined4 *frame, int *payload, uint *out). frame[1]=msg, frame[2]=&instancePtr. Switch on frame[1]:

LIFECYCLE
 case 4  : install parent/base proc FUN_006123a0 (CtlBase template) into *(code**)payload[3].
 case 8  : FUN_006217a0(payload) — measure/init pass.
 case 9  : ALLOCATE instance. Asserts (FUN_00487a80 0xa3a) if *slot already set. Style-gate FUN_0062fe20(frame,0x20000): style==0 -> plain alloc(line 0xa3e)+FUN_0061ecc0; style set -> alloc(0xa3c), wrap with vtable &PTR_FUN_00a509cc. Then FUN_00621ad0(payload).
 case 0xa (10): teardown notify — queries child (FUN_0062ef40 msg 0x5e), then FUN_0062cfc0/FUN_0062f150. Falls through to break.
 case 0xb (11): DESTRUCT instance via (*(vt+8))(1).

INPUT (all gated by +0x14==0)
 case 0x20 (32): keyboard nav. payload[0]: 0x1c/0x1e=next enabled row, 0x1d/0x1f=prev enabled row (skips rows whose flags&1 clear via FUN_00621070), wraps; commit FUN_00623240(row,1).
 case 0x24 (36): mouse-down. If payload flags&4 -> start drag (set +0x74=1, store +0x78/+0x7c). Else hit-test FUN_006234e0; left-click (payload0==0 & flag&1) sends child msg 7 (select); payload[5]==1 sends child msg 9 (activate/double) with rich cell struct.
 case 0x25 (37): clear selection (payload==NULL) -> FUN_00623390 with -1s.
 case 0x26/0x27/0x28/0x2a (38/39/40/42): FUN_00621dc0(0xd/0xe/0xf/0x10, payload) — focus/key edge events.
 case 0x2c (44): mouse-move/hover. If payload[5]==0 & !(flag&4): FUN_00620f00 hit-test -> FUN_00623390 set hover.
 case 0x2e (46): mouse-up. Consumes drag (+0x74). If selected +0x70!=-1: payload0==0 -> child msg 0x61 (commit select); payload0==2 -> child msg 0x63.
 case 0x2f (47): mouse WHEEL. Reads delta FUN_0060ca40, step depends on style 0x10000 (h/v), scrolls via FUN_006231b0(+0x58 +/- step).
 case 0x31 (49): SCROLLBAR command payload[2]: 7=line-up,8=line-down,9=page-up,10=page-down,0xb=thumb-track (uses +0x58,+0x90,+0x64; style 0x10000 flips direction).

STRUCTURE/DRAG
 case 0x37 : FUN_00621e90(payload).
 case 0x38 : FUN_00622090(payload).
 case 0x39 (57): invalidate+relayout: set +0x28=1, FUN_006211b0, FUN_0062f470/0062bd40/0062f110 on +0xb0.
 case 0x3a (58): attach/register child frame — walks internal string-cell lists (+0x5c area), matches payload[0], stamps id +0x54, copies text (FUN_00467680), re-lays out.
 case 0x3c/0x3f (60/63): end/cancel drag — if payload0==+0x24 clear +0x14/+0x24, reset anchor +0x2c, may re-send child msg 0x61.
 case 0x3d (61): BEGIN drag capture — set +0x24=payload0, +0x28=0, store anchor +0x2c and press point +0x80/+0x84, out = (payload[5]==0).
 case 0x3e : FUN_006222d0(payload).
 case 0x4c (76): reset all rendered text cells (frees temp strings, resets flags), relayout.

DATA / QUERY (0x56+ control-specific)
 case 0x56 (86): SET ROW COUNT / (re)populate — FUN_006224d0. Grows buffers, inits +0xa8 columns per row, refreshes selection & scroll.
 case 0x57 (87): CLEAR all rows — style 0x2000 keeps 1?, tears down all cells (FUN_00620730 loop), resets +0x70=-1,+0x90=0,+0x88/8c=-1, relayout, child msg 0x61.
 case 0x58 (88): FUN_006226a0(payload) — set/define column.
 case 0x59 (89): invalidate row(s) redraw — payload[1]==-1 special, clears cell dirty bits, FUN_0062bd40.
 case 0x5a : FUN_00622930(payload).
 case 0x5b (91): HIT-TEST point -> writes payload[2]=col/row-or-(-1), payload[3]=field id. Asserts (0x293) if field OOB, (0x298) if cell array null.
 case 0x5c : FUN_00622a90(payload).
 case 0x5d (93): GET item count -> *payload = *(inst+0x64).
 case 0x5f (95): GET top/scroll index -> *payload = *(inst+0x58).
 case 0x60 (96): GET selected index -> *payload = *(inst+0x70).
 case 0x61 (97): SET selection by index (payload0, -1=current) -> child msg 0xb via FUN_0062ee80.
 case 0x62 : FUN_00622c20(payload).
 case 99 (0x63): SET selection variant -> child msg 0x11.
 case 100 (0x64): SET user-data/context at +0x50 (frees old FUN_0046f850, dup new FUN_0046fda0), relayout.
 case 0x65 : FUN_00622e60(payload).
 case 0x66 (102): ensure row visible / scroll-to (bounds-assert 0x9df vs +0x64) -> FUN_006231b0(row,0).
 case 0x67 (103): dispatch payload to child render frame (FUN_0062cfc0 msg-0, assert 0x9e9 if none).
 case 0x68 (104): SET selected index (payload, -1 ok; bounds-assert 0x9f2) -> FUN_00623240 if changed.
 case 0x69/0x6a/0x6b (105-107): forward to base-template handler FUN_0062bc20(*frame,payload).

DEFAULT / tail: ALL cases (and unhandled msgs) fall through to thunk_FUN_00647170(frame,payload,out) = the installed CtlBase parent proc (FUN_006123a0), which owns paint (msg 1), size-query (0x15) and generic frame behavior. So CtlList itself does NOT paint directly — painting is delegated to CtlBase + the +0xb0 render frame.

- **Create recipe:**

Create a CtlList control (mirrors the verified CtlBase creation model):

1. Allocate the frame via the create primitive FUN_0062bfc0(parent, flags, child, proc=CtlList_Proc(0x0061f740), userdata, 0). CtlList_Proc self-installs the CtlBase parent proc (FUN_006123a0) on msg 4, so you only register CtlList_Proc.

2. Warm-up / init order that the proc expects:
   a. msg 4  -> lets it install the base template proc (do this first / implicitly on create).
   b. msg 9  -> allocates + constructs the instance (ctor FUN_0061ecc0 zero-fills, sets +0x14=0 interactive, +0x70=-1 no selection, +0x2b=0x40, +0x1a=0x10 grow chunk, +0xb0=render-frame handle passed as ctor param_2). Passing style bit 0x20000 selects the boxed-vtable variant (&PTR_FUN_00a509cc) — leave it clear for a plain list.
   c. msg 8  -> measure/init pass (FUN_006217a0).

3. Column setup: send msg 0x58 (define column) once per column BEFORE populating; +0xa8 tracks the column count.

4. Populate: send msg 0x56 with a row-count payload (FUN_006224d0). This grows the row buffer (+0x60 capacity, +0x68 buffer, FUN_00473880), inits +0xa8 cells per row, and lays out. Feed cell text via the msg-0x3a attach path / child frame.

5. Sizing: the control does NOT own layout math — the CtlBase parent proc answers size-query msg 0x15, and the +0xb0 render frame (FrameLayout) supplies row height (+0xac default 0x40) and paints. Set style 0x10000 to make it a HORIZONTAL list (flips all scroll/wheel direction math in cases 0x2f/0x31); style 0x2000 changes clear/populate edge behavior (keeps a phantom slot).

6. Selection & scroll after populate: msg 0x68 to set selected index, msg 0x66 to scroll a row into view, msg 0x61/0x63 to fire selection notifications to the child frame.

Getters usable any time: 0x5d=count, 0x5f=top index, 0x60=selected index.

- **Crash gotchas:**

- Double-alloc: msg 9 asserts FUN_00487a80(0xa3a) if the instance slot (*payload[2]) is already non-null. Never send msg 9 twice; free (msg 0xb) first.
- msg 0x56 (FUN_006224d0) asserts 0x7df if payload is NULL; asserts 0x7ed if style 0x2000 set with target row 0 while count!=0. Always pass a valid populate struct.
- msg 0x66 (scroll-into-view) asserts 0x9df if row index >= count (+0x64). Bounds-check before sending.
- msg 0x68 (set selection) asserts 0x9f2 if index >= count and index != -1.
- msg 0x67 asserts 0x9e9 if there is no child render frame (FUN_0062cfc0 msg-0 returns 0) — only valid after a real render frame is attached at +0xb0.
- msg 0x5b (hit-test) asserts 0x293 "Field out of bounds %s" if the resolved field exceeds column span (+0x58+ +0x90 vs +0x64), and 0x298 if the cell array pointer (+0x5c) is null — never hit-test before populate.
- msg 0x3a attach asserts 0x75c if a cell's temp-string handle (+0x54) is already set (double attach), and 0x171 on overlapping copy ranges.
- msg 0x59 with row payload asserts 0x4c1 if column index >= +0xa8.
- The +0x14 interaction gate must be 0 for input msgs to do anything; if a drag capture (msg 0x3d) is left open (+0x24 != -1) all pointer input is swallowed until msg 0x3c/0x3f clears it — a stuck drag looks like a frozen list.
- Ordering: sending data msgs (0x56/0x58/0x5b) before the instance exists (before msg 9) dereferences a null instance slot -> crash. Always alloc first.


### DlgMsg  (EXE 0x00623670, confidence: high)

- **WASM:** ram:80e536f8
- **Assertion file:** P:\Code\Engine\Dialog\DlgMsg.cpp (EXE @0x00a5102c) / ../../../../Engine/Dialog/DlgMsg.cpp (WASM @ram:0010cc7d)
- **Struct layout:**

DlgMsg is a game-layer *composite* dialog (message-box) FrameProc. Unlike the Engine\Controls primitives, its case 9 does NOT allocate a private heap instance via FUN_0047f340 and does NOT assert-on-already-set. Its "state" is the child-frame subtree it builds in FUN_00623be0. So there is no per-instance struct; the meaningful layouts are the CREATE payload and the child map.

CREATE payload (userdata passed to FUN_0062bfc0 -> arrives as param_2 to the case-9 handler FUN_00623be0):
  +0x00  wchar_t* messageText   (copied into label child id 1 via FUN_0060a420 if non-null)
  (only offset 0 is consumed at create; button/field captions are pushed later via 0x59/0x5b-0x5e/0x5a)

CHILD FRAME MAP (created in FUN_00623be0 via FUN_0062bfc0(parent,style,childId,proc,ud,0)):
  id 1  = message label     proc FUN_0060d410, style 0x20300  (always)
  id 3  = text input field  proc FUN_0060f4f0, style 0x10300  (only if parent style & 0x2000)
  ids 2/4/5/6 = buttons      proc FUN_0060f4f0, styles 0x442300/0x440300/0x444300/0x446300
              button set selected by style bits (see message_protocol / create_recipe)
  id 0  = icon/close child   proc FUN_00611890  (only if style & 0xe0000, and only wired to the
                              global dialog resource DAT_00c0ac40 when that resource is non-null)
Base/parent proc installed at case 4: FUN_00612240 (generic focusable frame template; also base-asserts 0xaf if the frame was already registered). Style is OR'd with 0x30 at setup.

STYLE BIT MEANINGS (read via FUN_0062fe20(frame,mask)):
  0x1000  = has secondary/negative button
  0x2000  = has text-INPUT field (child id 3); gates get/set-text msgs 0x57/0x5a
  0x4000  = (part of 3-button / retry set selector)
  0x8000  = has affirmative button
  0x10000 = (part of 3-button set selector)
  0x20000 = dialog-nesting/close-direction flag (affects close-button wiring)
  0xe0000 = has close(X) button child
  0x100000= suppress auto-close on button action (checked in FUN_00623ba0)

- **Message protocol:**

FrameProc FUN_00623670(msgframe* p1, payload p2, out* p3); switches on p1[1]=msg. Unhandled/break cases fall through to thunk_FUN_00647170 (base proc chain).
  case 4  SETUP: install base proc FUN_00612240 into *(p2+0xc); *(p2+4) |= 0x30; chain to base.
  case 9  CREATE: FUN_00623be0(frame, payload) -> build child label + buttons (+ input field / close btn per style). Reads payload[0] as message text.
  case 0x0a LAYOUT/RESIZE: query FUN_0062ef40(frame,0x56,..)=height; iterate child ids 2..6 and id1, position each via FUN_0062f150.
  case 0x31 ACTION/HOTKEY: sub-switch on *(p2+4) action id (1..6) with expected key in *(p2+8); maps to button notify events 7..0xc via FUN_00623ba0 / FUN_0062ee80 (Enter=affirm, Esc=cancel, etc.).
  case 0x37 MEASURE-PASS: FUN_00623e20 - measure child buttons (ids 2,5,4,6) with child-msg 0x89, lay out label(0)/input(3) with 0x94/0x105, finalize with 0x114.
  case 0x38 PREFERRED-SIZE: FUN_00624010 - same measurement; writes required width -> **(p2+8), height -> *(*(p2+8)+4), clamped to mins _DAT_00a51090/_DAT_0094f4e8.
  case 0x57 GET-INPUT-TEXT: assert 0xd3 if p3==NULL; assert 0xd4 if !(style&0x2000); *p3 = FUN_0060f4b0(childId 3). chain.
  case 0x58 SET-LABEL: FUN_0060a420(childId 1, payload); FUN_0062bd40(frame) relayout. chain.
  case 0x59 SET-BTN2-CAPTION: FUN_00624350(frame, childId 2, payload) -> FUN_0060fdf0 + relayout. chain.
  case 0x5a SET-INPUT-TEXT: assert 0xef if !(style&0x2000); FUN_0060f490(childId 3, payload).
  case 0x5b SET-child3-CAPTION: FUN_00624350(frame,3,payload). chain.
  case 0x5c SET-child4-CAPTION: FUN_00624350(frame,4,payload). chain.
  case 0x5d SET-child5-CAPTION: FUN_00624350(frame,5,payload). chain.
  case 0x5e SET-child6-CAPTION: FUN_00624350(frame,6,payload). chain.
  case 0x5f CLOSE/FORWARD: child id0 -> FUN_0062ef40(child,0x58,payload,0); FUN_0062bd40(frame) relayout. chain.
  cases 5-8,0xb-0x56 (the paint/size-query/generic band): break -> delegate to base proc (DlgMsg does not paint itself; the child frames paint).
Instance accessor for children: FUN_0062cfc0(frame, childId[, ...]). Style read: FUN_0062fe20(frame,mask). Dispatcher: FUN_0062ef40 / FUN_0062ee80.

- **Create recipe:**

DlgMsg is created as a child frame via the create primitive, then the dialog subsystem drives setup/create automatically:

1. (One-time, subsystem init) FUN_00623b40(themeResource) must have run so DAT_00c0ac40 (dialog theme/anchor resource) is set. It registers DlgMsg as message-handler slot 6 (FUN_00626800(6,&LAB_00623e00) + FUN_00626590(6,&LAB_00623e00,0)). If DAT_00c0ac40 is NULL the close-button wiring branch in create is skipped (safe, no crash).

2. Build a create payload: struct { wchar_t* messageText; } ud; ud.messageText = L"...";

3. Create: frame = FUN_0062bfc0(parentFrame, STYLE, childId, FUN_00623670, &ud, 0);
   STYLE selects the button set (OR the field/close bits as needed):
     - single OK/affirm button:            0x8000
     - two-button (affirm + negative):      0x8000 | 0x1000        (e.g. Yes/No)
     - retry/3-button set:                  0x10000 | 0x4000 [| 0x1000 for the 3rd]
     - add a free-text input line:          | 0x2000               (creates child id 3)
     - add a close (X) button:              | 0xe0000
   The primitive auto-sends case 4 (SETUP: base proc FUN_00612240 + style|=0x30) then case 9 (CREATE: children incl. label id1 seeded from ud.messageText).

4. Warm-ups / drive:
   - Set/replace message text later: FUN_0062ef40(frame, 0x58, wcharPtr, 0).
   - Set button captions: 0x59 (btn2), 0x5b/0x5c/0x5d/0x5e (children 3/4/5/6).
   - Seed input field text: 0x5a (requires style&0x2000).
   - Read what the user typed: FUN_0062ef40(frame, 0x57, &outPtr, 0) with non-NULL out (requires style&0x2000).
   - Layout is automatic on 0x0a/0x37/0x38; force relayout with FUN_0062bd40(frame).
Sizing is fully self-computed (case 0x38 measures children and clamps to minimums _DAT_00a51090 width / _DAT_0094f4e8 height); do not hard-size it.

- **Crash gotchas:**

- 0x57 (get input text): asserts FUN_00487a80(0xd3) if the out pointer p3 is NULL; asserts 0xd4 if the frame style lacks 0x2000 (no input field). Only send 0x57 to a dialog created with the 0x2000 style AND pass a valid out buffer.
- 0x5a (set input text): asserts FUN_00487a80(0xef) if style lacks 0x2000. Do not push input text into a message-only dialog.
- Base proc FUN_00612240 case 9 asserts FUN_00487a80(0xaf) via FUN_0062d6f0 if the frame is already registered under that proc — don't double-register / reuse the same frame slot.
- Close-button (style 0xe0000) create branch dereferences DAT_00c0ac40 and calls FUN_0062da90/FUN_0062d910/FUN_0062ef40(...,0x58,...). It is guarded by (DAT_00c0ac40 != 0 && closeChild != 0); if you request 0xe0000 before the dialog subsystem is initialized the X-button simply isn't wired (no crash) but won't dismiss the dialog.
- The get/set caption/text handlers all resolve children by fixed id via FUN_0062cfc0 and no-op if the child is absent (they null-check), so sending 0x59/0x5b-0x5e to a dialog that never created that button is silently ignored — but the corresponding button won't exist, so verify your STYLE actually created the button id you target.
- This is NOT a self-painting control; it delegates paint/size-query (band 5..0x56) to the base proc and relies on its child frames. Don't expect a case-1 paint body here.


### UiCtlDlgMsg  (EXE 0x00623670, confidence: high)

- **WASM:** ram:80e586ff
- **Assertion file:** P:\Code\Engine\Dialog\DlgMsg.cpp (EXE string @ 0x00a5102c)
- **Struct layout:**

RESOLUTION: WASM IUi__UiCtlDlgMsgProc_FrameMsgHdr (ram:80e586ff) -> assertion file "P:\\Code\\Engine\\Dialog\\DlgMsg.cpp" -> EXE string 0x00a5102c -> xrefs land inside FUN_00623670 (its own assert sites 0x6236a9/0x6236cf/0x623771, all MOV EDX,0xa5102c feeding FUN_00487a80). ToFunctionStart => FrameProc = 0x00623670. Confirmed frame proc (composite/game-layer modal message dialog), is_frame_proc=true.

This is a GAME-LAYER (Engine\\Dialog) composite dialog, NOT a Controls\\ primitive: it has NO private heap instance allocated via FUN_0047f340. Instead its "instance" state = the standard Frame object + a CHILD-FRAME TABLE. Children are created in the case-9 build (FUN_00623be0) and re-fetched everywhere via FUN_0062cfc0(frame, childIndex):
  child 0 = backdrop/background frame (proc FUN_00611890) — created only if style & 0xe0000; receives msg 0x58 (notify) and is the container/close target.
  child 1 = MESSAGE BODY text/content (proc FUN_0060d410, style 0x20300) — the main prompt text; primary layout anchor (msg 0x114 measured in layout).
  child 2 = button slot #1 (proc FUN_0060f4f0, style 0x442300) — default/primary button (e.g. OK/Yes).
  child 3 = TEXT-INPUT / edit field (proc FUN_0060f4f0, style 0x10300) — created ONLY if style & 0x2000; source for the 0x57 GET result and target of 0x5a SET.
  child 4,5,6 = additional button slots (proc FUN_0060f4f0, styles 0x440300/0x444300/0x442300) — extra buttons (No/Cancel/etc.), which ones exist depends on style bits.

FrameMsgHdr payload (param_2) fields used: *(payload+0)=frame-context ptr; **(payload+4)=style-flags word (case 4 ORs 0x30 in); **(payload+0xc)=parent-proc slot (case 4 writes FUN_00612240) / also key+state in input msgs (+4=action id, +8=state); *(payload+8)=out size-rect ptr (msg 0x38 writes width to **(payload+8) and height to *(*(payload+8)+4)).

STYLE FLAG SEMANTICS (read via FUN_0062fe20(frame,mask)), decide which children/buttons build:
  0x30       base container flags (auto-set on create).
  0x1000     enable second/No button (paired with 0x8000).
  0x2000     dialog HAS text-input field -> builds child 3; gates msgs 0x57/0x5a (assert otherwise).
  0x4000     used with 0x10000 to pick 3-button (Yes/No/Cancel-style) layout branch.
  0x8000     enable first/Yes button (paired with 0x1000).
  0x10000    alternate button-set branch selector.
  0x20000/0x40000/0x80000 (mask 0xe0000) build backdrop child 0 + close-box config (0x20000 => mode 2).
  0x100000   modal / keep-open: button events do NOT auto-close (FUN_00623ba0 skips FUN_0062c550).
  0x400000   taller top-margin variant (measure pass FUN_00624010 uses _DAT_00a51098 vs _DAT_00a51094).

- **Message protocol:**

FrameProc FUN_00623670 switches on msg = param_1[1]; unhandled/most msgs fall through to base via thunk_FUN_00647170 (parent proc FUN_00612240). Dispatcher = FUN_0062ef40(frame,msg,wparam,out); post = FUN_0062ee80; child fetch = FUN_0062cfc0(frame,idx); style read = FUN_0062fe20(frame,mask); assert = FUN_00487a80(code).

  4  (INSTALL BASE): sets parent proc **(payload+0xc)=FUN_00612240, ORs style 0x30, forwards to base.
  5,6,7,8 : create/attach phases — forwarded to base (no local work).
  9  (BUILD): FUN_00623be0(frame,payload) constructs all child frames per style flags (see struct_layout); primitive create = FUN_0062bfc0(parent, childStyle, childIndex, childProc, userdata, 0); if global template DAT_00c0ac40 set, seeds backdrop via FUN_0062ef40(child0,0x58,...).
  0xa (RELAYOUT/BROADCAST): queries content width via FUN_0062ef40(frame,0x56,0,&w); pushes width (FUN_0062f150) to button children idx 2..6 and to body child idx 1; forwards base.
  0xb..0x30, 0x32..0x36, 0x39..0x56 : pass-through to base (standard frame handling).
  0x31 (KEY/NAV INPUT): sub-switch on payload+4 (action id 1..6) gated by payload+8 (key state 7=down,8=up,9=repeat) -> fires button events via FUN_00623ba0(frame, eventId, arg) with eventId 7..0xc, or FUN_0062ee80(frame,9,onoff,0) for toggle (action 3). FUN_00623ba0 posts the event then, unless style 0x100000, closes/commits via FUN_0062c550.
  0x37 (ARRANGE/LAYOUT): FUN_00623e20 — positions children: measures buttons 0..3 (FUN_0062e8a0 msg 0x89), lays out backdrop (msg 0x94), input child 3 (msg 0x105), body child 1 (msg 0x114).
  0x38 (MEASURE/SIZE-QUERY): FUN_00624010 — computes preferred size, writes width to **(payload+8) and height to *(*(payload+8)+4); clamps to mins _DAT_00a51090/_DAT_0094f4e8.
  0x57 (GET INPUT RESULT): requires style 0x2000 else assert 0xd4; requires out ptr param_3 else assert 0xd3; reads child 3 (FUN_0062cfc0(frame,3)) text via FUN_0060f4b0 -> *param_3; forwards base.
  0x58 (CLOSE/DESTROY): child1 teardown FUN_0060a420, relayout FUN_0062bd40, forward base.
  0x59 : set button-2 label — FUN_00624350(frame,2,text).
  0x5a (SET INPUT TEXT): requires style 0x2000 else assert 0xef; child 3 FUN_0060f490(text).
  0x5b : set child-3 label/text — FUN_00624350(frame,3,text).
  0x5c : set button-4 label — FUN_00624350(frame,4,text).
  0x5d : set button-5 label — FUN_00624350(frame,5,text).
  0x5e : set button-6 label — FUN_00624350(frame,6,text).
  0x5f (NOTIFY/DISMISS): forwards 0x58 to backdrop child 0 (FUN_0062ef40(child0,0x58,payload,0)), relayout FUN_0062bd40, forward base.
  FUN_00624350(frame,idx,text) helper = FUN_0062cfc0(frame,idx) -> FUN_0060fdf0(child,text) -> FUN_0062bd40 relayout.

Note the separate registrar FUN_00623b40(proc) (other xref of the file string): installs the dialog template DAT_00c0ac40 = FUN_0046fda0(proc) and registers frame-message class 6 (FUN_00626800/FUN_00626590 with handler LAB_00623e00). It is the template/registration path, NOT the paint proc.

- **Create recipe:**

DlgMsg is a game-layer modal dialog; you do not paint it directly, you instantiate its frame and drive it with the message protocol.

1. PROC: FrameProc = 0x00623670. Parent/base proc is FUN_00612240 (installed automatically on msg 4).
2. FLAGS: choose behavior via style bits before/at build (read back with FUN_0062fe20):
     base 0x30 auto-added; add 0xe0000-group for backdrop/close-box; 0x8000(+0x1000) for primary(+secondary) buttons; 0x10000|0x4000 for 3-button set; 0x2000 to include a text-input field; 0x100000 to make button presses NON-closing (persistent modal); 0x400000 for tall-header variant.
3. CREATE ORDER (standard frame lifecycle): send 4 (installs base FUN_00612240, ORs 0x30) -> 5,6,7,8 (attach phases, base) -> 9 (BUILD: FUN_00623be0 spawns children via FUN_0062bfc0(parent, childStyle, childIndex, childProc, ud,0); child procs = body FUN_0060d410@idx1, buttons FUN_0060f4f0@idx2/4/5/6, input FUN_0060f4f0@idx3, backdrop FUN_00611890@idx0).
4. WARM-UPS after build: set body text and button labels via 0x59/0x5c/0x5d/0x5e (buttons 2/4/5/6) and 0x5b (child 3); if input dialog (0x2000) preload with 0x5a. Then let 0xa/0x37/0x38 run (broadcast width, arrange, measure) so it self-sizes — do not hardcode geometry; measure pass clamps to mins _DAT_00a51090 (width) / _DAT_0094f4e8 (height).
5. RUNTIME: keyboard nav arrives as 0x31 (action id in payload+4, state in payload+8) and is translated to button events 7..0xc; button press commits/closes via FUN_0062c550 unless style 0x100000.
6. READ RESULT: for input dialogs send 0x57 with a non-null out pointer to pull the entered string (FUN_0060f4b0 from child 3).
7. TEARDOWN: 0x5f (dismiss -> forwards 0x58 to backdrop) or 0x58 (destroy) then relayout FUN_0062bd40.
Registration alternative: FUN_00623b40(proc) registers the reusable template DAT_00c0ac40 and frame-class 6 handler LAB_00623e00 (call once at UI init, not per-dialog).

- **Crash gotchas:**

- Msg 0x57 (get input result) ASSERTS: FUN_00487a80(0xd3) if out ptr param_3 is NULL, and FUN_00487a80(0xd4) if the dialog was not built with style 0x2000 (no input child 3). Only call 0x57 on an input-style dialog and always pass a valid out buffer.
- Msg 0x5a (set input text) ASSERTS FUN_00487a80(0xef) if style 0x2000 not set (child 3 absent). Guard by checking the input flag first.
- FUN_00487a80 is marked no-return (fatal assert) — these are hard aborts, not recoverable errors.
- Children only exist per style flags: fetching child idx 2..6 / idx 3 / idx 0 via FUN_0062cfc0 returns 0 when that button/input/backdrop was not built; every setter (0x59/0x5b/0x5c/0x5d/0x5e via FUN_00624350) null-checks the child, so setting a label for a non-existent button silently no-ops (a UX bug, not a crash) — verify the flag set matches the labels you push.
- Do NOT send 0x59/0x5a/0x57 before msg 9 (build); children/table don't exist yet, and text ops would target uninitialized child slots.
- Msg 4 MUST run first: it installs parent proc FUN_00612240 and ORs style 0x30; skipping it leaves **(payload+0xc) parent slot unset so base forwarding (thunk_FUN_00647170) dispatches through a bad/parent pointer.
- Layout/measure (0x37/0x38) dereference **(payload+8) as the out size-rect pointer-to-pointer; a malformed measure payload causes a wild write of computed width/height.


### CursorFrame (IFrame::CursorFrameProc)  (EXE 0x00639aa0, confidence: high)

- **WASM:** ram:809357df
- **Assertion file:** P:\Code\Engine\Frame\FrGamepad.cpp (EXE string @0x00a5261c; WASM "../../../../Engine/Frame/FrGamepad.cpp" @ram:0010ec4f). Assert-expr string "overlayId" @EXE 0x00a526dc / WASM ram:001148ee. Resolution chain: WASM IFrame::CursorFrameProc -> assertion path FrGamepad.cpp -> EXE search_strings -> get_xrefs_to 0x00a5261c/0x00a526dc both land in FUN_00639aa0 @00639ad0/00639ad5 -> ToFunctionStart = 0x00639aa0.
- **Struct layout:**

NO OWN INSTANCE STRUCT. CursorFrameProc is a thin, stateless layout/reflow proc layered on top of a base image/quad frame (base proc = FUN_00611890). It never handles alloc(case 9)/free(0xb)/paint(1) itself — all of those fall through to the base via FrameMsgCallBase, so it declares no instance and has no FUN_0047f340("...cpp",size) allocation.

It uses only:
- The host frame's child slot: FrameGetChild(self,0) reads *(frameObj+0xbc) (via FUN_0062cfc0 -> FUN_0064ca80 -> +0xbc). The single child is the object it repositions.
- One module-global that acts as its "state":
    DAT_00c0b608 : int cursorMargin (screen inset in px; read as (float)(unsigned)). Currently 0 at rest; set by the builder from its param_4. If negative it is unsigned-corrected with _DAT_00937190 (=2^32, 0x4f800000).
Related builder globals (in FrGamepad.cpp, not part of the proc's own struct): DAT_00c0b5f8 = cursor parent frame handle, DAT_00c0b604 = cursor child frame handle, DAT_00c0b584 = cursor texture/quad source, DAT_00c0b5e4 = frame flag arg, _DAT_00c0af20/_DAT_00c0af24 = hotspot offsets, _DAT_00bef7a4 = scaled cursor extent.

On-stack scratch built for msg 0x37 (screen W,H in param_2[0],param_2[1]; m = cursorMargin):
  arg2 (size,  Coord2f)  = { W-m, H-m }
  arg3 (rect,  Coord2f[2]) = { m, m, W-m, H-m }   // min={m,m}, max={W-m,H-m}

- **Message protocol:**

FUN_00639aa0(msgframe* param_1, float* payload param_2, void* out param_3):
  self  = param_1[0] (frame handle), msg = param_1[1], baseProcIndex = param_1[5].

  case msg == 0x37 (55)  "relayout / screen-size changed":
     child = FrameGetChild(self, 0)            // FUN_0062cfc0
     if child == 0 -> ASSERT FUN_00487a80(0x65a="overlayId")   // child MUST exist
     m = (float)(unsigned)DAT_00c0b608          // cursor margin/inset
     payload param_2 = { screenW (px, float), screenH (px, float) }
     FrameSetPosition(child,                    // FUN_0062f770 -> FUN_0064a470(...,6)
                      size = {W-m, H-m},
                      rect = {m, m, W-m, H-m})   // stretch child to fill self minus margin

  default (every other msg incl. 1 paint, 4 install-base, 9 alloc, 0xb free, 0x15 size-query, 0x56+):
     -> FrameMsgCallBase(param_1,param_2,param_3)   // thunk_FUN_00647170 == FUN_00647170
        Walks proc chain from index param_1[5]-1 downward (proc table @frameObj+0xa8, count @+0xb0),
        invokes next non-null base proc with a rebuilt 6-dword msgframe. It explicitly SKIPS
        forwarding for msg 9 and 0xb (alloc/free are not chained here).

  So this proc's ONLY active behavior is: on a 0x37 reflow, resize its child to cover the screen inset by the cursor margin; all rendering/lifecycle is delegated to the underlying image frame.

- **Create recipe:**

Built by FUN_0063bed0(param_1=texture/def, param_2=uint[2]{srcW,srcH}, param_3=int[2]{hotspotX,hotspotY}, param_4=float margin). Steps (verified primitives):

 1. Guard: param_4 (margin) != 0 else ASSERT(0x720). Store DAT_00c0b608 = (int)param_4  (== the 'm' the proc later reads).
 2. Tear down any previous cursor frame: if DAT_00c0b5f8 != 0 -> FUN_0062c550(DAT_00c0b5f8); null DAT_00c0b5f8/DAT_00c0b604.
    (param_1==0 path = "hide cursor": zero hotspots, call FUN_00639bd0 and return — no frame created.)
 3. Build the cursor quad source: img = FUN_00669f90(param_1,0x30); quad = FUN_0065efa0(1,&img,&pxSize,&type=0x12,0,0,0x020003e0,0xb); FUN_0046f850(img).
 4. Create PARENT (cursor) frame:
       DAT_00c0b5f8 = FrameCreate(parent=0/root, flags=0x400, child=0, proc=FUN_00611890 [base image/quad proc], userdata=0, 0)   // FUN_0062bfc0
 5. INSTALL this proc on it:
       FUN_0062f150(DAT_00c0b5f8, FUN_00639aa0 /*CursorFrameProc*/, 0)   // pushes onto proc chain @+0xa8/+0xb0
 6. Attach quad + colors: FUN_00611da0(DAT_00c0b5f8, quad, &sizeCoord, &colorRGBA{1,1,1,1 = 0x3f800000}, &uv{0,0}).
 7. Z-order to top:   FUN_0062f5a0(DAT_00c0b5f8, 0x7fffffff)   // always render above everything
 8. Size:            FUN_0062f9a0(DAT_00c0b5f8, &sizeCoord{srcW,srcH})
 9. Flags/visibility:FUN_0062fcb0(DAT_00c0b5f8, DAT_00c0b5e4)
10. FUN_0046f850(quad)  // release local ref
11. Create the CHILD frame the proc repositions:
       DAT_00c0b604 = FrameCreate(parent=DAT_00c0b5f8, flags=0, child=0, proc=FUN_00611890, userdata=0, 0)   // FUN_0062bfc0
       (optionally attach DAT_00c0b584 image via FUN_00611da0 with margin-based rect; else FUN_0062fcb0(child,0)).
12. FUN_00639bd0() to finalize/apply.

Minimal proc-only recipe (to reuse CursorFrameProc on your own frame): create a base image frame (proc FUN_00611890, flags 0x400, z=0x7fffffff), give it EXACTLY ONE child frame (index 0), install FUN_00639aa0 via FUN_0062f150, set global DAT_00c0b608 to a non-zero margin, then post msg 0x37 with payload {screenW,screenH} to trigger the child stretch. No alloc/size-query warm-up needed (proc has no instance).

- **Crash gotchas:**

- MUST have a child at index 0 before msg 0x37 reaches the proc: FrameGetChild(self,0)==0 -> ASSERT FUN_00487a80(0x65a). The builder creates DAT_00c0b604 for exactly this reason. Installing the proc on a childless frame and then resizing the screen = hard assert.
- Margin global DAT_00c0b608 must be set (builder asserts margin!=0 at 0x720). At rest it reads 0 -> child stretched full-screen with no inset; that's non-fatal but means m=0.
- FrameSetPosition target (FUN_0062f770) asserts on null frame (0x840); guaranteed non-null here only because of the child assert above.
- Do NOT route alloc(9)/free(0xb) through this proc expecting base handling: FrameMsgCallBase explicitly bails on msg 9 and 0xb, so lifecycle must be driven by the standard create/destroy primitives (FUN_0062bfc0 / FUN_0062c550), not by messaging the cursor proc.
- Only a single global cursor instance is supported (DAT_00c0b5f8/DAT_00c0b604). Re-invoking the builder frees the previous frame first; holding a stale handle to the old parent/child after a rebuild is a use-after-free.
- Payload for msg 0x37 is two floats {W,H} in screen px; passing anything smaller reads past the payload (proc dereferences param_2[0] and param_2[1] unconditionally once msg==0x37).


### UiCtlBorder (IUi::UiCtlBorderProc)  (EXE 0x00857ce0, confidence: low)

- **WASM:** ram:80e02ef0
- **Assertion file:** none — UiCtlBorderProc has NO instance allocation, so there is no FUN_0047f340("<Ctl>.cpp",size) assertion string to anchor on. Searched EXE strings for "Border"/"Border.cpp": only unrelated tokens (ScreenBorderless, IconBorder, clientBorder, borderColor, and the login-screen child-frame names "BorderAdd"/"BorderCreate" inside FUN_00859230). The related game-layer file that USES it is UiCtlStat.cpp @0x00bc5a64 (WASM: IUi::CtlStat::CStatFrame::ValueBorderFrameProc calls UiCtlBorderProc directly).
- **Struct layout:**

NO OWN INSTANCE STRUCT. UiCtlBorderProc is a stateless decorative FrameProc: it never allocates (no msg-9 alloc / no FUN_0047f340), never asserts on double-init, never frees. It reads only:
- msgframe[0]  = HFrame (owning frame id) -> passed as target to the content-add engine
- msgframe[1]  = message id
- msgframe[4]  = frame STYLE dword (the border-variant selector; bits used: 0x1, 0x2, 0x4, 0x8, 0x10, 0x20)
Paint payload (void* payload, msgframe[2]): payload[0]=sub-pass flags (bit0=draw-border, bit9/0x200=alt border), payload+7 (byte +0x1c)=content Rect4f {L,T,R,B floats}. It borrows a transient HGrModel out-param from the image-template add on the local stack (WASM stack+0xc), optionally tints it, then closes it — no persistent state is kept.

- **Message protocol:**

Authoritative from WASM IUi::UiCtlBorderProc (ram:80e02ef0). NOTE WASM msg numbering: paint/content-build = msg 8 (EXE control family also uses case 8 for OnContentAdd; some EXE procs use case 1 for the PAINT sub-pass). Handled cases:

- msg 8 (OnContentAdd / build border content). Gate on payload sub-pass flags (*payload = payload[0]) and STYLE (msgframe[4]):
   * If (style & 1)==0 and (style & 8)!=0 and (payload[0] & 1)!=0: add ONE content-fit border template (default atlas entry) into a {32,32}-inset rect at payload+7, texop 4, capturing HGrModel out.
   * If (style & 1)==0 and (style & 8)==0 and (payload[0] & 1)!=0: SELECT border template by style corner bits — (style&2)->tmplA, else (style&4)->tmplB, else (style&0x10)->tmplC, else ->tmplD — add into {32,32} rect, texop 7, layer, capturing HGrModel out.
   * If (style & 1)!=0 and (payload[0] & 0x200)!=0: add the default border template, texop 7, layer 9.
   * Post-add: if HGrModel out valid AND (style & 0x20)!=0 -> GrModelSetColor(model, 0x80FFFFFF) (semi-transparent white / dimmed). Then HandleClose(model) ALWAYS (transient handle).
   Six atlas template pointers live in one 6-entry table (WASM ram:00167170..0016718e: {0x0102378b default, 0x010265b3 fit, 0x01021127 A, 0x01021128 B, 0x0102eea2 C, 0x01021129 D}).

- msg 0x15 (size query / border metrics), only if (style & 1)==0. Writes a Rect4f of border insets to out (payload3):
   * (style & 8)==0 -> {left=6.0, top=4.0, right=6.0, bottom=4.0}
   * (style & 8)!=0 -> {left=4.0, top=9.0, right=4.0, bottom=10.0}
   Returns WITHOUT calling base. If (style&1)!=0 it does NOT answer and falls through to base.

- ALL other messages (9/create, 0xa, 0xb/free, 0xc..0x14, and anything else) -> FrameMsgCallBase (EXE thunk_FUN_00647170) unchanged. It installs no base in a case-4 handler here (it is itself used as the base by wrappers like ValueBorderFrameProc, which post-adjusts: on msg 0x15 subtracts 2.0 from top).

EXE-mapping caveat: EXE image-template engine = FUN_0062b8e0 (FrameContentAddImageTemplate, {32,32} inset arg); base-call = thunk_FUN_00647170; style read = FUN_0062fe20(frame,mask). I inspected ~20 of 40 FUN_0062b8e0 callers; the small standalone EXE border FrameProcs FUN_00857ce0, FUN_008854f0, FUN_00878cd0 each draw a SINGLE border template + return insets from _DAT globals + delegate to base (the exact UiCtlBorderProc idiom, but single-variant). The full 6-template-select + 0x80FFFFFF tint + HandleClose idiom appears folded into larger control procs (e.g. the button proc FUN_00876880 uses PTR_DAT_00bf44cc/d0/d4/d8/dc/e0 select + 0x50FFFFFF tint + FUN_0046f850 close). A confident 1:1 EXE address for the generic UiCtlBorderProc could not be pinned; 0x00857ce0 is given as the closest standalone EXE border FrameProc, NOT a verified match.

- **Create recipe:**

You do NOT instantiate UiCtlBorderProc as a top-level control — it is a decorative BASE proc that other frame procs delegate to (its only WASM caller, ValueBorderFrameProc, invokes it directly and then tweaks the size query). To reproduce its effect on a native frame:
1. Create the frame with FUN_0062bfc0(parent, styleFlags, childId, proc, userdata, 0). Encode the border variant in styleFlags: bit0(0x1)=suppress (border draws nothing / no size answer), bit3(0x8)=tall variant (insets {4,9,4,10} instead of {6,4,6,4}), corner bits 0x2/0x4/0x10 select corner-template A/B/C (none set = D), bit5(0x20)=dimmed (tints border 0x80FFFFFF).
2. Warm-ups: NONE required — the proc has no static-init (msg 5) and no per-instance alloc (msg 9). It only needs the frame's graphics content system to be live (same prerequisite as any FrameContentAddImage* call).
3. Sizing: the border reports its own inset Rect4f on msg 0x15; let the layout/base consume it. Do not FrameSetSize the border to negative/oversize — insets are fixed pixel metrics.
4. Order: install/delegate to it as the BASE (msg-4 install target) of a wrapper proc, or route paint (msg 8) and size (msg 0x15) to it and forward everything else to FrameMsgCallBase.

- **Crash gotchas:**

1. NOT paint-before-graphics-safe in the usual sense but close: it holds NO static image lists, so unlike icon controls it cannot feed a null HFrameImageList; however FrameContentAddImageTemplate (FUN_0062b8e0) still requires the frame content subsystem up — driving msg 8 before graphics init can assert inside the engine.
2. Transient HGrModel: the border captures the model out-param, may GrModelSetColor it (style&0x20), and ALWAYS HandleClose()s it. It is created-and-closed within the single paint; do not cache or reuse that handle — it is invalid after the call.
3. Style bit0 (0x1) SUPPRESSES both the border draw and the size-query answer (falls through to base). A frame that unexpectedly has bit0 set will silently render no border and report base metrics — looks like "border missing", not a crash.
4. It has NO case-4 base install and NO case-9 alloc: using it as a *standalone* top-level proc (rather than as a delegated base) means create/destroy/most messages just hit FrameMsgCallBase; it will not manage any child/instance and will not assert — but it also won't self-manage lifetime.
5. Size-query out buffer: msg 0x15 writes 4 floats (Rect4f) to the out pointer with no null-guard in the core path — a wrapper passing a null/short out buffer for 0x15 will corrupt/fault (ValueBorderFrameProc-style wrappers additionally read-modify-write out+4, so the buffer must be a full Rect4f).


### UiCtlDlg (Dialog/window frame) — grip child proc @0x00876740; parent Dialog FrameProc @0x00876880  (EXE 0x00876740, confidence: high)

- **Assertion file:** P:\Code\Engine\Frame\FrApi.cpp (from the create primitive FUN_0062bfc0 / FUN_0047f340, size 0x132). Neither dialog proc carries its own Ctl cpp string; both are Frame-API frame procs, not P:\Code\Engine\Controls\*.cpp templates.
- **Struct layout:**

MESSAGE FRAME (param_1, the arg every frame proc gets):
  param_1[0] = frame/window handle (the "self" object; passed as *param_1 to all Fr* helpers)
  param_1[1] = message id (switch selector)
  param_1[2] = ptr to instance-data slot; *(param_1[2]) = per-instance struct (dialog: title-text buffer at +0, byte[3] of dword0 = "has custom caption/icon" flag). For the grip child @0x00876740, *(param_1[2]) is a single dword holding the created grip child-window handle.
  param_1[3] = base/parent proc slot (installed on msg 4 in the base template)
  param_1[4] = style/flags word (fVar13). Decoded bits used by 0x00876880: 0x1=has title bar, 0x8/0x10/0x18=caption button style group, 0x40=child/embedded (forces 0x200), 0x100=has bottom bar, 0x200=resizable(-> spawns grip child), 0x400=wide-caption. local_e4/local_bc/local_b4 are derived inset heights from these.

FRAME instance (allocated by FUN_0062bfc0 -> FUN_0047f340, 0x132 bytes): +0x84/0x88/0x8c=0, +0x90=0x40 (default style), +0x190(400)=creation flags(param_2), +0x1c4=0, +0xbc=returned handle. Proc+userdata installed at FUN_00647320(proc,userdata).

PAINT payload (param_2 on msg 8): [0]=sub-pass bitmask (b1=background/border, b2=caption buttons, b3=icon+title text, b5=title glyph); [7]=client left, [8]=top, [9]=right/width, [10]=bottom/height; [0xb],[0xc]=hover/pressed hit-codes feeding the close/min button glyph state.
HITTEST payload (param_2 on msg 0x17): [0]=x,[1]=y, [2]=region origin, [3]=extent, [4]=ptr to OUT hitcode.
QUERY payload (param_3 on msg 0x15): OUT 4 floats = caption/border insets {left,top,right,bottom}.

- **Message protocol:**

== 0x00876740 (RESIZE-GRIP CHILD proc, installed by parent's CREATE) ==
 msg 8  PAINT: FUN_0062d380 fetches metrics, FUN_00679a60(res 0x09f000000,0x20003e0,0)=grip texture, clamps quad to param_2[9]/[10] (client w/h), FUN_0062b2d0 draws it bottom-right, FUN_0046f850 releases. (draws the diagonal resize gripper)
 msg 9  CREATE/STORE: *(int*)param_1[2] = *param_2  (store this grip child's own handle into the slot)
 msg 0x2e DESTROY: if slot!=0 FUN_0062b040(*(slot)) destroy the grip window; else assert FUN_00487a80(0x27e).
 (all other msgs: no-op)

== 0x00876880 (THE DIALOG/WINDOW FRAME proc — title, drag, close, resize) ==
switch on param_1[1] (float-reinterpreted ints):
 5  INIT-GLOBAL: assert if DAT_010819c8!=0, then FUN_0062d790(...) creates the shared caption-button glyph resource DAT_010819c8 (variant chosen by feature-flag FUN_0049b9e0(0x71)); forwards to base.
 6  DEINIT-GLOBAL: FUN_0046f9b0(DAT_010819c8); DAT_010819c8=0.
 8  PAINT: draws border/background frame, caption bar (FUN_0062b8e0 with PTR_DAT_00bf44xx skins per style), icon+title text (FUN_0062bb30, color 0xffdcdcdc, "%s  [%s]" secondary via FUN_0046c440), caption buttons via DAT_010819c8 (FUN_0062b290) at close/min slots, and optional 0x12e overlay icon. Sub-passes gated by param_2[0] bits & style bits.
 9  CREATE: FUN_00877d90(enable/disable child buttons by focus), posts 0x10000141 & 0x46; if style&0x200 (resizable) walk child ids 10000..0x2718 (FUN_0062cfc0) and spawn the grip child: FUN_0062bfc0(container,0x80,id,FUN_00876740,self,0) then FUN_0062ede0(child,1,0) show.
 0xb DESTROY: FUN_008766e0(self) destroys grip children (ids 0x2718..10000).
 0x15 QUERY-INSETS: writes param_3[0..3] = caption/border margins computed from style (uses _DAT_00944e04 etc; adds caption height when style&0x20).
 0x17 HITTEST: writes *(param_2[4]) = region code: 2=caption(drag), 9/0xb=vertical resize edges(style&8/0x10), 0xc=bottom resize(if resizable), 0xd=right/close-area(style&0x100), 10=alt-edge. Bounds from param_2[0..3] & derived insets.
 0x20 COMMAND: if *param_2==9 or 0x12e -> FUN_0062b040(self) (close the dialog).
 0x2b STYLECHANGE: if param_2[1]&0x2004 -> FUN_0062bd80(self,0x24); forward.
 0x33 FOCUS/SHOW: post 0x10000084, FUN_00877d90 refresh buttons, forward.
 0x34 ACTIVATE: if !(style&0x100) & focused, clear style bit 0x20 via FUN_0062f830; FUN_00877d90; forward.
 0x37 RESIZE/LAYOUT (style&0x200): recompute size vs min via FUN_0062d380/FUN_0062d160, clamp aspect (_DAT_00b95ba8/_DAT_00b95ba0), FUN_0062f770 apply new rect; forward.
 0x41,0x43 MOUSE-ENTER/LEAVE-ish: if !(style&4) post 0x10000084; forward.
 0x10000141/0x46: default branch — repaint trigger FUN_0062bd40(self) (invalidate).
 0x10000142: sub-cmd *param_2==0x45 -> FUN_00877d90 + base FUN_00647170; else if title differs (*param_1[2]!=*param_2) store new caption ptr and FUN_0062bd40 invalidate.
 default: thunk_FUN_00647170 (base Frame template) — the parent proc that handles low-level lifecycle (msg 4 install-parent, 2, 10 warm-ups, alloc/free).

- **Create recipe:**

The grip child @0x00876740 is NOT created directly by app code — the Dialog's own CREATE (msg 9) spawns it when style&0x200. To create the DIALOG (0x00876880) and thereby get the grip:

1. FUN_0062bfc0(parentContainer, styleFlags, childId, FUN_00876880, userdata, 0)
   - allocs a 0x132-byte Frame (FrApi.cpp), installs proc+userdata (FUN_00647320), sets creation flags at +0x190, returns handle at +0xbc.
2. styleFlags for a resizable titled window: set 0x1 (title bar) | 0x200 (resizable) | optionally 0x100 (bottom bar) | caption-button group bits 0x8/0x10/0x18. 0x18 auto-adds 0x40; 0x40 forces resizable.
3. Warm-up messages the create primitive sends automatically, in order: FUN_0064dc70(4,..) = msg 4 (install base/parent proc into param_1[3]); FUN_00647fc0(2,..) = msg 2; FUN_00647c80(10,..) = msg 10. Then the frame manager drives msg 5 (init glyph resource, once/global), msg 9 (dialog CREATE -> spawns grip child via a second FUN_0062bfc0 with FUN_00876740, flags 0x80, ids 10000+, self as userdata, then FUN_0062ede0 show).
4. Set caption text by posting msg 0x10000142 with the new string ptr in *param_2 (stored at *param_1[2], triggers invalidate). Sizing/min-size handled on msg 0x37.
5. DAT_010819c8 (shared caption-button glyph) must be inited via msg 5 before painting; it is process-global and ref-freed on msg 6.

- **Crash gotchas:**

- 0x00876740 msg 0x2e: if param_1[2] slot is 0 it hard-asserts FUN_00487a80(0x27e) (no-return). The slot MUST have been populated by msg 9 first; destroying a grip that never received CREATE aborts.
- 0x00876880 msg 5: asserts if DAT_010819c8 already non-zero — INIT-GLOBAL must be paired 1:1 with msg 6 DEINIT. Double-init or leaked instance without msg 6 aborts on next init.
- Paint (msg 8) dereferences *(param_1[2]) as the caption/instance struct and reads byte[3] as the icon flag, plus param_2[7..10] as client rect and param_2[0] as sub-pass mask — a malformed/zero instance or missing paint payload dereferences garbage (title-text FUN_00679a60 / FUN_0062bb30 with bad ptr).
- Grip children live at frame ids 10000..0x2718 (10000..10008). CREATE scans this exact range with FUN_0062cfc0; overlapping user child ids in [10000,10008] collide and break both grip creation and FUN_008766e0 teardown.
- Grip child is only created when style&0x200 is set; hittest codes 0xc (bottom resize) and the grip are dead if not resizable. style bit 0x40 silently forces 0x200.
- 0x00876880 forwards nearly everything to thunk_FUN_00647170 (base FrApi template); it does NOT itself alloc/free the instance (that is the base's msg 4/9-lifecycle). Installing 0x00876880 without the base warm-ups (msg 4 etc, done by FUN_0062bfc0) leaves param_1[3] base-proc slot null and unhandled msgs crash on forward.


### UiCtlDlgCloser  (EXE 0x00876740, confidence: high)

- **WASM:** ram:80e5e206
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlDlg.cpp (game-layer; WASM ../../../../Gw/Ui/Controls/UiCtlDlg.cpp), assert line 0x27e=638
- **Struct layout:**

msgframe (param_1, int*/undefined4*):
  [0] hframe   - this closer button's own frame handle (passed as target to FrameContentAddImage on paint)
  [1] msg      - message id (int): 8=paint, 9=init, 0x2e=activate
  [2] pInstance- pointer to this frame's per-frame instance/userdata slot; *(param_1[2]) holds the owning dialog frame handle after msg 9
  [3] baseProc - inherited/base proc slot (unused by this proc)
  [4] style    - frame style/flags dword (used by the parent dialog proc, not this closer)

payload (param_2) is message-specific:
  msg 8 (paint): [9]=frame width (float), [10]=frame height (float)
  msg 9 (init):  [0]=userdata = owning dialog frame handle (written into *param_1[2])

Instance state for the closer = a single dword: the owning dialog frame handle. (Accessor pattern: **(msgframe+2).)

- **Message protocol:**

FrameProc FUN_00876740(msgframe param_1, payload param_2). Switches on param_1[1]=msg. This is a GAME-layer (Gw\Ui\Controls) sub-control proc, NOT the engine template, so it uses game message ids and does NOT chain unhandled messages to a base proc (no thunk_FUN_00647170 tail-call; unknown msgs are silent no-ops).

Handled messages:
- msg 8 (PAINT / draw the close 'X'): builds a solid-color material via FUN_00679a60(&color, &DAT_020003e0, 0) with Color4b = 0x9f000000 (semi-transparent black tint over the X texture at data ptr 0x020003e0). Queries own size via FUN_0062d380(0,0,&sizeCoord,0,0), then computes a rect clamped to at least frame width=param_2[9] and height=param_2[10]; UVs 0..1 (0x3f800000). Emits the image with FUN_0062b2d0(param_1[0]=hframe, &rect, hMaterial, &uv0, &uv1, 0, 0) [FrameContentAddImage] and releases the material with FUN_0046f850(hMaterial) [GrMaterial/Model release].
- msg 9 (INIT / attach owner): *(int*)param_1[2] = *param_2. Stores the userdata passed at create time (the OWNING DIALOG frame handle) into the closer's per-frame instance slot. Returns immediately.
- msg 0x2e (ACTIVATE / click): if param_1[2] != 0, calls FUN_0062b040(*(int*)param_1[2]) = FrameClose(owningDialogFrame) which resolves the frame (FUN_00647db0), gates on close-permission (*(frame+0xbc), FUN_00647c80/FUN_00648660 checks) and tears it down via FUN_0062ab40. If param_1[2] == 0 -> FUN_00487a80(0x27e) ErrorAssertion (UiCtlDlg.cpp:638). This is the actual "X closes the dialog" behavior.
- any other msg: no-op (falls through to return).

- **Create recipe:**

Never created standalone; it is spawned by the parent dialog proc FUN_00876880 (UiCtlDlg full window proc) during ITS create message (case int 9), and only when the dialog style bit 0x200 (close-box enabled) is set:
  parentRoot = FUN_0062d330(dialogFrame)              // owner/root container of the dialog
  for id in [10000 .. 0x2718]:                         // find first free child id
      existing = FUN_0062cfc0(parentRoot, id)          // lookup child by id
      if existing == 0: break (create with this id)
      else FUN_0062ede0(existing, 0, 1)                // hide stale one, try next id
      (if id hits 0x2718 first, FUN_008766e0(dialogFrame) resets then creates)
  closer = FUN_0062bfc0(parentRoot, 0x80, id, FUN_00876740, dialogFrame, 0)  // create primitive: parent, flags=0x80, childId, proc=closer, userdata=dialogFrame
  FUN_0062ede0(closer, 1, 0)                            // show/enable it

So the concrete recipe: create a child frame under the dialog's owner with flags 0x80, proc=FUN_00876740, userdata = the owning dialog frame handle. Warm-up/message order the engine delivers: msg 9 (init, latches userdata into instance slot) -> then paint (msg 8) each frame -> msg 0x2e on left-click, which closes the owning dialog. Sizing comes from the parent frame's own width/height (param_2[9]/[10] at paint), so give the closer frame a fixed small square via the standard style/rect setup; the X glyph auto-fits.

- **Crash gotchas:**

- msg 0x2e with param_1[2]==0 (instance slot never latched) triggers ErrorAssertion FUN_00487a80(0x27e) at UiCtlDlg.cpp:638. Always deliver msg 9 (with payload[0]=owning dialog handle) before any activate, i.e. set userdata at create time via FUN_0062bfc0 so the init handler populates the slot.
- The stored value must be a live/valid dialog frame handle. FrameClose (FUN_0062b040) asserts FUN_00487a80(0x409) if the handle is 0, and dereferences frame+0xbc; a stale/freed handle -> use-after-free during close.
- This proc does NOT forward unknown messages to a base proc, so do not rely on inherited default handling (size-query 0x15, style get/set 0x56+, alloc/free 0xb, etc. are all no-ops here). It is purely paint(8)/init(9)/activate(0x2e).
- Paint builds and releases a material every frame (FUN_00679a60 / FUN_0046f850); calling paint without a valid hframe in param_1[0] or with the X texture data (0x020003e0) unmapped will fault in FrameContentAddImage.
- Do not hand-pick a child id already used under the dialog root; the parent's create loop deliberately scans 10000..0x2718 for a free slot and hides collisions.


### UiCtlHeader  (EXE 0x00876880, confidence: high)

- **WASM:** ram:8144892b
- **Assertion file:** FUN_00876880 (UiCtlHeaderProc) is installed dynamically via a proc pointer (80+ DATA xrefs; no assertion .cpp of its own). Resolution path used: the only "*Header.cpp" string in the EXE is "P:\Code\Gw\Ui\Controls\UiCtlGroupHeader.cpp" @0x00b96100, whose 3 xrefs land in FUN_0087ddc0 = IUi::CGroupHeaderFrame::FrameProc (WASM ram:81192f33) — that is the COMPOSITE group-header wrapper, NOT the flat paint proc. The flat WASM IUi::UiCtlHeaderProc (ram:8144892b) was matched to the EXE by its unique paint signature (title text via FUN_0062bb30 with font=0x14, color=0xffdcdcdc, layer=3) found @0x0087756c inside FUN_00876880.
- **Struct layout:**

This proc is essentially STATELESS per-instance (unlike the sibling CGroupHeaderFrame which allocs a 0x60-byte TCtlInstance). All state lives in (a) the FrameMsgHdr and (b) the frame's own style word.
FrameMsgHdr *p1 (the switch subject):
  +0x00 uint  frameHandle      (passed as *p1 to every Frame* helper)
  +0x04 uint  msg              (switch(p1[1]))
  +0x08 ptr   propInOut        (p1[2]; deref'd for property get/set path msg 0x10000142)
  +0x0c ...   (payload/reserved)
  +0x10 uint  style            (p1[4]) bitmask: 0x1=draw header bar; 0x8/0x10=collapse-arrow dir; 0x18=group-header mode; 0x40=force-mobile layout; 0x100=minimize button; 0x200=tabbed + drag-resizable; 0x400/0x200 combine into inset math ((style&0x200|0x400)>>5/6).
Payload p2 (msg-specific): PAINT -> *p2=subflags(bit1 bg, bit2 minimize glyph, bit3 title, bit5 overflow), p2[7..10]=frame rect (l,t,r,b as floats); HIT-TEST -> p2[0..1]=cursor xy, p2[2..3]=rect, p2[4]=out-code ptr, p2[0xb..0xc]=modifier flags.
Output p3: SIZE-QUERY writes p3[0..3] preferred rect (floats).
Module globals: DAT_010819c8 = shared close/scroll glyph texture (single instance for ALL headers). Image templates table @0x00bf44c8: ptr[0]=0x0094d594 then 0x00b95b34..0x00b95b6c variants, followed by floats 18.0,18.0,4.0 (glyph sizes).

- **Message protocol:**

FrameProc(FrameMsgHdr* p1, void* p2, void* p3). msg = p1[1] (+0x04); frame handle = *p1 (+0x00); style bitmask = p1[4] (+0x10). Cases (int-decoded from Ghidra denormal floats):
 - 5 CREATE-RESOURCE: lazily creates the single shared close/scroll-glyph texture DAT_010819c8 via FUN_0062d790 (mobile vs desktop template chosen by FUN_0049b9e0(0x71)); asserts FUN_00487a80(0xd7) if already non-null.
 - 6 DESTROY-RESOURCE: FUN_0046f9b0(DAT_010819c8); DAT_010819c8=0.
 - 8 PAINT: draws background frame image(s) via FUN_0062b8e0 selecting template PTR_DAT_00bf44c8/cc/d0/d4/d8/dc/e0 by style bits (0x8/0x10 arrow dir, 0x18 group mask, mobile); when (subflags*p2 & 8) draws the title string via FUN_0062bb30(frame, text, 0xffffffff, &rect, 0x14, align, 0x40, 0xffdcdcdc, 0,0, 3); when (*p2 & 4) draws collapse/minimize glyph via FUN_0062b290(...DAT_010819c8...); optional overflow glyph via FUN_004a29a0(0x12e) when *p2&0x20.
 - 9 BUILD/LAYOUT: if style&0x200 (tabbed) loops tab ids 10000..0x2718 creating child frames via FUN_0062bfc0(...,FUN_00876740,...); hooks property msgs 0x10000141 & 0x46.
 - 0xb DESTROY children: FUN_008766e0(*p1).
 - 0x15 SIZE-QUERY: writes preferred rect to p3[0..3] (l/t/r/b); default header height ≈20px desktop (matches WASM 20.0 default), taller in mobile; margins from _DAT globals.
 - 0x17 HIT-TEST: given cursor in p2[0..1] and rect p2[2..3], writes region code to *(uint*)p2[4]: 9/0xb=open/close arrow, 2=title(drag), 0xd=minimize, 0xc=group toggle.
 - 0x20 -> FUN_0062b040 when sub is 9/0x45; 0x2b -> FUN_0062bd80(frame,0x24) begin move when style&0x2004; 0x33 activate (FUN_0062f0a0(0x10000084)+repaint); 0x34 deactivate (clear style bit 0x20 + repaint); 0x37 drag-resize when style&0x200 (ratio calc -> FUN_0062f770); 0x41/0x43 mouse enter/leave (style&4) -> FUN_0062f0a0(0x10000084); msg 0x10000142 w/ sub 0x44/0x45 & 0x46 = property/redraw -> FUN_0062bd40 invalidate.
 - default: FrameMsgCallBase = thunk_FUN_00647170(p1,p2,p3) chains to the base proc.

- **Create recipe:**

1) Create a frame with the create primitive FUN_0062bfc0(parent, flags, childId, proc, userdata, wchar_label). You can pass FUN_00876880 directly as the proc, OR (as many windows do) create the frame with a base proc and PUSH this header proc on top: FUN_0062f150(frame, FUN_00876880, userdata) — observed at FUN_0086d4f0 (0x0086d580): FUN_0062bfc0(root,0x30,0x14,FUN_008730a0,&ctx,0); FUN_0062f150(frame,FUN_00876880,0).
2) Set style bits on the frame to pick appearance: 0x1=show header/title bar; 0x8 or 0x10=collapse-arrow open/closed; 0x18=group-header variant; 0x100=minimize button; 0x200=tabbed + drag-to-resize; 0x40=force mobile layout (else auto via FUN_0049b9e0(0x71) mobile probe).
3) Set the title text (FrameSetTitle-equivalent) so PAINT (msg 8, gated by subflags&8) renders it at font size 0x14, color 0xffdcdcdc, layer 3.
4) Warm-up: do NOT pre-create the close/scroll glyph texture — the proc lazily builds the shared global DAT_010819c8 on msg 5 (first activation) and asserts if it already exists; msg 6 frees it.
5) Sizing: let the layout engine query msg 0x15 for preferred height (~20px desktop). For tabbed mode (0x200) the msg-9 build step auto-creates up to 9 tab children (ids 10000..0x2718) using tab-proc FUN_00876740.

- **Crash gotchas:**

- Shared-texture double-init: msg 5 calls FUN_00487a80(0xd7) (no-return assert) if DAT_010819c8 is already non-null. DAT_010819c8 is ONE global shared by every header instance; msg 6 nulls/frees it, so tearing down one header can pull the glyph out from under all other live headers.
- Paint requires a valid payload: msg 8 dereferences *p2 (subflags) and p2[7..10] (rect floats); a truncated/garbage payload reads OOB and draws with junk coordinates.
- Hit-test writes through p2[4]: msg 0x17 stores the region code at *(uint*)p2[4]; a null out-pointer crashes.
- Statelessness contract: because ~80 windows install this exact proc, it MUST stay re-entrant — all per-window state is read from the frame's style word (p1[4]) and children, never from a per-instance heap block. Do not assume a TCtlInstance object exists here (that belongs to the sibling CGroupHeaderFrame FUN_0087ddc0).
- Tabbed loop bounds: msg 9 with style&0x200 iterates ids 10000..0x2718 (10000..10008); FUN_008766e0 must be paired on destroy (msg 0xb) or tab children leak.
- Stack cookie: FUN_00876880 uses DAT_00bee340 canary over a large (~0x120 byte) frame; corrupting local_88[32]/rect buffers trips __security_check_cookie.
Note: The WASM twin (ram:8144892b) is a slimmer build of this same control (only the bg-image + title-text paint and a flat 20.0 size default); the EXE FUN_00876880 is the full-featured version (minimize/tabs/drag-resize/hit-test). Same control family, confirmed by the exact paint signature.


### UiCtlBtnGlass (IUi::CGlassBtn styled-button decorator)  (EXE 0x00877e60, confidence: high)

- **WASM:** ram:80e0b31d (CGlassBtn::FrameProc); thin wrapper UiCtlBtnGlassProc at ram:80e0b7ed
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlBtn.cpp (glass decorator lives here; base allocs in P:\Code\Engine\Controls\CtlBtn.cpp)
- **Struct layout:**

Glass is a DECORATOR: FUN_00877e60 allocates NO per-instance struct of its own (no case 9). Its drawing state lives entirely in the CtlBtn base instance, which the base FUN_0060f4f0 (installed via case 4) allocates on its own case 9 through FUN_006102b0 = FUN_0047f340("P:\\Code\\Engine\\Controls\\CtlBtn.cpp", 0x1da) => 474-byte CtlBtn instance:
  +0x04 dword  text/render sub-object ptr (points to a 0x2c-byte block freed in base case 0xb)
  +0x08 dword  0
  +0x0c dword  text length / count (0)
  +0x10 dword  0x80 default flags/capacity; low style bits (bit0 styleB, bits1/2 color-style) read by glass paint/size/case0x38
  +0x14 dword  0xFFFFFFFF (selected/hotkey index)
  +0x18 dword  cached image/texture handle (freed via FUN_0046f850 in base case 0xb)
  +0x24 dword  color A (default _DAT_00937edc)
  +0x28 dword  color B (default _DAT_00937edc)
Class-shared (not per-instance): DAT_010819cc = shared icon art model (created case 5, destroyed case 6). Constant tables: DAT_00bf44ec (art-model defaults, case 0x60), DAT_00bf4518/0x4528/0x4538/0x4548 (size-query rects), PTR_DAT_00bf456x..458x (state textures), PTR_DAT_00bf455c/0x4558 (overlay/model textures).

- **Message protocol:**

FUN_00877e60 is the EXE glass/styled-button FrameProc (a decorator over CtlBtn). switch(msgframe[1]=msg):
- case 1 PAINT (sub-pass = *payload): sub-pass 0 draws the beveled/glass background quad. It picks 1 of ~9 state textures via PTR_DAT_00bf456x/0x457x/0x458x, selecting by: FUN_0062fe20(frame,0x40000) style-enable gate; style bit0 of instance+0x10 (styleB=(*(byte*)(this+0x10))&1); enabled=FUN_0062e2a0(frame); pushed=bit0 via msg 0x58 helper FUN_0060f4b0; checked=bit2 via msg 0x59 helper FUN_0060f4d0; focus/highlight=FUN_0062e320. Emits FUN_0062b8e0(bg image)+, and if FUN_0062e320 (focused) an extra 32x32 (0x20) overlay via FUN_0062b3e0(PTR_DAT_00bf455c). sub-pass 1 draws the shared icon/art model DAT_010819cc via FUN_0062b290 with an index 0..5 chosen from enabled/checked/pushed. Other sub-passes -> base.
- case 4 INSTALL BASE: *(code**)payload[3] = FUN_0060f4f0 (the CtlBtn base proc; the actual instance-owning proc).
- case 5 CLASS-INIT (one-shot): builds shared art model DAT_010819cc = FUN_0062d790(0x11,7,0x12,size15x15,size0x80x0x20,PTR_DAT_00bf4558,6); asserts (FUN_00487a80(0x45)) if already set.
- case 6 CLASS-SHUTDOWN: FUN_0046f9b0(DAT_010819cc); DAT_010819cc=0.
- case 0x15 SIZE-QUERY: writes preferred rect payload[0..3] from DAT_00bf4518 (10.0,11.0,10.0,9.0) or DAT_00bf4528 when styleB set; if checked/pushed adds inset via FUN_00876690(&DAT_00bf4538/0x4548). (Matches WASM CGlassBtn size base 10.0f.)
- case 0x38: calls base first, then applies a color transform (_DAT_009411d0 or _DAT_0094519c) selected by instance style bits 1/2 of +0x10.
- case 0x5f DRAW-TEXT: FUN_0062bb30(...) with color 0xffa0a0a0 when disabled/masked else 0xffffffff; layer 6.
- case 0x60 GET-ART-MODEL: copies 9 dwords from DAT_00bf44ec (content 18.0x18.0, margin 4.0) into payload[0..8]. This 9-dword copy is the exact CGlassBtn signature (WASM case 0x60 copies the same 9 dwords).
- default: thunk_FUN_00647170 -> FrameMsgCallBase (delegates to CtlBtn base FUN_0060f4f0).
State query helpers used: 0x58=pushed(bit0), 0x59=checked(bit2), FUN_0062e2a0=enabled, FUN_0062e320=focus/highlight.

- **Create recipe:**

1. Class registration (once at UI init): the framework sends msg 5 to build shared art model DAT_010819cc before any glass button paints; msg 6 tears it down. Do not skip - paint sub-pass 1 dereferences DAT_010819cc.
2. Create the frame with the glass proc as its FrameProc: FUN_0062bfc0(parent, styleFlags, childId, FUN_00877e60, userdata, 0). On creation the engine auto-drives msg 4 (glass installs base FUN_0060f4f0) then base msg 9 (FUN_006102b0 allocs the 474-byte CtlBtn instance, sets +0x10=0x80, +0x14=-1, colors +0x24/+0x28). Typical style flags observed at real call sites: 0x40000 (plain), 0x4300 (list-cell variant), 0x90000; button gating requires style 0x40000 for the glass background to draw (paint checks FUN_0062fe20(frame,0x40000)).
3. Set label after create exactly like the IME paging buttons do: on the child's own msg 9 call CtlBtn base text setter FUN_0060fe60(*frame,&textLiteral) (WASM CtlBtnSetTextLiteral). Push-offset visual (rect +2/-2 when pushed) is applied by the owner proc's msg 0x15 override, not by glass itself.
4. Sizing: either let layout call msg 0x15 (returns 10/11/10/9 preferred insets) or override msg 0x15 in a subclass. For a toggle/checked look, set style bit0 of instance+0x10 so case 0x15 uses DAT_00bf4528 and paint uses the checked textures.
Reference wiring: PTR_FUN_00a50874 template + FUN_0062ef40(frame,0x57,0,tmpl) then FUN_0062bfc0 (see UiCtlImeCand FUN_0061d870 case 10) - though the IME paging buttons FUN_0061d7b0/0061d7e0 inherit the plain CtlBtn base FUN_0060f4f0 directly in this 06-14 build, not the glass skin.

- **Crash gotchas:**

- Do NOT call glass proc msg 5 twice: it asserts via FUN_00487a80(0x45) if DAT_010819cc already set. Painting a glass button before msg 5 ran leaves DAT_010819cc=0 and paint sub-pass 1 (FUN_0062b290) will use a null shared art model.
- Glass owns no instance; it REQUIRES its base FUN_0060f4f0 (CtlBtn) to be installed (case 4) and to have run case 9. If you install FUN_00877e60 without letting the base chain build, every non-glass message falls through thunk_FUN_00647170 to an uninitialized base and the CtlBtn instance (+0x04 text ptr, +0x18 image handle) is null -> crashes on text/paint.
- case 0x60 and case 0x15 blindly write 9 and 4 dwords into the caller payload; the caller must provide a big-enough out buffer (>=9 dwords for 0x60) or it corrupts stack.
- Base free (FUN_0060f4f0 case 0xb) releases +0x18 (FUN_0046f850) and the 0x2c sub-object; double-driving destroy or freeing while a paint is queued double-frees the texture handle.
- Style gate: if style flag 0x40000 is absent the glass background silently does not draw (button appears invisible) - this is why the IME paging buttons look plain when created without it.


### UiCtlTitleFrame  (EXE 0x00878950, confidence: high)

- **WASM:** ram:80f52106
- **Assertion file:** None of its own. FUN_00878950 is a SUBCLASS proc with no instance allocation (no FUN_0047f340("<Ctl>.cpp",size) call, no case 4/case 9), so it carries no assertion cpp string. It is installed over a CtlTextMl base (FUN_00610c40). Its only asserts are FUN_00487a80(0x35) if the shared image-list resource (DAT_010819d0) is double-created on msg 5. The bridging texture that resolved it is L"TxtPvmRestrict" @ 0x00941c98 (used by creator FUN_004b08b0); the generic proc lives in the UI-controls TU at 0x0087xxxx.
- **Struct layout:**

Frame: standard 0x1C8 CFrame (frameId at [0]). This subclass allocates NO heap instance struct.
Subclass state:
- p1[2] -> frame userdata dword: top byte (bits24-31) = enable/has-icon flag read as local_8 in msg 8; also reinterpreted as a float set/read by msg 0x7fffffff (SetValue).
- (byte)(p1+0x10) & 1 = frame chrome/resizable flag gating corner image + hit-test.
Paint payload p2 (CContent draw struct, float* pfVar8):
- +0x00 pfVar8[0]: content flags bit0=fill bg, bit1=border, bit2=corner handle.
- +0x1C..+0x28 pfVar8[7..10]: title-bar rect (x0,y0,x1,y1).
- +0x2C pfVar8[0xb], +0x30 pfVar8[0xc]: corner selectors (compared to float-bits 0x00000002).
Size-query out p3: 4 dwords = {7.0f, 9.0f, 7.0f, 9.0f/_DAT_00945988}.
Global resources: DAT_010819d0 = refcounted shared corner image-list; PTR_DAT_00bf4590/_458c = border textures; PTR_DAT_00bf4594 = corner atlas; _DAT_00944e00=7.0f, _DAT_00944e04=9.0f, _DAT_00945988 = alt size const.

- **Message protocol:**

FrameProc(FrameMsgHdr* p1, void* payload p2, void* out p3); msg = p1[1]; frameId = *p1; instance/userdata dword = *(p1[2]). Default for every unhandled msg = tail-call thunk_FUN_00647170 (FrameMsgCallBase -> CtlTextMl base FUN_00610c40).
- 5 (RESOURCE CREATE): lazily builds shared corner/handle image-list DAT_010819d0 = FUN_0062d790(0,7,0x12,&{0x10,0x10,0x10},&{0x80},PTR_DAT_00bf4594,3); asserts FUN_00487a80(0x35) if already set; then chains to base.
- 6 (RESOURCE DESTROY): FUN_0046f9b0(DAT_010819d0); DAT_010819d0=0; chains to base.
- 8 (PAINT / composite title bar), gated on paint-payload flags pfVar8[0]:
    * (flags&1 && (instance>>24 != 0)): builds a fill texture (FUN_0065efa0 op 0x20003e0) and blits title background over rect via FUN_0062b2d0 (rect = pfVar8[7..10] +/- margins _DAT_009413c8).
    * (flags&2): draws frame/border image via FUN_0062b8e0(frame, pfVar8+7, PTR_DAT_00bf4590 or _458c, {0x20,0x20}, 7,0,1,0).
    * (flags&4 && frameFlags&1): draws corner/resize handle via FUN_0062b290(frame, rect, DAT_010819d0, cornerSel, 2, 0), then chains to base.
- 0x15 (SIZE QUERY): writes out[0]=_DAT_00944e00(7.0f), out[1]=_DAT_00944e04(9.0f), out[2]=7.0f, out[3]=9.0f (or _DAT_00945988 when frameFlags&1) = min/pref Coord2f pair. (WASM analog returned 12.0/8.0 — same shape, build-specific values.) No null-check on out.
- 0x17 (HIT-TEST): if frameFlags&1, tests point (p2[0],p2[1]) against title rect (p2[2],p2[3] minus chrome margins _DAT_00937ed0/_DAT_009413d8); on hit stores *(p2[4]) = 2 (title-bar hit code).
- 0x2b (INVALIDATE-ON-STATE): if payload[1]&4, FUN_0062bd80(frame,4) (per-frame content invalidate), then chains.
- 0x7fffffff (custom SET-VALUE): if *(float*)p1[2] != *p2, store float and FUN_0062bd40(frame) invalidate, then chain.
- all others: FrameMsgCallBase to CtlTextMl base.

- **Create recipe:**

see message_protocol

- **Crash gotchas:**

1. NOT self-contained: no case 4 (base install) and no case 9 (instance alloc). It is a FrameNewSubclass overlay on a CtlTextMl base (FUN_00610c40). Creating it alone via CreateUIComponent/bare-proc registration -> default branch calls thunk_FUN_00647170 (FrameMsgCallBase) with no base -> null deref (same failure class as the Slider/Button cold-creation reports).
2. Shared image-list DAT_010819d0 is refcounted via msg 5/6; sending msg 5 while already set asserts FUN_00487a80(0x35). Lifecycle messages must arrive in order and exactly once per create/destroy.
3. msg 0x15 (size query) writes 4 dwords to out with NO null check — caller must pass a valid out buffer.
4. msg 8 paint dereferences the CContent payload floats pfVar8[7..10] (title rect) and instance dword *(p1[2]); painting before the base populates content/rect reads garbage floats -> bad geometry / potential fault.
5. Corner handle + hit-test are gated on frameFlags&1 ((byte)(p1+0x10)&1); if the create flags (0x24000) are not applied the title chrome silently fails to draw and 0x17 hit-test never reports code 2.


### UiCtlTip  (EXE 0x00878950, confidence: high)

- **WASM:** ram:80e09f09
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlTip.cpp (EXE string @ 0x00b95c58; assert line 0x35 via FUN_00487a80(0x35) in the CREATE case, matching the WASM ErrorAssertion(...,0x35))
- **Struct layout:**

This proc keeps almost no per-instance state; tooltip state lives in the frame-content system plus one global. 
FrameMsgHdr (stack, uint* param_1): +0x00 frame handle; +0x04 msg; +0x08 controlData* (points to Color4b/float, dereffed in PAINT and SET-SCALAR); +0x0c extra; +0x10 style/flags dword (byte@+0x10 bit0 = interactive/close-button enabled); +0x14 param5 (child index, used by base dispatcher). 
controlData blob (*(hdr+8)): +0x00 Color4b bgColor (alpha byte gates bg fill; same 4 bytes read as float in SET-SCALAR). 
Globals: DAT_010819d0 = shared HFrameImageList (close/scroll glyphs), lazily created on msg5 / freed on msg6, process-wide. Layout/margin consts: _DAT_009413c8 (content margin), _DAT_00937ed0 & _DAT_009413d8 (close-button insets), _DAT_00944e00/04, _DAT_00945988 (cached measure dims). 
Sibling: the actual control-template proc FUN_0087a4b0 owns the standard lifecycle (case4 installs THIS proc as base into *(payload[3]); case9 creates child primitive via FUN_0062bfc0(parent,(style&0xfffff000)|0x280,0,FUN_00877e60,*payload,0) + warmup FUN_0062fa20; case0x15 subtracts margin; cases 0xc/0x31/0x38). FUN_00877e60 is the tip's scroll/close-button content proc with its own image list DAT_010819cc.

- **Message protocol:**

FrameProc sig: void UiCtlTipProc(FrameMsgHdr* hdr /*param_1*/, const void* payload /*param_2*/, void* out /*param_3*/). Switches on hdr[1]=msg (uVar3). Header dwords used: hdr[0]=frame handle, hdr[1]=msg, hdr[2]=ptr to control data blob (first dword = Color4b bg / float value), hdr[4]=style/flags dword (bit0 = interactive/has close-button). Payload for paint/hittest is a FrameContent layout (float* pfVar8): pfVar8[0]=content flags (bit0 bg, bit1 border template, bit2 close-button), pfVar8[7..10]=rect L/T/R/B, pfVar8[0xb]/[0xc]=corner-anchor flags (==1 sentinel picks glyph index).
Cases:
- 5 CREATE: lazily builds process-global HFrameImageList DAT_010819d0 = FrameImageListCreate(FUN_0062d790)(fmt=0,texop=7,flags=0x12, minSize {0x10,0x10}, maxSize {0x80,0x10}, PTR_DAT_00bf4594, mips=3). Asserts FUN_00487a80(0x35) if DAT_010819d0 already non-zero, then forwards to base. 
- 6 DESTROY: HandleCloseSafe(FUN_0046f9b0)(DAT_010819d0); DAT_010819d0=0; forward base.
- 8 PAINT: if payload bit0 && bg color alpha(byte>>24)!=0 -> GrBuildSolidTexture(FUN_00679b10)(color) -> GrMaterialCreate(FUN_0065efa0)(1,tex,texop=7,flags=0x12,...,0x20003e0) -> FrameContentAddImage(FUN_0062b2d0) over rect inset by margin _DAT_009413c8; HandleClose both tex+material. If payload bit1 -> FrameContentAddImageTemplate(FUN_0062b8e0) border, glyph PTR_DAT_00bf4590 (alpha!=0) or PTR_DAT_00bf458c (alpha==0), size {0x20,0x20}. If payload bit2 && style bit0 -> pick glyph index cVar9 from corner flags (pfVar8[0xb],[0xc]==2.8026e-45 sentinel) and FrameContentAddImage(FUN_0062b290)(frame, rect(top-right, inset _DAT_00937ed0 and _DAT_009413d8), DAT_010819d0, idx, layer=2); then forward base.
- 0x15 MEASURE/SIZE-QUERY: writes cached dims out[0..3] = _DAT_00944e00,_DAT_00944e04,_DAT_00944e04, and out[3]= (style bit0 ? _DAT_00945988 : _DAT_00944e04). Returns without base.
- 0x17 HITTEST: only if style bit0. Tests point (payload[0],payload[1]) against the close-button rect (right/top region inset by _DAT_00937ed0 - _DAT_009413d8). If inside, writes 2 into *(int*)payload[4] (hit-code = close button). Returns.
- 0x2b INVALIDATE-REQ: if payload[1] bit2 -> FrameContentInvalidate(FUN_0062bd80)(frame, mask=4).
- 0x7fffffff SET-SCALAR (custom): if *(float*)hdr[2] != *(float*)payload -> store new value, FrameContentInvalidate(FUN_0062bd40)(frame), forward base.
- all others / fallthrough: thunk_FUN_00647170 (FrameMsgCallBase) forwards to the base/parent proc.

- **Create recipe:**

Do NOT hand-instantiate this proc as a standalone frame; it is the BASE PAINT proc of the UiCtlTip control template and expects a fully wired FrameContent host. Two verified install paths:
1) Standard control (preferred): drive template proc FUN_0087a4b0. On msg 4 it installs this proc: *(code**)payload[3] = FUN_00878950 (base of the proc chain). On msg 9 it creates the child frame: h = FUN_0062bfc0(parent, (style & 0xfffff000)|0x280, 0, FUN_00877e60, userdata, 0); FUN_0062fa20(h, FUN_00877e60, 1, 0) (warm-up / register content procs). This yields a tip whose paint is served by FUN_00878950.
2) Direct embed (as at 0x0087f9fb / 0x00889e36): create a primitive frame FUN_0062bfc0(parent, 0x4028, child, ...) then install this proc via FUN_0062f150(frame, 0x878950) (or MOV [frame_proc_slot],0x878950 then FUN_0062ee70).
Warm-up ordering that must occur before first paint: send msg 5 (CREATE) exactly once so DAT_010819d0 image list exists; ensure hdr[2] (controlData) points to a valid Color4b/float; set style bit0 if you want the close-button + hittest branch. Sizing comes from msg 0x15 (measure) which returns fixed cached dims minus margin _DAT_009413c8 (the template FUN_0087a4b0 also subtracts _DAT_009413c8 on all four edges). Teardown: send msg 6 (DESTROY) to free the image list.

- **Crash gotchas:**

- Double CREATE: msg 5 asserts FUN_00487a80(0x35) (no-return abort) if DAT_010819d0 is already non-zero. Never send CREATE twice without an intervening DESTROY (msg 6). 
- Global image list is process-shared and NOT ref-counted here: sending DESTROY (msg 6) frees DAT_010819d0 for ALL tooltips; freeing while another tip paints -> use-after-free of the HFrameImageList. Manage lifetime through the owning template, not per-instance. 
- Null/garbage hdr[2]: PAINT does *(Color4b*)hdr[2] and SET-SCALAR does *(float*)hdr[2] read+write; a null/invalid controlData pointer crashes. 
- PAINT/HITTEST assume a valid FrameContent payload: it derefs pfVar8[7..10] (rect) and pfVar8[4] (hit-result out ptr). Invoking paint/hittest with a bogus or too-short payload derefs wild pointers. 
- Texture/material leak: PAINT builds a solid texture + material each paint and HandleClose()es both; if you replicate the draw path without the paired HandleClose (FUN_0046f850) you leak GPU handles. 
- Style bit0 gating: without hdr[4]&1, HITTEST (0x17) returns without writing *(payload[4]) (caller sees stale hit-code) and MEASURE returns the alternate width (_DAT_00944e04 vs _DAT_00945988) — mismatched style bit vs. expected layout yields wrong sizing/no close-button hits.


### UiCtlAnimSelection  (EXE 0x00879d50, confidence: high)

- **WASM:** not-present (no AnimSelection symbol in /Gw.wasm; EXE address was already given/confirmed via inline assertion string)
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlAnimSelection.cpp (embedded inline as the alloc tag at 0x00879d9c, size 0xf6)
- **Struct layout:**

Instance = 0xf6 (246) bytes, allocated by FUN_0047f340(tag,0xf6) with heap/pool id 0x10 in ECX (LEA ECX,[EDX+0x10]). Accessed as dword[] via puVar4:
+0x00 (ptr)   ownerFrame  -- parent UIFrame; set from msgframe[0] (*puVar3) at create. Deref'd by paint/tick to re-dispatch/register.
+0x04 (float) animPhase   -- current scroll/pulse phase; seeded to current time by FUN_005b53b0 at create, and each 0x3b tick recomputed = fmod(speed*elapsed + phase, 1.0). (puVar4[1])
+0x08 (float) animSpeed   -- speed/scale constant chosen by style bit 0x1000: _DAT_00940ea8 (bit set) else _DAT_0094052c. (puVar4[2])
+0x0c (ptr)   geomHandle  -- render/mesh handle built by FUN_00879740 -> FUN_008798e0 (10-vert, fmt 0x101, stride 0x18 inset-border quad) -> FUN_00663cc0. Drawn via FUN_00664d40 / FUN_00665000; released via FUN_0046f850 on destroy. (puVar4[3])
+0x10..0xf5   reserved/embedded transform+vertex scratch (rest of the 246-byte block; sub-object initialized starting at instance+4 by FUN_00879740 called thiscall with ECX=instance+4).
Instance slot pointer = msgframe[2] (piVar1); *piVar1 holds the instance (0 before create, =instance after).

- **Message protocol:**

Dispatch: msg = msgframe[1]; jump table at 0x879eec (byte-index map at 0x879f00) indexed by (msg-8), valid range 8..0x3b (CMP EAX,0x33 JA default). msgframe: [0]=ownerFrame, [1]=msg, [2]=instance-slot-ptr. Handler is void FUN_00879d50(frame, wparam(param_2), lparam(param_3)). Every path (including default) tail-chains to base frame proc FUN_0062ee70(frame,wparam,lparam) via thunk_FUN_00647170.
- case 9 CREATE/instantiate: assert *slot==0 else FUN_00487a80(0xf5) (no-return); alloc 0xf6 bytes pool 0x10; inst[0]=ownerFrame; style=FUN_0062fe20(ownerFrame,0x1000); init anim sub-object at inst+4 over unit rect {0,0,1,1} via FUN_00879740(this=inst+4,&rect,style); *slot=inst; register color/alpha global _DAT_00946544 via FUN_00630080(ownerFrame,0,val).
- case 8 PAINT/submit: push matrix FUN_0066da30(2); set transform from wparam(+4)=x,(+8)=y with scale 1.0 via FUN_0066fb20(2,&vec); submit geometry FUN_00665000(geomHandle,0); then re-dispatch msg 9 to owner via FUN_0062ba80(ownerFrame,1,&args,9).
- case 0xb DESTROY: if instance: free geomHandle (FUN_0046f850(inst[0xc])) then free instance FUN_005acaeb(inst,0x10) (pool 0x10 must match alloc).
- case 0x3b TICK+ANIMATE: re-register color (FUN_00630080(ownerFrame,0,_DAT_00946544)); phase = fmod(animSpeed*wparam(+4=elapsed) + animPhase, 1.0) via FUN_005b53b0(x,1.0), store back to inst+4; push matrix FUN_0066da30(3); translate by -phase (FUN_00670340(3,&vec)); draw geomHandle FUN_00664d40; request continued redraw FUN_0062bd40(ownerFrame).
- default: pass-through to base proc only.
Note: NO case 4 (base install), NO case 1, NO case 0x15 size-query, NO 0x56+ get/set -- this control diverges from the standard template; it self-allocates on msg 9 and derives size from the unit rect scaled by the parent transform each paint.

- **Create recipe:**

1) Create a child primitive frame under the selectable parent: FUN_0062bfc0(parent, flags, child, proc=0x00879d50, userdata, 0). The framework then issues msg 9 to FUN_00879d50 through the normal create path; the control allocates its own 0xf6-byte instance and stores it at msgframe[2].
2) Warm-ups: none required beyond the parent frame existing. Parent must supply a valid style word -- style bit 0x1000 selects the animation-speed constant (set => _DAT_00940ea8 fast, clear => _DAT_0094052c slow). No explicit init sizing needed; geometry is the {0,0,1,1} unit inset-border quad scaled by the parent transform.
3) Sizing/placement: there is no 0x15 size-query. Position and scale arrive per-paint in the message payload (wparam+4 = x/pos, wparam+8 = y). Elapsed time for the animation arrives in wparam+4 on the 0x3b tick.
4) Drive it: send msg 8 to paint (submits the border geometry at the given transform) and msg 0x3b each frame to advance/scroll the highlight; send msg 0xb to tear down.

- **Crash gotchas:**

- Double-create assert: msg 9 while *msgframe[2] (instance slot) is already non-zero calls FUN_00487a80(0xf5), which does NOT return. Send create exactly once; ensure the slot is zero-initialized before first msg 9.
- Pool mismatch: alloc uses pool id 0x10 (ECX at 0x879da1) and free FUN_005acaeb(inst,0x10) must use the same id -- calling the wrong deallocator/pool corrupts the heap.
- Ordering: ownerFrame (msgframe[0]) must be valid at create; paint(8) and tick(0x3b) both deref inst[0] and dispatch back to the owner -- destroying the parent before the control leaves a dangling owner pointer.
- Uninitialized slot: msgframe[2] must point at real storage; the handler writes the instance there and reads it on every subsequent message.
- NaN animation: the 0x3b tick multiplies animSpeed by wparam+4 (elapsed). Passing garbage/uninitialized elapsed yields a NaN phase that propagates into the transform and can blank or mis-scroll the highlight.
- geomHandle lifetime: inst+0xc is freed on 0xb; issuing paint(8)/tick(0x3b) after destroy dereferences a freed render handle (use-after-free).


### UiCtlAnimSelection (IUi::UiCtlAnimatedSelectionProc)  (EXE 0x00879d50, confidence: high)

- **WASM:** ram:810aba46
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlAnimSelection.cpp (EXE string @0x00b95d08; WASM @ram:0010ae85 "../../../../Gw/Ui/Controls/UiCtlAnimSelection.cpp")
- **Struct layout:**

Instance = 0xf6 (246) bytes, allocated by FUN_0047f340 on msg 9. Verified fields (from FrameProc case accesses; remaining bytes are the inherited CSelection/CFrame sub-fields + the vertex/material scratch reserved by builder FUN_00879740):
  +0x00  uint   frameHandle        (owning frame; set *instance = *msgframe at create; used by FUN_00630080/FUN_0062ba80/FUN_0062bd40)
  +0x04  float  angle              (current rotation phase; wrapped each tick via FUN_005b53b0; negated for the rotation matrix)
  +0x08  float  angularVelocity    (angle advance per tick; angle += vel * dt)
  +0x0c  handle renderMesh/material(built by FUN_00879740 -> FUN_00663cc0; bound for draw in case 8, poked in case 0x3b via FUN_00664d40, freed in case 0xb via FUN_0046f850)
  +0x10..0xf5  inherited CSelection/CFrame state + builder scratch (not individually dereferenced by this override).
NOTE: builder FUN_00879740 writes its output triple (angle@0, color@4, material@8) into a 16-byte anim sub-struct; decompiler shows it via a stack alias (&local_14) at create time; the persisted copy lives in the instance and is what case 8/0x3b read back.

- **Message protocol:**

EXE FrameProc FUN_00879d50(msgframe *frame, void *payload/param_2, void *out/param_3). frame[1]=msg, frame[2]=piVar1 (payload ptr whose *piVar1 = instance slot). Switch handles ONLY 4 control-specific messages; everything else falls through to the parent proc-chain walker thunk_FUN_00647170 -> FUN_00647170 (which itself dispatches the CSelection base + generic CFrame messages: create-parent 4, paint 1, size-query 0x15, etc.). WASM confirms inheritance: IUi::UiCtlAnimatedSelectionProc simply forwards to IUi::CSelection::CSelectionProc.

CASES OVERRIDDEN:
- case 9 (CREATE/alloc): if *piVar1 != 0 -> assert FUN_00487a80(0xf5) (already-created guard). Allocates instance via FUN_0047f340("...UiCtlAnimSelection.cpp", 0xf6=246 bytes). instance[0]=frame handle (*puVar3). Reads style via FUN_0062fe20(frame,0x1000). Calls builder FUN_00879740(&anim, style) which constructs the highlight geometry: two vertex streams FUN_0065efa0(...,fmt 0x31a / 0x31a|0x800) + FUN_008798e0 color verts, combined into a render material via FUN_00663cc0 -> stored render handle; sets initial angle = FUN_005b53b0() (time-based wrap, __cintrindisp2). Stores *piVar1 = instance. Registers the repeating animation timer on the frame: FUN_00630080(instance[0]/frame, 0, _DAT_00946544 = tick interval) -> this is what drives the periodic case 0x3b.
- case 8 (RENDER/draw pass): puVar4=instance. Pushes matrix stack FUN_0066da30(2); loads translate = {payload+4 (x float), payload+8, 1.0} via FUN_0066fb20(2,&vec); binds render handle instance[+0xc] via FUN_00665000; draws through FUN_0062ba80(frame, 1, &handle, 9). Then falls through to base.
- case 0xb (DESTROY/free): iVar2=*piVar1; if nonzero: free sub-resource FUN_0046f850(*(instance+0xc)) then free instance FUN_005acaeb(instance, 0x10). Base still runs.
- case 0x3b=59 (ANIMATION TICK, fired by the FUN_00630080 timer): re-arms timer FUN_00630080(frame,0,_DAT_00946544); advance angle: tmp = instance[+8]*(*(float*)(payload+4)/dt) + instance[+4]; instance[+4] = FUN_005b53b0(tmp) (wrap/fmod); push rotation matrix FUN_0066da30(3); set rot = {-instance[+4],0,0} via FUN_00670340(3,&vec); touch mesh FUN_00664d40(instance[+0xc],0); invalidate/redraw frame FUN_0062bd40(frame). Returns after base delegation.

All other messages (1 paint, 4 base-proc install, 0x15 size, 0x56+ get/set) are handled by the inherited CSelection/base chain via FUN_00647170.

- **Create recipe:**

This IS a paintable control frame proc, but it is an ANIMATION OVERLAY child of a CSelection frame (a spinning/rotating selection-highlight ring), not a standalone widget. Create like any native frame:
1. Create the frame primitive: FUN_0062bfc0(parentFrame, flags, childId, proc=0x00879d50, userdata, 0). Set style so the proc's read FUN_0062fe20(frame,0x1000) returns the desired variant (bit 0x1000 toggles the two color/geometry presets inside FUN_00879740: DAT_0094052c/_DAT_00b95d3c vs _DAT_00940ea8/_DAT_00b95d38).
2. Send msg 9 (CREATE) exactly once as the warm-up: it allocates the 246-byte instance, builds the highlight mesh/material, seeds angle from the frame timer, and — critically — calls FUN_00630080(frame,0,_DAT_00946544) to REGISTER the repeating animation timer. Without msg 9 there is no instance (case 8/0x3b would deref *piVar1==0).
3. The engine's timer then auto-drives msg 0x3b every _DAT_00946544 interval, rotating the ring; msg 8 renders it at the payload-supplied {x,y} translation with alpha=1.0. You do not hand-drive these.
4. Teardown: msg 0xb frees the mesh handle (+0xc) then the instance. Do not free the parent's frame handle here.
Ordering/warm-ups: parent CSelection frame must exist first (this rides its proc chain); create (9) before any 8/0x3b; the create-guard asserts (0xf5) if 9 is sent twice without an intervening 0xb.

- **Crash gotchas:**

- Double-create: sending msg 9 while *piVar1 != 0 hits assert FUN_00487a80(0xf5). Always destroy (0xb) before re-creating.
- No-instance deref: case 8 and case 0x3b dereference *piVar1 (instance) and instance[+0xc] with no null check — firing render/tick before the create warm-up (msg 9) crashes. The animation timer FUN_00630080 is only armed inside case 9, so a manually-injected 0x3b before create is fatal.
- FUN_00630080 asserts on frame==0 (0xf6b), on interval<0 (0xf6c), and on interval>=_DAT_009432c4 (0xf6d) — pass the engine's own _DAT_00946544, do not fabricate.
- Destroy frees instance+0xc via FUN_0046f850 then the block; if the builder (FUN_00879740) partially failed the handle may be stale — but normal path is safe. Freeing the instance uses FUN_005acaeb(instance,0x10) (0x10 = allocator alignment/pool tag, NOT the size).
- This proc only overrides 4 messages; it MUST be installed on a frame whose parent proc chain is the CSelection base (WASM: forwards to CSelection::CSelectionProc). Installed standalone (no base in the chain walked by FUN_00647170), messages 1/4/0x15 are dropped and the highlight never paints/sizes.
- angle math reads instance[+4]/[+8] before they are set by the builder; if create skipped the builder, angle is uninitialized garbage -> ring spins wildly / NaN transform.


### UiCtlModeIcon  (EXE 0x00879f50, confidence: high)

- **WASM:** 0x80efdc08
- **Assertion file:** ../../../../Gw/Ui/Controls/UiCtlModeIcon.cpp (WASM); EXE instance alloc tags "P:\Code\Engine\Controls\CtlInstance.h". WASM confirms symbols IUi::CModeIcon / TCtlInstance<IUi::CModeIcon>::MsgProc and assert "modeIcon <= UI_MODE_ICONS".
- **Struct layout:**

TCtlInstance<IUi::CModeIcon>, total size 0x24 (36 bytes; freed as FUN_005acaeb(inst,0x24) in case 0xb).
+0x00  void** vtable            = &PTR_FUN_009404a4 (shared CtlInstance vtable; NOT control-specific, so vtable is NOT an identity marker)
+0x04  CFrame* frame            = *param_1 (owning frame handle; passed to all draw/tooltip calls as *(inst+4))
+0x08 .. +0x1F  base CtlInstance internals populated by base ctor FUN_006017e0() (do not touch directly)
+0x20  int  modeIcon            = EUiModeIcon, valid range 0..4 (UI_MODE_ICONS=4). Default set to 4 at construct (= hidden; paint requires modeIcon<4). This is the only CModeIcon-specific field.

Instance accessor: FUN_004a0440(frame_msg) returns *(int*)param_1[2] (the instance ptr); param_1[2] is the instance-slot pointer, param_1[1]=msg, param_1[0]=frame.

Global class/state (module-level, shared by all instances):
- DAT_010819d8 : shared icon draw resource (vertex/quad buffer) created in case 5 via FUN_0062d790(0,7,0x1a,&geo,&color,&DAT_00b95d50,4); freed in case 6. Used by paint (case 8).
- DAT_00b95d9c[mode] : int table of icon resource/file IDs indexed by modeIcon. Values seen: [0]=0x137ae, [1]=0x13806, [2]=0x187ca(=NONE sentinel, skipped), [3]=0x137b0, [4]=... ; 0x187ca means "no icon bound".
- DAT_00b95d40[mode] : int per-mode draw parameter (layer/quadrant) used by blit in case 8 (values 2,3,0,1,...).
- DAT_00b95d50 : icon tint color (0x0105ecff ABGR) fed into resource creation.

- **Message protocol:**

Switch on param_1[1]=msg. Unhandled/standard msgs fall to base via thunk_FUN_00647170.

CONSTRUCT/DESTRUCT/CLASS:
- case 4  INSTALL BASE PROC: empty body -> delegates to base template thunk (base installs parent proc into payload slot).
- case 5  CLASS STATIC INIT: builds shared icon resource DAT_010819d8 (FUN_0062d790). Runs once on first registration.
- case 6  CLASS STATIC TEARDOWN: frees DAT_010819d8; asserts FUN_00487a80(99) if already null.
- case 9  CONSTRUCT INSTANCE: asserts 0xae if slot already set (double-construct); allocs 0x24 via base (FUN_0047f340/FUN_006017e0), sets vtable=PTR_FUN_009404a4, frame=*param_1, modeIcon=4, then calls SetModeIcon to init. Asserts 0xb1 if reload mismatch.
- case 0xb DESTRUCT INSTANCE: tears down, frees inst as 0x24, clears slot.

LAYOUT/PAINT:
- case 8  PAINT: only draws if paint-state word *param_2 has bit 0x10 AND modeIcon(+0x20) < 4. Computes a scaled square via constants _DAT_00945140/_DAT_0094d1b0/_DAT_009407b0, then FUN_0062b290(frame, rect, DAT_010819d8, DAT_00b95d40[mode], 4, 0) blits the icon. modeIcon>=4 => nothing painted (hidden).
- case 0x37 SET GEOMETRY/BOUNDS: reads 4 floats param_2[2..5] -> FUN_00602060 (sets control rect).
- case 0x38 MEASURE / SIZE-QUERY: writes default size _DAT_009413fc into *param_2[2] (w,h), clamped down to caller-provided max in param_2[0]/[1] if nonzero.

CONTROL-SPECIFIC GET/SET (0x56+):
- case 0x56 (86) SetModeIcon(mode): FUN_0087a420(inst, mode). Asserts FUN_00487a80(0xaf) ("modeIcon <= UI_MODE_ICONS") if mode>4. If changed: stores +0x20, looks up DAT_00b95d9c[mode]; if != 0x187ca sentinel, loads icon (FUN_007c3bc0/FUN_0046bbb0) and binds via FUN_00630180 onto frame; requests redraw FUN_0062bd40.
- case 0x57 (87) BIND/REFRESH ICON+TOOLTIP: if payload==0 -> clear icon (FUN_00630270) and delegate; else if current mode's table id != 0x187ca, (re)load and bind icon resource via FUN_00630180. This is the tooltip/icon-attach refresh path.

PASS-THROUGH (ensure-instance then delegate to base proc FUN_004a0440 + thunk): msgs 1,3,7,0xa,0xc,0xf,0x13,0x15,0x20,0x24-0x2a,0x2c,0x2e,0x31,0x32,0x34,0x35,0x36,0x3a-0x3f,0x44,0x45,0x46,0x4b,0x4c,0x4e,0x4f,0x52 (standard mouse/keyboard/focus/layout handled by base).
- default (any other msg WITH instance): validates instance non-null & *instance!=0 (asserts 0x149 / 0x2c on null/corrupt), else delegates to base.

- **Create recipe:**

This is a TCtlInstance child control; create it as a framed child then drive it with messages.

1) Create the child frame with this proc:
   FUN_0062bfc0(parent_frame, flags, child_id, proc=0x00879f50, userdata, 0)
   The framework auto-sends case 4 (install base proc) then case 9 (construct instance, modeIcon defaults to 4 = hidden). Class static init (case 5) fires once globally to build DAT_010819d8 before any paint.

2) Give it geometry so it has a rect (msg 0x37) via the dispatcher:
   FUN_0062ef40(frame, 0x37, wparam, payload{floats: pad,pad,x,y,w,h}) -- or let parent layout drive it. Query natural size with msg 0x38.

3) Select which icon to show (this is what makes it visible):
   FUN_0062ef40(frame, 0x56 /*SetModeIcon*/, mode, 0) with mode in 0..3 (4 = hidden). Internally binds DAT_00b95d9c[mode] icon (skips if 0x187ca) and requests redraw.

4) (Optional) refresh/clear the icon+tooltip binding with msg 0x57 (payload 0 = clear).

Paint gate: the icon only renders while the base passes paint-state bit 0x10 in the paint payload AND modeIcon<4, so a freshly constructed control (mode 4) shows nothing until SetModeIcon(0..3).

Warm-ups/order: parent must exist; do NOT construct twice (case 9 asserts 0xae). Ensure class init (case 5) has run — guaranteed by framework on first control of this class. Use the standard dispatcher FUN_0062ef40 for post-create messages; instance accessor is FUN_004a0440.

- **Crash gotchas:**

- SetModeIcon / msg 0x56: mode>4 hits FUN_00487a80(0xaf) ("modeIcon <= UI_MODE_ICONS"). Clamp to 0..4; only 0..3 actually render, 4=hidden.
- Double construct: case 9 asserts FUN_00487a80(0xae) if the instance slot (*param_1[2]) is already non-null. Never send msg 9 to an already-constructed frame.
- Null/corrupt instance: default path asserts 0x149 (instance ptr slot present but *slot==0) or 0x2c; sending control msgs (0x56/0x57/paint) after destruct (case 0xb clears slot) => assert/crash.
- Class resource: case 6 asserts FUN_00487a80(99) if DAT_010819d8 already null (double-free). Paint (case 8) uses DAT_010819d8 without null-check; if class init (case 5) never ran it passes null into the blit -> bad draw. Framework normally guarantees case5-before-case8 ordering; don't manually paint before registration.
- Icon table sentinel: DAT_00b95d9c[mode]==0x187ca means "no icon" and is deliberately skipped (no bind). A mode whose table entry is the sentinel will select-but-show-nothing.
- Instance size is 0x24; if hand-allocating, must be >=0x24 and zeroed, with vtable=PTR_FUN_009404a4 and frame at +0x04, else base ctor/dtor mismatch (case 9 asserts 0xb1 on reload mismatch).
- Reentrancy: __thiscall setter takes this in ECX; the decompiler shows inconsistent arg forms (FUN_0087a420(param_2) vs FUN_0087a420(*param_2)) — real signature is SetModeIcon(this=instance, EUiModeIcon mode).


### UiCtlDistrict  (EXE 0x0087aff0, confidence: high)

- **WASM:** ?
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlDistrict.cpp
- **Struct layout:**

UiCtlDistrict instance = 0x28 bytes (10 dwords), allocated in case 9 via FUN_0047f340("...UiCtlDistrict.cpp",0x5ae), freed in case 0xb via FUN_005acaeb(inst,0x28). Instance ptr stored at *(msgframe[2]); accessor FUN_0087cf80 returns **(msgframe+8) and asserts(0x5c0) if null.

+0x00 dword frame        : owning UIFrame handle = *msgframe[0] (the frame this control drives). Passed to every FUN_0062cfc0/FUN_0062e2a0/FUN_0062ef00/FUN_0062ede0 call.
+0x04 float rect[0] x    : live layout rect, init 0x373 (=883)  -- treated as float in msg 0x56/0x174
+0x08 float rect[1] y    : init 7
+0x0c float rect[2] w    : init 0x12 (=18)
+0x10 float rect[3] h    : init 0xffffffff (-1 = auto)
+0x14 float saved[0]     : construct-time copy of rect[0], init 883
+0x18 float saved[1]     : init 7
+0x1c float saved[2]     : init 18
+0x20 float saved[3]     : init -1
+0x24 uint  state_flags  : init 0; bit0(0x1)=armed/pressed latch (cleared by msg 0x10000174 when rect origin matches), bit1(0x2)=hover/open latch (cleared by 0x10000119/0x10000130/0x10000177). Enabled/interactable recompute is gated on this being 0.

Note: rect[]/saved[] are two 4-float coordinate vectors; the integer inits (883,7,18,-1) are read back as (float)int in the compare paths (Ghidra reinterpret confusion — functionally a default x/y/w/h). The +0x24 flag "toggle detection" idiom ((old!=0)!=(new!=0)) drives whether FUN_0062c9c0(child,0/1) re-enables interactivity.

- **Message protocol:**

Outer FrameProc FUN_0087aff0(msgframe, payload, p3) switches on msgframe[1]=msg. Unhandled -> thunk_FUN_00647170 (base/parent template proc).

case 9  CREATE: assert(*msgframe[2]==0 else 0x5ad); alloc 0x28-instance; inst[0]=*msgframe[0] (frame); seed rect+saved=(883,7,18,-1); flags=0; store inst at *msgframe[2]. FUN_0062ede0(frame,0,-1) init; create child button primitive uVar=FUN_0062bfc0(frame,0x300,0,FUN_00878d90,0,0); FUN_00615410(uVar,_DAT_009416e8) (attach resource/font); acc=FUN_0062cfc0(frame,0); FUN_0062c9c0(acc, interactable?1:0) where interactable = FUN_0062e2a0(frame)!=0 && flags==0. Then SUBSCRIBE to 4 global msgs via FUN_0062ef00(frame, X): 0x10000119, 0x10000130, 0x10000174, 0x10000177.
case 0xb DESTROY: if inst!=0 FUN_005acaeb(inst,0x28); *msgframe[2]=0.
case 0xc (12) ENABLE/REFRESH: acc=FUN_0062cfc0(frame,0); FUN_0062c9c0(acc, (FUN_0062e2a0(frame)!=0 && flags==0)?1:0).
case 0x31 (49) PAINT/POPULATE: ensure instance; FUN_0087bd20(payload) (draw district list contents).
case 0x37 (55) LAYOUT/MEASURE: acc=FUN_0062cfc0(frame,0); build local rect {0,0,*payload,0}; FUN_0062d2a0(&out,acc,&in); if style FUN_0062fe20(frame,0x1000)==0 use computed height else use *payload; FUN_0062f770(acc, in, &out) commit measured size.
case 0x38 (56) MIN-WIDTH QUERY: inst (assert 0x5c0); in={*payload,0}; acc=FUN_0062cfc0(*inst... via *puVar6,0); FUN_0062d2a0(&out,acc,in); if style FUN_0062fe20(frame,0x4000)==0 clamp: result=min(*payload,out.x); write clamped {x,y} to *payload[2].
case 0x56 (86) SET-RECT: inst; if payload[0..3] differ from rect[0..3], store into rect[0..3]; acc=FUN_0062cfc0(frame,0); FUN_0056a450(acc) (invalidate); FUN_0087c420(); if FUN_0062e2a0(frame)!=0 FUN_0087cfb0(&rect) (relayout/refresh).
case 0x10000119 (global): clear flags bit1; if changed re-enable via FUN_0062c9c0; FUN_0087cfb0(&rect).
case 0x10000130 (global): inst (assert); if *payload==0.0 clear flags bit1; if toggled re-enable; FUN_0087cfb0(&rect).
case 0x10000174 (global): inst (assert); if payload[0]==rect[0] && payload[1]==rect[1] && (flags&1): clear bit0; if toggled re-enable; FUN_0087c420(); FUN_006144c0(acc).
case 0x10000177 (global): inst (assert); clear flags bit1; if toggled re-enable; FUN_0087cfb0(&rect).

Child button primitive proc FUN_00878d90 (created in case 9, flags 0x300): case1 paint(sub-pass *payload==0) -> FUN_0062b8e0 draw label text (font PTR_DAT_00bf45c4/c8/cc chosen by FUN_00614480 pressed / FUN_0062e2a0 enabled) + FUN_0062b3e0 draw the 0x20x0x20 dropdown-arrow quad (PTR_DAT_00bf45d0); case4 install base=FUN_006144e0; case 0xc/0x25 FUN_0062bd40 then base; case0x13 pos-map; case0x15 min-size {DAT_00bf45a4..b0}; case0x5b tooltip/ctxdata {PTR_FUN_00b95c94..}; case100 (0x64) hit/tint -> FUN_0062bb30 with color 0xffa0a0a0 (disabled) or 0xffffffff (enabled).

- **Create recipe:**

To instantiate a UiCtlDistrict on a parent UIFrame:
1. Register/host this proc as a control template keyed to FUN_0087aff0; the frame message pump must route control lifecycle msgs to it.
2. Ensure msgframe[2] points to a zeroed instance-ptr slot, then send msg 9 (CREATE). The proc allocates its 0x28 struct, seeds default rect (x=883,y=7,w=18,h=-1 auto), creates the internal button child via FUN_0062bfc0(frame,0x300,0,FUN_00878d90,0,0) and attaches the district-arrow resource FUN_00615410(child,_DAT_009416e8). It self-subscribes to the 4 global UI broadcast msgs (0x10000119/0130/0174/0177) — no manual wiring needed.
3. Warm-ups the host must satisfy before/around CREATE: frame must be a valid FUN_0062bfc0-created UIFrame; FUN_0062e2a0(frame) is consulted for enabled-state and FUN_0062e320 for interactability during child paint; global data _DAT_009416e8, PTR_DAT_00bf45c4/c8/cc/d0, DAT_00bf45a4..c0, PTR_FUN_00b95c94 (fonts/quads/tooltip) must be initialized (they are set up by the UI subsystem boot).
4. Sizing: send msg 0x38 to negotiate min width (respects style bit 0x4000), msg 0x37 to measure/commit layout (respects style bit 0x1000 for fixed height), and msg 0x56 to hard-set the {x,y,w,h} rect. Setting via 0x56 auto-invalidates (FUN_0056a450) and relayouts (FUN_0087cfb0) when the frame is live.
5. Painting: msg 0x31 populates/draws the district selector contents (FUN_0087bd20); the child proc renders the label+dropdown arrow every case-1 paint pass.
6. Teardown: send msg 0xb to free the instance (FUN_005acaeb(inst,0x28)) and null the slot.
Default (unlisted) messages fall through to the base template thunk_FUN_00647170.

- **Crash gotchas:**

- Null-instance asserts: msgs 0x38, 0x10000130, 0x10000174, 0x10000177 dereference *msgframe[2] and call FUN_00487a80(0x5c0) (no-return abort) if the instance is null. Never send these before CREATE (9) or after DESTROY (0xb).
- Double-create abort: sending msg 9 twice without an intervening 0xb hits assert 0x5ad (FUN_00487a80) because *msgframe[2] is already non-null.
- CREATE line/tag 0x5ae, destroy-size 0x28 must match: freeing with any other size corrupts the allocator; instance is exactly 10 dwords.
- The +0x24 flag toggle-detection uses ((old!=0)!=(new!=0)); if you poke state_flags directly you can desync the child's enabled state (FUN_0062c9c0) from the frame — always go through the messages.
- msg 0x56 stores raw payload floats into rect[0..3] but init/compare paths reinterpret the seed ints as (float)int; feeding NaN/garbage floats can make the != comparisons always true, forcing perpetual relayout (FUN_0087cfb0) each frame.
- Global broadcast msgs 0x10000119/0130/0174/0177 arrive asynchronously from the UI hover/selection bus; a control that CREATEs but is destroyed without the frame being torn down can still receive them — the null-check asserts guard this, so ensure the subscription (frame) outlives or is unsubscribed with the instance.
- Child button (FUN_00878d90) depends on globals (fonts PTR_DAT_00bf45c4.., quad PTR_DAT_00bf45d0, geometry DAT_00bf45a4..c0); if the UI resource subsystem isn't booted these are null and case-1 paint dereferences them.


### UiCtlDistrictSelector  (EXE 0x0087aff0, confidence: high)

- **WASM:** ram:8136478d
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlDistrict.cpp (EXE string @0x00b95dac; WASM ../../../../Gw/Ui/Controls/UiCtlDistrict.cpp @ram:00108c3b)
- **Struct layout:**

CDistrictShortcutsFrame instance = 0x28 bytes (10 dwords), allocated in case 9 via FUN_0047f340("...UiCtlDistrict.cpp",0x5ae), pointer stored at *(FrameMsgHdr[2]) i.e. hdr->payloadOut. Freed in case 0xb via FUN_005acaeb(ptr,0x28).

+0x00 uint   frameId        // owning frame handle (*param_1); used for all Frame* dispatch
+0x04 float  posRect[0]     // pos/geom rect x0 (msg 0x56 SetOrigin writes *param_2)   (init 0x373=883)
+0x08 float  posRect[1]     //   y0  (msg 0x56 writes param_2[1]; compared in 0x10000174) (init 7)
+0x0c float  posRect[2]     //   x1  (msg 0x56 writes param_2[2])                        (init 0x12=18)
+0x10 float  posRect[3]     //   y1  (msg 0x56 writes param_2[3])                        (init -1)
+0x14 int    nativeSize[0]  // cached default/native geometry (init 0x373=883)
+0x18 int    nativeSize[1]  // (init 7)
+0x1c int    nativeSize[2]  // (init 0x12=18)
+0x20 int    nativeSize[3]  // (init -1)
+0x24 uint   flags          // bit0(0x1)=origin-locked, bit1(0x2)=redirect/waiting; 0 => child enabled

The pointer FUN_0087cf80(hdr) is the standard 'get-or-assert instance' accessor (returns *(hdr[2]), asserts 0x5c0 if null). FUN_0062cfc0(frameId,childIdx) fetches child frame handles (droplist idx 0). Flags gate child enable via FUN_0062c9c0(child, enabled) where enabled = FrameIsEnabled(frame)!=0 && flags==0.

- **Message protocol:**

FrameProc(FrameMsgHdr* param_1, void* param_2 payload, void* param_3). Switches on param_1[1]=msg:

- 0x09 CREATE/ALLOC: assert *(hdr[2])==0 (else assert 0x5ad); alloc 0x28 (0x5ae); *inst=frameId; init fields as above; FUN_0062ede0(frame,0,-1) install default child-slot; create child droplist FUN_0062bfc0(frame,0x300,0,FUN_00878d90,0,0) then FUN_00615410(child,_DAT_009416e8); set child enable via FUN_0062c9c0; SUBSCRIBE to 4 broadcast/game msgs via FUN_0062ef00(frame, id) for 0x10000119, 0x10000130, 0x10000174, 0x10000177.
- 0x0B DESTROY/FREE: FUN_005acaeb(inst,0x28); *(hdr[2])=0.
- 0x0C ENABLE-REFRESH: recompute child enable from FrameIsEnabled + flags.
- 0x31 (49) NOTIFY/COMMAND: FUN_0087cf80(hdr) then FUN_0087bd20(payload) (droplist selection -> travel/populate path).
- 0x37 (55) SIZE-QUERY (both axes): builds Coord, FUN_0062d2a0 native-size, FUN_0062fe20(frame,0x1000) style test, writes size via FUN_0062f770.
- 0x38 (56) SIZE-QUERY (width/min axis): FUN_0062cfc0 child, FUN_0062d2a0, FUN_0062fe20(frame,0x4000) style test, clamps min width into param_2[2].
- 0x56 (86) SET-ORIGIN/RECT (control-specific set): compares payload float rect to posRect[0..3]; if changed stores them, FUN_0056a450 + FUN_0087c420, and if enabled repaints via FUN_0087cfb0(inst+1).
- 0x10000119 game-msg: clear flags bit1, refresh enable, FUN_0087cfb0.
- 0x10000130 game-msg: if *param_2==0 clear bit1 + refresh + repaint.
- 0x10000174 game-msg (SetOrigin ack): if payload x/y == posRect[0..1] and bit0 set, clear bit0, FUN_0087c420 + FUN_006144c0.
- 0x10000177 game-msg: clear bit1, refresh enable, repaint.
- default / 0x04 paint-template / 0x01 paint / 0x0A etc.: delegate to base template via thunk_FUN_00647170(param_1,param_2,param_3) (paint & create-slot handled by base UiCtl frame template).

Instance accessor asserts 0x5c0 if inst pointer null on any get.

- **Create recipe:**

This is a subclassed frame proc: it does NOT self-handle msg 4 (template install) or msg 1 (paint) — those are forwarded to the base template FUN_00647170. To instantiate the same way the game does:
1. Create the frame with FrameProc = 0x0087aff0 and userdata = 0. The engine sends msg 9 first: proc allocates the 0x28 instance and stashes it at hdr->out (*(hdr[2])). Do NOT pre-populate that slot (msg 9 asserts 0x5ad if non-null).
2. During msg 9 the proc auto-creates its child region-droplist via FUN_0062bfc0(frame,0x300,0,FUN_00878d90,0,0) — no manual child creation needed; child flags 0x300, proc FUN_00878d90 (the inner CDistrictShortcuts region droplist body).
3. Warm-up ordering: msg 9 (alloc+subscribe) must land before any msg 0x56 (SetOrigin) or 0x37/0x38 (size) — otherwise FUN_0087cf80 asserts 0x5c0 (null instance). Subscriptions (0x10000119/130/174/177) are registered inside msg 9, so party/redirect broadcasts only take effect after create.
4. Sizing: query native size with msg 0x37 (both axes) / 0x38 (width). Set placement with msg 0x56 passing a 4-float rect. Style bits queried: 0x1000 (msg 0x37) and 0x4000 (msg 0x38) via FUN_0062fe20 — set these frame styles before size query to control axis clamping.
5. Enable state is derived, not stored: toggling the frame's enabled flag then sending msg 0x0C refreshes child enable.
6. Destroy with msg 0x0B (frees 0x28). Base FUN_00647170 handles paint/hit-test each frame.

- **Crash gotchas:**

- Null-instance assert 0x5c0: any get (FUN_0087cf80) after destroy or before msg 9 aborts. Never send 0x56/0x37/0x38/0x31/0xC to a frame whose instance slot is null.
- Double-create assert 0x5ad: sending msg 9 twice (or with a non-null *(hdr[2])) aborts.
- Free size mismatch: destroy path frees exactly 0x28; the sibling control FUN_0087aa90 frees 0x18 — do not cross-wire the two procs or the heap will corrupt.
- Broadcast lifetime: the 4 game-msg subscriptions (0x10000119/130/174/177) are added in msg 9. If you free the instance without letting msg 0xB run the normal unsubscribe/teardown, a later broadcast will deref a freed frame.
- posRect fields [0x04..0x10] are reinterpreted between int (init) and float (msg 0x56 / 0x10000174 compares). Feed msg 0x56 a real Coord/rect float payload; passing ints produces denormals and mis-clamped geometry.
- msg 0x56 only repaints when the rect actually changes AND the frame is enabled (FUN_0062e2a0!=0); a set on a disabled frame silently no-ops the repaint.


### UiCtlHint  (EXE 0x0087d230, confidence: high)

- **WASM:** ram:80f067f5
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlHint.cpp (game-layer control; EXE string @0x00b95fa0, xref'd only from FUN_0087d230 at 0x0087d266/0x0087d280). WASM assertion string "../../../../Gw/Ui/Controls/UiCtlHint.cpp" @ram:00108503, used with "!s_closeStandardImgList" (line 0x36) and "!s_closeWarningImgList" (line 0x37).
- **Struct layout:**

RESOLUTION: WASM IUi::UiCtlHintProc(FrameMsgHdr const&,void const*,void*) @ram:80f067f5 -> assertion file "...\Gw\Ui\Controls\UiCtlHint.cpp" -> EXE string 0x00b95fa0 -> single code xref FUN_0087d230 = EXE FrameProc. Confirmed 1:1 by identical switch (cases 5,6,8,0x15,0x17,0x2b) and identical asserts.

UiCtlHint is a DECORATOR/overlay frame proc, NOT an owned-instance control. NO case 9 (FUN_0047f340 alloc), NO case 0xb instance free -- it holds no per-frame heap object. State lives on the frame message header + three module-global shared image-list handles.

Module globals (class state):
  DAT_010819dc  HFrameImageList  close-button "standard" severity list
  DAT_010819e0  HFrameImageList  close-button "warning" severity list
  DAT_010819e4  HFrameImageList  close-button "error" severity list
  (created msg 5, destroyed msg 6; msg-5 guard asserts if dc/e4 already set)

FrameMsgHdr param_1 (int*):
  [0] frame id -> *param_1 to FrameContent* calls
  [1] message id (switch var)
  [2] wparam ; [3] aux/out ptr
  [4] STYLE/SEVERITY dword = the real "struct":
        bit0x1=closable/has-"X"-button (also gates hit-test & taller size)
        bit0x2=ERROR severity ; bit0x4=WARNING severity ; neither=STANDARD
  [5] proc-stack index (used by FrameMsgCallBase)

Payload param_2 (float*), message-specific:
  msg8 paint:  *param_2 pass flags (bit0x2=draw bubble template, bit0x4=draw close btn);
     param_2[7](0x1c)=Rect4f* bubble rect; [9](0x24)/[10](0x28)=close anchor x/y;
     [0xb](0x2c)/[0xc](0x30)=close-btn state (==int2 -> pressed frame idx1 else 0)
  msg0x17 hit: [0]mouseX,[1]mouseY,[2]frameRight,[3]frameBottom; [4](0x10)=int* result out (set 2 when over close btn)
  msg0x15 out param_3: 4 dwords default-size rect (_DAT_00940ee4,_DAT_00945190,_DAT_00940ee4, height=(flags&1)?_DAT_00944228:_DAT_00945190)

Metric globals: _DAT_009413c8 right inset, _DAT_00944930 bottom inset, _DAT_009413d8 16px btn, _DAT_00940ee4/_DAT_00945190/_DAT_00944228 default w/h/tall-h.

- **Message protocol:**

FrameProc FUN_0087d230(msgHdr* p1, payload* p2, out* p3); switch(p1[1]); default -> thunk_FUN_00647170 = FrameMsgCallBase.

case 5 CLASS INIT: assert DAT_010819dc==0 (else FUN_00487a80(0x36)) and DAT_010819e4==0 (else 0x37); build 3 image lists via FUN_0062d790(0,7,0x12,&sz,&sz,atlas,2): standard(dc,PTR_DAT_00bf45e0), warning(e0,PTR_DAT_00bf45ec), error(e4,PTR_DAT_00bf45ec); CallBase.
case 6 CLASS DEINIT: FUN_0046f9b0(HandleCloseSafe) on dc/e0/e4, zero them; CallBase.
case 8 PAINT overlay: if(*p2&0x2) severity bubble template (error=PTR_DAT_00bf45e8/warning=PTR_DAT_00bf45e4/standard=PTR_DAT_00bf45dc) -> FUN_0062b8e0(*p1,p2+7,tmpl,&r,7,0,1,0)=FrameContentAddImageTemplate; if(*p2&0x4 && p1[4]&1) severity close list, frameIdx=(p2[0xb]==2||p2[0xc]==2)?1:0, 16x16 top-right rect -> FUN_0062b290(*p1,&r,list,idx,2,0)=FrameContentAddImage. NO CallBase (break).
case 0x15 GET DEFAULT SIZE: write size rect to p3; tall height (_DAT_00944228) if flags bit0x1.
case 0x17 HITTEST close btn: only if p1[4]&1; if mouse in 16x16 close rect set *(int*)p2[4]=2. No CallBase.
case 0x2b INVALIDATE-ON-STYLE: if(p2[1]&0x4) FUN_0062bd80(*p1,4)=FrameContentInvalidate(region4); CallBase.
default/7/9(alloc)/0xb(free)/others: CallBase FUN_00647170 (itself refuses to forward 9 and 0xb).

EXE=WASM helpers: FUN_0062d790=FrameImageListCreate, FUN_0062b8e0=FrameContentAddImageTemplate, FUN_0062b290=FrameContentAddImage, FUN_0062bd80=FrameContentInvalidate, FUN_0046f9b0=HandleCloseSafe, FUN_00487a80=ErrorAssertion, FUN_00647170=FrameMsgCallBase.

- **Create recipe:**

UiCtlHint attaches as an overlay proc onto an existing host frame; it is not instantiated standalone. Concrete install at FUN_0086c190 (UiCharSelect/TxtCharRestrict):
  1. frame = FUN_0062bfc0(root, 0, 2, FUN_00610c40 /*TxtCharRestrict base proc*/, 0, L"TxtCharRestrict");
  2. FUN_0062f1a0(root, L"UiCharSelect");            // name
  3. FUN_0062f150(frame, FUN_0087d230, 2);           // add Hint proc, priority/layer 2
  4. FUN_0062f5a0(frame, 1);                          // mark
  5. FUN_00611320(frame, textHandle); FUN_0062cb00(frame, ...) to show.

Warm-ups/order: class-init (case 5) MUST have run once at UI startup so DAT_010819dc/e0/e4 exist before any paint (case 8); re-sending 5 while non-null asserts. Set host style dword bit0x1=closable(adds X + hit-test + taller size), bit0x2=error, bit0x4=warning (else standard). To paint, the base pass must set payload bit0x2 (bubble) and bit0x4 (close btn) on msg 8. From Py4GW: create the host text frame first (FUN_0062bfc0 + base text proc) then FUN_0062f150 to attach 0x0087d230 -- do not call the create primitive with this proc as the primary.

- **Crash gotchas:**

1. Singleton guard: msg 5 asserts (FUN_00487a80(0x36)/(0x37), noreturn) if DAT_010819dc/e4 already non-null -- never double-init; msg 6 must zero them first.
2. Paint before class-init: msg 8 derefs DAT_010819dc/e0/e4 as image-list handles; if msg 5 never ran they are 0.
3. Close button needs BOTH host style bit0x1 (p1[4]&1) AND payload bit0x4; severity bits alone give a bubble with no interactive close/hit-test.
4. Not an owned-instance control: no case 9/0xb instance, **(msgframe+8) accessor is meaningless here; state = frame style dword + module globals.
5. Cases 8 and 0x17 deliberately skip CallBase; routing them through base double-paints/mis-hits.
6. Decompiler float 2.8026e-45 == integer 2 reinterpreted (pressed state); param_2[0xb]/[0xc] are ints.
7. FrameMsgCallBase (FUN_00647170) refuses to forward msg 9(alloc)/0xb(free); the Hint proc owns no instance to alloc/free.


### UiCtlGap  (EXE 0x0087da00, confidence: high)

- **WASM:** ram:811887c5
- **Assertion file:** No dedicated <Ctl>.cpp assertion (stateless, no alloc). Anchored instead by shared assert string "MathRectIsValid(rect)" @ EXE 0x0094a3e8 (WASM P:\\Code\\...\\Base\\rtl\\RtlMath.h line 0x238), fired via FUN_00487a80(0x238) in the paint path — line number 0x238 matches the WASM IUi::UiCtlGapProc exactly.
- **Struct layout:**

STATELESS control — NO heap instance. msg 0x09 does NOT allocate (unlike case-9 alloc controls); there is no FUN_0047f340("<Ctl>.cpp",size) call and no *(msgframe[2]) instance pointer to free. The related Ui::CLayout::Gap (WASM 80df4e69) creates a 0x2c-byte layout SizeNode (vtable &DAT_001670f8, type tag [10]=2, [1]=size, [9]=marginFlags) but that is a LAYOUT DATA MODEL in the CLayout size-node array, NOT this FrameProc's instance. This FrameProc reads only: (a) frame style flags via FrameTestStyles (0x1000/0x2000/0x4000), and (b) the paint/query context param_2: +0x00 flags(bit0=visible), +0x0c..+0x18 = Rect4f{L,T,R,B} float (paint), +0x08 = pointer to output Coord2f (msg 0x38). All sizing is derived live from FrameCoordGetDevicePixel * {3,4,12}.

- **Message protocol:**

FrameProc FUN_0087da00(frame** param_1, paintCtx* param_2, out* param_3); switch(param_1[1]=msg). Uses FUN_0062fe20(frame,mask)=FrameTestStyles, FUN_0062bfa0()=FrameCoordGetDevicePixel(devpix). LEAF proc: it does NOT install a base (no case 4) and does NOT delegate unknown msgs (no thunk_FUN_00647170) — every unhandled msg just returns/no-ops.
 - msg 0x08 PAINT (content render). Gated on (param_2[0] & 1)=frame-visible. Reads frame rect from param_2+0x0c(L),+0x10(T),+0x14(R),+0x18(B) as float; ASSERTS L<=R && T<=B (MathRectIsValid(rect)) else FUN_00487a80(0x238) -> hard halt. Style 0x4000 makes the draw rect fill the content extent. Then: if style 0x2000 CLEAR -> textured divider via FUN_0062b3e0 (FrameContentAddImageTemplate), image ptr = &DAT_00b96060 when style 0x1000 set else &DAT_00b96068, layer 7. If style 0x2000 SET -> solid colored bar via FUN_0062b790 (FrameContentAddColour/rect), colour _DAT_0093d950, inset by _DAT_00949070/_DAT_00943290, layer 7. If style 0x4000 SET -> the draw is wrapped in a GrTransform: FUN_0066f3f0(2)=GrTransformPush, FUN_0066d370(2,basis,scale,rot)=GrTransformBasis, FUN_00665000(model,0)=GrModelSetWorldTransform, FUN_0066ea30(2,1)=GrTransformPop (rotates the divider 90 deg = vertical). Ends with FUN_0046f850(frame) finalize.
 - msg 0x09 INIT/ENABLE: FUN_0062ede0(frame,0,0xffffffff)=FrameMouseEnable(disable) -> gap is non-interactive / click-through.
 - msg 0x15 SIZE-QUERY (min-size Rect4f -> param_3[0..3]): w = devpix*_DAT_00943280(=3.0). Style 0x2000 -> all zero (no min). Style 0x4000 -> {w,0,w,0} (horizontal min-extent). Else -> {0, w, 0, devpix*_DAT_00937ed0(=4.0)} (vertical).
 - msg 0x38 GET PREFERRED/DEFAULT SIZE (Coord2f at *(param_2+8)): style 0x2000 -> val=devpix*_DAT_009413d0(=12.0), else val=devpix*1. Written to component[0]=x when style 0x4000 set, else component[1]=y.
 - all other msgs: no-op (leaf, no base delegation).
STYLE BITS: 0x1000=alternate divider image; 0x2000=thick solid-bar mode (12px default, no min size, colored bar instead of textured); 0x4000=horizontal orientation (width axis / GrTransform-rotated), clear=vertical.

- **Create recipe:**

Register FUN_0087da00 directly as the FrameProc (it is a self-contained leaf; no base to pre-install, no image-list warm-up like Bullet's case-5, no per-instance alloc). Create via CreateUIComponent/FrameCreate(parent, style|F_VISIBLE(0x1), child_index, proc=0x0087da00, name, label). Choose style bits for the divider you want: 0x4000 = horizontal divider (spans width), clear = vertical; add 0x2000 for the thick/solid 12px bar (else a thin ~3px textured line); optionally 0x1000 for the alternate divider texture. It disables its own mouse on msg 0x09 so it is non-interactive by design. No destroy-time teardown beyond normal frame destroy (no CTimer/instance/image-list to release). In practice the game layers this proc onto list/menu frames (e.g. it is referenced by the DropdownFrame proc 0x0087f5f0) to paint separators; it can also be created standalone as a spacer.

- **Crash gotchas:**

1) msg 0x08 hard-asserts MathRectIsValid: if the frame's laid-out rect is inverted (R<L or B<T) FUN_00487a80(0x238) fires a non-returning halt. Ensure a valid, non-degenerate layout rect before it paints (0-width/0-height with L==R is fine; inverted is fatal). 2) Leaf proc with NO base delegation: unknown messages are silently dropped (no thunk_FUN_00647170), so it provides NO hit-testing/focus/standard-content behavior — do not expect base-frame semantics; layer it over a real base frame if you need them. 3) Style 0x4000 pushes a GrTransform and relies on reaching FUN_0066ea30(2,1) to pop; the assert-halt path bypasses the pop, so an invalid rect can also unbalance the transform stack. 4) msg 0x38 writes through *(param_2+8) as a Coord2f*; only the layout system passes a valid pointer — don't invoke 0x38 with a null/garbage out-slot. 5) The devpix scale globals (_DAT_00943280=3, _DAT_00937ed0=4, _DAT_009413d0=12) are runtime-initialized at startup (0 before init) — sizing only meaningful after the UI system is up.


### UiCtlTextShy  (EXE 0x0087f0d0, confidence: high)

- **WASM:** ram:8149a9a7
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlTextShy.cpp
- **Struct layout:**

Instance allocated in case 9 via FUN_0047f340("P:\\Code\\Gw\\Ui\\Controls\\UiCtlTextShy.cpp", 0x4e). Own-layer fields actually touched are only the first 8 bytes; the rest of the 0x4e (78) byte block is reserved/unused by this layer:
  +0x00  void*  ownFrame      // = *msgframe[0], the control's own frame handle (paint/tween target)
  +0x04  u32    watchedFrame  // frame handle/id whose hover dims this text; init 0xFFFFFFFF (none); set by msg 0x5E, consumed by msg 0x4E
Instance pointer is stored at *(msgframe[2]) (the frame's control-instance slot). Freed and zeroed in case 0xb.

This control does NOT own a text buffer of its own — text rendering/layout is entirely the Engine CtlText base (FUN_00610c40, whose own struct lives at *pfVar2 with fields at +0x0C len, +0x14 caret/-1, +0x18 color, +0x1C font, +0x30 highlight-color, etc.). UiCtlTextShy only mutates the frame alpha animator (FUN_006364d0 anim struct: [0]=duration,[1]=remaining,[2]=flags,[3]=startA,[4]=endA,[0xb]=currentA).

- **Message protocol:**

FrameProc FUN_0087f0d0(msgframe, payload, p3); switch on msgframe[1]=msg:
- case 4  (GET_BASE_PROC): writes parent proc into *(payload[3]) = FUN_00610c40 (Engine CtlText). => parent class is CtlText.
- case 9  (CREATE/ALLOC): asserts FUN_00487a80(0x4d) if slot *(msgframe[2]) already set (no double-create). Allocs 0x4e bytes, inits ownFrame=*msgframe[0], watchedFrame=0xFFFFFFFF, stores ptr in *(msgframe[2]), then subscribes the frame to broadcast msg 0x4E via FUN_0062ef00(ownFrame,0x4e) (FUN_00647db0 set-context + FUN_006480b0 register).
- case 0xb (DESTROY/FREE): if instance non-null FUN_005acaeb(instance,8) (pool 8 free); zero slot.
- case 0x4E (MOUSEOVER-CHANGED broadcast / tick): payload[0]=currently-hovered frame, payload[1]=previously-hovered frame. Asserts 0x60 if instance null. Resolves watchedFrame: root = FUN_0062d330(ownFrame) (returns *(root+0xbc), asserts 0x9d if null), target = FUN_0062cfc0(root, watchedFrame). If target!=0: bWas = payload[1] is target or contained-in-target (FUN_0062e200 containment); bIs = payload[0] is target or contained-in-target. On edge (bWas!=bIs): drive alpha tween FUN_0062cb00(ownFrame, startA, endA, durSec, 0):
    * entering  (bIs true):  start=1.0, end=0.2, dur=0.2  -> text dims/goes 'shy'
    * leaving   (bIs false): start=0.2, end=1.0, dur=0.6  -> text fades back to full
- case 0x5E (SET WATCHED FRAME): payload = new watched frame handle. Asserts 0x60 if instance null. If different from stored watchedFrame, recomputes hover state relative to the current global mouseover frame (FUN_0062ee20 = *(mouseover_root+0xbc)) with the same containment test and applies the same enter/leave fade, then stores watchedFrame = payload.
- default: forwarded to base CtlText proc via thunk_FUN_00647170(msgframe,payload,p3). (No local case 1 paint, no 0x15 size-query — those fall through to CtlText.)

Alpha tween FUN_0062cb00(frame, startA, endA, dur, flags) -> FUN_00647db0(frame)+FUN_006364d0(anim,startA,endA,dur,flags); all three floats asserted in [0,1] (asserts 0xEC8..0xECD), so the hardcoded 0.2/0.6/1.0 constants are safe.

- **Create recipe:**

1. Create the frame with FrameProc = 0x0087f0d0 using the standard control primitive FUN_0062bfc0(parent, flags, childIndex, proc=0x0087f0d0, userdata, 0). Parent it into a LIVE frame tree (a valid container returning *(root+0xbc)); it is a CtlText subclass so use CtlText-style flags/layout.
2. Engine lifecycle auto-drives: msg 4 installs base CtlText proc (FUN_00610c40); msg 9 allocs the 0x4e instance and subscribes the frame to the 0x4E mouseover broadcast. No manual warm-up needed beyond normal control creation.
3. Set the displayed text/color/font exactly as a normal CtlText (base handles the text-buffer, color +0x18, highlight +0x30, font +0x1C messages) — this control adds no new text API.
4. Optional: send msg 0x5E with the handle of the frame whose hover should dim this text. Default watchedFrame = 0xFFFFFFFF means it watches nothing and never fades.
5. Leave it in the tree; the frame system will deliver 0x4E on every mouseover change and the control fades to 20% alpha over 0.2s while the watched frame (or a descendant of it) is hovered, and back to 100% over 0.6s when the mouse leaves.

- **Crash gotchas:**

- Sending 0x4E or 0x5E before the create (msg 9) => instance slot null => hard assert FUN_00487a80(0x60). The frame must be fully created first.
- Re-issuing create (msg 9) on an already-created frame => assert FUN_00487a80(0x4d) (no double-create).
- Root/parent must be valid: msg 0x4E calls FUN_0062d330(ownFrame) which asserts 0x9d if the frame is not attached to a container returning *(root+0xbc). Do not send the mouseover broadcast to an unparented frame.
- Does NOT paint on its own (no case 1 / no size-query) — it relies entirely on the CtlText base for rendering; if the base proc is not installed (msg 4/9 skipped) the text will not draw and it only toggles alpha.
- FUN_0062cb00 asserts if start/end/dur are outside [0,1] (0xEC8..0xECD) — safe with the built-in constants; do not reuse it with out-of-range values.
- watchedFrame semantics are handle-vs-id sensitive: 0x5E stores the raw payload handle, 0x4E passes it through FUN_0062cfc0/FUN_0064ca80 to re-resolve; pass a genuine frame handle, not an arbitrary integer, or target resolution returns 0 and no fade occurs (silent no-op, not a crash).


### UiCtlTextShy2  (EXE 0x0087f0d0, confidence: high)

- **WASM:** ram:8149a8bf
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlTextShy.cpp (EXE string @ 0x00b9636c). NOTE: game-layer path (Gw\Ui\Controls), not Engine\Controls. WASM symbol IUi::UiCtlTextShyProc @ ram:8149a8bf is a thin dispatch shim that tail-calls IUi::TextShy::CTextShyFrame::FrameProc; that FrameProc is the EXE FUN_0087f0d0.
- **Struct layout:**

TextShy instance (allocated case 9 by FUN_0047f340; freed case 0xb by FUN_005acaeb(inst,8)) — small POD, NO vtable (unlike CtlText which sets &PTR_FUN_00a50108):
  +0x00  uint32  frameHandle   // = *param_1 (owning frame id/handle); used as arg to FUN_0062d330 and FUN_0062cb00
  +0x04  void*   activeChild   // last child under hover/focus; init 0xFFFFFFFF (none). Updated by case 0x5e; read by 0x4e/0x5e for transition detection
Only these 8 bytes are used by the shy logic. Actual text content/style lives in the inherited CtlText instance, which is a SEPARATE struct reached via *(float*)param_1[2] inside FUN_00610c40 (fields: +0x0c len, +0x14 caret/-1 sentinel, +0x18 color, +0x1c font-size, +0x20 child-frame array, +0x28 count, +0x30 aux 4-byte). TextShy does not touch that struct directly.

- **Message protocol:**

FrameProc FUN_0087f0d0(msgframe *param_1, payload *param_2, out param_3); switches on msg = param_1[1].

- case 4 (INSTALL_BASE): writes parent/base proc pointer FUN_00610c40 (= CtlText base, "Engine\Controls\CtlText.cpp") into *(param_2[3]). TextShy is a subclass of the standard Text control; it inherits ALL painting/sizing/text-get/set from CtlText.
- case 9 (CREATE/init): asserts *(int*)param_1[2]==0 (FUN_00487a80 line 0x4d if already set). Allocs instance via FUN_0047f340("...UiCtlTextShy.cpp", 0x4e) [0x4e = source LINE number, not size]. Writes inst[0]=frame-handle (*param_1), inst[1]=0xFFFFFFFF (no active child yet). Stores inst ptr at *(param_1[2]). Registers self for control message 0x4e via FUN_0062ef00(frame, 0x4e).
- case 0xb (DESTROY): if instance set, FUN_005acaeb(inst, 8) frees it; then *(param_1[2])=0. Assertion-free.
- case 0x4e (78 = SHY-HOVER update, the self-registered msg): inst = *(param_1[2]) (assert non-null, line 0x60). uVar1 = inst[1] (last-active child). iVar3 = FUN_0062d330(inst[0]) -> frame's child/anchor list (assert line 0x9d if 0); FUN_0062cfc0(list, uVar1) resolves the tracked child. Computes bVar5 = "new pointer param_2[1] is inside subtree", bVar6 = "old pointer *param_2 is inside subtree" via FUN_0062e200 (ancestor test). On transition (bVar5!=bVar6): if now-inside -> FUN_0062cb00(frame, 1.0f, 0.2f, 0.2f, 0) (fade text to FULL); else -> FUN_0062cb00(frame, 0.2f, 1.0f, 0.6f, 0) (fade text to DIM/shy). Else falls through to base.
- case 0x5e (94 = ACTIVE/FOCUS change): inst non-null (assert 0x60). If param_2 != inst[1]: recompute membership of stored active (inst[1]) vs incoming param_2 relative to FUN_0062ee20() (current global hover/focus frame), using FUN_0062d330/FUN_0062cfc0/FUN_0062e200. On transition apply the same FUN_0062cb00 alpha fade. Finally inst[1] = param_2 (remember new active child). Returns without base fallthrough.
- default: thunk_FUN_00647170(param_1,param_2,param_3) -> forwards to base CtlText proc FUN_00610c40, which handles paint, size-query, and text ops. Base CtlText msgs (int): 0x38 measure-extent, 0x4c self-text-invalidate (registered in CtlText init), 0x56/0x57/0x58 get-text/len/attr, 0x59 set 4-byte field @+0x30, 0x5a set color @+0x18, 0x5c set-text(active=-1)/0x5d set-text(active=0) -> both FUN_0062bd80(frame,0x40) redraw. TextShy adds NO paint/size logic of its own; it only re-tints inherited text on hover/focus.

FUN_0062cb00(frame, r/alpha, g, b, 0) validates each channel in [0,1] then FUN_00647db0(frame)+FUN_006364d0(...) to start a color/alpha animation. Constants: 0x3f800000=1.0 (opaque/full), _DAT_00940ea8=0.2, _DAT_00941d60=0.6.

- **Create recipe:**

1. Create the frame with the TextShy FrameProc as the control proc:
   FUN_0062bfc0(parentFrame, styleFlags, childOrdinal, /*proc=*/0x0087f0d0, userData, 0).
   The framework auto-drives: case 4 installs CtlText base, then case 9 allocates the shy instance and self-registers msg 0x4e.
2. Style flags (read by base via FUN_0062fe20 mask): to get an allocated/editable text buffer set bit 0x100000 (base asserts this present in its set-text path, line 0x1dd). Text-attribute bits consumed by base measure: 0x4000 (center?), 0x8000, 0x10000, 0x20000, 0x80000 map to render flags 1/2/8/4/0x10.
3. Warm-ups after create (send through the frame dispatcher FUN_0062ef40): set the string with base msg 0x5c (set-text, resets caret to -1) or 0x5d; optionally 0x5a to set text color (@+0x18) and 0x59 for the +0x30 aux field. These are handled by inherited CtlText.
4. Sizing: TextShy has no size-query; base CtlText answers extent via msg 0x38 (measure) using font-size @+0x1c and the flag bits. Let layout query it; do not hand-size.
5. Shy fade is fully automatic: it needs NO extra calls. As the framework routes mouse hover (msg 0x4e) and focus/active (msg 0x5e) with child-frame pointers, the proc fades the text alpha between full (1.0) when the tracked child is under the cursor/focus and dim (0.2/0.6) when not. For the effect to trigger, the frame must participate in the hover subtree that FUN_0062d330/FUN_0062e200 walk (i.e. be a real child frame of an interactive parent).

- **Crash gotchas:**

- Double-create: case 9 asserts (FUN_00487a80(0x4d)) if instance pointer at *(param_1[2]) is already non-zero. Never send msg 9 twice; the framework does it once at creation.
- Null instance: cases 0x4e and 0x5e assert (FUN_00487a80(0x60)) if the instance is null. Do not deliver 0x4e/0x5e to a frame whose TextShy instance was already destroyed (msg 0xb) or never created — order matters: create (9) before any hover/focus routing, destroy (0xb) only after hover/focus stops.
- Missing child list: case 0x4e/0x5e call FUN_0062d330(frame) and assert (FUN_00487a80(0x9d)) if it returns 0. The frame must be a valid interactive frame with a resolvable child/anchor list; attaching TextShy to a detached/never-laid-out frame will assert on first hover.
- FUN_0062cb00 asserts (0xec8-0xecd) if frame==0 or any alpha channel is outside [0,1] or NaN — only reachable with corrupt frame handle; keep inst[0] intact.
- Base set-text (msg via case that calls FUN_00487a80(0x1dd)) requires style bit 0x100000; without an allocated text buffer, setting text asserts.
- TextShy owns no paint/vtable of its own — if you install proc 0x0087f0d0 but the base install (case 4 -> FUN_00610c40) is bypassed, default msgs forward through thunk_FUN_00647170 to a base that was never wired, giving blank/garbage text. Always let the standard create path run case 4 then 9.


### CtlDropList  (EXE 0x0087f5f0, confidence: high)

- **WASM:** ram:80e3c9a3
- **Assertion file:** P:\Code\Engine\Controls\CtlDropList.cpp (string @ EXE 0x00a502fc). Frame allocator uses P:\Code\Engine\Frame\FrApi.cpp,0x132 (FUN_0062bfc0).
- **Struct layout:**

CtlDropList is a COMPOSITE control: a droplist frame + a collapsed "button" child + a popup list child. It has no single flat instance struct; state is spread across the frame object and per-frame "components" resolved through a hash map.

Frame object (base allocated by create-primitive FUN_0062bfc0 = FrApi.cpp,0x132; accessed via FUN_00647db0(frame)):
  +0x84 / +0x88 / +0x8c : layout/parent bookkeeping (zeroed at create)
  +0x90  (dflt 0x40)    : style-flags word (queried by FUN_0062fe20(frame,mask))
  +0xbc                 : pointer to the control's component/instance record (what FUN_0062cfc0 returns)
  +0x190 (=400)         : create-flags param stored at creation (param_2 of FUN_0062bfc0)
  +0x1c4                : SELECTED VALUE / INDEX slot. get = FUN_0062d6b0(frame) -> *(frame+0x1c4); set = FUN_0062fbf0(frame,val) -> *(frame+0x1c4)=val; initialized to 0 at create.

Component lookup: FUN_0062cfc0(frame, type) => FUN_0064ca80(frame,type) is a hash map keyed by (frameId, type); returns component; instance ptr = component+0xbc. Observed 'type' args:
  type 0 = list/content model (the droplist's data model / current content)
  type 1 = the interactive child frame (button/popup target)
  type 3 = extended/scroll sub-state (only when style 0x8000 set)

Style bits (FUN_0062fe20 masks, read by item-render proc FUN_0087da00):
  0x1000 = alt text alignment ; 0x2000 = icon/graphic item mode ; 0x4000 = two-column/measured layout ; 0x8000 = scrollable/extended droplist.
Create-flag words seen: 0x300 = droplist frame ; 0x80 = inner render primitive ; 0x20 = collapsed button part ; 0x4028 = popup list frame.

- **Message protocol:**

FrameProc signature: void proc(uint* msgframe, void* payload, code* extra). msgframe[0]=frame handle, msgframe[1]=message id. switch(msgframe[1]):

  9  CREATE/INIT: payload -> {code* subProc, void* subUserdata}. Builds inner render primitive: FUN_0062bfc0(frame, 0x80, 0, subProc, subUserdata, 0). Asserts 0xed if payload==NULL. (Per verified model, re-alloc asserts.)
  0x0a..0x55 (except specials below): no-op / return. NOTE: 0x15 (size-query) is a no-op here; extent is served via 0x38 and by the inner primitive.
  0xc  DESTROY: if payload==NULL, get child FUN_0062cfc0(frame,1) and FUN_0062c550(child); then finalize model FUN_0062cfc0(frame,0,payload) -> FUN_0062c9c0.
  0x31 INPUT/EVENT (-> FUN_0087f8e0): payload+4=group, +8=code, +0xc=data.
        group0/code7: collapse popup (destroy child list).
        group0/code8: OPEN popup -> create popup list frame FUN_0062bfc0(frame,0x4028,1,&LAB_00612ad0,0,0), attach item render FUN_00878950, size/position (FUN_0062f7b0 ext 0x12), notify 7; if data&2 highlight+scroll to current sel. If a popup already exists, forward 0x58 to it. Asserts 0x5b on open if popup child already present but state==closed.
        group1/code3: commit (set value=1, refresh 0x44, forward 0x58).
        group1/code7 with data[2]==7: ITEM CHOSEN -> read selected idx FUN_0062d6b0(data[0]), close popup, notify 8 with idx (selection-changed).
  0x38 GET-EXTENT/MEASURE: writes child's {w,h} pair into *(payload[2]).
  0x44 REFRESH/RELAYOUT: model value reset (FUN_0062fbf0(model,..)) + invalidate (FUN_0062f0d0(frame,0x44)).
  0x56 GET (-> FUN_0087f870 flag0): payload={out value, formatProc,...}; installs formatter (default &LAB_008891b0) then reads value.
  0x57 SET (-> FUN_0087f870 flag1): payload={value, formatProc,...}; installs formatter, sets value=payload[0], then commit FUN_0062c9c0. Asserts 0xa2 if child instance missing.
  0x58 SET-ITEM-RENDER-PROC: extra(param_3)=render proc, default FUN_0087da00; installs onto child via FUN_00612900 (=dispatch 0x57). Asserts 0xb6 if no child.
  0x59 GET-ITEM-RENDER-PROC: *param_3 = FUN_0062cfc0(frame,0). Asserts 0xc5 if param_3==NULL.
  0x5a CLEAR/RESET-SELECTION: FUN_0052b720(child) then notify 7 (FUN_0062ee80(frame,7,0,0)).
  0x5b FORWARD-SET-TO-CHILD: build 0x57 payload on child (FUN_0062cfc0(frame,0,0x57,payload,0)) and dispatch FUN_0062ef40.

Item-render default proc FUN_0087da00 (installed on the popup list) switches on its own msg: 8=paint item (bg via FUN_0062b790/FUN_0062b3e0 + text, style 0x1000/0x2000/0x4000 dependent), 9=activate, 0x15=measure item size (row height FUN_0062bfa0), 0x38=measure width/height into payload.

Dispatch layer: FUN_0062ef40(frame,msg>=0x56,in,out) control get/set (asserts 0xf2f if msg<0x56); FUN_0062ee80(frame,msg>=7,a,b) parent notify; FUN_0062ef00 single-arg notify.

- **Create recipe:**

Composite build (from live game-layer site FUN_00572d40); the CtlDropList proc is installed via thunk &LAB_0087fa80 (JMP 0x0087f5f0):

1. Have a parent frame handle (parentFrame).
2. Create the droplist frame with the control proc, passing {renderProc, ctx} as userdata:
     dropFrame = FUN_0062bfc0(parentFrame, 0x300, /*order*/2, &LAB_0087fa80, &{renderProc, ctx}, 0);
   -> internally this triggers msg 9, which builds the 0x80 inner render primitive from {renderProc, ctx}.
3. Create the collapsed button part:
     btn = FUN_0062bfc0(parentFrame, 0x20, /*order*/3, &LAB_005755a0, 0, 0); FUN_0062fcb0(btn, 0);
4. Create the list-content frame:
     flags = base|0x300 (use base|0x2001300 if style 0x8000 present);
     listFrame = FUN_0062bfc0(parentFrame, flags, /*order*/0, FUN_00565a70, 0, 0);
5. Attach item model / render proc:  FUN_0062ef40(listFrame, 0x58, itemModel, 0);
6. If no preselection:               FUN_0062ef40(listFrame, 0x57, 0, 0);
7. Set/refresh current selection value: send 0x57 to dropFrame with {value, formatProc}; read back with 0x56.
8. Register notify/hotkey hooks:     FUN_0062ef00(dropFrame, 0x10000039 / 0x1000011e / 0x1000011f / 0x10000115 / 0x10000124 / 0x10000126).

Warm-ups / ordering: msg 9 (create) MUST run before any 0x56/0x57/0x58/0x59 (they assert on missing child). Popup (open, group0/code8) is created lazily on user click; do not pre-create it. Sizing is pull-based: parent measures via 0x38 (writes child {w,h}); the row/item size comes from the item-render proc's 0x15/0x38 handlers.

- **Crash gotchas:**

- Msg 9 with NULL payload -> assert 0xed. Always pass a valid {subProc, subUserdata} pair. Re-sending 9 after instance exists asserts (double-create).
- 0x56/0x57 assert 0xa2 if the child instance is not yet created (FUN_0062cfc0(frame,1)==0). Only get/set the value after the create (msg 9) completed.
- 0x58 asserts 0xb6 if no child; 0x59 asserts 0xc5 if the out-pointer (extra) is NULL.
- Open-popup path (0x31 group0/code8) asserts 0x5b if a popup child already exists while state is 'closed' (inconsistent open/close bookkeeping) -> never manually create the popup frame; drive it only through 0x31.
- 0x38 (measure) writes into *(payload[2]); payload[2] must point at a writable {float w, float h} (actually child {w,h}) pair or it corrupts memory.
- Control dispatcher FUN_0062ef40 asserts 0xf2f when msg<0x56 and notify FUN_0062ee80 asserts 0xf4d when msg<7 -> use the right band per operation.
- Selection value is stored raw at frame+0x1c4 with NO range check; a 0x57 with an out-of-range index is accepted and later fed to the item-render proc (FUN_0087da00 case 8) which indexes the item list -> out-of-range read / garbage paint.
- item-render proc FUN_0087da00 case 8 asserts 0x238 if the item rect is degenerate (min>max on either axis); ensure list items get valid rects.


### UiCtlDropMenu  (EXE 0x0087f5f0, confidence: high)

- **WASM:** ram:8118a13f
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlDropMenu.cpp (EXE @0x00b963d0; WASM "../../../../Gw/Ui/Controls/UiCtlDropMenu.cpp" @ram:00107681)
- **Struct layout:**

No private instance struct is allocated by this control (unlike leaf controls that FUN_0047f340-alloc on case 9). "Layout" = the frame composition rooted at the DropMenu frame:
  DropMenu frame (proc=FUN_0087f5f0)
    child(0): BUTTON frame  (created on msg 9, flags 0x80, proc/userdata supplied in FrameMsgCreate) -> UiCtlDropMenuButton; carries the collapsed label + open/select style bits (bit1/0x2 tested in notify).
    child(1): LIST/popup frame (created lazily in OnFrameNotify on open, flags 0x4028, proc &LAB_00612ad0 = UiCtlList; item proc FUN_00878950). Its rows are UiCtlList items whose per-row proc defaults to FUN_0087da00 (or &LAB_008891b0 for the 0x56/0x57 append path). Each row's userParam = the caller-supplied item id (set via FrameSetUserParam).
FrameMsgCreate payload (msg 9 *param_2): { +0x00 childProc (code*), +0x04 childUserData (void*) }.
Add-item payload (msg 0x56/0x57 param_2): { +0x00 itemId/userParam, +0x04 rowProc-or-0, +0x08.. row create args (label/wchar*, etc.) }.

- **Message protocol:**

EXE FrameProc FUN_0087f5f0(frame*, payload*, code* param_3) switches on msgframe[1]=msg. This is a COMPOSITE CONTAINER control: it does NOT alloc a private TCtlInstance (no FUN_0047f340, no case 4 base-proc install, no case 9/0xb alloc/free of an instance struct). All state lives in two child frames of the DropMenu frame: child(0)=the drop-down BUTTON, child(1)=the popup LIST frame (created lazily). Child access is FrameGetChild = FUN_0062cfc0(frame, childIndex[, extra]).

Cases (msg -> behavior):
- 9  CREATE (OnFrameCreate): payload=*param_2 = FrameMsgCreate{[0]=childProc, [1]=childUserData}. Asserts payload!=0 (UiCtlDropMenu.cpp:0xED) else FUN_00487a80(0xed). Creates the button child: FUN_0062bfc0(self, flags=0x80, child=0, proc=create->proc, userdata=create->userdata, 0). The list child(1) is NOT created here.
- 0xC DESTROY/teardown: if child(1) [list] exists -> FrameDestroy FUN_0062c550(list); then get child(0) [button] and FrameEnable FUN_0062c9c0(button, payload).
- 0x31 NOTIFY (OnFrameNotify -> FUN_0087f8e0(self,payload)): the open/close/select engine. payload+4=source, payload+8=notifyCode. Source 0: code 7 -> destroy list child (close); code 8 -> if list not yet created, lazily create the popup list via FUN_0062bfc0(self, flags=0x4028, child=1, proc=&LAB_00612ad0 [UiCtlList proc], 0,0), install its item-proc FUN_0062f150(list,FUN_00878950,0), size it FUN_0062f7b0(list,rect,...,0x12), notify parent msg 7, and (if button style bit2) select+focus (FUN_0062ccd0/FUN_0062cd30); else forward FUN_0062ef40(list,0x58,0,0). Source 1: code 3 -> re-arm one-shot: FrameSetUserParam(button,1), FrameMsgRegister(self,0x44), forward list 0x58; code 7 w/ sub[2]==7 -> selection: read chosen index FUN_0062d6b0, destroy list, notify parent msg 8 with selected index (FUN_0062ee80(self,8,index,0)).
- 0x38 SIZE_QUERY: get child(0) button, FrameGetNativeSize FUN_0062d2a0, write Coord2 into payload[2].
- 0x44 DEFERRED_INIT (one-shot): get child(0), FrameSetUserParam FUN_0062fbf0(button,..), then FrameMsgUnregister FUN_0062f0d0(self,0x44) so it fires once.
- 0x56 ADD_ITEM (append): FUN_0087f870(self, payload, mode=0). Requires list child(1) or asserts UiCtlDropMenu.cpp:0xA2. Creates a list item FUN_00612900(list,0,0, itemProc=payload[1] or default &LAB_008891b0, payload+1); FrameSetUserParam(item, payload[0]).
- 0x57 ADD_ITEM+DISABLE: FUN_0087f870(self,payload, mode=1). Same as 0x56 then FrameEnable(item,0) (disabled/greyed row).
- 0x58 ENSURE/CREATE-ITEM: get child(1) list; assert list!=0 (UiCtlDropMenu.cpp:0xB6, "listFrame"); if param_3 (proc) ==0 use default row proc FUN_0087da00; FUN_00612900(list,0,1,proc,0).
- 0x59 GET_BUTTON_FRAME: assert param_3!=0 (UiCtlDropMenu.cpp:0xC5, "buttonFrameId"); *param_3 = child(0) button frame id.
- 0x5A CLEAR: get child(1) list; CtlFrameListClear FUN_0052b720(list); notify parent msg 7 (FUN_0062ee80(self,7,0,0)).
- 0x5B FORWARD-TO-BUTTON: get child(0) button; FrameMsgSend FUN_0062ef40(button, 0x57, payload, 0).
- 0x0A,0x0B,0x0D..0x30,0x32..0x37,0x39..0x43,0x45..0x55: fall through (break) -> no-op / handled by framework defaults. default: return.
Row/entry item template proc FUN_0087da00 handles its own msgs 8(paint bg via style FUN_0062fe20 masks 0x4000/0x2000/0x1000), 9(set text color FUN_0062ede0), 0x15/0x38(size query for the row). Style read primitive = FUN_0062fe20(frame,mask).

- **Create recipe:**

1) Create the DropMenu frame as a child of your container: FUN_0062bfc0(parentFrame, flags, childId, proc=FUN_0087f5f0 (EXE) / UiCtlDropMenuProc thunk, userdata, 0). The framework then delivers msg 9 (CREATE) to FUN_0087f5f0.
2) Supply a non-NULL FrameMsgCreate payload {childProc, childUserData} on msg 9, or it asserts at UiCtlDropMenu.cpp:0xED. On msg 9 it auto-creates the BUTTON child(0) with flags 0x80.
3) Populate items with FrameMsgSend(dropMenuFrame, 0x56, &{id,rowProc?,label...}, 0) for each entry (0x57 for a disabled entry). First append lazily requires the list; if you add before the list exists you must first trigger creation. Safer: send 0x58 to ensure a list item exists (creates list child(1) if the popup was opened) — but list child(1) is normally auto-created when the user opens the menu (notify code 8). If you must build before open, drive open programmatically so child(1) exists, else 0x56/0x58 assert at 0xA2/0xB6.
4) Sizing: the control answers native size (msg 0x38) from the button child's native size — no manual size needed; place via the parent's layout. The popup list is auto-sized (FUN_0062f7b0 rect, flags 0x12) on open.
5) Selection: on pick, the control notifies YOUR parent with msg 8 and the selected item's userParam/index (FUN_0062ee80(self,8,index,0)); msg 7 is sent to parent on open/clear. Handle notify 7/8 in the parent proc.
6) To read the button frame id: FrameMsgSend(dropMenuFrame, 0x59, 0, &out) (param_3=&out must be non-NULL). To clear all entries: msg 0x5A.
Order: FrameCreate(proc=FUN_0087f5f0) -> (auto msg 9 builds button) -> optionally msg 0x44 one-shot init fires -> add entries via 0x56/0x57 -> user open builds list child(1) -> selection -> parent msg 8.

- **Crash gotchas:**

see message_protocol


### UiCtlDropMenuBtn (IUi::UiCtlDropMenuButton::CDropMenuBtnFrame)  (EXE 0x0087fa90, confidence: high)

- **WASM:** ram:811867fd (dispatch shim) / ram:811868e5 (CDropMenuBtnFrame::FrameProc body)
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlInstance.h  (create/alloc + null-guard asserts route through the generic TCtlInstance template header; there is NO dedicated UiCtlDropMenuButton.cpp in either binary - only UiCtlDropMenu.cpp/UiCtlDropMenuEntry.cpp exist. The button is a template instantiation compiled into the DropMenu translation unit, which is why the WASM name resolves via UiCtlInstance.h rather than a control-specific cpp.) RESOLUTION: WASM CDropMenuBtnFrame::FrameProc (ram:811868e5) only asserts on UiCtlInstance.h (generic). Resolved structurally: DropMenu string P:\Code\Gw\Ui\Controls\UiCtlDropMenu.cpp (EXE 0x00b963d0) xrefs DropMenu proc FUN_0087f5f0 (thunk 0x0087fa80); the very next function 0x0087fa90 is a FrameProc with cases 0x56/0x57/0x58 setters, case 9 alloc FUN_0047f340("...UiCtlInstance.h",0x60) size 0x14, case 0xb free 0x14, delegating other msgs to base FUN_008783b0 - matching WASM exactly. Public entry is JMP-thunk 0x0087ff50, used as DATA by ~9 screen builders (FUN_00513cc0, FUN_0056a980, FUN_005882e0, FUN_008a6f10, ...).
- **Struct layout:**

CDropMenuBtnFrame instance = 0x14 bytes (20), alloc FUN_0047f340("...UiCtlInstance.h", line 0x60), freed FUN_005acaeb(p,0x14). Slot pointer lives at *(msgframe[2]).
+0x00 void*  vtable      -> &PTR_FUN_00b96438 (CDropMenuBtnFrame OnFrame* handler table; used by base dispatcher FUN_008783b0)
+0x04 uint32 frameId     -> owning frame handle; set on create = *msgframe. Target of FrameContentInvalidate / FrameContentAddImageArt.
+0x08 uint32 stateFlags  -> bit0x1 = checked/forced (msg 0x56); bit0x4 = open/expanded (msg 0x58); bit0x2 internal. OnFrameContentAdd reads (flags & 6) to pick base image variant (1/2 vs 4/5) and (flags & 1) to gate the mouse-focus highlight.
+0x0c uint32 iconModel   -> HGrModel/image handle for the dropdown-arrow indicator art (msg 0x57); passed to FrameContentAddImageArt as the 2nd layer image.
+0x10 uint32 reserved    -> zero-initialized (rounds instance to 0x14).

- **Message protocol:**

FrameProc FUN_0087fa90(msgframe*, wparam, lparam) switches on msg=msgframe[1]; instance slot = msgframe[2], instance = *slot.
CONTROL-SPECIFIC (handled before base):
 - 9  CREATE : assert(*slot==0) else FUN_00487a80(0x5f); p=FUN_0047f340("UiCtlInstance.h",0x60); p[1]=0; *p=&PTR_FUN_00b96438; p[2]=0; p[3]=0; *slot=p; instance[+4]=*msgframe (frameId). Then falls through to base FUN_008783b0.
 - 0xb DESTROY: base first, then FUN_005acaeb(instance,0x14); *slot=0. Asserts 0x72 if slot null / 0x74 if instance null.
 - 0x56 SET-FLAG1 (wparam!=0 -> flags|=1 else &=~1) : asserts 0x72/0x74; if changed, FUN_0062bd40(frameId) (content invalidate).
 - 0x57 SET-ICON  : instance[+0xc]=wparam; if changed FUN_0062bd40(frameId). asserts 0x72/0x74.
 - 0x58 SET-FLAG4 (wparam!=0 -> flags|=4 else &=~4) : asserts 0x72/0x74; invalidate on change.
ALL OTHER MSGS -> base wrapper FUN_008783b0 (TCtlInstance<CDropMenuBtnFrame>::FrameMsg) which dispatches into the +0x00 vtable then chains to base CCtlFrameMsg via thunk_FUN_00647170:
   1 paint(vt+0x08); 3 contentAdd(vt+0x0c -> OnFrameContentAdd, builds arrow/hover/focus art); 9 create-after(vt+0x1c then vt+0x18 with msgframe[+0x10]); 0xb destroy(vt+0x24); 0xf mouseDown(vt+0x2c); 0x13 mouseUp(vt+0x30 -> click -> parent DropMenu OnDropMenuButtonOpen); 0x15 sizeQuery(vt+0x34 -> OnFrameSizeQuery); 0x20 mouseFocus(vt+0x40); plus 0x24/0x25/0x2c/0x2e/0x2f/0x30/0x31/0x32/0x34-0x38/0x3a/0x3b/0x44/0x45/0x4b/0x4c/0x4f/0x52.
   msg 4 (install parent/base proc) is NOT handled here - absorbed by base CCtlFrameMsg in thunk_FUN_00647170.
WASM cross-check: identical control cases 0x56/0x57/0x58, base via TCtlInstance::FrameMsg -> CCtlFrameMsg::FrameProc.

- **Create recipe:**

Child control owned by a DropMenu, not a free-standing widget. Public proc address to register = 0x0087ff50 (JMP -> body 0x0087fa90).
1) Parent (UiCtlDropMenu frame, proc FUN_0087f5f0) on its own create (case 9) spawns the button child:
   FUN_0062bfc0(parentFrame, flags=0x80, child=0, proc=0x0087ff50, userdata, 0)
   (Screen builders write the proc into the child descriptor: MOV [desc+0]=0x0087ff50, MOV [desc+4]=userdata - see FUN_00513cc0 @0x00513d9f, also FUN_0056a980, FUN_005882e0, FUN_008a6f10.)
2) Base template auto-sends create(9) -> allocates the 0x14 instance (MUST precede any setter).
3) Warm-up/configure by dispatching control msgs to the child (FUN_0062ef40 dispatcher):
   - 0x57 : set dropdown-arrow image/model handle (instance+0xc).
   - 0x56 : optional checked/forced state (flags bit1).
   - 0x58 : open/expanded visual state (flags bit4) - normally driven by parent when menu opens.
4) Sizing answered by base msg 0x15 (OnFrameSizeQuery, WASM ram:811867b4); art (re)built in OnFrameContentAdd on invalidate.
5) Click flow: base mouseUp (0x13) -> notifies parent -> IUi::UiCtlDropMenu::CDropMenuFrame::OnDropMenuButtonOpen opens the popup list (parent creates it with proc &LAB_00612ad0, flags 0x4028 - see FUN_0087f8e0).
NOTE: standalone construction outside a DropMenu is not the intended path; reuse the DropMenu factory.

- **Crash gotchas:**

- Order: msg 0x56/0x57/0x58/0xb before create(9) -> FUN_00487a80(0x72) (msgframe[2] slot null) or FUN_00487a80(0x74) (*slot instance null). Always create first.
- Double create: sending 9 when *slot!=0 -> FUN_00487a80(0x5f). One instance per slot.
- Instance size fixed 0x14; destroy frees exactly 0x14 (FUN_005acaeb(p,0x14)). Do not repurpose the slot; alloc tag is ("...UiCtlInstance.h", 0x60) size 0x14.
- vtable at instance+0 (&PTR_FUN_00b96438) must be intact: base dispatcher FUN_008783b0 blind-calls vt slots (paint vt+8, contentAdd vt+0xc, sizeQuery vt+0x34, mouseUp vt+0x30, ...). A zeroed/corrupt vtable faults on the first non-control message.
- msg 0x57 icon handle (+0xc) is consumed by OnFrameContentAdd via FrameContentAddImageArt; a bad model handle corrupts paint.
- It is a child of DropMenu: expects a valid parent proc chain (thunk_FUN_00647170 / CCtlFrameMsg) installed via base msg 4; wrong parent breaks click->open routing.


### UiCtlProgressAction (IUi::Progress::CProgressActionFrame)  (EXE 0x00880ce0, confidence: high)

- **WASM:** ram:80f84601 (FrameProc; trampoline UiCtlProgressActionProc at ram:80f84519)
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlProgress.cpp (EXE string @0x00b964c8; game-layer, not Engine). Skin-bound assert "skin <= UI_CTL_PROGRESS_ACTION_SKINS" @0x00b96668.
- **Struct layout:**

Instance = 0x3C (60) bytes, allocated in case 9 via FUN_0047f340("UiCtlProgress.cpp",0x275); freed case 0xb via FUN_005acaeb(inst,0x3c). Instance slot = *(param_1[2]); accessor FUN_00884980(frame) = **(frame+8), asserts 0x287 if null.
  +0x00 u32  hFrame           (frame handle; copied from *param_1 at create; used as target of FrameContentInvalidate/FrameMsgRegister)
  +0x04 ptr  contentArray.data (TArray<ContentEntry>; each entry 0x10 bytes: [+0]=nested-array ptr, [+8]=nested count)
  +0x08 u32  contentArray.capacity
  +0x0c u32  contentArray.count
  +0x10 int  =0x10 (16; reserved/max slots, init constant)
  +0x14 float value           (progress value, set by msg 0x23; compared before UpdateModelAlphas)
  +0x18 float fadeTimer        (msg 0x45 decrements by dt; when 0 -> FrameContentInvalidate 0x30; init 0)
  +0x1c int  prevSkin          (init 4; snapshot of curSkin on skin change)
  +0x20 HObject handleA        (init 0; freed in 0xb via FUN_0046f850)
  +0x24 int  curSkin           (init 4; current skin index 0..4)
  +0x28 float animAccum        (msg 0x45 accumulator; init 0)
  +0x2c HObject handleB        (init 0; freed in 0xb via FUN_0046f850)
  +0x30 float animAlpha        (interp alpha computed in 0x45 via FUN_00882340; init 0)
  +0x34 int  animMode/state    (0,1=running variants asserted at 0x309; 2=settled; init 2)
  +0x38 int  skinIndex         (init 4; set by msg 0x62, 0..4)
Note: base class proc is CProgressFrame at 0x00618b70 (installed by msg 4).

- **Message protocol:**

Switch on msg=param_1[1]. payload=param_2, out=param_3.
FRAMEWORK:
  4  GetBaseProc: *(void**)param_2[3] = &LAB_00618b70 (base CProgressFrame proc).
  5  ClassInitialize: FUN_008825b0() loads skin resources (once per class).
  6  ClassDeinitialize: walk skin cache table DAT_01081a08..DAT_01081a98 (stride 9 dwords), FUN_0046f850(handle) + zero each.
  9  Create/Construct: assert *(param_1[2])==0 else FUN_00487a80(0x274); alloc 0x3c (line 0x275); init fields above; FUN_0062f5e0(hFrame,1)=FrameSetManualFading(enable).
  0xb Destroy: free handleA(+0x20)/handleB(+0x2c), free each ContentEntry nested array (bounds-checked, assert 0x24b), FUN_004fc450 free contentArray, FUN_005acaeb(inst,0x3c); *(param_1[2])=0.
  0x15 SizeQuery: FUN_00884980; assert param_3 (0x3c7); write default rect param_3[0..3] from _DAT_0093c89c / _DAT_00943278.
CONTROL-SPECIFIC (0x23+):
  0x23 (35) SetValue: if inst+0x14 != *param_2 -> inst+0x14=*param_2; FUN_00884ae0 (UpdateModelAlphas).
  0x38 (56) Measure: *(param_2[2])=*param_2 (width); *(param_2[2]+4)=FrameGetDefaultTextHeight(hFrame)+2.0 (FUN_0062d0e0 + _DAT_009413c8).
  0x45 (69) Advance/Tick: dt=*param_2; decrement fadeTimer(+0x18) clamp 0, at 0 -> FrameContentInvalidate(hFrame,0x30); animMode(+0x34): if 2 idle, else accumulate(+0x28), assert mode in {0,1} (0x309), threshold vs _DAT_00945b00/_DAT_00b96908 -> set mode 2 + invalidate 0x200, else interp alpha via FUN_00882340 into +0x30/+0x0c; FUN_00884ae0.
  0x5e (94) ContentAdd: FUN_00882de0(param_2) (OnSubclassMsgContentAdd).
  0x5f (95) ContentInvalidate: flags = ((param_2&3)!=0?0x30:0) | ((param_2&4)?0x40:0); FUN_0062bd80(hFrame,flags).
  0x60 (96) StartAnimMode0: inst+0x34=0; reset +0x28/+0x0c; FUN_0062ef00(hFrame,0x45)=FrameMsgRegister(advance); FUN_0062bd80(hFrame,0x200).
  0x61 (97) StartAnimMode1: inst+0x34=1; same reset/register/invalidate.
  0x62 (98) SetSkin: assert (int)param_2<=4 else FUN_00487a80(0x4fc); if changed set inst+0x38, prevSkin=curSkin, curSkin=mapped(0..4); if both !=4 -> +0x18=_DAT_00940eb0, register 0x45, invalidate 0x30; else +0x18=0, invalidate 0x30.
  default: thunk_FUN_00647170(param_1,param_2,param_3) = FrameMsgCallBase -> base CProgressFrame (handles PAINT msg 1 and all others).

- **Create recipe:**

This is a paintable SUBCLASS frame; painting is inherited from base CProgressFrame (0x00618b70) via the default->FrameMsgCallBase path (msg 1 is not overridden here).
1. Ensure class init ran once: send msg 5 (ClassInitialize) so skin resources (DAT_01081a08 table) are loaded before any instance renders; msg 6 tears it down.
2. Create the frame with the generic create primitive FUN_0062bfc0(parent, flags, child, proc, userdata, 0), registering this control's FrameProc thunk 0x00884a40 (tail-jumps to 0x00880ce0). The framework then drives: msg 4 (fetch base proc &0x00618b70), msg 9 (construct the 0x3c instance, enables manual fading via FrameSetManualFading).
3. Sizing: query default rect with msg 0x15 (fills 4-dword rect from _DAT_0093c89c/_DAT_00943278); layout width/height via msg 0x38 (Measure).
4. Drive content/animation: msg 0x62 to pick skin (0..4), msg 0x23 to set the progress value, msg 0x60/0x61 to start animation (auto-registers per-frame advance 0x45), msg 0x5e to add content, msg 0x5f to invalidate.
5. Instance pointer at runtime: FUN_00884980(frame) = **(frame+8).
Teardown: msg 0xb frees instance + content; msg 6 frees class skin cache.

- **Crash gotchas:**

- Msg 9 asserts (FUN_00487a80(0x274)) and refuses if the instance slot *(param_1[2]) is already non-zero: never send create twice without an intervening destroy (0xb).
- All content/value/skin messages call FUN_00884980 which asserts 0x287 if the instance (**(frame+8)) is null: sending 0x23/0x38/0x45/0x5e-0x62 before msg 9 (or after 0xb) crashes.
- Msg 0x62 SetSkin asserts skin index <= 4 (UI_CTL_PROGRESS_ACTION_SKINS, FUN_00487a80(0x4fc)) — passing >4 aborts.
- Msg 0x15 asserts param_3 (out rect) non-null (0x3c7).
- Msg 0x45 asserts animMode(+0x34) in {0,1} when not settled (FUN_00487a80(0x309)); corrupting +0x34 to another value while animating aborts.
- Msg 0x0b bounds-checks each content nested array (assert 0x24b) — heap corruption of contentArray count triggers it.
- Requires manual-fading enabled (done at create via FUN_0062f5e0(hFrame,1)); the fade timer (+0x18) drives 0x30 invalidations, so skipping create init leaves fading state inconsistent.


### UiCtlProgress  (EXE 0x008812e0, confidence: high)  [NOT a frame proc]

- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlProgress.cpp (EXE string @ 0x00b964c8; WASM @ ram:001092d4)
- **Struct layout:**

Instance = 0x28 bytes / 40 (alloc msg 0x09 via FUN_0047f340, freed FUN_005acaeb size 0x28):
+0x00 dword  ownerFrame        (copy of frame handle *frame)
+0x04 dword  callback/userData (set by msg 0x62; drives arrow count in paint)
+0x08 dword  primaryRenderHandle (render buffer/material; freed msg 0x0b; refreshed msg 0x45/0x60)
+0x0c float  primaryValue       (animated fill amount, counts down in msg 0x45; init 0.0)
+0x10 dword  primaryColorA      (init 0xffffffff)
+0x14 dword  primaryColorB      (init 0xffffffff)
+0x18 dword  secondaryRenderHandle (freed msg 0x0b; refreshed msg 0x45/0x61)
+0x1c float  secondaryValue     (animated fill, counts down msg 0x45; init 0.0)
+0x20 dword  secondaryColorA    (init 0xffffffff)
+0x24 dword  secondaryColorB    (init 0xffffffff)
Shared class statics: DAT_01081a98/DAT_01081abc = the two rate-arrow image lists; DAT_010819f8=refcount, DAT_010819fc=shared arrow glyph vertex buffer.

- **Message protocol:**

FrameProc = FUN_008812e0 (public JMP thunk 0x00884a50), switches on msgframe[1]=msg. Instance accessor = FUN_008849b0(frame). Cases:
0x04 INSTALL_BASE: *(payload[3]) = &LAB_00618b70 (base template proc).
0x05 CLASS_INIT (one-time): builds the two shared "rate arrow" image-lists via FUN_0065efa0(1,...,style 0x20003e0,0): DAT_01081a98 (asset DAT_00b966b0) and DAT_01081abc (asset DAT_00b966dc), each 16x16 cells laid out 6x5 (sm_...ImageList); bumps shared glyph refcount DAT_010819f8/buffer DAT_010819fc; asserts 0x636/0x651 if double-init.
0x06 CLASS_TEARDOWN: frees both image lists (null them); decrements DAT_010819f8 (assert 0x181 if already 0); at 0 frees shared glyph buffer DAT_010819fc.
0x09 CONSTRUCT: assert slot empty (0x5aa); alloc 0x28 via FUN_0047f340("...UiCtlProgress.cpp",0x5ab); init fields (see struct); store to *(payload[2]); FUN_0062ef00(frame,0x45) arms the tick.
0x0b DESTRUCT: FUN_0046f850 frees render handles at +0x18 and +0x08; FUN_005acaeb(inst,0x28); null slot.
0x15 SIZE_QUERY: assert out!=null (0x68a); writes default extent _DAT_00943278 into out[0..3].
0x38 EXTENT/POS: out[0]=payload[0]; out[1]=frameBaseline(FUN_0062d0e0)+_DAT_009413c8.
0x45 TICK/ANIMATE: dt=*payload; decrement primaryValue(+0x0c) and secondaryValue(+0x1c) toward 0; while >0 rebuild colored fill quad via FUN_008823d0 -> FUN_006641e0 on render handles (+0x08 primary, +0x18 secondary); falls through to base.
0x5e PAINT: FUN_008849b0 then FUN_00883790(payload) builds geometry: style bit 0x10=background image, 0x20=fill image, 0x40=rate-arrows (calls the utility FUN_008801a0 with arrow count = inst[+0x04]... actually param_1[1]), 0x100=border/frame.
0x5f INVALIDATE: if (payload&3) FUN_0062bd80(frame,0x30).
0x60 SET_PRIMARY(value,color): assert payload!=null (0x71f); store value at +0x14; recolor +0x0c..+0x14 (gradient base _DAT_0094052c) via FUN_008823d0.
0x61 SET_SECONDARY(value,color): assert payload!=null (0x729); store value at +0x24; recolor +0x1c..+0x24.
0x62 SET_CALLBACK/USERDATA: store payload at +0x04; FUN_0062bd80(frame,0x40) to refresh.
default: forward to base thunk_FUN_00647170(frame,payload,out).

- **Create recipe:**

This is a game-layer (Gw\Ui) styled control; do not hand-alloc. Create through the standard control-create primitive FUN_0062bfc0(parent, styleFlags, &child, proc, userdata, 0) with proc = UiCtlProgress FrameProc 0x008812e0 (or its registered thunk 0x00884a50). The proc auto-receives 0x04 (install base &LAB_00618b70) then 0x09 (construct 0x28 instance).
Warm-up: CLASS_INIT (msg 0x05) must have run once so DAT_01081a98 and DAT_01081abc (arrow image lists) + DAT_010819fc (glyph buffer) are non-null before any paint that uses rate-arrows, else the util asserts.
Style bits selecting rendered parts (checked in FUN_00883790 on frame style word): 0x10 background image, 0x20 fill image, 0x40 rate-arrows, 0x100 border. Combine as needed.
Post-create: send 0x60 (primary value+color), optionally 0x61 (secondary value+color), 0x62 (callback/userData ptr; also forces a 0x40 refresh). Animation runs itself off the 0x45 tick armed at construct. Query preferred size with 0x15 (returns _DAT_00943278); placement via 0x38. Read style with FUN_0062fe20(frame,mask).

- **Crash gotchas:**

GIVEN ADDRESS 0x008801a0 is the rate-arrow layout/emit UTILITY (draws N repeated arrow quads along the bar, called from paint builder FUN_00883790 when style bit 0x40 set). Its asserts: (0x197) frame param_1 != 0; (0x198) pass/subpass param_2 <= 9; (0x199) rect must be normalized right>=left AND bottom>=top (param_3[2]>=param_3[0], param_3[3]>=param_3[1]); (0x19a) arrow count param_4 != 0; (0x19b) arrow height param_5 > 0.0; (0x19c) param_6 must be finite AND non-zero (NaN or 0.0 both fault). Optional out-array param_7 is grown in place (FUN_00467740/FUN_004738f0) and receives floats.
FrameProc 0x008812e0 gotchas: construct asserts if slot already set (0x5aa); class double-init asserts (0x636/0x651); class teardown underflow assert (0x181) if refcount already 0; SIZE_QUERY needs non-null out (0x68a); SET_PRIMARY/SET_SECONDARY need non-null payload (0x71f/0x729). Painting before CLASS_INIT (image lists null) will crash inside the rate-arrow path.


### UiCtlProgressSlim (IUi::Progress::CProgressSlimFrame::FrameProc)  (EXE 0x00881940, confidence: high)

- **WASM:** ram:80f86746 (FrameProc); thin wrapper UiCtlProgressSlimProc at ram:80f8665e
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlProgress.cpp (WASM ../../../../Gw/Ui/Controls/UiCtlProgress.cpp @ ram:001092d4)
- **Struct layout:**

Instance = 0x24 bytes (9 dwords), allocated in case 9 via FUN_0047f340(file,0x7d3), freed in case 0xb via FUN_005acaeb(inst,0x24). Accessor FUN_008849e0(frame)= **(frame+8) (assert 0x7e5 if null).
 +0x00 HFrame  owningFrame        (= param_1[0] captured at create)
 +0x04 float   rate/stiffness     (default _DAT_0094052c = 0.5; used as denominator in msg 0x45 spring step)
 +0x08 float   fadeState/pos      (animated blend; 0..1; msg 0x60 forces 1.0; msg 0x45 integrates; feeds color lerp in UpdateModelColors)
 +0x0c float   fadeRest/base      (spring rest target, msg 0x45)
 +0x10 float   fadeVelocity       (spring velocity, msg 0x45)
 +0x14 float   progress           (0..1 target fraction; set by msg 0x23; alpha = progress^2 * 255 in UpdateModelColors)
 +0x18 HGrModel backgroundModel   (GrModelDuplicate(sm_whiteRectangleModel); freed w/ assert 0x7c5)
 +0x1c HGrModel foregroundModel   (GrModelDuplicate(sm_whiteRectangleModel); freed w/ assert 0x7c9)
 +0x20 Color4b  tint/flashColor    (default 0xffffffff; bytes read at +0x20/+0x21/+0x22 as B/G/R by UpdateModelColors; set by msg 0x61)
Class-static shared state: DAT_01081a00 = sm_whiteRectangleModel (created msg 5 / freed msg 6); DAT_010819f8/fc = shared render-atlas refcount+handle. Warm-up helpers: FUN_00884c00 = UpdateModelColors (uses +0x08,+0x14,+0x18,+0x1c,+0x20), FUN_00884d00 = UpdateModelTransforms (positions bg/fg quads from frame width, models at [6]/[7]).

- **Message protocol:**

FrameProc(param_1=frame/msgHdr, param_2=payload, param_3=out). switch(param_1[1]=msg):
 case 4  ClassGetBaseProc: *(void**)param_2[3] = &LAB_00618b70 (base template proc).
 case 5  ClassInitialize: build shared sm_whiteRectangleModel (DAT_01081a00) via FUN_0065efa0/FUN_00679730; assert 0x88b if already set.
 case 6  ClassTerminate: free sm_whiteRectangleModel; assert 0x89a if null.
 case 9  Create: assert 0x7d2 if *(payload[2]) already set; alloc 0x24 instance; init fields (+0x04=0.5,+0x05... actually +0x14=1.0,+0x08=0,+0x20=0xffffffff); dup white-rect twice -> bg@0x18/fg@0x1c via FUN_00663e60; store inst at *(payload[2]); FUN_0062f5e0(frame,1)=FrameSetManualFading; warm-ups FUN_00884c00 + FUN_00884d00.
 case 0xb Destroy: free bg (assert 0x7c5) & fg (assert 0x7c9) models; free 0x24 struct; null slot.
 case 0x15 GetInsets/Margins: accessor+zero out param_3[0..3]; assert 0x8af if param_3 null.
 case 0x23 SetProgress: if inst+0x14 != *(float*)param_2 -> write it, then UpdateModelColors.
 case 0x37 Refresh: UpdateModelTransforms.
 case 0x38 Measure/GetSize: param_2[2][0]=*param_2; param_2[2][1]= FUN_0062bfa0()*_DAT_00943280 (~3 device px tall -> the 'slim' height).
 case 0x45 AnimateTick(manual-fade): spring/damp step on +0x08/+0x0c/+0x10 using rate +0x04; UpdateModelColors; CallBase.
 case 0x5e AddContentModels: bit0 -> FrameContentAddModels(frame,1,&bg,0); bit1 -> (...,&fg,1)  (FUN_0062ba80).
 case 0x5f ContentChanged: if (mask&3) UpdateModelTransforms.
 case 0x60 FlashFull: inst+0x08=1.0; UpdateModelColors; FUN_0062ef00(frame,0x45) (post animate to self).
 case 0x61 SetColor: if Color4b at inst+0x20 changed -> write; UpdateModelColors.
 default: FrameMsgCallBase = thunk_FUN_00647170(param_1,param_2,param_3).

- **Create recipe:**

This is an engine control-class FrameProc (proc = 0x00881940), not an immediate painter and not a base template. Registration/dispatch goes through FUN_00884a10/00884a60 (only caller of the proc) via the frame-class factory.
1) Ensure the class is initialized once: msg 5 must have run so sm_whiteRectangleModel (DAT_01081a00) exists BEFORE any create (msg 9 duplicates it twice).
2) Create a child frame with proc=0x00881940 through the create primitive FUN_0062bfc0(parent, flags, childId, 0x00881940, userdata, 0). The engine sends msg 4 (install base &LAB_00618b70) then msg 9 (alloc 0x24 instance, dup bg/fg models, enable manual fading, prime colors+transforms). Defaults: progress(+0x14)=1.0, color(+0x20)=0xffffffff, rate(+0x04)=0.5.
3) Drive it: SetProgress via msg 0x23 (float 0..1); SetColor via msg 0x61 (Color4b); FlashFull via msg 0x60; measure via msg 0x38. The bar renders through two GrModel quads (bg/fg) added to frame content by msg 0x5e and transformed each frame by UpdateModelTransforms; there is NO paint(case1) handler.

- **Crash gotchas:**

- msg 9 blindly GrModelDuplicate(DAT_01081a00): if ClassInitialize(msg 5) never ran, or msg 6 already freed sm_whiteRectangleModel, it duplicates a null handle -> crash/garbage models. Always init class before first create.
- msg 9 asserts 0x7d2 (FUN_00487a80) if the instance slot *(payload[2]) is already non-null -> never double-create on the same frame.
- Accessor FUN_008849e0 asserts 0x7e5 if instance is null; every runtime msg (0x23,0x37,0x38,0x45,0x5e,0x5f,0x60,0x61,0x15) calls it -> sending any of them before msg 9 aborts.
- msg 0x15 asserts 0x8af if out param_3 is null.
- Destroy (0xb) asserts 0x7c5 / 0x7c9 if bg/fg model handles are null -> a partially-constructed instance (create interrupted after alloc, before model dup) will abort on teardown.
- Color at +0x20 is consumed component-wise (bytes +0x20/+0x21/+0x22 as B/G/R) by UpdateModelColors and alpha derived from progress^2; writing a raw ARGB dword in the wrong byte order gives swapped channels.
- Struct is exactly 0x24 bytes and freed as 0x24 (FUN_005acaeb) -> any layout mismatch corrupts the allocator.


### UiCtlProgressStat  (EXE 0x00881e60, confidence: high)

- **WASM:** ram:80f8777f (FrameProc); ram:80f87697 (UiCtlProgressStatProc trampoline)
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlProgress.cpp (EXE string @0x00b964c8; WASM "../../../../Gw/Ui/Controls/UiCtlProgress.cpp" @ram:001092d4). Note: WASM symbol is UiCtlProgressStatProc but both stat + plain progress skins live in UiCtlProgress.cpp. Unique disambiguator string "skin <= UI_CTL_PROGRESS_STAT_SKINS" @0x00b968c8 xref'd only from this proc.
- **Struct layout:**

Instance struct: 0x2C bytes (11 dwords), allocated in case 9. Defaults in ( ):
+0x00 int      hFrame            owning frame id (= *hdr at alloc)
+0x04 float    fillFadeTimer     (0) fade countdown ms; driven by paint (0x45), smoothstep -> alpha
+0x08 int      fillSrcA/size     (0x12=18) default fill-source/size metric
+0x0C HGrModel hFadeModel        (0) fade overlay model; GrModelSetAlpha in paint; freed at 0xb & delete
+0x10 int      fillSrcB/size     (0x12=18)
+0x14 int      field14           (-1) set via msg 0x61 (invalidate 0x20)
+0x18 int      field18           (0)  set via msg 0x62 (invalidate 0x100)
+0x1C int      skin              (9)  UI_CTL_PROGRESS_STAT skin idx; set via msg 100, asserted <=9
+0x20 int      colorId           (8)  COLOR_IDS idx; set via msg 0x65, asserted <=8
+0x24 int      field24           (0)
+0x28 uint     flags             (0)  bit0=msg0x60, bit1=msg99; changes invalidate 0x200
Base/parent proc installed at case 4 = 0x00618b70 (base progress-frame template).

- **Message protocol:**

EXE FrameProc FUN_00881e60(hdr*, wparam(float* / raw), out*) switches on hdr[1]=msg:
- case 4  INSTALL: writes base/parent proc into *(wparam[3]) = &LAB_00618b70 (base CProgressFrame template). Subclass hookup.
- case 5  CLASS_INIT: FUN_008828b0 -> loads shared skin-model table (DAT_01081ae0..DAT_01081d68, 9-dword stride) and refcount DAT_010819f8.
- case 6  CLASS_UNINIT: releases each skin model (FUN_0046f850), decrements DAT_010819f8; asserts FUN_00487a80(0x181) on underflow (double-uninit).
- case 9  ALLOC: asserts 0x9be if *(hdr[2])!=0 (already created); FUN_0047f340("...UiCtlProgress.cpp",0x9bf) allocs 0x2c bytes; inits fields (see struct); stores ptr at *(hdr[2]).
- case 0xb FREE: if inst, frees fade model *(inst+0xc) via FUN_0046f850, then FUN_005acaeb(inst,0x2c); clears *(hdr[2]).
- case 0x15 SIZE/BORDER QUERY: inst=FUN_00884a10; asserts 0xb29 if out(param_3)==null; if FrameTestStyles(frame,0x10000)==0 fills out[0..3] = _DAT_00943278 (uniform border).
- case 0x38 TEXT-HEIGHT SIZE: out[2].x = wparam[0]; out[2].y = FrameGetDefaultTextHeight(frame) + _DAT_009413c8 (+2).
- case 0x45 PAINT: inst=FUN_00884a10; if fadeTimer(inst[1])>0 decrements by dt(*wparam), clamps>=0; when it reaches 0 invalidates 0x30 then base-paints; else runs smoothstep -> GrModelSetAlpha(inst[3]) then base-paints (thunk_FUN_00647170 = FrameMsgCallBase).
- case 0x5e CONTENT_ADD: FUN_00883c30(wparam) (OnSubclassMsgContentAdd).
- case 0x5f INVALIDATE: FrameContentInvalidate(frame, mask built from wparam bits: bit0->0x10,bit1->0x30,bit2->|0x100).
- case 0x60 SET_FLAG_A: inst[10] bit0 = (wparam!=0); if changed invalidate 0x200.
- case 0x61 SET_FIELD@0x14: inst[5]=wparam; invalidate 0x20.
- case 0x62 SET_FIELD@0x18: inst[6]=wparam; invalidate 0x100.
- case 99(0x63) SET_FLAG_B: inst[10] bit1=(wparam!=0); if changed invalidate 0x200.
- case 100(0x64) SET_SKIN: assert 0xcbc if wparam>9 (UI_CTL_PROGRESS_STAT_SKINS); inst[7](+0x1c)=wparam; FUN_008804d0 (BeginFillSourceFade).
- case 0x65 SET_COLORID: assert 0xcc9 if wparam>8 (COLOR_IDS); inst[8](+0x20)=wparam; FUN_008804d0 (BeginFillSourceFade).
- default: thunk_FUN_00647170 (FrameMsgCallBase) -> parent proc.
Instance accessor FUN_00884a10(hdr)=**(hdr+8), asserts 0x9d1 if null. Send-msg helpers: FUN_0062ef40(f,msg,wparam,out) / FUN_0062ef00(f,msg). Invalidate FUN_0062bd80(f,mask). Style read FUN_0062fe20(f,mask).

- **Create recipe:**

Created as a child frame of a parent stat/party frame (observed builder FUN_00517640, a health/energy stat bar).
1) child = FUN_0062bfc0(parentFrame, styleFlags, childOrder, &LAB_00884a70 /*thunk->0x00881e60*/, userdata=0, 0);
   - childOrder observed 4 (primary) and 3 (secondary/second bar variant).
   - styleFlags built from parent style bits; typical base 0x8100 (+0x10000 if style 0x2000, +0x28100 if style 0x200000, |0x40000 if 0x800000, |0x80000 if 0x1000000).
2) FUN_00604aa0(child, 0x800);            // set child flag/layout weight
3) FUN_0062f5a0(child, 0xFFFFFFFF);        // set tint/color (white)
4) Warm-ups (deferred/broadcast sends to the frame tree):
   FUN_0062ef00(parent, 0x45);             // enable paint if bar present
   FUN_0062ef00(parent, 0x10000007);       // deferred class-uninit token
   FUN_0062ef00(parent, 0x10000008);       // deferred class token
   FUN_0062ef00(parent, 0x10000009);       // deferred ALLOC (msg 9) -> creates 0x2C instance
   FUN_0062ef00(parent, 0x10000020);
Lifecycle order that MUST hold: CLASS_INIT(5) [refcounted, first instance] -> ALLOC(9) -> set skin(100)/colorId(0x65)/fields -> PAINT(0x45) each frame -> FREE(0xb) -> CLASS_UNINIT(6) [last instance].
Configure after alloc: send msg 100 (skin 0..9), msg 0x65 (colorId 0..8), msg 0x60/99 (flag bits), msg 0x61/0x62 (fields @0x14/@0x18).

- **Crash gotchas:**

- Instance accessor FUN_00884a10 asserts 0x9d1 (and null-derefs) if any get/set/paint (0x15,0x38,0x45,0x5e-0x65) runs before ALLOC(msg 9). Always alloc first.
- Double-alloc: case 9 asserts 0x9be (FUN_00487a80) if instance already set.
- skin > 9 asserts 0xcbc (UI_CTL_PROGRESS_STAT_SKINS); colorId > 8 asserts 0xcc9 (COLOR_IDS). Both are hard aborts.
- msg 0x15 asserts 0xb29 if the out pointer (param_3) is null.
- Class is refcounted (DAT_010819f8): CLASS_UNINIT(6) beyond zero aborts via FUN_00487a80(0x181). Balance init/uninit; skin-model table must be loaded (msg 5) before first paint or the fade model / skin lookups are invalid.
- Paint fade path calls GrModelSetAlpha on inst+0x0c; if the fade model handle is stale/freed but nonzero, alpha write targets a dead model. Free (0xb) clears it; don't paint after free.
- proc pointer must be the thunk 0x00884a70 (JMP 0x00881e60); base/parent proc 0x00618b70 is auto-installed by case 4 during subclassing — do not register it directly.


### UiCtlBullet  (EXE 0x00884f20, confidence: high)

- **WASM:** ram:8134512b
- **Assertion file:** Bullet control frame proc itself has no direct FUN_0047f340(\"*.cpp\") allocation site (no case 9). Its shared image-list resource is built through FUN_0062d790, which asserts on \"P:\\Code\\Engine\\Frame\\FrApi.cpp\" (lines 0xa47-0xa4e) and tags the object \"HFrameImageList\". The control has no per-instance .cpp assert of its own.
- **Struct layout:**

This control is effectively STATELESS per-instance; it keeps ONE process-global resource, not an allocated instance struct.

msgframe (param_1, undefined4*):
  [0] = frame/target handle  -> passed as *param_1 to dispatcher FUN_0062ef40
  [1] = msg id               -> switch selector

payload (param_2, byte*):
  +0x00        also used as the (payload==0) truth flag for msg 0x5a
  +0x08 (word) = out-slot for msg 0x38 "get": receives 2 floats {_DAT_00940ee4, _DAT_00940ee4+4} = {10.0f, 45.0f}
  +0x0c (word) = base-proc slot; case 4 writes &LAB_00611400 here (payload[3])

out params (param_3, undefined4*): size-query (msg 0x15) receiver:
  [0]=0, [1]=0, [2]=_DAT_00943278 (=2.0f raw), [3]=0

Global shared state:
  DAT_01081d68 = HFrameImageList handle (0 when uncreated). Created by msg 5, freed by msg 6, drawn by msg 0xa.

Global constants (floats):
  _DAT_00943278 = 0x40000000 = 2.0f  (size/thickness reported by 0x15)
  _DAT_00940ee4 = 0x41200000 = 10.0f, +4 = 0x42340000 = 45.0f  (reported by 0x38)

- **Message protocol:**

switch(msgframe[1]):
 case 4  (install base): *(payload+0xc)=&LAB_00611400; then chain base thunk_FUN_00647170.
 case 5  (create/warm-up): if DAT_01081d68!=0 -> FUN_00487a80(0x32) ASSERT(already created); else DAT_01081d68 = FUN_0062d790(2,7,0x12,&DAT_00bf46a0,&DAT_00bf46a8,&DAT_00b96950,2) building an HFrameImageList; then chain base.
 case 6  (destroy): FUN_0046f9b0(DAT_01081d68); DAT_01081d68=0; then chain base.
 case 0xa (10) (PAINT/draw): local{DAT_01081d68,0}; dispatch FUN_0062ef40(*msgframe, 0x59, &local, 0) -> emits the bullet glyph from the image list; then chain base.
 case 0x15 (21) (SIZE-QUERY): out[0]=0,out[1]=0,out[2]=2.0f,out[3]=0; return via base chain (returns directly after thunk).
 case 0x38 (56) (GET metrics): write {10.0f,45.0f} to *(payload+8); RETURN immediately (no base chain).
 case 0x5a (90): dispatch FUN_0062ef40(*msgframe, 0x58, (payload==0), 0); then chain base.
 default / case 7 and any unlisted: fall straight through to base thunk_FUN_00647170(msgframe,payload,out).

Dispatch helper: FUN_0062ef40(frame, subMsg, argptr, out). Base/parent proc = LAB_00611400 (a raw code label, no Ghidra function boundary; the shared UI base template).

- **Create recipe:**

UiCtlBullet is a cosmetic marker frame that paints from a shared image list; it does NOT self-allocate (no case 9/0xb). Recipe:
1. Create the primitive frame with FUN_0062bfc0(parent, flags, child, proc=0x00884f20, userdata, 0) so FUN_00884f20 becomes its FrameProc.
2. The framework sends msg 4 automatically -> control installs base LAB_00611400 into payload[3]. (You must let the base chain run; every non-terminal case falls through to thunk_FUN_00647170.)
3. WARM-UP: send msg 5 EXACTLY ONCE (process-global). This builds the shared HFrameImageList (DAT_01081d68). Guild Wars normally does this once at UI init; a second msg-5 without an intervening msg-6 triggers ASSERT FUN_00487a80(0x32).
4. Sizing: the control is fixed/cosmetic; query with msg 0x15 (reports 2.0f) or msg 0x38 (reports {10.0f,45.0f}). Do not expect it to negotiate a large rect.
5. Paint happens on msg 0xa, which re-emits sub-msg 0x59 with the shared handle. No per-frame data needed beyond a valid DAT_01081d68.
6. Teardown: send msg 6 to free the shared image list (sets DAT_01081d68=0) only when no bullet frames remain.
Ordering: msg 5 must precede any msg 0xa paint that relies on the glyph; otherwise the draw uses a null image handle.

- **Crash gotchas:**

- DOUBLE-CREATE ASSERT: msg 5 while DAT_01081d68!=0 calls FUN_00487a80(0x32) (no-return). The resource is GLOBAL/refcount-free, so two bullet frames both sending msg 5 will assert. Treat msg 5/6 as a singleton owned by UI init, not per-frame.
- USE-AFTER-FREE: msg 6 frees the global and nulls it; any other live bullet frame that paints (msg 0xa) afterwards draws from DAT_01081d68=0. Only free when the last bullet is gone.
- FrApi assert chain: FUN_0062d790 asserts (FrApi.cpp 0xa47-0xa4b) if the size args are degenerate (zero dims or max<min). The hardcoded args (2,7,0x12,...) are valid, so only a corrupted call site trips these.
- msg 0x38 returns WITHOUT chaining to base (early return) and writes 8 bytes to *(payload+8); the caller must pass a buffer with a valid +8 slot or it corrupts adjacent payload memory.
- LAB_00611400 is a bare code label (no function record); do not treat it as an allocatable/instanced base — it is the shared template proc entry the control chains into via thunk_FUN_00647170.


### UiCtlPageTabButton  (EXE 0x00885340, confidence: high)

- **WASM:** ?
- **Assertion file:** P:\Code\Engine\Controls\CtlPage.cpp (inherited; this proc is a sub-control of CtlPage. It has NO own alloc/assert — the allocation + "CtlPage.cpp",599 assert live in the parent proc FUN_0061a950 case 9. FUN_00885340 itself contains no FUN_0047f340 call.)
- **Struct layout:**

This proc allocates NO instance of its own (no case 9). Per-button visual state is read from the frame, not a struct:
  - selected/active flag: obtained by dispatching msg 0x58 to the parent (FUN_0060f4b0 -> CtlPage), returns nonzero when this tab is the selected one.
  - render/interaction flags word (FUN_0064dce0 = *flags & mask): bit 0x10 = dimmed/disabled -> grey label; bit 0x40 = set by this proc during active paint (highlight/draw marker).

Owning CtlPage instance struct (allocated by FUN_0061a950 case 9 via FUN_0047f340("CtlPage.cpp",599)):
  +0x00  uint32 frameId        (copied from msgframe[0])
  +0x04  int32  selectedTabIndex (initialised 0xFFFFFFFF = none)
  ...    (tab list managed by CtlPage msgs 0x59..0x5e)

Global assets used by the button:
  DAT_00b96984 = 0x01021140  texture atlas cell, SELECTED tab icon
  DAT_00b9698c = 0x01021141  texture atlas cell, UNSELECTED tab icon
  DAT_00b9697c               texture cell used by the static sibling FUN_008854f0
  PTR table 0x00b96994 = { 0x008854f0 (static tab proc), 0x00885340 (stateful tab proc) }

- **Message protocol:**

FrameProc signature: void proc(uint* msgframe, byte* payload, uint* out). msgframe[0]=frameId, msgframe[1]=msg, msgframe[2]=payloadPtr, msgframe[5]=proc-chain index. Dispatch to self/other frames via FUN_0062ef40(frame,msg,wparam,out) (asserts msg>=0x56 for control-specific). Handled cases:

- case 1 (paint pass 1 / bg): NO-OP early return. Deliberately suppresses the generic frame-background paint; all custom drawing is done in 8 and 0x5f.

- case 8 (icon/glyph paint): if (payload[0] & 1): queries selected-state via FUN_0060f4b0(frameId) (= dispatch msg 0x58 -> parent CtlPage). Picks texture DAT_00b96984 (0x01021140, SELECTED) when state!=0 else DAT_00b9698c (0x01021141, UNSELECTED). Draws a 32x32 atlas cell at payload+0x1c via FUN_0062b8e0(frameId, payload+0x1c, tex, &{w=0x20,h=0x20}, 7, 0,0,0). Payload layout for msg 8: [+0] byte flags (bit0=draw-enable), [+0x1c] int32 destX, [+0x20] int32 destY.

- case 0x15 (size query): writes 4 dwords to out[0..3] = preferred/min box. out[0]=_DAT_009407c8 (w), out[1]=height (_DAT_00943278 selected / _DAT_0093c89c unselected), out[2]=_DAT_009407c8, out[3]=(_DAT_009413f4 selected / _DAT_00945190 unselected). Size depends on selected state.

- case 0x5f (95, label paint, control-specific >=0x56): computes color from render-flags — FUN_0062e2a0(frameId) tests draw-flag 0x10: if flag SET -> color=0xffa0a0a0 (grey/dimmed); else FUN_0062e320(frameId) SETS draw-flag 0x40 and color=0xffffffff (white). Then FUN_0062bb30(frameId, payload[+0], payload[+4], payload+8, payload[+0x18], 0xffffffff, (payload[+0x1c] | 0x40), color, payload[+0x24], payload[+0x28], 6) renders the label text run. Payload layout for 0x5f: [+0] dw, [+4] dw, [+8] text/rect struct, [+0x18] dw, [+0x1c] style flags (OR'd with 0x40), [+0x24] dw, [+0x28] dw.

- default: thunk_FUN_00647170(msgframe,payload,out) walks the frame's inherited proc-chain (array @ base+0xa8, count @ base+0xb0), so create(9)/destroy(0xb)/base-install(4) and ALL tab-management ops (0x56=get,0x57=select-off,0x58=select-on/query,0x59..0x5e) are serviced by the parent CtlPage proc FUN_0061a950.

Sibling static variant FUN_008854f0 handles only 8 (single texture DAT_00b9697c, no state) and 0x15; no 0x5f label, no selected/unselected switch.

- **Create recipe:**

Not user-constructed standalone — it is instantiated internally as a child of a CtlPage tab strip. Proc chain (leaf->root): [game-layer menu FUN_008daa40] -> UiCtlPageTabButton FUN_00885340 -> base button/frame template installed by the chain -> CtlPage FUN_0061a950.

To reproduce the container that spawns these buttons:
1. Create the CtlPage frame with proc FUN_0061a950 (via the create primitive FUN_0062bfc0(parent,flags,child,proc,userdata,0)). On msg 4 it self-installs its base proc FUN_006123a0 into *(payload+0xc); on msg 9 it allocs its instance (asserts *slot==0 first) and chains to base.
2. The page builds its tab strip children using the descriptor selected by FUN_00885590 (msg 0x5e): PTR_FUN_00b96994 -> {static FUN_008854f0, stateful FUN_00885340}. Each tab child frame carries FUN_00885340 as its custom paint proc.
3. Warm-ups / ordering: tab buttons must be children of a CtlPage that answers msg 0x58 (selected-state) and the tab-management msgs 0x59..0x5e, otherwise the icon/label state queries return garbage. Add tabs via CtlPage msg 0x5d (FUN_0061b520); switch selection via 0x57/0x58.
4. Sizing: icon is fixed 32x32 (atlas cell); overall button box comes from msg 0x15 (differs selected vs unselected). No manual size needed — the layout engine queries 0x15.

- **Crash gotchas:**

- FUN_0062b8e0 (case 8 icon draw) hard-asserts (FUN_00487a80) on: frameId==0 (0xe7a), atlas subpass>9 (0xe7b), atlas w not power-of-two (0xe7c), atlas h not power-of-two (0xe7d), w<h (0xe7e), texture ptr==0 (0xe7f). The DAT_00b96984/8c texture handles must be valid & loaded (loaded by the CtlPage owner) or the icon draw aborts the process.
- FUN_0062bb30 (case 0x5f label) asserts frameId==0 (0xcf8) and payload/text-buffer==0 (0xcf9).
- FUN_0062ef40 (all >=0x56 dispatches incl. the 0x58 selected-state query) asserts frame==0 (0xf2e) and msg<0x56 (0xf2f). Sending a control-specific msg below 0x56 through it crashes.
- This proc has no case 9/0xb, so it MUST be chained under a parent that allocates/frees the CtlPage instance; installing it as a standalone top-level proc means msg 0x58 falls through with no CtlPage to answer -> selected-state read is undefined and the tab renders wrong (not a crash, but visually broken). The parent CtlPage case 9 asserts 0x256 if its instance slot is already non-zero (double-create) and 0x25b on destroy if slot already zero (double-free).
- case 1 intentionally returns nothing; do not assume it paints — it suppresses the default background.


### UiCtlPageItemProc  (EXE 0x00885340, confidence: high)

- **WASM:** ram:80e09277
- **Assertion file:** No own TU assertion (stateless leaf: no case 4 base-install, no case 9 alloc, so it never calls FUN_0047f340). It belongs to the styled UiCtl page-tab family; the owning page container asserts under P:\Code\Engine\Controls\CtlPage.cpp. WASM symbol: IUi::UiCtlPageItemProc(FrameMsgHdr const&, void const*, void*).
- **Struct layout:**

NO per-instance struct of its own. This proc allocates nothing and stores no state on the frame; it is a pure paint/layout/measure leaf for one page (tab) item. All data arrives in the message payload param_2 (the FrameMsgContent for the item) plus the parent CtlPage instance queried via msg 0x58.

Message payload (param_2) fields actually read:
  +0x00 dword  flags     (case 8 gates image draw on bit0; case 1 unused)
  +0x04 dword  text/id param   (forwarded to FrameContentAddText in case 0x5f)
  +0x08        text/label content ptr (case 0x5f)
  +0x18 dword  text param (case 0x5f)
  +0x1c        case 8: image handle (HGrModel/atlas cell) passed to AddImageTemplate; case 0x5f: text-style flags, OR'd with 0x40
  +0x24, +0x28 extra text params (case 0x5f)

Style/resource globals used (must be resident):
  &DAT_00b96984 -> 0x01021140  active/selected tab image template (9-slice descriptor)
  &DAT_00b9698c -> 0x01021141  normal/inactive tab image template
  case 0x15 size floats: _DAT_009407c8 (common), active {_DAT_0093c89c,_DAT_00945190} vs inactive {_DAT_00943278,_DAT_009413f4}

- **Message protocol:**

FrameProc FUN_00885340(hdr* param_1, content* param_2, out* param_3); msg = param_1[1]; frame handle = *param_1. switch(msg):
 case 1  (paint root pass): no-op return. Actual pixels come from the content templates queued in case 8 / 0x5f.
 case 8  (build image content): if (param_2[0] & 1): rect = 32x32 (local_c=local_8=0x20); active = FUN_0060f4b0(frame) which sends msg 0x58 to self/parent to read selected state; template = &DAT_00b96984 (active) else &DAT_00b9698c (inactive); FrameContentAddImageTemplate FUN_0062b8e0(frame, imageHandle=param_2+0x1c, template, &rect, layer=7, 0,0,0). This paints the tab button background/icon.
 case 0x15 (OnFrameSizeQuery): writes Rect4f into param_3 (out[0..3]); dimensions depend on active state from FUN_0060f4b0 (selected tab measures differently). The page auto-sizes each item from this.
 case 0x5f (build text/label content): color = 0xffa0a0a0 (dimmed) if FUN_0062e2a0(frame)==0 (not focused), else FUN_0062e320(frame) + 0xffffffff (white); FrameContentAddText FUN_0062bb30(frame, param_2[0], param_2[1], text=param_2+8, param_2+0x18, 0xffffffff, flags=(param_2+0x1c)|0x40, color, param_2+0x24, param_2+0x28, layer=6).
 default: thunk_FUN_00647170(param_1,param_2,param_3) -> base-proc chain walker -> parent CtlPage / frame base (handles create/free/hit-test/layout msgs 4,9,0xb,0x37,0x38,0x58,etc.).
Note active-state query uses dispatcher FUN_0062ef40(frame,0x58,0,&out); the parent CtlPage must supply msg 0x58 (selected-index/per-item state) for the active vs inactive art to be correct.

- **Create recipe:**

Not created standalone and has NO Create entry point. It is installed automatically as the per-item painter by the styled page wrapper UiCtlPageProc (FUN_00885590): that wrapper's msg 0x5e metrics/config table PTR_FUN_00b96994 carries entry[1] = 0x00885340 (this proc) and entry[0]=0x008854f0. When the CtlPage container adds a page/tab item (AddTab -> CtlPage::OnCtlAddItem, CtlPage.cpp), the container spawns a child frame per item and uses this table's proc to paint/measure each item.

To obtain it in practice:
 1. Create the tabs container: base CtlPageProc FUN_0061a950 (flags 0x300/0x40000, resolved via assertion "!IsBtnCode(pageCode)" in CtlPage.cpp).
 2. Layer the styled wrapper UiCtlPageProc FUN_00885590 as PRIMARY proc (its case 4 sets base=FUN_0061a950; its case 0x5e returns the styled config table that carries this item proc). Do this BEFORE AddTab (post-create FrameNewSubclass crashes, msg 4 is only sent at create).
 3. AddTab/AddItem each tab -> each gets a UiCtlPageItem child painted by 0x00885340 automatically. Active vs inactive art comes from image templates 0x01021140 / 0x01021141; ensure the tab atlas is loaded.
Do NOT FrameSetSize the container or hand-position items; CtlPage self-lays-out on 0x37/0x38 using this item's 0x15 size query.

- **Crash gotchas:**

- Stateless: it never allocates (no case 9) and never asserts on its own, so it has no double-create abort of its own.
- MUST run under a CtlPage base chain: it queries selected/active state with msg 0x58 (FUN_0060f4b0 -> FUN_0062ef40). If installed as a bare primary proc on a frame without the CtlPage parent, msg 0x58 returns garbage/0 and every tab paints with the inactive template (and mis-measures on 0x15).
- Payload trust: case 8 dereferences param_2+0x1c as an image handle whenever param_2[0]&1 is set; a malformed/short content payload makes FrameContentAddImageTemplate consume a bogus handle. case 0x5f reads text ptr at +0x08 and params up to +0x28 - undersized payloads read OOB.
- Resource dependency: image templates 0x01021140 (active) / 0x01021141 (inactive) and the size-float globals must be initialized (tab UI atlas loaded); otherwise tabs render blank/untextured or with zero size.
- Do not intercept/replace msg 0x5e on the wrapper without preserving entry[1]=0x00885340, or items lose their painter.


### UiCtlFade (IUi::Controls::CCtlFade / TCtlInstance<CCtlFade>)  (EXE 0x008858c0, confidence: high)

- **WASM:** ram:80dffca4 (IUi::UiCtlFadeProc) -> ram:80dffd8c (TCtlInstance<CCtlFade>::MsgProc)
- **Assertion file:** P:\Code\Engine\Controls\CtlInstance.h (shared template header, line 0xaf; CCtlFade has NO dedicated CtlFade.cpp/UiCtlFade.cpp string in either binary)
- **Struct layout:**

Instance object = 0x20 (32) bytes, allocated in case 9 via FUN_0047f340("...\Engine\Controls\CtlInstance.h",0xaf), freed in case 0xb via FUN_005acaeb(obj,0x20). Reached by double-indirection: msgframe payload param_1[2] holds a pointer slot; *(param_1[2]) = objPtr.
  +0x00  void* vtable        = &PTR_FUN_009404a4 (-> 0x004a0430); re-stamped twice in ctor
  +0x04  uint  frameId       (host frame id; set from *param_1 during case 9)
  +0x08  CCtlLayout m_layout  (~24 bytes; ctor via vfunc (**(code**)*obj)(obj+2); FUN_006017e0 ctor, FUN_00601810 dtor; SetFrameId=FUN_00602020, Size=FUN_00602060, SizeQuery=FUN_00602900)
Instance accessor (WASM ::Ptr) = FUN_004a0440(msgframe) — asserts obj != null (CtlInstance.h lines 0x2b/0x2c).
Semantic constants: _DAT_00949018 = 0x3f333333 = 0.7f (idle/dimmed opacity); 0x3f800000 = 1.0f (active opacity); _DAT_00940ea8 = 0x3e4ccccd = 0.2f (fade duration seconds).

- **Message protocol:**

FrameProc(param_1=msgframe, param_2=payload, param_3=out); dispatch = switch(param_1[1] = msg). Tail of every path calls thunk_FUN_00647170 = FrameMsgCallBase (chain to base/host proc).
- case 9 (CREATE/attach): assert *(param_1[2])==0 (else FUN_00487a80(0xae)); alloc 32B instance; stamp vtable 0x009404a4; layout ctor FUN_006017e0; store obj into *(param_1[2]); verify Ptr(FUN_004a0440)==obj else assert 0xb1; frameId = *param_1; FUN_00602020(frameId) (layout SetFrameId); FUN_0062f6c0(frameId, 0.7f) = FrameSetOpacity to idle 0.7; FUN_0062ef00(frameId, 0x4e) = FrameMsgRegister — SUBSCRIBE to global msg 0x4e; call layout init vfunc; base.
- case 0xb (DESTROY): Ptr; layout dtor FUN_00601810 + free(obj,0x20) via FUN_005acaeb; *(param_1[2])=0; base.
- case 0x37 (SIZE/PLACE): reads rect from payload[2..5] into local_14/10/c/8; FUN_00602060(&rect) = CCtlLayout::Size; base.
- case 0x38 (SIZE-QUERY): FUN_00602900(&local_c, payload) computes preferred (w,h); writes to *(float*)payload[2]; returns without base if size non-zero.
- case 0x4e (FADE TICK / focus-changed notification — the reason it registers 0x4e): payload = (oldFocusFrame=*param_2, newFocusFrame=param_2[1]); iVar6=FUN_0062e200(frameId, old), iVar7=FUN_0062e200(frameId, new) (FrameIsAncestorOf-style: is this control an ancestor of old/new focus). If iVar6!=iVar7 (focus crossed this subtree): if now leaving (iVar6==0) FUN_0062cb00(frameId, 1.0f, 0.7f, 0.2, 0) fade OUT to dim; else FUN_0062cb00(frameId, 0.7f, 1.0f, 0.2, 0) fade IN to full. FUN_0062cb00(frame, srcOpacity, tgtOpacity, seconds, flags) = opacity animator (IFrame::CContent::Fade). base.
- cases {1,3,7,8,0xa,0xc,0xf,0x13,0x15,0x20,0x24-0x2a,0x2c,0x2e,0x31,0x32,0x34-0x36,0x3a-0x3f,0x44-0x46,0x4b,0x4c,0x4f,0x52}: touch instance (FUN_004a0440 assert-exists) then FUN_004a0440 + base (pass-through, keep instance alive).
- cases 4,5,6: no-op then base (base-install handled by host/primary proc, since Fade is a SECONDARY handler).
- default: assert instance/slot non-null (FUN_00487a80(0x149)/(0x2c)); base.
NOTE: message enum numbering (0x4e etc.) is stable between the WASM and EXE builds here (verified: both register 0x4e), but treat other numeric msg ids as build-specific.

- **Create recipe:**

This is an OVERLAY / behavior proc, NOT created standalone. It is layered onto an existing frame as a secondary message handler:
1. Create/have a host frame: e.g. FUN_0062bfc0(parent, flags, childOrder, hostProc, userdata, L"Name") (create primitive).
2. Attach the fade behavior: FUN_0062f150(hostFrame, &LAB_00885c20 /*fade proc thunk -> 0x008858c0*/, 0). FUN_0062f150 = add-secondary-msg-handler(frame, proc, priority). This triggers case 9 on the fade proc, which self-registers msg 0x4e and sets idle opacity 0.7f.
3. From then on the host frame renders at 0.7 opacity when the mouse/focus is outside its subtree and animates to 1.0 (0.2s) when focus enters, and back out when it leaves — driven entirely by the global 0x4e focus-changed broadcast.
Confirmed create sites: FUN_00858340 (attaches to the "HideUi" action/login bar frame) and FUN_0055b240. Both use FUN_0062f150(frame,&LAB_00885c20,0).
To reproduce from Py4GW: pick a real frame id, then send the control-create/attach message that maps to FUN_0062f150 with this proc thunk (0x00885c20) at priority 0; do NOT try to instantiate it as a top-level control (it has no user-visible geometry of its own — SizeQuery/Size just mirror the host via CCtlLayout).

- **Crash gotchas:**

- Re-attach without destroy: case 9 asserts *(param_1[2])==0 first (FUN_00487a80(0xae)); attaching the fade proc twice to the same frame slot aborts the process.
- Post-alloc identity check: after alloc it re-reads Ptr and asserts it equals the freshly allocated obj (FUN_00487a80(0xb1)); a corrupted/mismatched instance slot hard-aborts.
- Any message other than 9 that reaches the proc before case 9 ran (obj==null in the slot) hits the default/Ptr assertions (FUN_00487a80(0x149)/(0x2c) and CtlInstance.h 0x2b/0x2c) — order matters: the frame's primary proc must have created the payload slot before Fade is attached.
- Must forward to base: every branch tail-calls FrameMsgCallBase (thunk_FUN_00647170). If you reimplement/hook this proc and swallow messages, the host frame's real proc never runs (broken layout/paint/free -> leaks or use-after-free on 0xb).
- It relies on the global 0x4e (focus/mouse-target changed) broadcast; it only animates on state transitions (iVar6!=iVar7). If 0x4e is not delivered (control not registered, or frame detached from the tree so FUN_0062e200 ancestor test is meaningless) the opacity stays frozen at 0.7 — looks like a "stuck dim" bug, not a crash.
- Frees exactly 0x20 (32) bytes on case 0xb; the 0xaf passed to the allocator is the CtlInstance.h __LINE__, not the size — don't mistake it for the struct size.


### UiCtlHideUi  (EXE 0x00885c30, confidence: high)

- **WASM:** ? (not resolved from WASM; identity confirmed via EXE create-site name string)
- **Assertion file:** P:\Code\Engine\Controls\CtlInstance.h (generic CtlInstance allocator; no dedicated CtlHideUi.cpp assert — this control reuses the base instance template)
- **Struct layout:**

Instance = 0xAF (175) bytes, generic CtlInstance template (FUN_0047f340("CtlInstance.h",0xAF)); freed via FUN_005acaeb(inst,0x28) [0x28 = dtor vtable-dispatch selector, not size].
+0x00 dw[0]: vtable = &PTR_FUN_009404a4
+0x04 dw[1]: owning frame handle (set from *msgframe; used everywhere as *(inst+4))
+0x08..+0x1F: base CtlInstance fields (initialized by FUN_006017e0; child/render bookkeeping)
+0x20 dw[8]: secondary flag, init 0
+0x24 dw[9]: hide-state flag, init 1 (1 = UI visible/not-hidden; 0 = UI currently hidden). Toggled in case 0x45; forced back to 1 on destroy(0xB).
+0x28..+0xAE: base template render/child-frame state (compass/options-button glyph state drawn by parent FUN_00877e60).
Global singleton: DAT_01081d6c = current HideUi instance (only one allowed; enforced in case 9 create & 0xB destroy).

- **Message protocol:**

FrameProc FUN_00885c30(msgframe param_1, payload param_2, param_3); switches on param_1[1]=msg. Instance resolved via FUN_004a0440(param_1) = **(msgframe[2]); base/parent proc = FUN_00877e60.

- Pass-through group {1,3,7,8,0xA,0xC,0xF,0x13,0x15,0x20,0x24-0x2A,0x2C,0x2E,0x31,0x34,0x35,0x36,0x3A,0x3C-0x3F,0x44,0x46,0x4B,0x4C,0x4E,0x4F,0x52}: resolve instance then forward to base (thunk_FUN_00647170). msg 1 = paint, 0x15 = size-query (both handled by base FUN_00877e60).
- default: null/zero-instance asserts (0x149 / 0x2C). If msg==0x57 -> FUN_00886290(payload): enable(nonzero)/disable(0) the 5 global hotkeys + show/hide render. Then forward.
- case 4 (install parent proc): *(payload[3]) = FUN_00877e60 (base template); OR style bit 0x10000 into *(payload[1]); forward+return.
- case 5,6 (class init/deinit): no-op, forward.
- case 9 (create): assert *(msgframe[2])==0 (0xAE) else abort; alloc 0xAF bytes via FUN_0047f340("CtlInstance.h",0xAF); vtbl=&PTR_FUN_009404a4; FUN_006017e0() base ctor; set +0x24=1, +0x20=0; store instance; verify FUN_004a0440==inst (0xB1); +0x04=frame(*param_1); FUN_00602020(frame); release prior singleton (FUN_0062c550(DAT_01081d6c[1])) and set DAT_01081d6c=inst; FUN_0060fdf0(frame, FUN_007c3bc0(0xC551)) install render blob; call vtbl[0](inst+2).
- case 0xB (destroy): get inst; if +0x24!=1 set +0x24=1 and re-enable UI (thunk_FUN_006351e0(1)/thunk_FUN_006383e0(1)); unregister 5 hotkeys FUN_00626800(key,&LAB_00886210) keys {0x20,0x1E,0x1A,0x0E,0x0D}; assert DAT_01081d6c==inst (0xF8); clear singleton; FUN_00601810()+FUN_005acaeb(inst,0x28) free; clear *(msgframe[2]).
- case 0x32 (visibility change; payload[2]): ==8 SHOWN -> register 5 hotkeys FUN_00626590(key,&LAB_00886210,1), FUN_00630080(frame,1,1.0f), forward. ==9 HIDDEN -> FUN_0062f0d0(frame,0x45), reset render (FUN_0060fdf0 w/ 0xC551), unregister 5 hotkeys, forward. else fall through to forward.
- case 0x37 (move/rect): FUN_00602060(&rect) with rect={payload[2],payload[3],payload[4]f,payload[5]f}; forward.
- case 0x38 (hit-test/measure): forward first, FUN_00602900(&out,payload), write out floats to *(payload[2]).
- case 0x3B (=59, activate/hover FX): assert *payload==1 (0x10E); if FUN_0060f4b0(frame) build tinted render (tex &DAT_0094B0DC via FUN_007c4060/FUN_007c3f30) then FUN_0062ef00(frame,0x45).
- case 0x45 (=69, TOGGLE HIDE-UI — the action): FUN_004b12b0(*payload,&flt); optional tinted render if flt!=0; if FUN_004b1380()>=0: set frame render, and if +0x24!=0 -> set +0x24=0 and HIDE UI (thunk_FUN_006351e0(0)/thunk_FUN_006383e0(0)), forward+return; else forward.
- LAB_00886210 = shared hotkey callback for keys {0x20,0x1E,0x1A,0x0E,0x0D} (drives the toggle path).

- **Create recipe:**

Canonical create is inside FUN_00858340 (bottom-bar assembly), NOT a raw FUN_0062bfc0 call by consumers:
1. handle = FUN_0062bfc0(parent, flags=0, childOrder=1, proc=&LAB_00886360 [tail-JMP to 0x00885c30], userdata=0, name=L"HideUi").
2. FUN_0062f150(handle, &LAB_00885c20, 0)  // register msg-handler variant slot 0
3. FUN_0062f150(handle, FUN_00879090, 4)   // register msg-handler variant slot 4
4. FUN_0062f5a0(handle, 1)                  // enable/visibility flag
5. if FUN_0049b9e0(0x14): FUN_0060f490(handle, 1)  // conditional feature toggle
The frame proc self-bootstraps its instance on msg 9 (no manual alloc): it allocs 0xAF, wires vtable &PTR_FUN_009404a4, installs base parent FUN_00877e60 on msg 4, registers itself as global DAT_01081d6c, and warms render via FUN_0060fdf0(frame, FUN_007c3bc0(0xC551)). A parent variant (FUN_0055b240 case 9) instead creates it as a child: FUN_0062bfc0(parentFrame, 0x300, 1, &LAB_00886360, 0, 0) after FUN_0062f150(...,FUN_00879090,4) and FUN_0062f150(...,&LAB_00885c20,0). Flags of 0x10300/0x300 seen for embedded-child instances; top-level bottom-bar uses flags=0.
Sizing/paint is delegated: msg 4 installs FUN_00877e60 which answers msg 1 (paint of the button glyph) and msg 0x15 (size-query, reads DAT_00bf4518.. rects). Warm-ups: on show (msg 0x32==8) it registers 5 global hotkeys and calls FUN_00630080(frame,1,1.0f) to fade in.

- **Crash gotchas:**

- Singleton-enforced: create (msg 9) aborts (FUN_00487a80(0xAE)) if *(msgframe[2]) already non-null; destroy (msg 0xB) aborts (0xF8) if DAT_01081d6c != this instance. Do NOT instantiate two HideUi controls; releasing an old one before creating a new is done via FUN_0062c550(DAT_01081d6c[1]).
- Instance-null / zero-vtable asserts in default path: 0x149 and 0x2C fire if payload references a freed/zero instance — never dispatch control-specific msgs (0x31/0x37/0x38/0x3B/0x45/0x57) before msg 9 create completes.
- Hotkey balance: keys {0x20,0x1E,0x1A,0x0E,0x0D} are registered (FUN_00626590/FUN_00626800 with &LAB_00886210) on show(0x32==8)/enable(0x57) and MUST be unregistered on hide(0x32==9)/disable/destroy(0xB); leaking them leaves dangling callbacks into a freed instance.
- Msg 0x3B asserts *payload==1 (0x10E) — wrong payload word aborts.
- The registered proc is the tail-JMP thunk LAB_00886360 (JMP 0x00885c30); hooking must target the thunk, not only the body.
- +0x24 hide-flag is authoritative for the game-wide UI-hidden state (drives thunk_FUN_006351e0/thunk_FUN_006383e0); force it back to 1 (UI visible) if you tear the control down while UI is hidden, or the client stays with UI suppressed.
- Free uses FUN_005acaeb(inst,0x28) after FUN_00601810(); calling C free() on the 0xAF block directly skips vtable dtor and the singleton clear.


### UiCtlBtnToggle  (EXE 0x00886370, confidence: high)

- **WASM:** ram:816b67fd
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlBtnToggle.cpp
- **Struct layout:**

Two distinct instance structs exist because UiCtlBtnToggle is a thin overlay proc chained on top of the base button proc; each proc in the chain owns its own instance slot addressed by msgframe[2] (piVar2 = *(msgframe[2])).

TOGGLE OVERLAY INSTANCE (this proc, allocated case 9, size 0x18 / freed as 0x18 via FUN_005acaeb(p,0x18)) = an icon-pair descriptor:
  +0x00 u32  icon0.texHandle   (unchecked-state icon; = FUN_0046fda0(desc0[0]) ref/copy of texture id)
  +0x04 u32  icon0.field1      (desc0[1]; atlas/frame index, e.g. u or width)
  +0x08 u32  icon0.field2      (desc0[2]; atlas/frame index, e.g. v or height)
  +0x0c u32  icon1.texHandle   (checked-state icon; = FUN_0046fda0(desc1[0]))
  +0x10 u32  icon1.field1      (desc1[1])
  +0x14 u32  icon1.field2      (desc1[2])
  (Paint picks icon0 vs icon1 by the checked flag returned from base msg 0x58; when checked it reads +0x04/+0x14 pair, when unchecked +0x08/+0x10 pair — the two 'field' slots are the frame indices for the two draw sub-quads.)

BASE BUTTON INSTANCE (parent proc FUN_0060f4f0, allocated by its case 9 = FUN_006102b0, size 0x2c / freed as 0x2c) — separate slot, owns the real button state:
  +0x04 u32  label glyph buffer ptr (freed via FUN_0047f3a0)
  +0x08 u32  label buffer capacity/len
  +0x0c u32  label glyph count / cursor
  +0x14 u32  cached layout width (init 0xffffffff = dirty)
  +0x18 u32  tooltip/label texture handle (freed via FUN_0046f850)
  +0x1c ptr  callback/context set by msg 0x5a
  +0x24 f32  override width  (msg 0x13 min-size / 0x5e)
  +0x28 f32  override height
State bits live in the frame's own style word (accessed as *puVar3 in base proc): bit0 = checked/pressed-latch (toggled by 0x57), bit1 = pushed (0x3b/0x5d), bit2 = highlight/hover-toggle (0x24/0x2c/0x2e/0x56), bit3 area. Frame style flag 0x10000 = "is toggle/checkbox", 0x20000 = radio-group mutual-exclusion, 0x1000000 = "draw custom icon" (read by toggle paint case 1 via FUN_0062fe20(frame,0x1000000)).

- **Message protocol:**

FrameProc(param_1=msgframe, param_2=payload/float*, param_3=out). Switch on msgframe[1]=msg. Instance = *(int*)msgframe[2]. Unhandled -> thunk_FUN_00647170 (forward to parent chain).

Handled directly by UiCtlBtnToggle (0x00886370):
- case 1  PAINT: no-op unless *param_2 (sub-pass)!=0. Draws the checkbox icon only when sub-pass==1 (*param_2==1) AND param_2[6]==4 (layer/quad tag). Reads style 0x1000000 (custom-icon flag). Calls FUN_0060f4b0(frame) -> sends base msg 0x58 to get checked state, selects icon0(unchecked)/icon1(checked). If no custom-icon style set: draws two sub-quads (bg at param_2[2..5], then icon offset by param_2[4]*ui_scale) via FUN_0062b290(frame,rect,texHandle,frameIdx,5,0). If custom-icon: single FUN_0062b290 with param_2[7] color.
- case 4  INSTALL BASE: forces frame style |= 0x10000 (toggle) and &= ~0x40000; installs parent proc *(payload[3]) = FUN_0060f4f0 (base button proc); zeroes payload[4], payload[5].
- case 9  CREATE: instance = FUN_0047f340("...UiCtlBtnToggle.cpp",0x57) (debug alloc, 0x18-byte icon-pair). Reads create-params *payload = ptr to {desc0*, desc1*}; each descN = {texId, field1, field2}; copies via FUN_0046fda0(texId) into the two icon triples. Either desc may be NULL.
- case 0xb DESTROY: FUN_0046f9b0(icon0.tex); FUN_0046f9b0(icon1.tex); FUN_005acaeb(instance,0x18).
- case 0x38 GET-PREFERRED-SIZE: s = FUN_0062d0e0(frame)*ui_scale; writes {2*s, s} to *(param_2[2]).
- case 0x60 GET-DEFAULT/MIN-SIZE: s = FUN_0062d0e0(frame)*ui_scale; param_3[0]=s, param_3[1]=2*s, param_3[2]=0, param_3[8]=1 (flag).

Delegated to base button proc FUN_0060f4f0 (the real checkbox/button behaviour):
- 0x4/0x9/0xb its own base install (parent=FUN_006123a0 base control) / 0x2c-byte instance / free
- 0x13 min-size query   0x15 metrics/color query   0x20 click action
- 0x24 mouse-up (toggle highlight bit2, radio via 0x20000)  0x2c drag/enter  0x2e mouse-leave
- 0x38 label size  0x39/0x3a/0x3b text edit/caret  0x4c relayout
- 0x56 PRESS (activate)   0x57 SET-CHECKED (xor bit0, invalidate)   0x58 GET-CHECKED (out=bit0)
- 0x59 GET-HIGHLIGHT (out=bit2)   0x5a set callback ctx   0x5b set label text (FUN_0046fda0)
- 0x5c set glyph buffer   0x5d set pushed/latched   0x5e set override size   0x5f draw label text
Base default -> FUN_006123a0.

- **Create recipe:**

Create through the standard control-create primitive and let the proc self-configure:

1) proc = FUN_00886370 (UiCtlBtnToggle FrameProc).
2) FUN_0062bfc0(parent, flags, childId, proc=FUN_00886370, userdata, 0). Style bit 0x10000 (toggle) is force-set by the proc's case 4, so it need not be in `flags`; add 0x20000 in flags if you want radio-button mutual-exclusion within a group, and 0x1000000 if you will supply a custom single icon rather than the default 2-quad checkbox glyph.
3) On creation the framework sends, in order: msg 4 (install base -> installs FUN_0060f4f0, then that installs FUN_006123a0) then msg 9 (create). For msg 9 supply payload[0] -> a {desc0*, desc1*} pair where descN = {textureId:u32, frameIdx1:u32, frameIdx2:u32}; desc0 = unchecked icon, desc1 = checked icon. Either may be NULL to skip.
4) Label: after create send base msg 0x5b with a wide-string ptr to set caption (or 0x5c for a preallocated glyph buffer). Optional callback context via 0x5a.
5) Initial state: send 0x57 to toggle checked on; query with 0x58. For radio behaviour set style 0x20000 so 0x24/0x2c auto-clear siblings.
6) Sizing: the control self-reports size via 0x38 (preferred {2s,s}) and 0x60 (default {s,2s}) where s = FUN_0062d0e0(frame)*ui_scale (font line metric * global UI scale); you normally do not set an explicit size. Use 0x5e / +0x24/+0x28 only to override.

Warm-ups: none required beyond the automatic 4->9 sequence; the proc asserts-free path expects msg 9 to run once (it does not itself assert-if-already-set, but the base proc's create does).

- **Crash gotchas:**

- Instance size mismatch: case 9 debug-alloc call shows FUN_0047f340("...UiCtlBtnToggle.cpp",0x57) but the live struct is 0x18 bytes (case 0xb frees exactly 0x18 and only offsets 0..0x17 are written); treat 0x18 as the real size. Do NOT free with a different size or you corrupt the pool.
- Paint reads *(msgframe[2]) as the icon-pair; if you skip msg 9 (no create) this is NULL and the case-1 paint dereferences *piVar2 -> crash. Always let the 4->9 create sequence complete before the frame is painted.
- Paint gates on *param_2!=0, param_2[6]==4 and *param_2==1: calling paint with a malformed float payload silently draws nothing (not a crash, but a 'why is my checkbox invisible' trap).
- FUN_0046fda0 in case 9 ref-copies the texture id; case 0xb releases both via FUN_0046f9b0. Passing a raw/borrowed texture handle you also free elsewhere = double-free.
- The checked/highlight/pushed state lives in the FRAME style word bits (bit0/bit2/bit1), not in the 0x18 icon struct. Writing those bits directly instead of via msgs 0x57/0x56 skips FUN_0062bd40/FUN_0062f470 invalidation, so the visual won't refresh.
- Style 0x40000 is force-cleared by case 4; setting it in create flags is pointless (it will be stripped) and may indicate you meant a different button subclass.
- ui_scale/line-metric globals (_DAT_00948c18, _DAT_009407b0) are runtime-initialized (read 0 in the static image); sizing math only works on a live, initialized UI — computing size offline yields 0.


### UiCtlUrl  (EXE 0x00886690, confidence: high)

- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlUrl.cpp (string @ 0x00b96b28); base layer P:\Code\Engine\Controls\CtlTextBtn.cpp (alloc in FUN_00616c00 case 9). Note the unrelated Base\Services\Url.cpp @0x00a46be4 is a different subsystem, NOT this control.
- **Struct layout:**

UiCtlUrl's OWN per-layer instance = a single dword at *(msgframe[2]): 
  +0x00 urlIndex (uint 0..25) — selects both the visible label (DAT_00b96a5c[idx]) and the URL opened on click (DAT_00b96a58[idx]).

Underlying CtlTextBtn instance (0xa9=169 bytes, FUN_0047f340, in the base layer's slot):
  +0x00 stateFlags   (bit0 = pressed/active; toggled by base msgs 0x20/0x22/0x24/0x2c/0x2e/0x56)
  +0x04 wchar* textBuffer (caption)
  +0x08 textCapacity (dword)
  +0x0C textLength   (chars)
  +0x10 growGranularity = 0x80
  +0x14 selection/caret index (0xffffffff = none)
  +0x18 normalColor  (default 0xff64beeb)
  +0x1C hoverColor   (default 0xff78d2ff)
  +0x20 style        (default 0x100)
  +0x24 childFrame array ptr (=0)
  +0x28 array capacity (=0)
  +0x2C array count (=0)
  +0x30 = 0x40 (flags)
  +0x34 userField (set by base msg 0x5e)

- **Message protocol:**

UiCtlUrl FrameProc FUN_00886690(msgframe, payload, param3) switches on msgframe[1]=msg. It is a THIN DERIVED control over the Engine text-button CtlTextBtn (base proc FUN_00616c00, alloc string "P:\\Code\\Engine\\Controls\\CtlTextBtn.cpp",0xa9). Instance accessor = *(msgframe[2]) (the URL layer's own slot). Only 4 messages are handled; everything else forwards to the base via thunk_FUN_00647170.

URL-LAYER MESSAGES (FUN_00886690):
- case 4  (CLASS TEMPLATE INIT): reads urlIndex = payload[2] (asserts idx<=0x19 / 26 entries else FUN_00487a80(0x46)); installs base proc: *(payload[3]) = FUN_00616c00 (CtlTextBtn); computes default caption = FUN_007c3bc0(DAT_00b96a5c[idx*8]) and stores it at *(payload[5]) so the base ctor paints it. Then falls through to forward.
- case 9  (CONSTRUCT): stores the URL index into this layer's instance dword: *(msgframe[2]) = payload[0]; then forwards to base (base case 9 allocs the 0xa9-byte CtlTextBtn instance, default colors 0xff64beeb normal / 0xff78d2ff hover, style 0x100, and sets the caption text).
- case 0x32 (COMMAND/NOTIFY): if payload[2]==7 (activation/click notify code) -> bounds-check stored index (*(msgframe[2])<=0x19 else FUN_00487a80(0x58)) -> FUN_004a1d60(DAT_00b96a58[idx*8]) = OPEN THE URL. FUN_004a1d60 formats the URL string by id via FUN_005e2e60(id,0x100,buf) then dispatches system UI msg 0x10000184 (open-url) via FUN_0062f0a0. This is the hyperlink click action.
- case 0x61 (SET URL INDEX at runtime): treats payload as an integer index; caption = FUN_007c3bc0(DAT_00b96a5c[idx*8]); FUN_006177b0(msgframe[0], caption) -> sends base msg 0x5f (set text); stores *(msgframe[2]) = idx; forwards.
- cases 5-8,0xa-0x60 (except 9,0x32): no-op break then forward to base.
- default: forward to base.

TWIN LOOKUP TABLE (26 entries, 8-byte stride, base 0x00b96a58): each entry = {+0: urlId (arg to FUN_004a1d60, must be <0x34), +4: labelStringId (arg to FUN_007c3bc0)}. First 8 entries {urlId,strId}: {26,40153},{27,13},{28,14},{29,16},{30,15},{31,40153},{32,13},{33,89069}. DAT_00b96a5c is simply base+4 (the label field of the same table).

INHERITED BASE (CtlTextBtn FUN_00616c00) MESSAGES the control relies on: 4=install its own base FUN_006123a0 + caption; 8=paint text (uses colors +0x18/+0x1c, style +0x20, hover via FUN_0062e320); 9=alloc instance; 0xb=free instance; 0x20/0x22/0x24/0x25/0x2c/0x2e=mouse/keyboard hit (keys 0x14 enter,0x15 space,0x69 click set/clear pressed bit0 and fire FUN_0062ee80(...,7,...)); 0x38=hit-test/char rect; 0x3a=append text; 0x4c=commit/layout text; 0x56=activate->emits notify code 7 (the click that reaches URL case 0x32); 0x57/0x58=get normal/hover color; 0x59=get text; 0x5a=get text length; 0x5b=set normal color; 0x5c=set style; 0x5d=set hover color; 0x5e=set field+0x34; 0x5f=set text; 0x60=set text w/ max len.

Helpers: FUN_007c3bc0(id)->FUN_007c3be0(id,0) = fetch localized/encoded wstring. FUN_006177b0(ctrl,str) asserts str!=0 then FUN_0062ef40(ctrl,0x5f,&str,0). FUN_004a1d60 = open URL (asserts 0<id<0x34).

- **Create recipe:**

Create via the standard primitive FUN_0062bfc0(parent, flags, childId, proc=FUN_00886690, userdata=urlIndex, caption):

  hUrl = FUN_0062bfc0(parentFrame, flags, childId, 0x00886690, urlIndex, L"UrlName");
  FUN_0062f150(hUrl, FUN_004a5210, 0);   // attach hyperlink hover/cursor+color callback

Verified live call sites:
  - FUN_0085f230 (Login dialog): FUN_0062bfc0(param_1, 0, 8, FUN_00886690, 0xd, L"UrlSupport"); then FUN_0062f150(hUrl, FUN_004a5210, 0);
  - FUN_008637c0 @0x00863971: FUN_0062bfc0([ESI+4], 0, 4, FUN_00886690, 0xd, caption); FUN_0062f150(...,FUN_004a5210,0);
  - FUN_00867380 @0x00867583: FUN_0062bfc0([EBX+4], 1, 0xf, FUN_00886690, <ud>, caption) with pre-set colors via FUN_0059fee0/FUN_0060a2d0 (custom normal/hover color e.g. 0xff78d2ff).

Key args: 
  * userdata = urlIndex (0..25), the table row; 0xd (13) is the common "Support" link. This is what case 9 stores and case 0x32/0x61 read; it drives BOTH the caption text and the launched URL. Passing an index > 0x19 asserts (FUN_00487a80(0x46) at init, 0x58 at click).
  * caption (last arg) is optional — the control auto-labels from DAT_00b96a5c[idx] at case 4; pass L"..." only as the frame's debug/name string.
  * flags: 0 for plain inline link; other dialogs use 1 or style bits.
Post-create tweaks (all forwarded base msgs): set normal color FUN_0059fee0(h,&argb) (base 0x5b), hover color FUN_0060a2d0(h,&argb) (base 0x5d), style base 0x5c. To relabel/retarget at runtime send msg 0x61 with a new index via FUN_0062ef40(h,0x61,newIndex,0). Warm-up: parent dialog issues FUN_0062ef00(parent,0x4c) after building children to commit layout/text.

- **Crash gotchas:**

1) urlIndex bounds: case 4 asserts idx<=0x19 (FUN_00487a80(0x46)); case 0x32/click asserts stored idx<=0x19 (0x58). Never create with userdata>25.
2) URL id range: FUN_004a1d60 asserts 0<urlId<0x34 (52) (error 0x3ee if 0, 0x3ef if >=0x34) and asserts the formatted URL string is non-empty (0x3fc). The table maps idx->urlId, so a table row pointing at an unregistered/empty URL id crashes on click, not on create.
3) It is a DERIVED control: you MUST let base msgs 4 and 9 run (they install FUN_00616c00 / FUN_006123a0 and alloc the 0xa9 instance). Do not stub the forward (thunk_FUN_00647170) or the instance/caption is never built.
4) Caption comes from the localized string table (FUN_007c3bc0 on DAT_00b96a5c[idx]); an invalid string id yields a blank/garbled link but the encoded-string fetch itself does not bound-check here.
5) FUN_006177b0 asserts the text pointer !=0 (0x242) — do not send msg 0x61 style set with a null resolved string.
6) The click that opens the URL arrives as base notify 7 -> URL msg 0x32 subcode 7; if you reparent so the notify never reaches this proc, the hyperlink silently won't open.


### UiCtlBtnExpand  (EXE 0x008867f0, confidence: high)

- **WASM:** ram:80e7b6f7
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlBtnExpand.cpp (EXE string @0x00b96b68; WASM ../../../../Gw/Ui/Controls/UiCtlBtnExpand.cpp @ram:0010e985). Note game-layer Gw\Ui path, not Engine\Controls.
- **Struct layout:**

No per-instance instance struct is allocated. Unlike the canonical model there is NO case 9 (alloc via FUN_0047f340) and NO case 0xb (free) here: UiCtlBtnExpand stores zero per-frame data. The paintable "instance" is the frame itself; checked/hover state is read from the base UiCtlBtn frame via CtlBtnIsChecked (FUN_0062e320) and FrameIsMouseFocus (FUN_0060f4b0).

Only owned state = ONE process-global shared image list:
  DAT_01081d70 : HFrameImageList*  (the 4-frame chevron atlas; ref-counted create/free)

Image list build (case 5, FUN_0062d790 = FrameImageListCreate(pixelFmt=0x11, texOp=7, flags=0x1a, coord1*, coord2*, texName, frameCount=4)):
  Desktop  (FeatureFlag 0x71 == 0): fullSize {0x20,0x20}, cellSize {0x10,0x10}, tex=&DAT_00b96b9c
  Mobile   (FeatureFlag 0x71 != 0): fullSize {0x40,0x40}, cellSize {0x1c,0x1c}, tex=&DAT_00b96b94

Paint msgframe payload (param_2) for msg 1:
  payload[0]  = paint sub-pass (only sub-pass 0 draws)
  payload+2   = Rect4f (dest rect)   -> FrameContentAddImage arg
  payload[6]  = EFrameContentLayer
Image index computed = (CtlBtnIsChecked?1:0) + (FrameIsMouseFocus?2:0)
  0=collapsed/idle, 1=expanded/idle, 2=collapsed/hover, 3=expanded/hover

- **Message protocol:**

Dispatch: switch(param_1[1]) where param_1=FrameMsgHdr, param_2=payload, param_3=out.

case 1  PAINT: if payload[0]==0 (sub-pass 0): idx=(CtlBtnIsChecked(FUN_0062e320)?1:0)+(FrameIsMouseFocus(FUN_0060f4b0)?2:0); FUN_0062b290(frame, payload+2 /*Rect4f*/, DAT_01081d70 /*imageList*/, idx, payload[6] /*layer*/, 0 /*model*/). (FUN_0062b290 = FrameContentAddImage.)
case 4  INSTALL BASE PROC: *(code**)payload[3] = FUN_00877e60 (base UiCtlBtn proc); payload[1] style |= 0x30000.
case 5  CREATE SHARED IMAGELIST: assert DAT_01081d70==0 else FUN_00487a80(0x54); build atlas (desktop/mobile variant) into DAT_01081d70 via FUN_0062d790.
case 6  FREE SHARED IMAGELIST: assert DAT_01081d70!=0 else FUN_00487a80(0x75); FUN_0046f850(DAT_01081d70); DAT_01081d70=0.
case 0x15 SIZE-QUERY: zero all four out words (*param_3..[3]=0) -> contributes no intrinsic size; footprint comes from base button.
default  -> thunk_FUN_00647170 (FrameMsgCallBase) -> chains to base UiCtlBtn (FUN_00877e60), which itself paints checked/hover glyphs, handles msg 0x38/0x5f/0x60, and case 4 installs grandparent FUN_0060f4f0.

WASM parity confirmed: same msg ids 1/4/5/6/0x15; asserts at lines 0x54 (imageList already set) and 0x75 (imageList missing); default -> FrameMsgCallBase.

- **Create recipe:**

Primitive: FUN_0062bfc0(parent, flags, childId, proc, userData, name) = FrameCreate.

Two verified live call sites:
 1) Group header (FUN_0087e090): h = FUN_0062bfc0(parentFrame, 0, 0, FUN_008867f0, 0, L"CheckOpen");  paired with a TxtName label child; header itself styled UiCtlGroupHeader / UiCtlGroupHeaderMobile.
 2) List/collapsible row (FUN_00865ef0): h = FUN_0062bfc0(parentFrame, 0, 0, FUN_008867f0, 0, NULL); then FUN_0062c2a0(h, 1) to make it interactive/checkable.

Minimal recipe to spawn an expander chevron:
  1. h = FUN_0062bfc0(parent, flags=0, childId=0, proc=FUN_008867f0, userData=0, name=L"CheckOpen" or NULL)
  2. (optional) FUN_0062c2a0(h, 1)  -> enable click/toggle
  3. Toggle state read/set through base UiCtlBtn checked API (CtlBtnIsChecked FUN_0062e320 / setter chain); parent typically wires the CheckOpen button to FUN_0062cfc0/FUN_0062fcb0 to drive panel open state.
Warm-up: the shared chevron atlas (DAT_01081d70) is created lazily by the framework via msg 5 the first time any UiCtlBtnExpand is registered and freed via msg 6 when the last one is destroyed -- caller does NOT allocate it. Flags 0, childId 0, no per-instance alloc.

- **Crash gotchas:**

- msg 5 asserts (FUN_00487a80(0x54), a no-return ErrorAssertion) if DAT_01081d70 is already non-null: never send the imagelist-init message twice; it is a global singleton.
- msg 6 asserts (FUN_00487a80(0x75)) if DAT_01081d70 is null: freeing/deinit before init crashes. These two form a strict ref-counted create/destroy pair managed by the frame registrar, not by callers.
- Paint (msg 1) passes DAT_01081d70 to FrameContentAddImage with no null guard; forcing a paint before the atlas init message will hand a null image list to the content layer.
- FUN_0062c2a0 asserts (FUN_00487a80(0xfe9)) on a null handle -- always pass the handle returned by FUN_0062bfc0.
- No per-instance destructor: because there is no case 9 alloc, do not expect a per-frame free hook; treat this control as stateless aside from the shared atlas.
- Desktop vs mobile atlas differs (FeatureFlag 0x71): cell sizes 0x10 vs 0x1c; do not hardcode chevron cell dimensions.


### UiCtlEdit  (EXE 0x00888aa0, confidence: high)

- **WASM:** ram:80e0f5ab
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlEditBox.cpp (EXE string 0x00b96bd8, xref'd only from FUN_00888aa0). Underlying engine layer: P:\Code\Engine\Controls\CtlEdit.cpp (0x00a4df4c).
- **Struct layout:**

Two tiers of state.

CLASS-LEVEL / static (shared by all UiCtlEdit instances, built by msg 5, freed by msg 6):
  DAT_01081d78  : resource handle - primary fill texture (built from ARGB 0xfff0f0f0 via FUN_00679a60, style 0x20003e0)
  DAT_01081d7c  : resource handle - secondary fill/overlay texture (from &DAT_00bf46f8)
  DAT_01081d80  : resource handle - 0x11x0x11 caret/glyph atlas (FUN_0062d790, cell 0x80x0x80, desc DAT_00b96c18, stride 0x18)
  PTR_DAT_00bf46fc : static 9-slice border texture, ACTIVE/FOCUSED state
  PTR_DAT_00bf4700 : static 9-slice border texture, NORMAL state
  _DAT_00940ee0 = 6.0f, _DAT_009407b8 = 3.0f : default min content dims (used by size-query 0x15)

PER-INSTANCE accessor helper (allocated in msg 0x60):
  size 0x2a (42 bytes) via FUN_007c3bc0(0x2a)
  +0x00 : (object body / base)
  +0x04 : handler proc = FUN_00878950 (stored as [1] of returned block)
The actual edit buffer / caret / selection state lives in the underlying Engine CtlEdit instance struct (owned by CtlEdit.cpp proc that this subclasses), not in this wrapper.

Incoming frame message layout (param_1 = FrameMsgHdr): [0]=frame id, [1]=msg, [2..4]=params, [5]=subclass index. Paint payload (param_2): [0]=sub-pass, [2..5]=rect, [6]=clip/parent, [7]=flags/context, [10]=text ptr (for 0x5f).

- **Message protocol:**

FrameProc FUN_00888aa0 (WASM IUi__UiCtlEditProc, asserts P:\Code\Gw\Ui\Controls\UiCtlEditBox.cpp). NOTE: this is a GAME-UI-LAYER (IUi/Gm) styling subclass installed ON TOP of the Engine CtlEdit proc (CtlEdit.cpp, FUN_00603cc0 family). It therefore uses the Gw UI FrameMsg set, NOT the Engine control set (no case 4/9/0xb here — parent-install and instance alloc/free are done by the underlying CtlEdit engine proc that this subclasses). Dispatch is switch(param_1[1]=msg); unhandled msgs fall through to base dispatcher thunk_FUN_00647170 (=FUN_00647170, the subclass-chain walker that itself skips msg 9 and 0xb).

MESSAGES:
- case 1 PAINT, sub-dispatch on *param_2 (paint sub-pass):
  * sub 0 = frame/border: state=FUN_0062e2e0(frame); picks PTR_DAT_00bf46fc (active/focused) vs PTR_DAT_00bf4700 (normal, also gated by FUN_0056a410); draws 9-slice via FUN_0062b8e0(frame, rect=payload+2, tex, &dims{0x20,0x10}, flags=7, 0, payload[6], payload[7]).
  * sub 1 = fill layer: FUN_0062b2d0(frame, payload+2, DAT_01081d78, &scale{1.0,1.0}, &origin{0,0}, payload[6], payload[7]).
  * sub 0xc = caret/scroll glyph: qtype=FUN_006275e0(); guarded (returns early if 0 or 5); pos=FUN_006275f0(); if hi-word set requires value 2 or 3 else assert FUN_00487a80(0x9a), applies +4 (val2) / +0xf (val3) offset; draws DAT_01081d80 glyph via FUN_0062b290.
  * sub 0xd = secondary layer: FUN_0062b2d0 with DAT_01081d7c, scale 1.0.
- case 5 CLASS-INIT (one-time static resource build): if DAT_01081d78==0 lazily builds DAT_01081d78=FUN_00679a60(&0xfff0f0f0,0x20003e0,0), DAT_01081d7c=FUN_00679a60(&DAT_00bf46f8,0x20003e0,0), DAT_01081d80=FUN_0062d790(0x11,7,0,&{0x11,0x11},&{0x80,0x80},&DAT_00b96c18,0x18); then chains base. If already initialized -> assert FUN_00487a80(0x3c).
- case 6 CLASS-SHUTDOWN: FUN_0046f9b0 frees DAT_01081d78/7c/80, nulls them, chains base.
- case 0xc INSTANCE DETACH/CLEANUP: FUN_0062bd40(frame), chains base.
- case 0x15 SIZE-QUERY: param_3[0..3] = {6.0f,3.0f,6.0f,3.0f} (min/pref content dims from _DAT_00940ee0=6.0, _DAT_009407b8=3.0).
- case 0x5f TEXT-RENDER: state=FUN_0062e2a0(frame); FUN_0062bb30 draws edit text, color=(state?0x505050:0)-0x5f5f60 masked (active=dark, inactive=gray), payload[10]=string, flags 6.
- case 0x60 CREATE-ACCESSOR: obj=FUN_007c3bc0(0x2a) (42-byte helper); *param_3=obj; param_3[1]=FUN_00878950 (handler); chains base.
- case 0x61 IFACE/VTABLE-QUERY: if param_3==0 assert FUN_00487a80(0xd0); else param_3[0..2]={FUN_00889480,FUN_00889560,FUN_0087d5d0}; falls through to base.
- default: base FUN_00647170.

- **Create recipe:**

UiCtlEdit is NOT created via the raw create-primitive FUN_0062bfc0 directly as a standalone control; it is a STYLING SUBCLASS layered over the Engine CtlEdit. Lifecycle/order:
1. One-time (per class): send msg 5 to build the shared textures (DAT_01081d78/7c/80). This MUST happen before any paint. It is idempotent-guarded: a second msg 5 without an intervening msg 6 asserts (0x3c). The GW UI framework triggers this during control registration; if you drive it manually, guard it yourself.
2. Create the base edit: the UI layer creates a CtlEdit frame (Engine proc via FUN_0062bfc0(parent,flags,child,editProc,userdata,0)) and installs FUN_00888aa0 as a subclass on it (WASM FrameNewSubclass path). The subclass chain is walked by FUN_00647170; base proc install is the Engine CtlEdit responsibility (its case 4), not this wrapper.
3. Warm-ups before first paint: ensure msg 5 ran (textures non-null) and the base CtlEdit instance exists. Send size-query (0x15) to obtain min dims {6,3}; the framework uses these for layout.
4. Per-instance accessor: msg 0x60 allocates the 0x2a helper (handler FUN_00878950) — sent by the framework when an external accessor/handle is requested; msg 0x61 returns the {get/set/misc} vtable {FUN_00889480,FUN_00889560,FUN_0087d5d0}.
5. Teardown: instance cleanup via msg 0xc; class-level texture free via msg 6 (only at shutdown, frees the shared statics for ALL instances).
Flags/proc: parent=host frame, proc=this FUN_00888aa0 as subclass over the CtlEdit engine proc, style read via FUN_0062fe20(frame,mask); active/focus state via FUN_0062e2e0 / FUN_0062e2a0 selects textures/colors.

- **Crash gotchas:**

1. Paint-before-init NULL deref: paint sub-passes 1/0xc/0xd dereference class statics DAT_01081d78/DAT_01081d7c/DAT_01081d80. If msg 5 (class-init) has not run, these are NULL and FUN_0062b2d0/FUN_0062b290 deref null -> crash. Always run msg 5 once before painting.
2. Double class-init assert: sending msg 5 twice without an intervening msg 6 hits FUN_00487a80(0x3c) (DAT_01081d78 already set).
3. Shared-state footgun: msg 6 frees the class-level textures for ALL UiCtlEdit instances; sending it while any edit is still live -> subsequent paints NULL-deref. Only free at true class shutdown.
4. Interface query null-out assert: msg 0x61 with param_3==NULL -> FUN_00487a80(0xd0). Caller must pass a 3-slot out buffer.
5. Caret paint assert: sub-pass 0xc, if FUN_006275f0() returns a hi-word-set value that is neither 2 nor 3 -> FUN_00487a80(0x9a). Only happens with corrupted selection/scroll state.
6. Base-dispatcher asserts (FUN_00647170): invalid/stale frame id or bad subclass index trip FUN_00487a80 with 0x256 (id range), 0x221 (frame table null), 0x223 (subclass index >= count), 0x24b (per-slot bounds). Do not dispatch to a destroyed frame.
7. Size-query out buffer: msg 0x15 writes 4 floats to param_3 unconditionally (no null check) — pass a valid 4-float buffer.


### UiCtlEditBox  (EXE 0x00888aa0, confidence: high)

- **WASM:** ram:80e0e3e0
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlEditBox.cpp (EXE string @ 0x00b96bd8, xref'd 3x from FUN_00888aa0 at the FUN_00487a80 assert sites, lines 0x3c/0x9a/0xd0)
- **Struct layout:**

FrameProc signature: void FUN_00888aa0(FrameMsgHdr* hdr /*param_1*/, void* payload /*param_2*/, void* out /*param_3*/).

FrameMsgHdr (param_1), 4-byte ints:
  +0x00 [0] hFrame    (frame id/handle; passed to all Frame* helpers)
  +0x04 [1] msg       (message id the switch() dispatches on)
  +0x10 [4] style     (bitflags; read as param_1[4]&mask in sibling layer FUN_00879090)
  (higher slots belong to the shared FrameContext, not this control)

Paint payload (param_2) for msg 1 = FrameContentDrawParams:
  [0] contentLayer / sub-pass index (0,1,0xc,0xd)
  [1] secondary sub-index (used by text pass 0x5f)
  [2..5] Rect4f bounds  (payload+2)
  [6],[7] HGrModel handles / layer params
  [10] TArray<HGrModel*> text-model array (msg 0x5f)

Instance data: NONE at this layer. FUN_008852e0 case 9 registers this proc via FUN_0062f150(frame, FUN_00888aa0, 0) -> 0 extra instance bytes. All editable text/caret/selection state lives in the CtlEdit engine installed by msg 0x61 (procs FUN_00889480/FUN_00889560/FUN_0087d5d0).

Process-GLOBAL (class-level, not per-instance) shared render resources, lazily built in msg 5:
  DAT_01081d78 = border solid material (Color4b 0xfff0f0f0) via FUN_00679a60=GrBuildSolidMaterial
  DAT_01081d7c = caret/selection solid material (color @DAT_00bf46f8)
  DAT_01081d80 = IME-indicator HFrameImageList (fmt 0x11, tex @DAT_00b96c18) via FUN_0062d790=FrameImageListCreate

- **Message protocol:**

switch(hdr[1]):

case 1  PAINT — sub-switch on payload[0] (content layer):
  sub 0  background: FUN_0062e2e0=FrameIsKeyFocus + FUN_0056a410=CtlEditGetReadOnly pick texture (PTR_DAT_00bf46fc focused vs 00bf4700 default), then FUN_0062b8e0=FrameContentAddImageTemplate (rect payload+2, size 0x10x0x20).
  sub 1  border ring: FUN_0062b2d0=FrameContentAddImage using global material DAT_01081d78.
  sub 0xc IME indicator: FUN_006275e0=EventCliGetImeLang, FUN_006275f0=EventCliGetImeMode -> frame index; FUN_0062b290=FrameContentAddImage w/ imagelist DAT_01081d80. Asserts line 0x9a on unexpected IME lang.
  sub 0xd caret: FUN_0062b2d0=FrameContentAddImage using material DAT_01081d7c.

case 5  CLASS-INIT (first-instance, lazy): if DAT_01081d78==0 build the 3 global resources then FrameMsgCallBase; ELSE assert line 0x3c (double-init).
case 6  CLASS-DEINIT (last-instance): FUN_0046f9b0=HandleCloseSafe on the 3 globals, zero them, FrameMsgCallBase.
case 0xc INVALIDATE: FUN_0062bd40=FrameContentInvalidate(frame), FrameMsgCallBase.
case 0x15 GETSIZE: writes default Rect4f 6.0 x 3.0 (0x40c00000,0x40400000,...) into out[0..3].
case 0x5f DRAW-TEXT (control-specific): FUN_0062e2a0=FrameIsEnabled -> text color (0xf0f0f0 enabled / 0xa0a0a0 disabled); FUN_0062bb30=FrameContentAddText using text array payload[10].
case 0x60 GET-PASSWORD-CHAR (control-specific): FUN_007c3bc0=TextEncode('*'=0x2a) -> out[0]; out[1]=FUN_00878950 (mask callback); FrameMsgCallBase.
case 0x61 GET-SUBCLASS-PROCS (control-specific): assert line 0xd0 if out==NULL; writes CtlEdit engine chain out[0]=FUN_00889480, out[1]=FUN_00889560, out[2]=FUN_0087d5d0.
default / fallthrough: thunk_FUN_00647170 = FrameMsgCallBase (parent proc LAB_00619c50 installed by the FUN_008852e0 wrapper's case 4).

Lifecycle msgs 4(install-parent)/9(alloc)/0x64(class-descriptor) are NOT handled here — they are handled by the outer class proc FUN_008852e0 which installs this layer.

- **Create recipe:**

Real in-game creation is GmChat's EditName field (FUN_0051b580 @ 0x0051b605):

1. Ensure a valid parent frame (FUN_0062bfc0 chain root).
2. Create the primitive with the EditBox CLASS proc FUN_008852e0 (NOT FUN_00888aa0 directly):
     frame = FUN_0062bfc0(parent, 0x892e000 /*style*/, 3 /*child order*/, FUN_008852e0, 0 /*userdata*/, L"EditName");
   (Chat's multiline input variant instead uses proc FUN_0087d9a0 with flags 0x2020000, order 2, name L"EditMessage" — FUN_0087d9a0 also installs FUN_00888aa0 at its case 9.)
   Internally: FUN_008852e0 case 4 installs parent LAB_00619c50; case 9 calls FUN_0062f150(frame, FUN_00888aa0, 0) to push THIS paint layer; on first ever instance msg 5 lazily builds the 3 global materials; msg 0x61 hands back the CtlEdit engine procs FUN_00889480/FUN_00889560/FUN_0087d5d0.
3. Warm-ups after create:
     FUN_0062f150(frame, FUN_0051ce20, 0)   // attach app-level message/notify layer
     FUN_00604aa0(frame, 0x14)              // CtlEditSetMaxChars = 20
     txt = FUN_007c3bc0(0x2da); FUN_005636a0(frame, txt)  // set label/prompt text
     FUN_00604b00(frame, initialText)       // set initial contents (optional)
4. Sizing: default is msg 0x15 = 6.0 x 3.0; class descriptor PTR_FUN_00b96960 carries sizing floats {1.0,-1.0,0.0,0.0,100.0}. Override via layout on the parent, not by editing this proc.
Do NOT invoke FUN_00888aa0 standalone or as the FUN_0062bfc0 proc — it is a layer, not the class entry.

- **Crash gotchas:**

- msg 0x61 with out(param_3)==NULL -> FUN_00487a80(0xd0) assert/abort. Callers requesting the subclass procs must pass a >=3-slot output buffer.
- msg 5 sent while DAT_01081d78 already non-null -> FUN_00487a80(0x3c) assert. Class-init is a strict single init/deinit (msg5/msg6) pair; the 3 globals are NOT ref-counted, so re-init without an intervening msg 6 crashes.
- The 3 render resources (DAT_01081d78/7c/80) are PROCESS-GLOBAL and shared by every editbox. msg 6 (HandleCloseSafe) tears them down for ALL instances -> use-after-free if another editbox instance is still painting (msg1/0x5f) afterward. Only the last live instance may send msg 6.
- Paint layer holds 0 instance bytes; msg 0x5f (DRAW-TEXT) dereferences the CtlEdit text array (payload[10]) which only exists once the msg-0x61 subclass chain is installed. Painting before FUN_008852e0's alloc/subclass setup completes reads uninitialized text -> crash.
- Paint sub 0xc (IME): FUN_00487a80(0x9a) aborts on an unexpected EventCliGetImeLang value (only 0/2/3 handled, else assert) — corrupt/foreign IME state can bring it down.
- Because case 4/9/0x64 fall through to FrameMsgCallBase here, mis-registering this proc as the top class proc (instead of via FUN_008852e0) leaves the parent (LAB_00619c50) and instance alloc uninstalled -> null base proc chain on the next dispatch.


### UiCtlDropMenuEntry  (EXE 0x00888ef0, confidence: high)

- **WASM:** ?
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlDropMenuEntry.cpp (EXE string 0x00b96c54; xref'd from 0x00888f5b inside FUN_00888ef0). Parent control string P:\Code\Gw\Ui\Controls\UiCtlDropMenu.cpp at 0x00b963d0 -> proc FUN_0087f5f0.
- **Struct layout:**

This proc owns NO heap instance: unlike the base template it has no case 4 (install base) and no case 9 alloc via FUN_0047f340 and no case 0xb free. It is a COMPOSITE/logic frame proc whose entire state lives in (a) its two child frames [id0 = content/icon, id1 = text label] and (b) the frame's own style/enabled/hover bits read via FUN_0062e2a0/FUN_0062e320. So the meaningful layout is the msg-0x09 creation-config struct (pointed to by payload[0]):
  cfg+0x00 : (the cfg base = payload[0]; must be non-null or assert 0x67)
  cfg+0x04 : void(*contentProc)(frame,payload,out)  — optional icon/content child proc; child order 0, flags 0x1300
  cfg+0x08 : void* contentUserdata                  — userdata handed to contentProc
  cfg+0x0c : wchar_t*/textctx* labelText           — optional; built-in text child (proc FUN_00610c40), order 1, flags 0xa0200, style 0x40
Row metric G = global _DAT_00943278 (fixed entry height reported by size-query).
Parent DropMenu (FUN_0087f5f0) manages entries: its msg 0x56 (append) / 0x57 (append+select) call FUN_0087f870, which creates each entry via FUN_00612900(container=FUN_0062cfc0(dropmenu,1), 0,0, proc = payload[1]?payload[1]:&LAB_008891b0, userdata=&payload[1]); FUN_0062fbf0(entry, payload[0]) sets the entry value; FUN_0062c9c0(entry,0) if selected.

- **Message protocol:**

Entry FrameProc = FUN_00888ef0(frame* param_1, payload* param_2, out* param_3); switch(param_1[1]=msg). Registered/passed as the JMP thunk LAB_008891b0 (JMP 0x00888ef0) — that pointer, not the raw proc, is what the framework stores. Dispatched via FUN_0062ef40(frame,msg,wparam,out). frame handle = *param_1.

Messages actually handled (all others 0x0a-0x36 fall through to a no-op break => delegated/ignored):
- msg 0x08 PAINT-BG: if (payload[0] & 1) { enabled=FUN_0062e320(frame,0); FUN_004a54f0(frame, &payload[3] /*rect*/, 0,0, enabled); } else no-op. Draws the row highlight/background bitmap.
- msg 0x09 CREATE/BUILD-CHILDREN: cfg = payload[0] (pointer). Asserts FUN_00487a80(0x67) NORETURN if cfg==NULL. Builds:
    if cfg[+0x04]!=0: childA = FUN_0062bfc0(frame, 0x1300, order=0, proc=cfg[+0x04], userdata=cfg[+0x08], 0)  // caller-supplied content/icon frame
    if cfg[+0x0c]!=0: childB = FUN_0062bfc0(frame, 0xa0200, order=1, proc=FUN_00610c40 /*text/label proc*/, userdata=cfg[+0x0c] /*text ptr*/, 0); FUN_0059fee0(childB, 0x40) // set text style/align
    FUN_0062ccd0(frame, 0x30, 0)  // set layout flags
    FUN_008891c0(frame)           // apply state colors + relayout (see below)
- msg 0x0c and msg 0x25 STATE/RELAYOUT: FUN_008891c0(frame).
- msg 0x15 SIZE-QUERY: writes out rect param_3 = {0, G, 0, G} where G = global _DAT_00943278 (default entry cell metric/handle). i.e. min=(0,G), pref=(0,G) -> fixed-height row.
- msg 0x2e SELECT/NOTIFY: if (payload[4]!=0 && payload[0]==0) FUN_0062ee80(frame, 7, 0, 0)  // post notify code 7 to parent DropMenu.
- msg 0x37 MOUSE-HITTEST (no button): pt={payload[0],payload[1]}; FUN_0062ec50(_DAT_00943278,0xc,&pt); if child0=FUN_0062cfc0(frame,0) forward FUN_0062e8a0(child0,0x86,&pt,0) + FUN_0062ec50(_DAT_0093c89c,4,&pt); if child1=FUN_0062cfc0(frame,1) forward FUN_0062e8a0(child1,0x60,&pt,0).
- msg 0x38 MOUSE-MOVE (magnitude payload[2]): pt build via FUN_0062e800(_DAT_00943278,0xc,&pt,payload[2]); forward FUN_0062e700(child,0x86,&pt,payload[2],0) to child0 and child1.

State helpers used by FUN_008891c0 (relayout/colorize): iVar1=FUN_0062e2a0(frame) [enabled?], iVar2=FUN_0062e320(frame,?) [hover?]. Label child (id1) text color: !enabled->0xFFA0A0A0, !hover->0xFFF0F0F0, else 0xFFFFEAB8 (highlight gold) via FUN_00604aa0. Content child (id0) gets FUN_0062ef40(child0,0x56,{0|1},0) so it can mirror hover state; then FUN_0062bd40(frame) requests repaint.

- **Create recipe:**

Preferred (normal) path — let the parent DropMenu build entries:
 1. Have a DropMenu frame (proc FUN_0087f5f0 / UiCtlDropMenu.cpp).
 2. Dispatch to it FUN_0062ef40(dropmenu, 0x56, &payload, 0) to append, or 0x57 to append+select, where payload = {value/id @[0], entryProc @[1] (pass 0 to use the default entry proc thunk 0x008891b0), then the entry config fields (content proc, content userdata, label text) laid out so entry msg-9 sees them at cfg+4/+8/+0xc}.
 3. Framework sends the new entry frame msg 9; the entry proc builds its icon child (if content proc given) and label child (if text given), sets layout 0x30, colorizes.

Direct instantiation (if bypassing DropMenu):
 create = FUN_0062bfc0(parentContainer, flags=0xa0200|context, order, proc=0x008891b0 (thunk to 0x00888ef0), userdata=&cfg, 0); the create pump will deliver msg 9 -> ensure cfg!=NULL and set cfg+0x04 (contentProc) and/or cfg+0x0c (labelText) beforehand. Optionally send msg 0x08 only after msg 9 has run so the child frames exist. Warm-ups: none beyond a live UI frame pump; the global context handles _DAT_00943278 / _DAT_0093c89c must be initialized (they are once the UI subsystem is running).

- **Crash gotchas:**

- msg 0x09 with payload[0]==NULL -> FUN_00487a80(0x67) is NORETURN (assert/abort). Always supply a non-null config for the build message.
- config+0x04 contentProc is caller-supplied and is invoked by the framework with flags 0x1300; a bad/garbage proc pointer crashes on the child's first message. config+0x0c is passed as userdata to the internal text proc FUN_00610c40 (expects a valid text/text-context pointer) — a non-string pointer will fault inside the label paint.
- No case 0x0b/free and no owned instance: do NOT send instance alloc/free messages expecting base-template semantics; lifetime is via the child frames + FUN_0062bd40/FUN_0062c9c0. Sending a raw destroy that only tears the parent can leak the two children if not routed through the DropMenu.
- msg 0x37/0x38 dereference the global context handles _DAT_00943278 and _DAT_0093c89c; outside a live UI pump (handles null/stale) these hit-test forwards fault. Child lookups FUN_0062cfc0(frame,0/1) are null-guarded, so painting (msg 8) or relayout before msg 9 built the children is safe (no-op), but mouse messages assume the context globals are valid.
- Entry reports a FIXED row height from _DAT_00943278 via size-query (msg 0x15); overriding size externally is ignored — height is not derived from content.


### UiCtlImeCand  (EXE 0x00889480, confidence: high)

- **WASM:** ? (not a single WASM function addr resolved; identity confirmed via WASM assertion strings ram:0010e9da "../../../../Gw/Ui/Controls/UiCtlImeCand.cpp" for this proc and ram:0010ea06 "../../../../Engine/Controls/CtlImeCand.cpp" for its base FUN_0061d870)
- **Assertion file:** Gw\Ui\Controls\UiCtlImeCand.cpp (game layer, WASM ram:0010e9da). Runtime base is Engine\Controls\CtlImeCand.cpp (EXE string 0x00a508a4, WASM ram:0010ea06), whose FrameProc is FUN_0061d870 / LAB_0061d860.
- **Struct layout:**

TWO-LAYER CONTROL. FUN_00889480 (UiCtlImeCand, game layer) is a thin class-descriptor/subclass proc; the real runtime FrameProc is its base FUN_0061d870 (Engine CtlImeCand). Instance is allocated & owned by the base.

msgframe (param_1 in every proc): [0]=frame/control handle (self), [1]=msg id, [2]=ptr to the instance-ptr slot (so instance = **(msgframe+8) via accessor FUN_0061e0e0, which asserts non-null with code 0x7d).

Instance object: alloc'd in base case 0xa via FUN_0047f340("P:\\Code\\Engine\\Controls\\CtlImeCand.cpp", 0x6b) = 0x6b (107) bytes. Header init = {frame, 0, -1, 0}; observed fields (derived from FUN_0061e110 / case-0xa init):
  +0x00  void* frame        // self control handle (used to reach children via FUN_0062cfc0)
  +0x04  int  pageBaseCache // cached first-candidate index of current page (init 0; set = candMsg[4])
  +0x08  int  hiSlotCache   // currently-highlighted child slot idx, -1 = none (init -1); drives 0x56/0x57 highlight toggle to child
  +0x0c  void* srcListCache // cached candidate-list source ptr for change detection (init 0)
  +0x10..0x6a  internal working storage (list geometry / scratch)

Candidate-message payload (param_2 of the 0x56 refresh, FUN_0061e110): [0]=flag, [1]=count, [2]=?, [3]=selectedIdx(-1 none), [4]=pageBase, [5]=rows, [6]=cols, [8]=startChar. NOTE hard cap: rows+2<=0xc and cols+2<=0xc (i.e. <=10 each).

Child descriptor table (case 0x57 source PTR_FUN_00b96c84, 11 dwords = 5 procs + 6 floats):
  [0]=0x00889260  [1]=0x00889330  [2]=0x00889400 (candidate-slot item proc; wraps FUN_00885620)  [3]=0x0087d5d0 (separator/scroll glyph proc)  [4]=0x00889450
  floats: 2.0, 3.0, 6.0, 16.0, 60.0, 24.0 (padding/spacing/rows/geometry defaults).

- **Message protocol:**

FUN_00889480 (UiCtlImeCand game-layer class proc) switch(msgframe[1]):
  case 4  GET_BASEPROC: *(payload[3]) = &LAB_0061d860 (install Engine CtlImeCand base FUN_0061d870 as parent class).
  case 8  : no-op (return).
  case 9  REGISTER_HANDLERS: FUN_0062f150(frame, FUN_00879090, 4) -> installs per-instance overlay handler in dispatch slot 4 (asserts code 0x49b if frame==0). FUN_00879090 handles its own msg 8 (draw candidate-string quads, style-bit dependent) and msg 0x15 (size query).
  case 0x57 GET_CHILD_TEMPLATE: if out(param_3)!=0 copy 11 dwords from PTR_FUN_00b96c84; else assert code 0xa1.
  default : forward to base FUN_00647170.

Runtime base FUN_0061d870 (LAB_0061d860, Engine CtlImeCand) switch(msg):
  case 0xa CREATE: assert-if-already-set (code 0x6a); alloc 0x6b instance; init {frame,0,-1,0}; store into *(payload[2]); self-query 0x57 for child template; spawn 14 children via FUN_0062bfc0(frame,flags,id,proc,0,0):
     id0  proc 0x00889260 flags 0x40000
     id1  proc 0x00889330 flags 0x40000
     id2..0xb (10 candidate slots) proc 0x00889400 flags 0x4300
     id0xd proc 0x0087d5d0 flags 0
     id0xe proc 0x00889450 flags 0x90000 (page-counter label, renders L"%u/%u")
  case 0xb DESTROY: FUN_005acaeb(instance,0x10); clear *(payload[2]).
  case 8  PAINT: background quad when style bit1 set.
  case 0x31 KEYNAV: page/next/prev candidate -> FUN_00651850 IME commands.
  case 0x37/0x38 POINTER: hover/select (FUN_0061dca0 / FUN_0061df40).
  case 0x56 REFRESH: FUN_0061e110 pushes candidate-list state into the 10 slot children (+counter). Asserts 0xba/0xbb on cols/rows>10.
  cases 9,0xc..0x55: swallowed (break->forward).
Style reads via FUN_0062fe20(frame,mask). Instance access via FUN_0061e0e0 (=**(msgframe+8), assert 0x7d).

- **Create recipe:**

You do not hand-create this; it is spawned by the IME parent control FUN_00888aa0, whose msg 0x61 (GET_SUBCLASSES) returns the descriptor triple *out={FUN_00889480 (this, candidate window), FUN_00889560 (reading/aux), FUN_0087d5d0 (glyph)}. To instantiate manually, replicate the framework sequence:
  1. Register class proc = FUN_00889480 via the create primitive FUN_0062bfc0(parent, flags, child_id, FUN_00889480, userdata, 0).
  2. Framework sends msg 4 -> base FUN_0061d870 installed as parent class (MUST happen before create).
  3. Framework sends msg 9 -> overlay handler FUN_00879090 registered (needs valid frame handle, else assert 0x49b).
  4. Framework sends msg 0xa (CREATE) -> base allocs the 0x6b instance, self-queries 0x57 for the child template, spawns the 14 children (2 frame bits + 10 candidate slots + separator + "%u/%u" counter). Sizing comes from the 6 float defaults in the 0x57 table (2/3/6/16/60/24).
  5. Per update: send msg 0x56 with a candidate-state payload (rows<=10, cols<=10) to lay out and highlight; msg 0x31 for nav keys; msg 8 repaints.
Warm-ups: 0x57 must return a valid 11-dword buffer before CREATE can spawn children; base install (msg4) must precede CREATE; overlay-handler register (msg9) needs a live frame handle.

- **Crash gotchas:**

- Instance-before-create: FUN_0061e0e0 asserts (FUN_00487a80 code 0x7d) if instance is null. Never send 0x56/0x31/0x37/0x38 before CREATE (msg 0xa) has run.
- Double-create: base case 0xa asserts (code 0x6a) if the instance slot is already non-null. Single instance per frame; do not re-CREATE.
- 0x57 NULL out buffer: FUN_00889480 case 0x57 asserts (code 0xa1) if param_3==0. Always pass a >=11-dword out buffer.
- Grid overflow: FUN_0061e110 (msg 0x56) asserts code 0xba if cols(param_2[6])+2>0xc and code 0xbb if rows(param_2[5])+2>0xc. Candidate grid is hard-capped at 10x10 to match the 10 slot children; larger candidate messages crash.
- Handler-register with dead frame: FUN_0062f150 (msg 9 path) asserts code 0x49b if frame handle (*msgframe)==0.
- Ordering: msg4 (install base) must precede msg0xa (create); otherwise child-spawn (which self-queries 0x57 and dereferences the base) and the instance accessor blow up.


### WindowSubclassProc  (EXE 0x008895d0, confidence: medium)

- **WASM:** not resolved (EXE FrameProc address was supplied directly; WASM symbol not cross-checked)
- **Assertion file:** P:\Code\Engine\Frame\FrApi.cpp (create primitive FUN_0062bfc0 allocs the 0x132-byte frame via FUN_0047f340 with this file); the subclass proc itself carries no distinct assertion string
- **Struct layout:**

Frame instance = 0x132 bytes, allocated by FUN_0062bfc0 (FrApi.cpp). Fields touched at construction / used by dispatcher:
  +0x84 = 0, +0x88 = 0, +0x8c = 0 (init)
  +0x90 = 0x40
  +0xa8 = pointer to proc-chain array (each entry 0xc bytes: [0]=proc fn ptr, +4/+8 = per-proc rect/data used by FUN_00647170)
  +0xb0 = proc-chain entry count (bounds-checked by base dispatcher)
  +0xbc = frame handle/id (returned by create)
  +0x190 (dec 400) = create flags (param_2)
  +0x1c4 = 0
Subclass-attached sub-objects (not inline in the 0x132 struct): a 0x18-byte object (installed via msg 0x59) and a 0x156-byte layout/state object (installed via msg 0x58), plus a float opacity property. Paint proc FUN_00876880 treats msgframe[4] as the style/flags word and msgframe[2] as a pointer to the model; message payloads for paint/size/hit-test are rect arrays of >=13 floats.

- **Message protocol:**

FUN_008895d0(msgframe*, payload*, out) — a thin frame subclass that overrides only 3 messages and delegates the rest down the proc chain (base = FUN_00876610, ultimate base = FUN_00623670). msgframe layout confirmed from base dispatcher FUN_00647170: [0]=frame handle, [1]=msg, [2]=wparam/ptr, [3]=lparam, [4]=extra, [5]=proc-chain depth index.

CASES HANDLED:
- case 4 (INSTALL_BASE): OR 0x101001 into the style word *(payload[1]) (bits 0,12,20), and store base proc FUN_00876610 into *(payload[3]). Then chain via thunk_FUN_00647170.
- case 9 (CREATE/INIT, per-instance): (1) obj18 = FUN_007c3bc0(0x18); dispatch FUN_0062ef40(frame,0x59,obj18,0) — attach 0x18-byte model. (2) obj156 = FUN_007c3bc0(0x156); dispatch FUN_0062ef40(frame,0x58,obj156,0) — attach 0x156-byte layout/state model. (3) set opacity/alpha via FUN_00630080(frame,0,alpha) where alpha = opacity-table[7] (&DAT_00bfd658, via FUN_004990d0(7)) → normally _DAT_009407b8 (1.0), else 0. (4) install paint callback FUN_00876880 via FUN_0062f150(frame,FUN_00876880,0). Then chain to base.
- case 0x3b (detach/hide): if payload[0]==0 → FUN_0062fcb0(frame,1) (toggles state flag 0x200 / sends internal msg 0x36) + FUN_0062e560(frame), then chain; else assert FUN_00487a80(0x30).
- default: chain unchanged to base FUN_00876610.

The heavy lifting (paint=msg 8, size-query=msg 0x15, hit-test=msg 0x17 returning HT codes 2/9/10/0xc/0xd, plus msgs 5/6 tooltip, 0x20,0x2b,0x33,0x34,0x37,0x41,0x43,0x46 and the 0x10000141/0x10000142 value-set path) is performed by the attached callback FUN_00876880, which reads the style word at msgframe[4] and the model ptr at msgframe[2]. Control-specific setter/getter dispatch (msg >= 0x56, incl. the 0x58/0x59 model attaches) goes through FUN_0062ef40 → FUN_00647c80.

- **Create recipe:**

Created as a CHILD frame of an existing parent via the FrApi create primitive:
  FUN_0062bfc0(parent, flags=0, child_id, proc=0x008895d0, userdata=0, 0)
cdecl push order observed at callers (e.g. 0x004a7211, 0x004bcf09, 0x004d29ac, 0x0085b7f1): PUSH 0; PUSH 0(userdata); PUSH 0x008895d0(proc); PUSH child_id; PUSH 0(flags); PUSH parent; CALL 0x0062bfc0. Observed child_ids: 0xe, 0x11, 0x17, 0x23 (per-parent slot ids — pick a unique one within the parent). flags are always 0 at create; the real style word 0x101001 is OR'd in later by the case-4 INSTALL_BASE handler. No manual warm-up/sizing needed — case 9 self-initializes: it allocates and attaches the 0x18 and 0x156 model objects, sets opacity, and installs the paint callback. After create, drive it with the standard frame messages (paint 8 / size 0x15 / hit-test 0x17) which flow to FUN_00876880. Frame handle is returned in EAX (== *(frame+0xbc)).

- **Crash gotchas:**

- Model-attach dispatch FUN_0062ef40 asserts (FUN_00487a80 0xf2e/0xf2f) if frame==0 or msg < 0x56; the 0x58/0x59 attach msgs are intentionally in the >=0x56 control-specific range, do not renumber them below 0x56.
- case 0x3b asserts FUN_00487a80(0x30) unless payload[0]==0 — never send it with a non-zero wparam.
- Opacity setter FUN_00630080 asserts 0xf6b (frame==0), 0xf6c (alpha<0), 0xf6d (alpha>=DAT_009432c4) — keep opacity in [0, max).
- Base dispatcher FUN_00647170 asserts 0x221 (frame not found), 0x223/0x24b (proc-chain index msgframe[5] >= count at frame+0xb0) — corrupting msgframe[5], or freeing/destroying the frame mid-dispatch, faults hard.
- case 9 has NO double-init dup-guard (unlike the standard FUN_0047f340 assert path): re-sending msg 9 re-allocs and re-attaches the 0x18/0x156 models, leaking the previous ones.
- Paint callback FUN_00876880 dereferences msgframe[2] as the model pointer and indexes the payload as a large float rect array; sending paint/hit-test (8/0x17/0x15) before case 9 has attached the models, or with a short payload, dereferences garbage.


### GmCtlSkImage  (EXE 0x008c0430, confidence: high)

- **WASM:** not resolved (worked EXE-first; assertion string "P:\Code\Gw\Ui\Game\Controls\GmCtlSkImage.cpp" confirms identity directly in the EXE)
- **Assertion file:** P:\Code\Gw\Ui\Game\Controls\GmCtlSkImage.cpp
- **Struct layout:**

GmCtlSkImage instance = 0x20 bytes / 8 dwords. Allocated in case 9 via FUN_0047f340("...GmCtlSkImage.cpp",0x106) [0x106 = source line, NOT size] and freed in case 0xb via FUN_005acaeb(inst,0x20). Instance accessor = FUN_008c2280(param_1) (== **(msgframe+8)); asserts 0x118 if NULL. All 8 dwords are zero-initialised in case 9.

+0x00 base_frame  : handle to the underlying UICtl/UIFrame. Used as `*inst` for every framework call (FUN_0062fe20 style read, FUN_0062cfc0 get-child, FUN_0062bfc0 create-child, FUN_0062bd80 invalidate).
+0x04 info_id     : set by msg 0x5c. On change frees cached +0x08/+0x0c and calls FUN_0062bd80(base,0x20) (invalidate/relayout). A skill-info/lookup id.
+0x08 cached_res_a: lazily built heap resource; freed with FUN_0046f850. Rebuilt on paint; nulled whenever +0x04 or +0x10 changes.
+0x0c cached_res_b: lazily built heap resource (a GrModel/id object); freed with FUN_0046f850. Msg 0x57 reads it via FUN_00663e60 -> "HGrModel" to compute natural content size. Nulled with +0x08.
+0x10 skill_id    : set by msg 0x67 (range asserted 0..0xd6f). Drives icon load FUN_004a1b20(skill_id,1). On change: frees +0x08/+0x0c, invalidate(0x20), destroys child#7, rebuilds +0x14 texture, forwards to child#3, repaints.
+0x14 icon_tex    : skill-icon texture/image object = FUN_004a1b20(skill_id,1) (resolves skill record via FUN_005a6e20, picks icon at record +0x8c normal / +0x90 alt when FUN_0049b9e0(0x61) campaign gate / +0x94). Freed via FUN_008cbcb0; applied via FUN_008cbd10(tex,0).
+0x18 overlay_a   : set by msg 0x66; triggers FUN_008c02e0 (repaint path A).
+0x1c overlay_ctx : set by msg 0x58; compared via FUN_00525490(*(inst+0x1c)) against payload in the registered-message handlers (0x100000ef/0x100000f2); triggers FUN_008c22b0 (repaint path B).

- **Message protocol:**

Switch on msgframe[1]=msg. Lifecycle + control-specific getters/setters. Numbers are the raw msg ids.

-- Class lifecycle --
5  (init)    : FUN_008c1bd0() one-time class registration. Must have run once at UI startup.
6  (deinit)  : class teardown. Frees shared globals DAT_010823d4/d8/dc/e0 and the DAT_010823e4..414 texture table, decrements refcount DAT_01082418; when it hits 0 frees DAT_01082414 table. Asserts (0x841/0x846/0x48c...) on double-free / zero-refcount.

-- Instance lifecycle --
9  (create)  : asserts 0x105 if instance already set. Allocs 0x20, zeroes 8 dwords, stores base frame at +0x00, calls FUN_008c22b0(). If base has style 0x2000 (FUN_0062fe20): enables registered msgs via FUN_0062ef00 for 0x10000009,0x1000000a,0x10000020,0x100000ef,0x100000f2. Always enables 0x10000141.
0xb (destroy): frees +0x0c,+0x08 (FUN_0046f850), +0x14 (FUN_008cbcb0), frees instance (FUN_005acaeb,0x20), nulls *(msgframe[2]).

-- Paint / layout / input --
8  (paint)   : if base style & 0x20: FUN_008c0190 transform setup, FUN_0066da30(2)/FUN_0066fb20(2,quad), FUN_00665000, FUN_0062ba80(base,1,inst+3,5) draws icon, and if a hover/child#7 present creates overlay child (proc LAB_008cb190, child#7).
0x31(49)     : notification; if payload[1]==0xc && payload[2]==7 destroys child#7 (FUN_0062c550) + FUN_008c02e0.
0x37(55)     : pointer/pos event; builds a (x,y) float pair from payload and forwards msg 9 to child#6 (FUN_0062cfc0(base,6)->FUN_0062e8a0).

-- Registered (high-bit) events (skill-state change repaints) --
0x10000009 : asserts style 0x2000 (0x50e). If payload matches (thunk_FUN_007e0c40 == *payload) -> FUN_008c22b0 repaint.
0x1000000a : style-gated (0x51b) -> FUN_008c22b0.
0x10000020 : style-gated (0x526) -> FUN_008c22b0.
0x100000ef : style-gated (0x52f). If FUN_00525490(inst+0x1c)==*payload && payload[2]==0 -> FUN_008c22b0.
0x100000f2 : style-gated (0x53e). Same match on +0x1c -> FUN_008c22b0.
0x10000141 : if *payload==0x61 and +0x10 skill changed (FUN_004a1b20(inst+4,1) != inst+5): rebuild icon tex at +0x14, apply FUN_008cbd10.

-- Control-specific getters/setters (0x56..0x67) --
0x56(86)  : internal helper -- create child#2 (proc FUN_008c8d30), style 0xe. Used by the *set* messages to (re)build a sub-frame with a value.
0x57(87)  : GET natural/content size. Requires non-null out param_3 (assert 0x580). Writes {w=FUN_00663e60(*(inst+0xc)),0,0,1.0f,1.0f}.
0x58(88)  : SET overlay_ctx (+0x1c); repaint FUN_008c22b0.
0x59(89)  : SET background/ratio -> child#1 (proc LAB_008cafd0,style 3). Computes ratio payload[0]/payload[1]; 0 payload tears child down.
0x5a(90)  : forward GET-size (0x57) to child#1. payload must be non-null (assert 0x5cb).
0x5b(91)  : TOGGLE child#0 (proc FUN_008cae50,style 8) on non-null payload; destroy on null.
0x5c(92)  : SET info_id (+0x04); clears cached +0x08/+0x0c; invalidate FUN_0062bd80(0x20).
0x5d(93)  : SET child#3 (proc LAB_008cafe0,style 2) when payload float>0; else destroy.
0x5e(94)  : TOGGLE child#4 (proc LAB_008caff0,style 0xb).
0x5f(95)  : TOGGLE child#5 (proc FUN_008cb000,style 0xc).
0x60(96)  : SET child#6 (proc LAB_008cb180, create-flag 0x100, style 10). payload must be 0 or in 0x80..0x129 (assert 0x664).
0x61(97)  : TOGGLE child#8 (proc FUN_008cb1a0,style 0xd).
0x62(98)  : TOGGLE child#9 (proc LAB_008cb330,style 6).
0x63(99)  : TOGGLE child#10 (proc FUN_008cb340,style 9).
0x64(100) : SET child#0xc (proc LAB_008cb640,style 4) when payload float>0; else destroy.
0x65(101) : TOGGLE child#0xe (proc FUN_008cb660,style 5).
0x66(102) : SET overlay_a (+0x18); repaint FUN_008c02e0.
0x67(103) : SET skill_id (+0x10). Asserts <=0xd6f (0x726). Frees cached +0x08/+0x0c, invalidate(0x20), destroys child#7, rebuilds +0x14 icon tex from FUN_004a1b20(id,1)+FUN_008cbd10, forwards to child#3 (0x56), repaint FUN_008c22b0.
default/7,0xa,0xc..0x55 : no-op (return). Note base-proc install (case 4) is NOT handled here -> handled by the parent/base template, so this proc must be chained under the standard UICtl base.

- **Create recipe:**

GmCtlSkImage is a Gm-layer composite skill-icon control (icon + up to ~13 overlay sub-frames for recharge sweep, adrenaline, disabled tint, cost badge, hover popup, etc.). It is NOT created standalone from raw FUN_0062bfc0; it is installed as a registered control proc and instantiated by the UI framework. Recipe:

1. WARM-UP (once, at UI system startup): ensure class init msg 5 (FUN_008c1bd0) has run so the shared texture/global table (DAT_010823xx / DAT_01082414) and refcount DAT_01082418 are live. This proc chains under the standard UICtl base template, which supplies base-proc install (case 4) and the size/paint scaffolding.
2. CREATE the base frame with FUN_0062bfc0(parent, flags, childId, &FUN_008c0430, userdata, 0). For the registered skill-event messages (0x10000009/0a/20/ef/f2) to be armed, the base frame MUST carry style bit 0x2000 (FUN_0062fe20(base,0x2000)!=0); without it those handlers assert instead of repaint. Give it paint style bit 0x20 so msg 8 actually draws.
3. CONSTRUCT: framework sends msg 9 -> allocates the 0x20 instance, stores base at +0x00, enables the event messages. Do NOT send 9 twice (assert 0x105).
4. POPULATE via dispatcher FUN_0062ef40(base, msg, &payload, out):
   - msg 0x67 = skill_id (0..0xd6f)  -> loads the icon texture (mandatory to show anything).
   - msg 0x5c = info_id (optional context).
   - overlay toggles as desired: 0x59 progress/ratio, 0x5b/0x5e/0x5f/0x61/0x62/0x63/0x65 boolean overlays, 0x5d/0x64 float-gated overlays, 0x60 badge (0 or 0x80..0x129), 0x58/0x66 context ptrs.
   - msg 0x57 (needs non-null out) queries natural content size for layout.
5. DESTROY: framework sends msg 0xb (frees cached resources, texture, and the 0x20 instance). Class teardown is msg 6 (refcounted; only the last owner frees the shared table).

- **Crash gotchas:**

- Instance accessor asserts 0x118 if instance is NULL: every 0x56..0x67 setter and msg 8/0xb requires a completed msg-9 construct first.
- msg 9 asserts 0x105 if *(msgframe[2]) is already non-null -> never double-construct.
- Registered event handlers (0x10000009/0a/20/ef/f2) and their post-construct enable path call FUN_0062fe20(base,0x2000) and assert (0x50e/0x51b/0x526/0x52f/0x53e) with a no-return if the base frame lacks style bit 0x2000. Create the base with 0x2000 set.
- msg 0x67 skill_id > 0xd6f -> assert 0x726 (no return). Clamp/validate skill ids.
- msg 0x60 payload must be exactly 0 or within [0x80,0x129] -> assert 0x664.
- msg 0x57 requires non-null out buffer (assert 0x580); msg 0x5a requires non-null payload (assert 0x5cb).
- Class teardown (msg 6) asserts on any already-freed global (0x48c/0x492/0x496/0x49a/0x4a2) and on zero/underflow refcount DAT_01082418 (0x841/0x846). Do not deinit the class while instances still live or twice.
- Cached +0x08/+0x0c are heap (FUN_0046f850) while +0x14 icon tex is a resource object (FUN_008cbcb0) -- they use different free paths; mixing them corrupts the heap. They are auto-nulled on skill/info change, so external code must never free instance fields directly.
- FUN_004a1b20(skill_id,1) dereferences the skill record from FUN_005a6e20; a skill id with no valid record yields a null/garbage icon (no assert) -> blank draw, so validate ids exist.


### GmCtlSkList  (EXE 0x008c3350, confidence: high)

- **WASM:** ? (not resolved; EXE address was supplied directly, WASM symbol not needed for this catalog)
- **Assertion file:** P:\Code\Gw\Ui\Game\Controls\GmCtlSkList.cpp (game-layer, referenced by the owning control proc FUN_008c35f0 at 008c364c via FUN_0047f340(\"...GmCtlSkList.cpp\",0x65b))
- **Struct layout:**

0x14-byte instance: +0x00 parentFrameId, +0x04 mode(1..5), +0x08 displayKind, +0x0c glyphIdA, +0x10 glyphIdB (see message_protocol/create_recipe for full detail)

- **Message protocol:**

TWO cooperating frame procs belong to GmCtlSkList.cpp:

== FUN_008c3350 (THE TARGET) = paint/glyph child proc == switch on msgframe[1]:
  case 1  PAINT -> FUN_008c4260(frame, payload). payload[0]=sub-pass:
      1/2 = draw border cell from border atlas DAT_0108241c (2=hover,1=pressed offset); cell only if FUN_0062e2a0(frame)!=0
      3   = draw highlight cell from atlas DAT_01082420
      4/5 = draw icon glyph from large atlas DAT_01082424; atlas cell = f(payload[1] item/skill-type, pressed=(subpass==4)); icon-only branch (FUN_0062e2a0==0) allows type 0..4 else assert 0x2ee; full branch allows type 0..0x10 else assert 0x30e
      blit via FUN_0062b290(frame, rect=payload+2, atlas, cell, payload[6], payload[7]); guarded by `if(atlas!=0)`
  case 4  GET_BASE_PROC -> **(payload+0xc) = &LAB_0087ff50  (install parent/base proc; chains upward)
  case 5  CLASS_INIT -> asserts each global atlas is null (0x331/0x33c/0x347) then loads 3 shared atlases via FUN_0062d790: DAT_0108241c border(&DAT_0095042c,3), DAT_01082424 icons(&DAT_00b9ac68,0x24), DAT_01082420 highlight(&DAT_00949514,1)
  case 6  CLASS_SHUTDOWN -> asserts each atlas non-null (0x357/0x35b/0x35f), frees via FUN_0046f850, nulls them
  case 0xc  FUN_0062bd40(frame) layout/reset
  case 0x38 SIZE/DIM QUERY -> *(payload+8)[0..1] = _DAT_0095044c pair (default cell dimensions)
  default  thunk_FUN_00647170(frame,msg,wparam) base default handler

== FUN_008c35f0 = owning GmCtlSkList control proc (state + child factory) == switch on frame[1]:
  case 9  ALLOC: assert *inst==0 (0x65a); inst=FUN_0047f340(\"...GmCtlSkList.cpp\",0x65b)->0x14 bytes; seed [2]=0x11,[3]=[4]=0x187ca; store at *(frame[2]); create paint child FUN_0062bfc0(parent=inst[0], flags=0x280, child=0, proc=&LAB_0087fa80 base template, userdata={FUN_008c3350,0}, 0)
  case 0xb FREE: FUN_005acaeb(inst, 0x14)
  case 0xc dispatch to child (FUN_0062cfc0/FUN_0062c9c0) + FUN_008c59c0 repaint
  case 0x31 FUN_008c46f0(param) bulk config
  case 0x38 forward size query to child, copy pair out to *(param+8)
  case 0x56..0x5a SET DISPLAY STATE: set inst[1]=mode(1..5) (re-sends internal msg 0x5a when mode changes), then inst[2]=kind, inst[3]/[4]=glyph-id pair, then FUN_008c59c0 repaint. 0x56 param 0/1/2 (else assert 0x440); 0x57 param 0/!=0; 0x58 -> FUN_008c3be0(param,inst+2); 0x59 param 0/1/2 (else 0x4cd); 0x5a sets [2]=0x10,[3]=0x15bf0,[4]=0x15bf1

- **Create recipe:**

GmCtlSkList is a skill/effect icon control (border + icon glyph + highlight over a shared atlas set). It is NOT self-created by FUN_008c3350; the UI framework registers the owner proc FUN_008c35f0 and drives it:

1. CLASS WARM-UP (once, before any paint): send msg 5 to the paint proc so the 3 global atlases (DAT_0108241c/01082424/01082420) load. Painting before this simply no-ops (final `if(atlas!=0)` guard), so glyphs stay blank until warmed.
2. INSTANTIATE: send msg 9 to owner FUN_008c35f0 with msgframe[2] -> slot. It: (a) allocates 0x14-byte instance, (b) seeds [2]=0x11,[3]=[4]=0x187ca (default skill icon), (c) creates the paint child frame: FUN_0062bfc0(parent=inst[0], flags=0x280, child=0, proc=&LAB_0087fa80 [base template dispatcher], userdata={FUN_008c3350, 0}, 0). The registered proc is the base template LAB_0087fa80; FUN_008c3350 rides as userdata[0] (the derived paint override), and on msg 4 chains up to base LAB_0087ff50.
3. CONFIGURE: send one of msg 0x56..0x5a to the owner to select what the icon shows (mode/kind/glyph pair). Each call sets inst[1..4] and issues FUN_008c59c0 to repaint.
4. TEARDOWN: msg 0xb frees the instance (size 0x14); msg 6 (paint proc) frees the shared atlases at class shutdown.

Key constants: child frame flags = 0x280; instance size = 0x14; base template proc = LAB_0087fa80; base/parent proc installed on msg 4 = LAB_0087ff50; blit = FUN_0062b290 (textured quad, UV scale 1.0).

- **Crash gotchas:**

All FUN_00487a80(id) calls are NO-RETURN asserts (hard crash):
- Double-alloc: owner msg 9 asserts if instance slot already set (id 0x65a). Never send msg 9 to an already-created control.
- Class init/shutdown NOT idempotent: msg 5 asserts if an atlas is already loaded (0x331/0x33c/0x347); msg 6 asserts if an atlas is already null (0x357/0x35b/0x35f). Send init exactly once, shutdown exactly once, and only after init.
- Paint type-index bounds: icon-only mode (FUN_0062e2a0==0) accepts type 0..4 else assert 0x2ee; full mode accepts type 0..0x10 else assert 0x30e. A bad payload[1] crashes during paint.
- Set-API param validation: msg 0x56 param must be 0/1/2 (else 0x440); msg 0x59 param 0/1/2 (else 0x4cd); msg 0x5a path asserts 0x4d8. Out-of-range set values crash.
- Null-subframe guards (0x425, 0x4b2, 0x4d8, 1099) protect inst+2; structurally unreachable but present.
- Safe case: painting before msg 5 (atlases null) is a benign no-op due to `if(atlas!=0)` guard in FUN_008c4260 — no crash, just invisible icon.


### GmCtlVirtualJoystick  (EXE 0x008c5b10, confidence: high)

- **WASM:** ? (not resolved; game-layer Gm control, not needed — EXE proc found directly via embedded assertion string)
- **Assertion file:** P:\Code\Gw\Ui\Game\Controls\GmCtlVirtualJoystick.cpp (embedded literal in case 9 of FUN_008c5b10; alloc line 0x1ee)
- **Struct layout:**

Instance size = 0x1C (28 bytes / 7 dwords). Allocated in case 9 via FUN_0047f340("...GmCtlVirtualJoystick.cpp",0x1ee); freed in case 0xB via FUN_005acaeb(inst,0x1C). Instance ptr stored into *(msgframe[2]) i.e. *piVar1. Accessor per model: **(msgframe+8).

+0x00 (idx0) frame_token: = *msgframe (this frame's handle). Used as target of every FUN_0062ede0/FUN_0062ee80/FUN_0062ef40 dispatch.
+0x04 (idx1) cfg_a: default DAT_00bf4b04 = 1 (int). Overwritten from create payload[0] if payload (*param_2) non-null.
+0x08 (idx2) cfg_b: default DAT_00bf4b08 = 0x40400000 = 3.0f. Overwritten from create payload[1].
+0x0C (idx3) thumb_child: handle of the active joystick-knob child frame; 0 when idle. Created by FUN_008c6400 (FUN_0062bfc0(parent,0,1,&LAB_008c5ae0,&pt,0)); destroyed by FUN_0062c550. Guards all drag/release logic.
+0x10 (idx4) capture_source: id of the input source that grabbed the stick; default 0xFFFFFFFF. Set = *param_2 on press; matched against *param_2 on move/release.
+0x14 (idx5) press_mode: 0 = mouse/pointer path (opened via 0x3D, moved via 0x3E, released via 0x3C/0x3F); 1 = touch path (opened via 0x24, released via 0x2E).
+0x18 (idx6) enabled_state: 0 default. case 0x56 toggles frame style (7/0 when enabled, 0/0xFFFFFFFF when disabled) via FUN_0062ede0.

- **Message protocol:**

Dispatch: FrameProc(param_1=msgframe, param_2=payload, param_3=out). switch on msgframe[1]=msg. piVar1=msgframe[2] (holds inst ptr slot). ALL handled cases fall through to base thunk_FUN_00647170(frame,payload,out) at the end (except case 0x3D which returns early after forwarding).

case 9  CREATE: alloc 0x1C, init [1]=DAT_00bf4b04(1), [2]=DAT_00bf4b08(3.0f), [3]=0, [4]=0xFFFFFFFF, [5]=0, [6]=0; FUN_0062ede0(frame,0,0xffffffff) (base style); store inst into *piVar1; if payload(*param_2)!=0 override [1]=payload[0],[2]=payload[1]; FUN_006302c0(frame,1,0) (set style flag 1).
case 0xB DESTROY: FUN_005acaeb(inst,0x1C) free.
case 0x0A,0x0C-0x23,0x25-0x2C,0x2F,0x30,0x32-0x37,0x39-0x3B,0x40-0x55: no-op (explicit empty), then base.
case 0x24 (36) TOUCH-PRESS BEGIN: if payload[4]!=0 && thumb_child==0: capture_source=payload[0], press_mode=1, FUN_008c6400(payload+2) spawns thumb, FUN_0062ee40(payload[0]).
case 0x2D (45) TICK/RETARGET: if thumb_child!=0: FUN_0062ef40(thumb_child,0x56,payload,0).
case 0x2E (46) TOUCH-RELEASE: if thumb_child!=0 && payload[0]==capture_source && press_mode!=0: FUN_0062c550(thumb_child); thumb_child=0; capture_source=0xFFFFFFFF; FUN_0062ee80(frame,8,0,0); press_mode=0.
case 0x31 (49): if payload[1]==1 && payload[2]==7: FUN_0062ee80(frame,7,payload[3],0).
case 0x38 (56) MEASURE/SIZE-QUERY: *(payload[2])=payload[0]; *(payload[2]+4)=payload[1] (writes size into caller struct).
case 0x3C/0x3F (60/63) MOUSE-RELEASE: if thumb_child!=0 && payload[0]==capture_source && press_mode==0: destroy thumb, reset source, FUN_0062ee80(frame,8,0,0).
case 0x3D (61) MOUSE-PRESS BEGIN: if payload[4]!=0 && payload[5]==0 && thumb_child==0: capture_source=payload[0], press_mode=0, FUN_008c6400(payload+2) spawn thumb, *param_3=1, forward to base and RETURN (early).
case 0x3E (62) MOUSE-MOVE/DRAG: if thumb_child!=0 && payload[0]==capture_source && press_mode==0: FUN_0062ef40(thumb_child,0x57,payload,0) (drag update to knob).
case 0x56 (86) SET-ENABLED: if payload[0]!=enabled_state: enabled_state=payload[0]; if 0 -> FUN_0062ede0(frame,0,0xffffffff) else FUN_0062ede0(frame,7,0).
default: forward to base thunk_FUN_00647170 and return.

Sub-frame spawn FUN_008c6400(inst,pt): reads pointer coords, normalizes via FUN_006275c0/FUN_004a2180 (scale *(+100)) and FUN_00627600, computes local point, creates knob child FUN_0062bfc0(frame,0,1,&LAB_008c5ae0,&pt,0) -> inst[3], then FUN_0062ee80(frame,8,1,0). LAB_008c5ae0 is the inline knob/thumb child proc (not a first-class function; renders/tracks the draggable knob and consumes 0x56/0x57 tick+drag messages).

- **Create recipe:**

This is a game-layer touch/pointer virtual-joystick control (Gm namespace). Recipe:
1) Create the frame with FrameProc = 0x008c5b10 using the base create primitive FUN_0062bfc0(parent, flags, child, proc=0x008c5b10, userdata, 0). The framework then drives msg 4 (install base/parent proc into *(payload[3])) followed by msg 9 (alloc instance) automatically.
2) Optional create payload: pass *param_2 as a 2-dword array [cfg_a, cfg_b] to override defaults +0x04 (default 1) and +0x08 (default 3.0f). Pass NULL to keep defaults.
3) No extra warm-up messages required for display: case 9 self-installs base style (FUN_0062ede0 frame,0,0xffffffff) and FUN_006302c0(frame,1,0). Send msg 0x56 with payload[0]=1 to enable/show, payload[0]=0 to disable (style swap).
4) Sizing: respond-path — the control answers measure query 0x38 by writing requested [w,h] (payload[0],payload[1]) into the caller-supplied struct at payload[2]; you feed it via the parent layout, no explicit size setter here.
5) Interaction lifecycle is automatic: pointer/touch press opens a knob child (0x24 touch or 0x3D mouse), drag routes 0x3E->0x57 to the knob, tick routes 0x2D->0x56, release (0x2E touch / 0x3C/0x3F mouse) tears the knob down. Do NOT open a second press while thumb_child(+0x0C)!=0 — all begin-cases guard on it.

- **Crash gotchas:**

- FUN_0062ede0 / FUN_006302c0 assert-and-abort (FUN_00487a80) if frame handle (+0x00) is 0. Never dispatch paint/style before case 9 has run and stored a valid frame token.
- case 9 alloc line 0x1ee; the alloc helper FUN_0047f340 asserts if the instance slot (*piVar1) is already populated — do NOT send msg 9 twice for one frame.
- Struct is exactly 0x1C bytes; free (case 0xB) frees 0x1C. Treating it as larger reads garbage; the 0x1ee passed to alloc is the source line, not the size.
- Press/begin handlers key off thumb_child(+0x0C)==0 AND capture_source(+0x10). If you inject a synthetic 0x24/0x3D while a knob is live, it silently no-ops; if you desync capture_source, release cases 0x2E/0x3C/0x3F/0x3E will never match (*param_2==+0x10) and the knob child leaks (never FUN_0062c550'd).
- press_mode(+0x14) must stay consistent: mouse open (0x3D,mode0) can only be closed by 0x3C/0x3F (mode0 guard); touch open (0x24,mode1) only by 0x2E (mode!=0 guard). Crossing paths leaves an orphaned knob frame.
- case 0x3D returns EARLY after forwarding to base and sets *param_3=1 (handled/consume). Other cases fall through to base once; don't assume uniform post-processing.
- FUN_008c6400 dereferences pointer/scale globals (FUN_004a2180 +0x64) and payload+2 as a coord pair — calling the spawn path with a malformed payload (fewer than payload[4]/[5] present) can fault.


### GmCtlSelection  (EXE 0x008c65b0, confidence: high)

- **Assertion file:** P:\Code\Gw\Ui\Game\Controls\GmCtlSelection.cpp
- **Struct layout:**

Instance struct allocated in case 9 via FUN_0047f340("P:\\Code\\Gw\\Ui\\Game\\Controls\\GmCtlSelection.cpp", 0x87) => 0x87 (135) bytes. This derived proc only touches the first 8 bytes; the remainder is owned by the base control template reached through thunk_FUN_00647170.

Instance layout (stored at *(int*)msgframe[2], i.e. *piVar1):
  +0x00  void*  frameHandle / render context. Set in case 9 from *msgframe (msgframe[0]). Passed as arg0 to the reticle draw (FUN_004a54f0) and to FUN_0062ede0 at registration.
  +0x04  uint32 styleFlags. Init 0 in case 9.
           bit0 (0x1)  = "selected" bracket variant (message 0x56 sets/clears). Passed as param_5 to FUN_004a54f0.
           bit1 (0x2)  = "hover/target" bracket variant (message 0x57 sets/clears). Passed as param_4 (via flags>>1 & 1) to FUN_004a54f0.
  +0x08..+0x86  reserved/base-template state (untouched by this proc).

msgframe layout (param_1, undefined4*): [0]=frame/control handle, [1]=msg id (switch selector), [2]=pointer to the instance slot (piVar1; *piVar1 = instance ptr). payload = param_2.

Reticle geometry: FUN_004a54f0(ctx, float* rect, 0, hoverBit, selectedBit, 0) reads rect as float[4] (x,y,w,h at payload+0xc), insets by margin _DAT_009413c8, and picks color/variant index iVar1 = (selected!=0)+1 when hover set, else 0, indexing (&PTR_DAT_00be69b4)[iVar1]. Final draw goes through FUN_0062b8e0 -> FUN_00635470 (corner-bracket reticle). If both style bits are 0, nothing is drawn.

- **Message protocol:**

FrameProc FUN_008c65b0(msgframe* param_1, payload* param_2, arg param_3) switches on msgframe[1]:

- case 8  (RENDER/UPDATE reticle): gated by (payload[0] & 1). Reads instance flags (inst[1]); calls FUN_004a54f0(inst[0], payload+0xc /*float[4] rect*/, 0, (flags>>1)&1 /*hover*/, flags&1 /*selected*/, 0) to draw the corner-bracket reticle around the target rect. Then chains base proc. (This control paints on msg 8, not msg 1.)
- case 9  (CREATE/ALLOC): asserts (FUN_00487a80(0x86)) if instance already set. Allocs 0x87 bytes via FUN_0047f340(file,0x87). instance[0]=msgframe[0] (frame handle), instance[1]=0 (flags). Stores ptr into *piVar1. Registers into render tree: FUN_0062ede0(inst[0], 0, 0xffffffff). Chains base.
- case 0xb (DESTROY/FREE): if instance set, frees via FUN_005acaeb(instance, 8). Chains base.
- case 0x56 (SET SELECTED bit0): payload!=0 => flags|=1, payload==0 => flags&=~1. If changed, FUN_0062bd40(inst[0]) to invalidate/repaint. Falls through to base chain.
- case 0x57 (SET HOVER/TARGET bit1): payload!=0 => flags|=2, payload==0 => flags&=~2. If changed, FUN_0062bd40(inst[0]) invalidate. Falls through to base chain.
- default / all cases: tail-call thunk_FUN_00647170(msgframe, payload, arg) (base/parent proc). No local case 1, case 4, or case 0x15 — layout/paint-pass/size-query are all delegated to the base template.

Notable: there is NO case 4 (parent-proc install) in this derived proc; base install is handled by the template FUN_00647170 chain.

- **Create recipe:**

Verified from creator FUN_008cde20 (this is how the game spawns the selection reticle as a child of a game/world frame):

  child = FUN_0062bfc0(parentFrame /*=*msg[0]*/, flags=0, childOrder=0, proc=FUN_008c65b0, userdata=0, 0);
  FUN_0062f5a0(child, 0xffffffff);   // warm-up: set clip/order sentinel to -1

Sequence:
  1. Create the child frame with FUN_0062bfc0(parent, 0, 0, FUN_008c65b0, 0, 0). This synthesizes and dispatches msg 9 (create) to the proc, which allocates the 0x87-byte instance and registers a render node via FUN_0062ede0(inst,0,-1).
  2. Warm-up FUN_0062f5a0(child, 0xffffffff).
  3. Drive state each frame:
       - Set target rect + paint: dispatch msg 8 with payload = { byte gate(bit0=1), pad..., float rect[4] at +0xc }.
       - Toggle selected bracket: FUN_0062ef40(child, 0x56, nonzero_or_0, out).
       - Toggle hover/target bracket: FUN_0062ef40(child, 0x57, nonzero_or_0, out).
  4. Teardown: dispatch msg 0xb (free) before destroying the frame.

Dispatch through FUN_0062ef40(frame, msg, wparam, out). Style bits are order-independent; at least one of bit0/bit1 must be set for anything to draw.

- **Crash gotchas:**

- Double-create: dispatching msg 9 when the instance slot (*piVar1) is already non-zero triggers assert FUN_00487a80(0x86) (no-return). Never send create twice.
- Msg 8 before create: case 8 dereferences *piVar1 (instance) and inst[0]; if the instance was never allocated (no msg 9) this reads a null/garbage slot. Always create first.
- FUN_0062ede0 asserts (line 0x574) if inst[0] (frame handle) is 0 — msgframe[0] must be a valid frame when create runs.
- Reticle rect (payload+0xc) must be valid float[4]; FUN_0062b8e0 asserts on its own atlas args (0xe7a..0xe7f) — power-of-two texture dims and non-null context are validated downstream; a malformed draw context asserts, not just no-op.
- FUN_004a54f0 asserts (line 0xb1) only in an impossible branch (param_4==0 && param_5==0 after the outer guard) — safe in practice, but implies at least one style bit must be consistent with the guard.
- Freeing (msg 0xb) only runs when instance is set; sending 0xb twice is a silent no-op (guarded by *piVar1 != 0), but the frame's memory is released — do not reference inst afterwards.
- Style setters 0x56/0x57 only invalidate (FUN_0062bd40) when the bit actually changes; redundant sets are cheap no-ops.


### GmCtlSkCard  (EXE 0x008c6750, confidence: high)

- **WASM:** unresolved (game-layer Gm control; resolved directly via EXE assertion string "P:\\Code\\Gw\\Ui\\Game\\Controls\\GmCtlSkCard.cpp" embedded in case 9)
- **Struct layout:**

Instance = 0x1fc (508) bytes, allocated in case 9 via FUN_0047f340("P:\\Code\\Gw\\Ui\\Game\\Controls\\GmCtlSkCard.cpp",0x1fc). Accessed as inst = **(msgframe[2]) (piVar1=msgframe[2]; inst=*piVar1). Verified fields:
+0x00 u32 frameHandle  -> self frame id; copied from msgframe[0] (*local_18) at create; first arg to every FUN_0062cfc0/FUN_0062bfc0/FUN_0062f1a0 child op.
+0x04 u32 skillId      -> current skill (0=none). Init 0. Set by msg 0x58. Passed to skill-data lookup FUN_005a6e20(id), to FUN_004f9e10/FUN_004f9960 (description calc), and dispatched as 0x67 to icon child.
+0x08 u32 styleFlags   -> Init 0. Toggled by msg 0x57 (inst[2] ^= payload). bit0 -> re-inits child0 via FUN_0062cfc0(...,0x5c...); bits 0x2/0x4 -> tag/no-tag description mode (chooses string res 0x387 vs 0x388) and triggers refresh.
+0x0c u32 contextId    -> Init 0. Set by msg 0x56. Used as 2nd arg to FUN_004f9960(skillId,ctx) in refresh and as event filter for global msg 0x10000030; also emitted in hover-region payload (case 0x24 local_10).
+0x10..+0x1fb: scratch/reserved (~0x1ec bytes) used by refresh string builders (name/tag/description composition) and child bookkeeping; not touched by the FrameProc directly.
Note: skill-data struct returned by FUN_005a6e20(skillId) fields referenced: +0x29,+0x2a (event guard bytes), +0x34/+0x35/+0x36/+0x38 (stat presence flags), +0x3c (float stat), +0x44 (type, 0x20000=special), +0x4c (stat, sentinel 0x7fffffff), +0x98 (name string id).

- **Message protocol:**

FrameProc FUN_008c6750(msgframe, payload); msg = msgframe[1]; inst = *(int*)msgframe[2]. Cases:
- 9 CREATE/ALLOC: alloc 0x1fc; zero +4/+8/+0xc; asserts FUN_00487a80(0x1fb) if slot already set. Builds children: ImgIcon(idx0, flags0, proc LAB_008c1b80[thunk]) + FUN_0062ede0(icon,0,0xffffffff); TxtDesc(idx5, flags 0x20000, proc FUN_00878340, userdata=&local struct); TxtName(idx7, flags 0x80000, proc FUN_00610c40)+FUN_0062f4b0(,8); TxtTag(idx6, flags 0x88000, proc FUN_00610c40)+FUN_0062fcb0(,0)+FUN_0062f4b0(,2). Sets layout style FUN_0062f1a0(*inst,L"GmCtlSkList-Description-NoTag"). Subscribes globals via FUN_0062ef00: 0x10000030, 0x10000065, 0x10000141.
- 0xb DESTROY: if slot set, FUN_005acaeb(inst,0x10) (free).
- 0x24 (36) DRAW/REGISTER-HOVER-REGION: only if skillId(+4)!=0 and *payload==0. Queries icon child geometry (FUN_0062ee80 msg 8 then msg 7), scales by UI-scale _DAT_009407b0 & _DAT_00a4cbc8, spawns transient frame FUN_0062c210(0,&LAB_008c1b80,...), pushes 0x67(skillId) to it, then FUN_0062ed80(*inst,*payload,0,8,{skillId,ctx,8},0xc) to register hit region.
- 0x26 (38): delegates to thunk_FUN_00637a90 (default hit/cursor helper).
- 0x56 (86) SET-CONTEXT: if payload!=inst+0xc, store inst+0xc=payload, fall to refresh.
- 0x57 (87) SET-STYLE-FLAGS: v=inst[2]^payload; if unchanged return; inst[2]=payload; if (v&1) re-init child0 (FUN_0062cfc0(*inst,0,0x5c,payload&1,0)->FUN_0062ef40); if (v&6)==0 return else refresh.
- 0x58 (88) SET-SKILL: FUN_008c6b60(inst,skillId): if same return; inst+4=skillId; icon child 0x67(skillId); 0x5e(empty?); destroy stat children idx1..4 (FUN_0062c550); if skillId!=0 read skill-data and (re)create SkillStat1..4 sub-controls (proc LAB_008c80e0, userdata=&skillId) conditioned on skill-data flags; asserts 0x199 (both stat flags) and 0x1ce (type 0x20000 + flag+0x36); then refresh + FUN_0060e1d0(enable child5).
- Global 0x10000030: match only if payload[0]==inst+0xc AND skill-data(+0x29)==*payload[1] -> refresh.
- Global 0x10000065: match only if skill-data(inst+4)(+0x2a)==payload -> refresh.
- Global 0x10000141: match only if *payload==0x32 -> refresh.
- default: no-op.
REFRESH FUN_008c6d80(inst): builds description string (FUN_007c3bc0/FUN_004f9e10/FUN_004f9960/FUN_004f9e50) into child5 via FUN_0060a420; name string (skill-data+0x98) into child7 (FUN_00611320); tag: if flags bit1->res 0x387, elif bit2->res 0x388 into child6 and style "GmCtlSkList-Description-Tag" else "GmCtlSkList-Description-NoTag".

- **Create recipe:**

1) Parent instantiates as a child control: FUN_0062bfc0(parentFrame, flags, childIndex, &FUN_008c6750 (or its JMP thunk 0x008c6b50), userdata, L"<name>"). Framework auto-sends msg 9 which allocs the 0x1fc instance and builds ImgIcon/TxtDesc/TxtName/TxtTag children and subscribes the three global events — no manual child creation needed.
2) Optional pre-config: send msg 0x56 (contextId) and/or 0x57 (styleFlags) to set attribute/profession context and tag-mode before populating.
3) Populate: send msg 0x58 with the skill id (via dispatcher FUN_0062ef40(frame,0x58,skillId,0)). This drives the icon, rebuilds SkillStat sub-controls, and triggers the description/name/tag refresh. Card renders blank until a non-zero skill id is set.
4) Sizing/layout is data-driven: the control positions children by named layout styles ("GmCtlSkList-Description-Tag"/"-NoTag") and UI-scale globals (_DAT_009407b0, _DAT_00a4cbc8); there is no explicit case 0x15 size-query handler here — geometry is delegated to the framework/children.
5) Teardown: framework sends msg 0xb to free.

- **Crash gotchas:**

- Double-create: msg 9 calls FUN_00487a80(0x1fb) (no-return assert) if the instance slot is already non-null. Never send create twice / reuse an occupied slot.
- Malformed skill data in msg 0x58 path (FUN_008c6b60): asserts FUN_00487a80(0x199) if the skill has both stat-presence flags (skill+0x35 ptr!=0 AND skill+0x38!=0); asserts 0x1ce if skill type(+0x44)==0x20000 while flag(+0x36)!=0. Only feed valid skill ids from the game skill table (FUN_005a6e20 must resolve).
- skillId 0 is a safe "clear" (blanks card) — not a crash.
- contextId(+0xc) is dereferenced/used in FUN_004f9960 during refresh; passing a bogus context handle can fault the description calc. Set a valid context (or leave 0) before/with SetSkill.
- Child procs are indirect JMP thunks (LAB_008c1b80 = E9 rel32 -> real ImgIcon proc; LAB_008c80e0 = SkillStat proc); they must be present/relocated correctly or the create calls install a bad proc.
- The three subscribed globals (0x10000030/65/141) call refresh with skill-data guards; if inst+4 points to a freed skill after teardown ordering issues, refresh could read stale skill data — ensure msg 0xb ordering.


### GmCtlSkProgress (child fill/overlay frame proc)  (EXE 0x008c6e70, confidence: high)

- **WASM:** ? (not needed — EXE resolved directly from assertion string "P:\\Code\\Gw\\Ui\\Game\\Controls\\GmCtlSkProgress.cpp" @ 0x00b9afdc; xref -> FUN_008c6e70)
- **Assertion file:** P:\Code\Gw\Ui\Game\Controls\GmCtlSkProgress.cpp (string @ 0x00b9afdc). Both procs assert against it: child FUN_008c6e70 alloc line 0x65 (101); container FUN_008c70c0 alloc line 0x135 (309).
- **Struct layout:**

CHILD instance (FUN_008c6e70), 0x24 bytes / 9 dwords. Allocated in case 9 via FUN_0047f340(file, line=0x65); freed in case 0xb via FUN_005acaeb(ptr, 0x24). (Note: FUN_0047f340's 2nd arg is the SOURCE LINE for leak-tracking, NOT the size — confirmed because the container variant frees only 0xc bytes though its alloc "arg" was 0x135.)

+0x00 frame_handle        int    <- msgframe[0] (*puVar4 = *param_1); this child frame's own handle, passed to every render/anim call
+0x04 texture_atlas       ptr    <- descriptor[0]; MUST be non-null (assert 0x9c). Source texture/atlas for the blit
+0x08 tex_width           int    <- descriptor[1]; exact power of two (=16)
+0x0c tex_height          int    <- descriptor[2]; exact power of two (=16)
+0x10 uv/color_0          u32    <- descriptor[3]
+0x14 uv/color_1          u32    <- descriptor[4]
+0x18 uv/color_2          u32    <- descriptor[5]
+0x1c uv/color_3          u32    <- descriptor[6]
+0x20 rewind_duration     float  <- descriptor[9]; compared to sentinel _DAT_00949130; reused by msg 0x3b as the rewind animation duration

The progress animation inputs descriptor[7]=fill_duration(float) and descriptor[8]=end_fraction(float,=1.0) are consumed immediately in case 9 (kick off FUN_0062cb00) and are NOT stored in the instance.

CREATE DESCRIPTOR (the case-9 payload; param_2 -> *param_2 -> piVar2), 10 dwords / 0x28 bytes, built on the container's stack (FUN_008c70c0 case 0x58):
[0] texture ptr (&DAT_00b9b068 / &DAT_00b9b070)  [1] 0x10 width  [2] 0x10 height  [3..6] uv/color dwords  [7] fill_duration(float)  [8] 1.0f end_fraction  [9] aux float -> instance+0x20

CONTAINER instance (FUN_008c70c0), 0xc bytes / 3 dwords (freed 0xc in case 0xb):
+0x00 frame_handle  +0x04 bound_skill_ptr (set/read by msgs 0x5a/0x59)  +0x08 hover/hittest_bool (msg 0x34)

- **Message protocol:**

CHILD FrameProc FUN_008c6e70 switch(msgframe[1]):
- case 8  RENDER/PAINT: inst = *(msgframe[2]); assert non-null (0x77). If paint-payload flag (*param_2 & 0x20) set, blit the textured progress quad: FUN_0062b790(frame=inst[0], colorPayload=param_2+0xc, uv=&inst[4], texture=inst[1], dims=&inst[2], 4, 0, layer=5, 0). Texture-dim/layer asserts live in FUN_0062b790.
- case 9  CREATE/INIT: assert slot empty (0x64); alloc 0x24 (line 0x65); inst[0]=msgframe[0]; assert descriptor ptr non-null (0x99) and descriptor[0]/texture non-null (0x9c); copy descriptor[0..6]->inst[1..7], descriptor[9]->inst[8]. Then FUN_0062ede0(inst[0],0,0xffffffff) (set color = opaque white). Then FUN_0062cb00(inst[0], 0.0, end=descriptor[8], dur=descriptor[7], mode=4) to start the fill animation. If descriptor[9]!=sentinel _DAT_00949130: FUN_00630080(inst[0],0,descriptor[7]).
- case 0xb DESTROY: if slot set, FUN_005acaeb(inst,0x24); zero slot.
- case 0x3b (59) REWIND/RESET: inst = slot; assert non-null (0x77). If *param_2==0: cur = FUN_0062d2f0(inst[0]) (read current fill fraction); FUN_0062cb00(inst[0], cur, 0.0, dur=inst[8], mode=1) — animate current->0.
(No case 1/4/0x15 handled here — this child does not install a base proc or answer size-query; parenting/base is handled by the primitive create + the container.)

CONTAINER FrameProc FUN_008c70c0 (the outer GmCtlSkProgress, drives the child): 9 create(alloc 0xc; installs a hyperlink child FUN_0062bfc0(...,&LAB_008c1b80) and a body child ...&LAB_00884a40, sets styles, FUN_0062ef40(child,0x62,3,0)); 0xb destroy(free 0xc); 0x31 mouse enter/leave -> FUN_0062ee80(...,7/8); 0x34 hittest/hover -> updates inst+0x08 + FUN_0062f470; 0x37 pass-through; 0x56/0x57 hide/show -> FUN_008c7a20(0/1); 0x58 BUILD-BARS (creates the two FUN_008c6e70 fill children, see recipe); 0x59 GET bound skill (*param_3 = inst+0x04); 0x5a SET skill (binds skill ptr, FUN_0062ef40(child,0x67,skill,0)); 0x5b SET progress value/duration -> FUN_0062cfc0(...,4) then 0x62.

- **Create recipe:**

This child is NEVER created standalone by app code — it is instantiated by the container FUN_008c70c0 in message 0x58 ("build bars"). Exact sequence per fill layer:
1. Container already exists (its own instance = *puVar2, frame handle inst[0]).
2. Build a 10-dword descriptor on the stack: [0]=texture ptr (&DAT_00b9b068 for layer A / &DAT_00b9b070 for layer B), [1]=0x10, [2]=0x10, [3..6]=uv/color globals, [7]=fill_duration float, [8]=1.0f (0x3f800000) end-fraction, [9]=aux float.
3. Guard: only create if FUN_0062fe20(parent, 0x1000) == 0 (style bit 0x1000 clear).
4. child = FUN_0062bfc0(parent=inst[0], flags=0x100, childId=2 (layer A) or 3 (layer B), proc=FUN_008c6e70, userdata=&descriptor, 0).  -> fires msg 9 into FUN_008c6e70 with the descriptor.
5. FUN_0062f5a0(child, zorder)  -> zorder 3 for layer A, 2 for layer B (two stacked fill quads).
6. After both children built: on the container's sub-frame FUN_0062cfc0(*puVar2,4): FUN_0062ef40(sub,0x62,0,0) then FUN_0062ef40(sub,0x60,0,0) to prime initial state.
7. Drive progress at runtime by sending container msg 0x5b (value) / 0x5a (bind skill); container relays to the fill children.
Warm-ups/sizing: flags 0x100 (child, style-inheriting); the fill texture is fixed 16x16 (power-of-two, mandatory); layer index passed to the blit is 5 (must be <=9); color initialized opaque white (0xffffffff).

- **Crash gotchas:**

- Send msg 9 (CREATE) BEFORE any 8 (PAINT) or 0x3b (REWIND): those deref the instance slot and assert FUN_00487a80(0x77) if null.
- Re-sending msg 9 while the slot is already populated asserts (0x64) — one instance per frame.
- Descriptor must be fully populated: null descriptor ptr asserts 0x99; descriptor[0]/texture null asserts 0x9c.
- Animation bounds (FUN_0062cb00): end-fraction descriptor[8] must be in [0.0,1.0] (assert 0xec9 if <0, 0xeca/0xecb if >1); duration descriptor[7] must be > 0 (assert 0xecc/0xecd). The rewind (0x3b) reuses inst+0x20 as duration — must be >0 too.
- Blit (FUN_0062b790): tex_width/tex_height (inst[2]/inst[3]) must be EXACT powers of two (asserts 0xe7c/0xe7d) and width>=height (0xe7e); texture handle inst[1] non-null (0xe7f); layer index <=9 (0xe7b) — the hard-coded 5 is fine.
- Do not free with the wrong size: destroy path frees exactly 0x24; the container frees 0xc — mismatched sizes corrupt the tracked heap.
- FUN_0047f340's 2nd arg (0x65/0x135) is a SOURCE LINE for leak tracking, NOT the alloc size; do not treat 0x65 as the struct size (actual instance is 0x24).


### GmCtlSkStat  (EXE 0x008c7d30, confidence: high)

- **WASM:** not-present (no matching WASM symbol; assertion file "P:\\Code\\Gw\\Ui\\Game\\Controls\\GmCtlSkStat.cpp")
- **Assertion file:** P:\Code\Gw\Ui\Game\Controls\GmCtlSkStat.cpp
- **Struct layout:**

GmCtlSkStat instance struct (0xC bytes, allocated in case 9 via FUN_0047f340("...GmCtlSkStat.cpp",0x1af)):
  +0x00 dword  frameHandle   -- copied from *msgframe (the owning UI frame handle); target of child-create calls
  +0x04 dword  skillId       -- from creationParams[0]; bounded <=0xD6F, indexes skill table DAT_009837e8 (stride 0xA4) via FUN_005a6e20
  +0x08 dword  statType      -- from creationParams[1]; selects which stat field to show AND indexes icon table &DAT_00b9b078[statType*4]

Skill record source (FUN_005a6e20 -> &DAT_009837e8 + skillId*0xA4). Fields read by the value formatter FUN_008c7ba0(skillId,statType):
  statType 1: (u16 @skill+0x38)/DAT_009448a0 (scaled ratio)
  statType 2: constant 5
  statType 3: u8 @skill+0x35 -> FUN_005a6e60 lookup
  statType 4: u8 @skill+0x36
  statType 5: float FUN_004f9a90(skillId)
  statType 6: u32 @skill+0x4C
  statType 7: constant 1
  statType 9: u8 @skill+0x34
  default:    FUN_007c3bc0(3)

Refresh-listener object (FUN_008c7d00, 0xC bytes, line 0xD0): { +0x00 vtable=&PTR_FUN_00b9b0c8 (={0x008c7b40,0x008c7b70,0x00417c40,0x004a0430}), +0x04 skillId, +0x08 statType } registered via FUN_00630180 to re-render when skill data changes.

Two child primitives created in construct:
  child 0 (icon):  FUN_0062bfc0(frame,0x300,0,&LAB_00611400,0,0); FUN_00604a70(child,DAT_01082438,DAT_00b9b078[statType]) -- textured icon from shared atlas DAT_01082438
  child 1 (value): FUN_0062bfc0(frame,0x88300,1,FUN_00610c40,<encoded text>,0) -- standard Engine CtlText.cpp control (proc FUN_00610c40); FUN_0062f4b0(child,1)

- **Message protocol:**

FrameProc FUN_008c7d30(msgframe*, payload*), switch on msgframe[1]=msg. Instance slot piVar2=*(msgframe[2]); creationParams=payload (payload[0]=params ptr for construct). NOTE: this game-layer (Gm) control does NOT use the base template's case1-paint/case4-install/case0x15-size; it uses control-specific 0x37/0x38 and one-time class resource msgs 5/6:
  case 5  CLASS-INIT (one-time): if DAT_01082438==0 -> DAT_01082438=FUN_0062d790(0x13,7,0x12,&{16,16},&{0x80,0x20},&DAT_00b9b104,0xb) (shared icon atlas/font resource). Else ASSERT(0x12F).
  case 6  CLASS-FREE: if DAT_01082438!=0 -> FUN_0046f850(it); =0. Else ASSERT(0x140).
  cases 7..0x36  no-op (return) -- common frame/mouse/etc msgs ignored here.
  case 9  CONSTRUCT: ASSERT(0x1AE) if slot already set; alloc 0xC struct; copy frameHandle=*msgframe; ASSERT(0x149) if payload[0]==0; read skillId/statType from *payload[0]; create icon child0 + text child1; register refresh listener (FUN_00630180 w/ FUN_008c7d00,size 0xC).
  case 0xB DESTRUCT: if *slot!=0 -> FUN_005acaeb(*slot,0xC) (free instance); else no-op.
  case 0x37 PAINT/RENDER: x=payload[0], y=payload[1]; child0=FUN_0062cfc0(frame,0,0x8a,&ctx,0);FUN_0062e8a0(child0); FUN_0062ec50(_DAT_0093c89c,0x10,&ctx); child1=FUN_0062cfc0(frame,1,0x8a,&ctx,0);FUN_0062e8a0(child1) -- draws icon then value.
  case 0x38 MEASURE/SIZE-QUERY: out rect=payload[2]; accumulates child0+child1 preferred sizes via FUN_0062d2a0(...,FUN_0062cfc0(frame,i)); writes summed width to out[0], max height to out[1].
  default: return.
Dispatcher/accessors per model: FUN_0062ef40 dispatch, FUN_00618aa0 instance accessor, FUN_0062bfc0 create-primitive, FUN_0062fe20 style-read.

- **Create recipe:**

GmCtlSkStat is a composite skill-stat widget = [icon child0] + [formatted value text child1] for one skill attribute.
1. CLASS-INIT once at startup: send msg 5 to create the shared icon atlas DAT_01082438 (FUN_0062d790(...,&DAT_00b9b104,0xb)). Must happen before any instance construct because child0 binds DAT_01082438 via FUN_00604a70. Tear down with msg 6 at shutdown.
2. CONSTRUCT: send msg 9 with payload[0] = pointer to a 2-dword params block {skillId, statType}. skillId<=0xD6F. statType in {1,2,3,4,5,6,7,9} (others hit default formatter and, importantly, an UNCHECKED icon-table index).
   - Framework must have the instance slot (*(msgframe[2])) zeroed first (double-construct asserts 0x1AE).
   - Construct auto-creates: child0 icon (flags 0x300, proc LAB_00611400) textured from DAT_01082438 + icon table DAT_00b9b078[statType]; child1 text (flags 0x88300, standard CtlText proc FUN_00610c40) whose string = FUN_008c7ba0(skillId,statType) encoded value; FUN_0062f4b0(child1,1).
   - Registers a data-change listener (FUN_00630180 + FUN_008c7d00 clone) so the value auto-refreshes.
3. LAYOUT: parent sends 0x38 to get preferred size (icon width + text width, max height).
4. PAINT: parent sends 0x37 with payload = {x,y,...}; proc renders child0 (icon) then child1 (value text).
5. DESTRUCT: send msg 0xB to free the instance.
No case-4 base-proc install and no default paint(case1) are handled by this proc itself; rely on the Gm control framework for common event routing.

- **Crash gotchas:**

- msg 9 ASSERT(0x1AE) on double-construct (instance slot non-zero). Zero the slot before constructing.
- msg 9 ASSERT(0x149) if payload[0]==0: creation params {skillId,statType} pointer is MANDATORY.
- msg 5 ASSERT(0x12F) on double class-init (DAT_01082438 already set); msg 6 ASSERT(0x140) on free-before-init.
- skillId must be <=0xD6F (3439) or FUN_005a6e20 ASSERT(0xEF6) reading skill table (stride 0xA4).
- statType icon lookup &DAT_00b9b078[statType*4] is UNBOUNDED in construct -> out-of-range statType yields a garbage icon-frame pointer passed to FUN_00604a70 (crash/corrupt). The value formatter FUN_008c7ba0 has a default case, but the icon table does not.
- Ordering hazard: constructing an instance before class-init (msg 5) leaves DAT_01082438==0, so FUN_00604a70 binds a null atlas.
- Value depends on live skill record fields (+0x34/+0x35/+0x36/+0x38/+0x4C); a refresh listener (vtable PTR_FUN_00b9b0c8) is installed - don't free the instance while it remains registered (destruct msg 0xB frees via FUN_005acaeb; must go through it, not a raw free).


### GmCtlBadgeList  (EXE 0x008c8230, confidence: high)

- **WASM:** ram:8129e956 (TCtlInstance<IUi::Game::CBadgeList>::MsgProc); related: 8129e5a7 CBadgeList::CtlMsgProc, 8129e86e GmCtlBadgeListProc, 8129d8fa UpdateBadges, 8129dfd3 OnFrameSize, 812a1ae3 OnCtlLayout, 812a1921 Ptr
- **Assertion file:** P:\Code\Engine\Controls\CtlInstance.h (generic TCtlInstance template header, line 0xaf; the concrete type is IUi::Game::CBadgeList, confirmed via WASM symbols)
- **Struct layout:**

CBadgeList instance = 0x38 bytes (14 dwords), alloc "CtlInstance.h":0xaf, vtable &PTR_FUN_009404a4:
+0x00  void** vtable (=&PTR_FUN_009404a4)
+0x04  FrameId owning frame handle (set at construct; used as *(inst+4) in all child ops)
+0x08  embedded subobject (24 bytes, ctor FUN_006017e0 / dtor FUN_00601810) — internal list/state
+0x20  uint badgeMask (bitmask of visible badge slots; only bits 0..2 used; popcount -> badge count)
+0x24  slot[0] resource/icon handle (retained via FUN_0046bf20, released via FUN_0047f3a0)
+0x28  slot[1] resource/icon handle
+0x2c  slot[2] resource/icon handle
+0x30  shared payload/data ptr (forwarded to badge children lacking own handle)
+0x34  int layoutFlag (0=tight, nonzero=spaced horizontal)
Child badge userdata table DAT_00b9b11c = {0,1,3} indexed by slot 0..2.

- **Message protocol:**

FrameProc FUN_008c8230(FrameMsgHdr* param_1, void* payload, void* out). Switches on param_1[1]=msg. Instance ptr via FUN_004a0440(param_1) = **(param_1+8) (== model's accessor, asserts non-null). Instance = iVar6.

LIFECYCLE:
- case 4/5/6: no-op (base template install pass-throughs; fall to base).
- case 9 CONSTRUCT: asserts *(param_1[2])==0 (not already built); allocs 0x38-byte instance via FUN_0047f340("CtlInstance.h",0xaf); sets vtable +0x00=&PTR_FUN_009404a4; constructs embedded subobject at +0x08 (FUN_006017e0); zero +0x20/+0x30/+0x34; stores instance into *(param_1[2]); sets +0x04=frame(*param_1) and FUN_00602020(frame); +0x20 = *payload (initial badge bitmask); calls FUN_008c8720 (UpdateBadges/relayout); calls vtable[0](instance+2); forwards to base.
- case 0xb DESTRUCT: releases 3 resource slots at +0x24/+0x28/+0x2c (loop x3 FUN_0047f3a0), destructs subobject +0x08 (FUN_00601810), frees 0x38 bytes (FUN_005acaeb), clears *(param_1[2])=0; forwards to base.

PAINT / GENERIC (forwarded to base FUN_004a0440+thunk_FUN_00647170): cases 1,3,7,8,0xa,0xc,0xf,0x13,0x15,0x20,0x24-0x2a,0x2c,0x2e,0x31,0x32,0x34-0x36,0x3a-0x3f,0x44-0x46,0x4b,0x4c,0x4e,0x4f,0x52 (includes paint=1 and size-query=0x15).

LAYOUT:
- case 0x37 (OnCtlLayout): computes uniform scale from constraint payload[0]/[1] vs natural size (FUN_008c8170), clamps to 1.0, then walks child frames (FUN_0062caa0 iterate) positioning each badge horizontally with per-item advance = base(_DAT_0094d1b0) or spaced(_DAT_009413d8) depending on +0x34 flag; forwards to base.
- case 0x38 (OnFrameSize/measure): forwards to base first, then fills *(payload[2]) with natural size from FUN_008c8170 and rescales by min(w/natW,h/natH,1.0).

CONTROL SETTERS (default branch; each asserts instance present, then after 0x56/0x57/0x58 calls FUN_008c8720 to rebuild child badges):
- 0x56 SetBadgeMask: instance+0x20 = payload (uint bitmask, only low 3 bits meaningful -> up to 3 badges).
- 0x57 SetSharedPayload: instance+0x30 = payload (fallback data forwarded to each badge child via child-msg 0x57 when its slot handle is 0).
- 0x58 SetSlotHandle: payload[0]=slot index (asserts index<3 else FUN_00487a80(0x8b)); instance+0x24+index*4 = FUN_0046bf20(payload[1]) (retained resource/icon handle), after FUN_0047f3a0.
- 0x59 SetLayoutFlag: instance+0x34 = payload (bool; nonzero = spaced/horizontal layout using _DAT_009413d8 advance, zero = tight _DAT_00948a30); then invalidates frame (FUN_0062f470) and forwards to base.
- any other default msg: forward to base.

CHILD REBUILD (FUN_008c8720 UpdateBadges): FUN_0062c760(frame) begin; for slot i in 0..2, if bit i of +0x20 set, create child frame FUN_0062bfc0(frame, flags=0, childId=i, proc=&LAB_0087a4a0, userdata=(&DAT_00b9b11c)[i]={0,1,3}, 0), set z-order FUN_0062f5a0(child,-i); if slot handle +0x24+i*4==0 send child msg 0x57 with +0x30, else bind resource via FUN_00630180(child,0,FUN_00895bd0,handle,...). FUN_0062f470(frame) end/invalidate.

- **Create recipe:**

Do NOT create GmCtlBadgeList as a top-level frame; it is a game-layer child control installed by parent widgets. Verified pattern (from parent FUN_008a03b0, also FUN_008a1580/FUN_008a4900):
1. Create the child frame under the parent: FUN_0062bfc0(parentFrame, flags=0, childId=7, proc=&LAB_008c8220 [trampoline -> FUN_008c8230], userdata=initialBadgeMask, 0). LAB_008c8220 is the registration trampoline whose only xref target is this proc.
2. FUN_0062ede0(child,0,0xffffffff) to set full-span layout weight.
3. If already existing, toggle visibility FUN_0062fcb0(child,1) and re-push mask via FUN_0062ef40(child,0x56,badgeMask,0).
4. Configure content: send 0x56 (badge bitmask, low 3 bits), optional 0x57 (shared payload), 0x58 per slot (payload={index<3, handle}) to bind up to 3 icons, and 0x59 (layout flag; parent uses bit10 of its style word: *(parent+0x28)>>10 & 1).
5. Message send uses FUN_0062ef40(child,msg,wparam,out). Each 0x56/0x57/0x58 auto-rebuilds children (FUN_008c8720); order-independent, but set mask before/with slots.
Construction (msg 9) and destruction (msg 0xb) are driven by the framework, not sent manually.

- **Crash gotchas:**

- Instance accessor FUN_004a0440 (**(param_1+8)) asserts (FUN_00487a80(0x2b)/(0x2c)) if the msgframe slot or instance ptr is null — never send control setters (0x56-0x59) before the framework has run construct (msg 9), or it aborts.
- msg 9 asserts *(param_1[2])==0: sending a second construct on an already-built instance calls FUN_00487a80(0xae) (no-return) — do not double-create.
- msg 9 also asserts the freshly stored instance equals the accessor result (FUN_00487a80(0xb1)).
- msg 0x58 asserts slot index < 3 (FUN_00487a80(0x8b)); indices 0..2 only — passing >=2 (i.e. 3+) as float-cast index aborts. Bitmask +0x20 likewise only honors 3 bits.
- Default branch asserts if instance present but *(instance)==0 (FUN_00487a80(0x2c)) and if param_1[2] non-null but *(int*)param_1[2]==0 (FUN_00487a80(0x149)) — a half-torn-down instance will abort rather than no-op.
- Resource handles in slots are retained (FUN_0046bf20) and released x3 at destruct; overwriting a slot via repeated 0x58 leaks/rebinds through FUN_0047f3a0 — always route through the message, do not poke +0x24 directly.
- All 0x56/0x57/0x58 trigger a full child rebuild (FUN_008c8720) which recreates child frames each call; batching many sets per frame causes churn.


### GmCtlSkCapture (IUi::Game::GmCtlSkillCaptureProc)  (EXE 0x008c8d30, confidence: high)

- **WASM:** IUi::Game::GmCtlSkillCaptureProc(FrameMsgHdr const&, void const*, void*) — WASM ram:~0x81164000 (string xrefs at ram:811641bf / 811641f5)
- **Assertion file:** P:\Code\Gw\Ui\Game\Controls\GmCtlSkCapture.cpp (WASM string ram:0010d7c9 = "../../../../Gw/Ui/Game/Controls/GmCtlSkCapture.cpp")
- **Struct layout:**

Instance struct = 0x14 (20) bytes. Allocated in case 9 via FUN_0047f340("...GmCtlSkCapture.cpp", 0x103); freed in case 0xb via FUN_005acaeb(inst, 0x14). NOTE: the 0x103 arg to FUN_0047f340 is an alloc TAG/id, NOT the byte size — true size (0x14) is the free size. (Confirmed by comparison: parent GmCtlSkImage allocs tag 0x106 but frees 0x20.)

Layout (offsets confirmed by field access):
  +0x00  u32   base/header (untouched by this proc; zeroed by allocator)
  +0x04  u32   base/header (untouched)
  +0x08  u32   frameHandle  <- msgframe[0] (the owning frame); used as target for FUN_0062ba80 render-submit and FUN_0062c550 self-destroy
  +0x0c  u32   meshHandle   <- render mesh/quad-group built in case 9 (FUN_00663cc0 result, FUN_00664ba0(mesh,6)); freed with FUN_0046f850 in case 0xb
  +0x10  f32   elapsedTime  <- accumulated animation time; init 0 in case 9, += delta each 0x52 tick; when > DAT_009407b8 the frame self-destroys

Message-frame layout (param_1, the FrameMsgHdr): [0]=frameHandle(owner), [1]=msg, [2]=&instanceSlot (piVar1; *piVar1 = instance ptr). param_2 = message payload (for 0x52 it is float* deltaTime).

- **Message protocol:**

switch on msgframe[1]:
- case 0x08 PAINT/RENDER-SUBMIT: FUN_0062ba80(frame=+0x08, 1, &mesh(=+0x0c), 4) -> submits the built mesh to render pass 4. (This control family paints on msg 8, not msg 1.)
- case 0x09 CREATE/INIT: assert if slot already set (FUN_00487a80(0x102)); alloc 0x14-byte instance; store frame at +8; build a textured quad/mesh: local color/uv struct assembled from DAT_00b9b1xx globals -> FUN_008c87e0(&verts) (emits 0x12 verts / 8-index quad list via FUN_00657070(0xc,0x103,...)), FUN_0065efa0(...,0x20003e0,...) material, FUN_00663cc0 -> meshHandle at +0xc, FUN_00664ba0(mesh,6); free temp buffers; set elapsedTime=0; FUN_0062ede0(frame,0,0xffffffff) (set visible clip/interval); FUN_0062ef00(frame,0x52) (subscribe/enable the 0x52 update-tick message).
- case 0x0b DESTROY: FUN_0046f850(mesh at +0x0c); FUN_005acaeb(inst,0x14); clear slot.
- case 0x52 (82) ANIMATION TICK: param_2 = float* dt. elapsedTime(+0x10) += *dt; t = min(elapsedTime/DAT_00943280, 1.0). Piecewise alpha curve using DAT_00943208/DAT_00943258, floored by DAT_00937ec8, scaled by DAT_00944218 -> packs into RGBA via FUN_0046df70 and FUN_006641e0(mesh,&rgba) (per-vertex color). Then three transform layers set via FUN_008c90e0(layerIdx 0/1/2, scale, offset) using DAT_00940ec8/00944928/009407b0/00943280/00943288/00948c18. If elapsedTime > DAT_009407b8 -> FUN_0062c550(frame): the flash finishes and destroys itself.
- cases 0x0a, 0x0c..0x51 and default: no-op (fall through to return). No size-query, no base-install (case 4) and no get/set (0x56+) implemented — this is a leaf visual-only child frame.

Helper FUN_008c90e0(layer, colorScale, param): reads frame world transform (FUN_0062d380), builds a scaled/translated quad transform (FUN_0066da30/FUN_00670010/FUN_0066f890) and applies color via FUN_00665000(mesh at +0x0c, colorScale). Drives the 3-layer expanding-ring flash.

- **Create recipe:**

Not created standalone by user code — it is a private child frame of the GmCtlSkImage control (skill icon). Parent = FUN_008c0430 = IUi::Game::GmCtlSkImageProc.

Spawn site (parent case 0x56, at EXE 0x008c08a2):
  child = FUN_0062bfc0(ownerFrame, 0x80 /*flags*/, 2 /*sub-frame index*/, FUN_008c8d30 /*this proc*/, 0 /*userdata*/, 0);
  FUN_0062f5a0(child, 0x0e);   // set paint sub-pass / z-order = 14 (draws on top)
The framework then auto-delivers msg 9 (init) -> the proc builds the mesh, subscribes to msg 0x52, and the flash animates and auto-destroys.

Trigger chain: parent GmCtlSkImage receives "capture progress" set-message 0x59 with a progress fraction > 0 -> routes 0x56 down to the capture sub-frame layer -> this proc's sub-frame (index 2) is created. When progress reaches its end / on completion the 0x52 ticks drive elapsedTime past DAT_009407b8 and FUN_0062c550 tears it down.

To reproduce manually: create/own a GmCtlSkImage frame, then FUN_0062bfc0(frame,0x80,2,0x008c8d30,0,0) + FUN_0062f5a0(child,0xe); do NOT send msg 9 yourself (framework does it). Feed msg 0x52 with a float* dt each frame to animate, or let the frame's own update subscription drive it.

- **Crash gotchas:**

- Double-init asserts: case 9 calls FUN_00487a80(0x102) (no-return) if the instance slot (*msgframe[2]) is already non-null. Never send msg 9 twice to the same slot.
- FUN_0047f340 second arg (0x103) is an allocation TAG, not a size; the real instance size is 0x14 (from the free FUN_005acaeb(inst,0x14)). Don't assume 0x103 bytes — allocating/copying 0x103 bytes over this 20-byte struct corrupts the heap.
- case 0x52 dereferences param_2 as float* (delta time) unconditionally — passing a null/garbage payload with msg 0x52 reads *param_2 and crashes.
- Self-destruct: once elapsedTime(+0x10) exceeds DAT_009407b8 the proc calls FUN_0062c550(frame) which destroys the frame from inside its own message handler; the following msg 0xb frees mesh(+0xc) and the 20-byte struct. Holding a stale pointer to the instance or mesh after a 0x52 tick is a use-after-free.
- meshHandle(+0xc) is only valid between case 9 and case 0xb; case 8 paint submits it every frame — painting after destroy would submit a freed mesh.
- Do not treat this as a top-level control: it has no case 4 (base-proc install), no 0x15 (size query), no 0x56+ get/set. It only responds to 8/9/0xb/0x52; all other messages are silently ignored, so generic control drivers expecting size/hit-test replies will get nothing.


### GmCtlSkImageEffect  (EXE 0x008c91a0, confidence: high)

- **Assertion file:** P:\Code\Gw\Ui\Game\Controls\GmCtlSkImageEffect.cpp
- **Struct layout:**

Instance = 256 bytes allocated (FUN_0047f340 size 0x100) but only 0x1c used and freed with size-class 0x1c; treated as undefined4[] (puVar6[n]=+4*n):
+0x00 void*  frame        // owning control/frame handle (=*param_1 at create); target of all paint/invalidate/dispatch
+0x04 float  alpha        // opacity / recharge-fill amount 0..1; default 1.0 (0x3f800000); set by msg 0x56
+0x08 int    frameIndex   // current animation frame 0..15; init = rand()&0xf (FUN_0046d0c0); advanced by tick, wraps at 16
+0x0c float  frameTimer   // per-frame accumulator; init = rand float (FUN_0046d130(0,_DAT_0094bc68)); vs _DAT_0094bc68 threshold
+0x10 float  lifetime     // remaining lifetime countdown; init = _DAT_009432c4; set by msg 0x57; decremented by tick
+0x14 float  fadeStart    // lifetime value at which blink/fade begins; set by msg 0x57 (clamped); decayed during fade
+0x18 int    toggle       // expired/blink flag; init 0; set to 1 when lifetime expires; XOR-toggled during fade (hides fill in paint when !=0)
+0x1c .. 0xff  unused/reserved (over-allocated)

Parent (GmCtlSkImage, FUN_008c0430, "GmCtlSkImage.cpp" size 0x106) instance is a separate ~0x20 struct; slot table entries via FUN_0062cfc0(frame, slot) — this effect lives at child slot 1.

- **Message protocol:**

CONFIRMED FrameProc FUN_008c91a0(msgframe* param_1, float* payload). Switches on param_1[1]=msg. Instance accessor FUN_008cad60(param_1) = **(int**)(param_1+8) (i.e. *(int*)param_1[2]); it ASSERTS (0x112) if the instance ptr is null, so every get/set/paint/tick that isn't alloc will crash if sent before msg 9.

This is a GAME-layer (Gw\Ui\Game\Controls) leaf control, so message IDs differ from the engine template: there is NO case 4 (parent/base install), NO case 1 paint, NO case 0x15 size-query. Alloc=9 / free=0xb match engine convention; paint=8, tick=0x45.

Cases:
- 5  RESOURCE-INIT: if global atlas DAT_01082440==0, create it via FUN_0062d790(0xf,0xd,0x18a, &{0x40,0x40}, &{0x100/*=256*/}, &DAT_00b9b1f4, 0x10) -> 16-frame (0x10) 64x64 tile / 256px sheet animation atlas. If already created, ASSERT 0x14d (no-return).
- 6  RESOURCE-SHUTDOWN: FUN_0046f850(DAT_01082440); DAT_01082440=0. ASSERT 0x15e if null.
- 8  PAINT: inst=FUN_008cad60. Only if (payload[0] & 1) (visible flag). FUN_0062d910(atlas, inst.frameIndex[+0x08], &uvA,&uvB) resolves the current frame UVs, then draws TWO textured quads via FUN_0062b2d0(inst.frame[+0x00], ...): a "filled" portion whose height = (payload[6]-payload[4]) * alpha[+0x04] (forced 0 when toggle[+0x18]!=0) and the remainder quad with swapped UVs — a vertical reveal/recharge sweep over the skill icon. Uses payload[3..6] as the paint rect. Frees the temp UV handle (FUN_0046f850).
- 9  ALLOC INSTANCE: asserts (0x105->via *(param_1[2])!=0 path, ASSERT 0xff) if already set. FUN_0047f340("...GmCtlSkImageEffect.cpp",0x100) -> 256-byte instance. Inits fields (see struct), stores at *(void**)param_1[2], then FUN_0062ef00(inst.frame,0x45) to schedule the recurring animation tick.
- 0xb FREE INSTANCE: if set, FUN_005acaeb(inst,0x1c) (free, size-class 0x1c); *(param_1[2])=0.
- 0x45 TICK (payload = delta-seconds float): frameTimer[+0x0c]+=dt; if >= _DAT_0094bc68 (per-frame duration) advance frameIndex[+0x08] (wrap at 0x10=16), reset timer, invalidate (FUN_0062bd80(frame,1)). Then if lifetime[+0x10]>0: lifetime-=dt; if it crossed <0 set toggle[+0x18]=1 (expired) + invalidate; else once lifetime<=fadeStart[+0x14] run blink/fade: toggle[+0x18]^=1, decay fadeStart by a clamped step, invalidate.
- 0x56 SET-ALPHA/PROGRESS (payload=float): clamp to [0,1] (>_DAT_00937188 ->1.0, <_DAT_00937ec8 ->0.0); if changed, alpha[+0x04]=v and invalidate. This is the recharge-fill amount.
- 0x57 SET-LIFETIME/DURATION (payload=float): lifetime[+0x10]=max(0,v); fadeStart[+0x14]= (v>_DAT_00937ed0 ? _DAT_0093c89c : v); toggle[+0x18]=0.
- 7,0xa,0xc..0x44,0x46..0x55 and default: no-op break/return.

Dispatch/invalidate primitives used: FUN_0062bd80(frame,mask)=invalidate/dirty, FUN_0062ef00(frame,msg)=post-self message.

- **Create recipe:**

This is a CHILD control spawned by parent GmCtlSkImage (FUN_008c0430); it is not created standalone. Spawn/refresh sequence (parent msg 0x59 "set effect progress"):
1) child = FUN_0062bfc0(parentFrame /*=*inst*/, 0x80 /*flags*/, 1 /*child slot*/, &LAB_008cafd0 /*thunk that JMPs to 0x008c91a0*/, 0 /*userdata*/, 0);
   -- create only if FUN_0062cfc0(parentFrame,1) returned 0 (no existing child).
2) FUN_0062f5a0(child, 3);            // render layer / z = 3
3) FUN_0062ede0(child, 0, 0xffffffff); // color mask = opaque white
4) FUN_008c02e0();                     // parent relayout/notify
5) FUN_0062ef40(child, 0x56, &progressRatio, 0);  // send SET-ALPHA (0..1)
Optional lifetime (parent msg 0x5a): FUN_0062ef40(child, 0x57, &duration, 0).

Internal warm-up (handled by the proc itself): on msg 9 (alloc) it inits the struct and self-posts msg 0x45 (FUN_0062ef00(frame,0x45)) to start the animation loop; the shared 16-frame atlas is lazily built once on msg 5 (FUN_0062d790) and freed on msg 6. To manually stand one up for testing you must: (a) ensure atlas init (msg 5) has run, (b) create the frame with proc 0x008cafd0/0x008c91a0 via FUN_0062bfc0 under a valid parent, (c) let the engine deliver msg 9 before sending 8/0x45/0x56/0x57.

- **Crash gotchas:**

- Accessor FUN_008cad60 ASSERTS 0x112 (FUN_00487a80, NO-RETURN) if the instance ptr *(param_1[2]) is null: sending paint(8)/tick(0x45)/set(0x56/0x57) before the alloc(9) hard-crashes.
- msg 9 ASSERTS 0xff if the instance already exists (double-alloc) — never send 9 twice.
- msg 5 ASSERTS 0x14d if atlas already built; msg 6 ASSERTS 0x15e if atlas is null (double-free / free-before-init). The atlas DAT_01082440 is a PROCESS-GLOBAL shared resource with no refcount here — msg 6 frees it unconditionally, so a stray shutdown can pull the texture out from under other live effect instances.
- Allocated with size 0x100 but freed with size-class 0x1c (FUN_005acaeb(inst,0x1c)); the mismatch is intentional (over-alloc) — don't "fix" it.
- Not a top-level/base control: it has no case 4 base-install, so it must be parented by GmCtlSkImage; instantiating it under the wrong parent leaves +0x00 frame/slot wiring invalid.
- payload semantics differ by message: 0x45/0x56/0x57 take a float* (single float), but 8 takes a paint payload where [0] is a flags word (bit0=visible) and [3..6] are rect floats — passing the wrong payload shape misreads geometry.
- Tick relies on _DAT_0094bc68 (frame duration) and several float consts (_DAT_00937188/00937ec8/00937ed0 clamps); frameIndex must stay 0..15 or FUN_0062d910 indexes past the 16-tile atlas.


### GmCtlSkListGroup  (EXE 0x008cd0b0, confidence: high)

- **WASM:** unresolved — game-layer control, assertion file "P:\Code\Gw\Ui\Game\Controls\GmCtlSkListGroup.cpp" (not the Engine\Controls template layer); resolution not required, EXE addr was given directly and confirmed via the cpp string literal inside case 9.
- **Assertion file:** P:\Code\Gw\Ui\Game\Controls\GmCtlSkListGroup.cpp
- **Struct layout:**

GmCtlSkListGroup instance = 0x28 bytes (10 dwords). Allocated in case 9 via tracked allocator FUN_0047f340("...GmCtlSkListGroup.cpp", 0x349 [source-line/alloc tag, NOT the size]); freed in case 0xB with FUN_005acaeb(inst, 0x28). Instance pointer stored at *(msgframe[2]).

Offsets (idx = dword index):
+0x00 [0] owning frame id  (init from *msgframe[0]; every child op uses FUN_0062cfc0(this[0], childIdx))
+0x04 [1] attribute-A / column param broadcast to every child skill-row via msg 0x5A (set by msg 0x61; init 0)
+0x08 [2] pointer to dynamically-allocated short[] label/id buffer (built in warm-up; freed in case 0xB; init 0)
+0x0C [3] label-buffer secondary field (capacity/aux; zeroed on destroy; init 0)
+0x10 [4] label-buffer element count / length (init 0; set in warm-up; asserts if 0 -> 0x24b)
+0x14 [5] 0x80  (default style/flags constant; init 0x80)
+0x18 [6] live child-row counter (++ on msg 0x58 add, -- on msg 0x59 remove; drives header count display via FUN_007c3be0(0xe9b9,...))
+0x1C [7] texture/skin id pushed to the HEADER child via msg 0x58 (set by msg 0x63/99; init 0)
+0x20 [8] base/context id (set in warm-up from descriptor+0; returned by GET msg 0x5F; init 0xFFFFFFFF then overwritten)
+0x24 [9] mode/sort selector (init 3; set by msg 0x62; broadcast to children via msg 0x5B; when in {0,1} installs sort cb FUN_008ccea0 + compare cb FUN_008ccfe0, else clears them)

Two child frames (via FUN_0062cfc0(this[0], idx)):
  child 0 = HEADER sub-frame  (created only if label buffer non-empty; proc LAB_0087e240, flags 0x300)
  child 1 = SCROLLING LIST frame (proc LAB_00612b90, flags 0x8300) — the actual container that paints/lays-out rows
Per-row skill frames are created under child 1 with proc LAB_008ced50.

- **Message protocol:**

Dispatcher FUN_0062ef40(frame,msg,wparam,out); child accessor FUN_0062cfc0(frame,idx: 0=header,1=list). NOTE: this control implements NO case 1 (paint), case 4 (base-install) or case 0x15 (size-query) — all standard template msgs 0xA,0xC..0x55 fall through as no-ops; it is a pure composite/group that relies on its two child frames for paint+layout.

LIFECYCLE:
 0x09 CREATE — assert 0x348 if instance slot already set; alloc 0x28 + init defaults; run warm-up FUN_008cdb40(descriptor). payload param_2 = construction descriptor (see recipe).
 0x0B DESTROY — free label buffer at [2] (FUN_0047f3a0 if set), zero [2]/[3]/[4], free instance (0x28).

INPUT/EVENT ROUTING:
 0x31 UI event pump — sub-dispatch on param_2[1] (category 0/1) and param_2[2] (subcode, stored as raw-int-in-float: 1=0x1,7,8,9). Forwards mouse enter/leave/press/release (msgs 0x9-0xD) to header child and click routing (FUN_0062ee80 / FUN_00612b00 / FUN_008cdac0) to the list child.
 0x37 hover/move — compute local x/y (param_2[0],param_2[1]); forward 0x130 to header child, 0x60 to list child.
 0x38 hit-test-with-writeback — like 0x37 but writes hit coords into *param_2[2] and forwards 0x130 to both children with extra arg param_2[2].

SELECTION / ITEMS:
 0x56 reset/clear selection on list child (FUN_00612b20).
 0x57 advance selection — read current sel, iterate, set, fire callback FUN_008cdac0.
 0x58 ADD ROW — FUN_00612900(listChild, style, id=(rowIdx|colIdx<<16), &LAB_008ced50, payload); push [1] via msg 0x5A and [9] via msg 0x5B; ++[6]; refresh header count. Asserts 0xFE if row-id>0xFFFF, 0xFF if col/index>0xFFFF.
 0x59 REMOVE ROW — FUN_00520320(listChild, key); assert 0x23A if row not found, assert 0x241 if [6]==0; --[6]; refresh count. Also used internally as a per-child GET during 0x5C/0x5E enumeration.
 0x60 SELECT BY HANDLE — param_2 = handle (<0x10000, else assert 0xFE); set selection, fire msg 8 (selection-changed) to header child.

GETTERS (all assert on null out-param param_3):
 0x5A is-empty -> *param_3 = (firstChild==0); assert 0x24A if param_3 null.
 0x5B forward msg 0x57 to child; assert 0x25C.
 0x5C get current selection -> forwards msg 0x59, out into param_3; assert 0x26A.
 0x5D get row count -> FUN_008cda40 (walks children) -> *param_3; assert 0x281.
 0x5E bulk-export entries -> enumerate children (msg 0x59) into caller's growable array descriptor param_3 (ptr/cap/len triple + inline growth via FUN_00473880/FUN_004738f0); assert 0x28A.
 0x5F get base/context id [8] (offset 0x20) -> *param_3; assert 0x2B2.

SETTERS:
 0x61 set attribute-A [1]; broadcast to every child row via msg 0x5A (only if changed).
 0x62 set mode [9]; broadcast via msg 0x5B; install/clear sort(FUN_008ccea0)+compare(FUN_008ccfe0) callbacks when mode in {0,1}.
 0x63 (99) set texture/skin [7]; push to header child via msg 0x58; relayout (FUN_0062fcb0/FUN_0062f470/FUN_0062f110).

- **Create recipe:**

GmCtlSkListGroup is a COMPOSITE group; you do not paint it, you construct it and feed it rows.

1) Parent: have a live parent frame id.
2) Send msg 0x09 to the GmCtlSkListGroup frame proc with param_2 = pointer to a construction descriptor:
     descriptor+0x00 -> stored to instance[8] (base/context id, later readable via msg 0x5F)
     descriptor+0x04 -> label text ptr. If non-null, warm-up builds a short[] label buffer (len = FUN_0046c270(text)+1) and creates the HEADER child (proc LAB_0087e240, flags 0x300, then pushes texture via msg 0x58). If null, a 1-element empty buffer is made and NO header child is created.
     descriptor+0x08 -> passed to FUN_00612c30 on the list child (list config/context).
3) Warm-up FUN_008cdb40 automatically creates the SCROLLING LIST child:
     FUN_0062bfc0(this[0], 0x8300, 1, &LAB_00612b90, 0, 0); FUN_00612c30(list, descriptor+0x08); FUN_0062fcb0(list, this[7]).
   Base create primitive is the standard FUN_0062bfc0(parent, flags, childOrder, proc, userdata, 0): header flags=0x300 order=0; list flags=0x8300 order=1.
4) Configure (order-independent): msg 0x63 texture/skin, msg 0x61 attribute-A, msg 0x62 mode/sort.
5) Populate: msg 0x58 per row (payload = per-skill row descriptor; row proc LAB_008ced50). Query with msg 0x5D (count), 0x5C (selection), 0x5E (bulk export). Remove with msg 0x59.
Sizing/painting: none on the group itself (no case 1/0x15); the list child (LAB_00612b90) owns layout/scroll and each row (LAB_008ced50) paints itself.

- **Crash gotchas:**

Every branch that fails calls the no-return assert FUN_00487a80(line):
- msg 0x09 when instance slot already non-null -> 0x348 (double construct). Send 0x09 exactly once.
- warm-up: descriptor pointer null (*param_2==0) -> 0x11D.
- warm-up: computed label count == 0 -> 0x24B.
- warm-up / bulk-export: overlapping memmove src/dst -> 0x171.
- msg 0x58 / 0x59 / count-walk: row id > 0xFFFF -> 0xFE; column/index > 0xFFFF (i.e. >64k rows) -> 0xFF.
- msg 0x59 remove: no matching child -> 0x23A; [6] live-count already 0 -> 0x241.
- All getters assert on null out-param param_3: 0x5A->0x24A, 0x5B->0x25C, 0x5C->0x26A, 0x5D->0x281, 0x5E->0x28A, 0x5F->0x2B2.
- ALL post-create messages dereference the instance at *(msgframe[2]->slot) with no null guard: sending any get/set/add before msg 0x09 crashes on null. Instance access pattern is piVar1=msgframe[2]; inst=*piVar1.
- The tracked-alloc tag 0x349 passed to FUN_0047f340 is a source-line token, NOT the allocation size; the true struct size is 0x28 (from the case-0xB free). Do not confuse it when writing a shim.


### GmCtlSkListEntry  (EXE 0x008ce100, confidence: high)

- **Assertion file:** P:\Code\Gw\Ui\Game\Controls\GmCtlSkListEntry.cpp (EXE string @0x00b9b610; WASM @ram:00106bcb). Note this is the GAME-layer (Gw\Ui\Game\Controls) control, not the engine-layer P:\Code\Engine\Controls template.
- **Struct layout:**

Instance = 0x24 bytes (9 dwords), allocated in case 9 via FUN_0047f340("...GmCtlSkListEntry.cpp",0x393), freed in case 0xb via FUN_005acaeb(inst,0x24):
+0x00 u32  frame            self UI frame handle (= creation payload[0], *param_1)
+0x04 u32  skillId          skill id; init from creationParams[0]; 0 is illegal (asserts 0x1bd/0x1c3)
+0x08 u32  context          second creation param (palette/agent/context); init 0xffffffff
+0x0c void* userData        callback/user data ptr (set via msg 0x5a; used by input cb FUN_00538840)
+0x10 wchar_t* textBuf      growable label/text buffer data ptr (0 until msg 0x3a)
+0x14 u32  textCapacity     buffer capacity in wchar elements
+0x18 u32  textCount        current wchar count/length
+0x1c u32  initCapHint      = 0x80 (growable-array seed capacity)
+0x20 u32  style/mode       0,1 = compact icon-only row; 2 = detailed multi-field row (built by FUN_008cde20); 3 = passive/custom (no rebuild). Set via msg 0x5b.
Note: [0x10..0x18] is the standard Gw growable-array triple managed by FUN_00473880/FUN_004738f0/FUN_0046da80.

- **Message protocol:**

FrameProc FUN_008ce100(frame*, wparam int*, out uint*), switches on msg = param_1[1]:
- 0x09 CREATE/INIT: alloc 0x24 instance (tag 0x393); asserts if *slot!=0 (0x392). Copies creationParams: [0]->skillId(+4), [1]->context(+8). If skillId!=0: resolve skill def FUN_005a6e20(skillId), pull texture/tooltip at def+0x98 via FUN_007c3bc0, apply FUN_00632d90; register input callback FUN_00538840 via FUN_00630180(...,0x14); self-send 0x4c. Asserts skillId==0 (0x1c3/0x1bd).
- 0x0b DESTROY: free text buffer (inst+0x10) if non-null, zero +0x10/+0x14/+0x18, free instance FUN_005acaeb(inst,0x24).
- 0x24 MEASURE/AUTOSIZE: query icon child natural metrics (FUN_0062ee80 subs 8/10/9), build sizing sample FUN_0062c210 scaled by _DAT_009407b0, feed FUN_0062ed80 (sub 8).
- 0x25 GET (style-routed): style0/1->route sub 0x61 (wparam1); style2->0x56 (wparam0); style3->noop. Dispatch FUN_0062cfc0.
- 0x26: base/default thunk_FUN_00637a90.
- 0x34 REFRESH: FUN_008cee50 (relayout children).
- 0x37 INPUT/EVENT: FUN_008cea30(wparam) (click/hover handler).
- 0x38 PROP-GET (indexed by style inst+0x20): out[2] gets pair — 0:(_DAT_0094a030,..); 1:(_DAT_00b9b67c,..); 2:(selfframe,..); 3:(0,0). Asserts default (0x2f7).
- 0x3a SET-TEXT: grow buffer to strlen(wparam[1])+1 (FUN_0046c270), copy, set count inst+0x18, FUN_008ced60 relayout; if new len==0 self-send sub 0xb.
- 0x4c SET-ICON/TOOLTIP: re-resolve skill def(+0x98)->FUN_007c3bc0->FUN_00632d90(iconchild, tex, wparam[1]).
- 0x56 GET (style-routed): style0/1->0x65(w0); style2->0x57(w0); via FUN_0062cfc0.
- 0x57 STATE-QUERY: early-out if style bit FUN_0062fe20(frame,0x1000)!=0; else route 0x65/0x57.
- 0x58 GET-BUFFER: writes count to out[2], copies text buffer; asserts out==0 (0x34f).
- 0x59 GET-GEOMETRY: out[0]=inst+4, out[1]=inst+8; asserts out==0 (0x358).
- 0x5a SET-USERDATA: inst+0xc = wparam; re-register FUN_00630180(frame,0,FUN_00538840,...,0x14).
- 0x5b SET-STYLE: inst+0x20 = wparam; destroy children FUN_0062c760; if style 0/1 build compact (create icon child proc LAB_008c1b80, warm FUN_0062ede0(_,0,0xffffffff), then icon-child msgs 0x5e=greyed(FUN_004f9ab0==0), 0x5c=flag(skillFlags&1), 0x67=setSkillId); if style 2 call FUN_008cde20 (full detailed build); else assert 0x37f. Finish: FUN_008cee50 + FUN_0062f110 + FUN_0062f470 (relayout+invalidate).
Unhandled msgs (incl. 0x01 PAINT, 0x04 base-install, 0x15 size-query) fall through to return -> handled by the parent/base template proc, not here.
Icon child (proc LAB_008c1b80) protocol used: 0x67 set skill id, 0x5e set greyed/enabled, 0x5c set flag; label text children use proc FUN_00610c40, stat-field children use proc LAB_008c80e0.

- **Create recipe:**

Create the primitive with the RESOLVED frame proc FUN_008ce100 (NOT 0x008cde20):
1. frame = FUN_0062bfc0(parentFrame, flags, childId, FUN_008ce100, userData, 0). The runtime then delivers msg 0x09 to FUN_008ce100.
2. Creation payload (wparam[1]) must point to a 2-dword struct {u32 skillId, u32 context}; skillId MUST be non-zero or the proc asserts (0x1bd/0x1c3) and aborts. context defaults to 0xffffffff if unused.
3. On 0x09 the proc self-sends 0x4c to fetch the skill texture/tooltip; no extra warm-up needed for the icon.
4. Choose row style with msg 0x5b (wparam = 0/1 compact, 2 detailed). Default style after alloc is 3 (no children); you must send 0x5b to actually render a row.
   - Style 0/1 builds one icon child (LAB_008c1b80) and pushes 0x67/0x5e/0x5c.
   - Style 2 runs FUN_008cde20 which builds: child1=icon (LAB_008c1b80, warm FUN_0062ede0(_,0,0xffffffff)), child0=proc FUN_008c65b0 (warm FUN_0062f5a0(_,0xffffffff)), child6=name label (FUN_00610c40, flags 0x80100, warm FUN_0062f4b0(_,0)), optional child7=PvP/PvE tag label (userdata string 0x387/0x388 via FUN_007c3bc0, warm FUN_0062f4b0(_,2)), and stat-field text children ids 2/3/4/5 (proc LAB_008c80e0, flags 0x100, each warm FUN_0062ede0(_,0,0xffffffff)) gated on skill-def fields (+0x38 adrenaline, +0x3c energy, +0x4c recharge, +0x44 profession/type, +0x36/+0x34 flags).
5. Set label text with 0x3a (wparam={_,wchar* str}); set user/callback data with 0x5a; refresh with 0x34.
Order: create(0x09) -> [0x4c auto] -> 0x5b(style) -> 0x3a/0x5a as needed -> 0x34.

- **Crash gotchas:**

- SUPPLIED ADDRESS MISMATCH: 0x008cde20 (FUN_008cde20) is NOT the frame proc — it is the style-2 detailed-row LAYOUT BUILDER helper (creates icon + name + stat-field child controls) invoked from case 0x5b of the real proc. It takes the instance, not a (frame,msg) triple, and does not switch on msg. Always register the control with the resolved proc FUN_008ce100.
- skillId==0 at create -> non-returning assert FUN_00487a80 (0x1bd / 0x1c3). Never create with a zero skill id.
- Double-create: msg 0x09 when the instance slot is already non-null -> assert 0x392.
- Wrong style value on 0x5b: only 0,1,2 accepted; anything else -> assert 0x37f. Style 3 is a valid stored state but 0x5b won't build it.
- 0x58/0x59 getters assert (0x34f / 0x358) if the out pointer (param_3) is null.
- Growable-array overlap guard: buffer grow paths call FUN_00487a80(0x171) if src/dst ranges alias — do not hand msg 0x3a/0x58 a buffer that overlaps the instance's own text buffer.
- The proc does NOT handle PAINT (0x01) or base-install (0x04); it relies on the parent/base template proc for those. Registering it standalone without the base chain yields an unpainted frame.
- FUN_008cde20 style-2 build reads the resolved skill-def record (FUN_005a6e20) fields at +0x10/+0x34/+0x36/+0x38/+0x3c/+0x44/+0x4c; a stale/garbage skillId that resolves to a bad def can mis-drive which stat children are created (no bounds assert on those field reads).


### UiCtlPlace  (EXE 0x009238f0, confidence: high)

- **WASM:** IUi::UiCtlPlaceProc(FrameMsgHdr const&, void const*, void*) — body ~ram:8100e4xx (assertion string ram:0010e624)
- **Struct layout:**

Instance = 0x88 (136) bytes, allocated in case 9 via FUN_0047f340("P:\\Code\\Gw\\Ui\\Controls\\UiCtlPlace.cpp", 0x88). Instance ptr is reached by FUN_00923850 = **(int**)(msgframe+8) (asserts 0x9a if null). Layout:
+0x00 int   m_pendingRelayout / one-shot-activate guard. 0=idle, 1=relayout pending. Set to 1 by 0x10000143 (activate) and by warm-up FUN_00923480 when parent rect empty; consumed/cleared by 0x45 and by FUN_00923480 on successful reflow. Msg 0x45 asserts (0xf2) if this is 0.
+0x04 int   m_targetFrameId  — the child/target frame being placed. Taken from create-payload[0] (*(uint*)payload[0][0]).
+0x08 int/float m_anchorMode  — placement/anchor-edge enum. Written (as raw float) by 0x2b (=payload[2]); read (as int) by 0x34, matched against edge codes {4,5,7,8,0xb} to decide which sides move.
+0x0c int   m_ownerFrame     — handle of the frame this proc is bound to (= *param_1 at create). Passed to all FUN_0062ef00/FUN_0062f7b0/FUN_0062bd80 dispatch calls.
+0x10 int   m_stateHandle    — from create-payload[1] (payload[0][1]); seeds the +0x14 object and is used by FUN_0049be00/0049c600/0049c6e0/0049c7a0 (rect/transform snapshot for drag).
+0x14..0x88 (0x74 bytes) constructed object initialized by FUN_0049bc30(payload[0][1], inst+0x14) — the saved/working placement rect + drag bookkeeping (vector/list-like). Fields beyond here not individually resolved (confidence medium on internal breakdown).

- **Message protocol:**

Standard control FrameProc; switches on msgframe[1]=msg. thunk_FUN_00647170 = chain-to-base. Messages handled:
- 0x04 SETUP/REGISTER: `*(uint*)payload[1] |= 0x20` (adds style/behavior bit 0x20 to the frame template), then chain base.
- 0x08 NOTIFY(destroy-side): get-instance (FUN_00923850) then FUN_00923670(payload); chain base.
- 0x09 CREATE: assert(0x87) if instance slot != 0 (no double-create); alloc 0x88; set +0x04=payload[0][0], +0x0c=ownerFrame(*param_1), +0x10=payload[0][1]; FUN_0049bc30(payload[0][1], inst+0x14); FUN_00923480() initial reflow; subscribe owner frame to 0x1000017d, 0x1000017e, 0x10000143 via FUN_0062ef00; chain base.
- 0x0B DESTROY: FUN_005acaeb(instance,0x28) free; null the slot; chain base.
- 0x17 (23) HITTEST/GETPART: payload[0..3]=point/rect, payload[4]=out. Iterates handle parts 4..0xb through part-rect helper FUN_00923550; if point inside a handle writes that part index to *(uint*)payload[4]; else if inside body writes 0xc. (Parts: 8 resize handles + body-move.)
- 0x20 (32) NUDGE (arrow-key move): payload[0]=key (raw-float ints 28/29/30/31 = arrows). Gets grid step FUN_0062bfa0, adjusts x(+/-)/y(+/-) via cases (0x1c..0x1f), reclamps with FUN_004a18e0, applies to target and owner frame via FUN_0062f7b0, FUN_00923880(), chain base.
- 0x21 (33) INVALIDATE: FUN_0062bd40(target frame).
- 0x2B (43) SET-ANCHOR/VALUE: if payload[2]!=0 -> FUN_0062e560; if (payload[0]&1) and value==1 snapshots rect (0049be00/0049c600/0049c6e0); store payload[2] into +0x08; FUN_0062bd80(target,1) invalidate; chain base.
- 0x34 (52) DRAG/MOVE (core placement): resolves target frame; if +0x00==0 (not busy) computes new rect from anchor mode at +0x08 — modes {4,7,0xb} move left edge by delta, {4,5,8} keep top, else move via bottom/right — clamps with FUN_004a18e0 (grid via style 0x800), applies FUN_0062f7b0, FUN_0062bd80(target,1); chain base.
- 0x41/0x43 (65/67) RELAYOUT ON RESIZE/SHOW: FUN_00923480() reflow, then FUN_0062d4e0 + FUN_0049c7a0/FUN_0049c600 recompute snapshot; chain base.
- 0x45 (69) DEFERRED RELAYOUT: assert(0xf2) if +0x00==0; run FUN_00923480(); chain base. (Self-scheduled, do not send manually.)
- 0x1000017D custom: assert(0x9a) if instance null; FUN_0062c550(targetFrame+0xc) — observe/register on target. (No chain.)
- 0x1000017E custom: assert(0x9a) if null; FUN_0062fcb0(targetFrame+0xc, payload) — data/rect push; chain base.
- 0x10000143 custom ACTIVATE (one-shot): assert(0x9a) if null; if payload[0][0]==inst+0x10 and +0x00==0 -> set +0x00=1, FUN_0062ef00(ownerFrame,0x45) schedule relayout, chain base.
Part-rect helper FUN_00923550(out, part, rect): part 4=left-mid,5=right-mid,6=BR,7=TL,8=top-mid,9=bottom-mid,10=right-mid-h,0xb=BL (8 handles, _DAT_009407b0 = 0.5 for midpoints), 0xc=whole body rect, default=zero rect.

- **Create recipe:**

Game-layer (P:\Code\Gw\Ui\Controls) interactive placement/resize gizmo — it draws draggable handles around a target frame and repositions/resizes it (a UI-editor "move/anchor" control). It is created through the normal frame-creation path, not by directly poking memory:
1. Create a child frame whose FrameProc = 0x009238f0 (e.g. via FUN_0062bfc0(parent, flags, child, proc=0x009238f0, userdata, 0)). The framework auto-delivers 0x04 (SETUP, which OR-in style bit 0x20) then 0x09 (CREATE).
2. For 0x09 CREATE, supply payload where payload[0] is a struct { u32 targetFrameId; u32 stateHandle; }: targetFrameId -> inst+0x04 (the frame to be placed), stateHandle -> inst+0x10 / seed for the +0x14 object.
3. CREATE auto-subscribes the owner frame to 0x1000017d, 0x1000017e, 0x10000143 and runs an initial reflow (FUN_00923480). No extra warm-up needed.
4. To activate the gizmo send 0x10000143 with payload[0][0]==inst+0x10 (matches stateHandle) — it flips +0x00 and schedules 0x45 relayout.
5. Drive interaction with 0x17 (hit-test to find handle/body), 0x34 (drag/move), 0x20 (arrow nudge), 0x2b (set anchor mode). Sizing/anchoring is handled internally against the parent rect via FUN_004a18e0 (grid snap enabled when frame style 0x800 set).

- **Crash gotchas:**

- Double-create: 0x09 asserts (FUN_00487a80(0x87)) if the instance slot is already non-null. Never send CREATE twice to the same frame.
- Use-before-create: 0x10000143, 0x1000017d, 0x1000017e and the instance accessor FUN_00923850 all assert (0x9a) if the instance pointer is null. These are only valid after 0x09 CREATE and before 0x0b DESTROY.
- 0x45 relayout asserts (0xf2) if +0x00 (pending flag) is 0 — it is self-scheduled by activate/warm-up; do not send it manually with the flag clear.
- 0x34/0x20/0x2b silently no-op (fall through to base) if FUN_0062cfc0 can't resolve the target frame (targetFrameId at +0x04 stale/destroyed) — keep the target frame alive for the gizmo's lifetime.
- Anchor mode at +0x08 must be one of the recognized edge codes {4,5,7,8,0xb} for 0x34 to move edges; other values leave position at *payload (no-op edge), which can look like a frozen drag.
- Ordering: 0x04 SETUP must precede 0x09 CREATE (SETUP sets style bit 0x20 the create path relies on); let the framework deliver them in order rather than hand-issuing.


### UiCtlLabelText  (EXE 0x009240d0, confidence: high)

- **WASM:** ram:80fdc7f6
- **Assertion file:** No own .cpp / no own assertion — this proc allocates nothing. Backing instance is CtlText: FUN_0047f340("P:\\Code\\Engine\\Controls\\CtlText.cpp", 0x18a/0x18b). The only assert reachable from this proc is inside FrameSetDefaultTextStyle (FUN_0062f4b0): FUN_00487a80(0xb7f) via "P:\\Code\\Engine\\Frame\\FrApi.cpp" if frameId==0.
- **Struct layout:**

UiCtlLabelText has NO instance struct of its own (proc stores/reads nothing per-frame). It is backed entirely by the CtlText instance, allocated in FUN_00610c40 case 9 (~0x34 bytes) and stored into the frame's instance slot (*pfVar2). CtlText instance layout (offsets that the base proc touches):
- +0x00: vtable ptr = &PTR_FUN_00a50108
- +0x04: wchar_t* text buffer
- +0x0c: int text capacity/char-count
- +0x14: uint highlight/selection index (0xffffffff = none)
- +0x18: RGBA color (set via msg 0x8c)
- +0x1c: ptr/handle (set via msg 0x8d; read during 0x38 measure)
- +0x20: child glyph-frame array base ptr
- +0x24: (array field)
- +0x28: int child-frame count
- +0x2c: init 0x40 (flags)
- +0x30: 4-byte tag/color, compared bytewise, propagated to children (msg 0x8b)
Separately, the "default text style" this control sets lives on the FRAME (not the instance): frame+0x194 is the CText render subobject; frame+0xa8 is the CMsg subobject used for dispatch. Style index 3 is written to frame+0x194 by FrameSetDefaultTextStyle.

- **Message protocol:**

FUN_009240d0(msgHdr* p1, const void* p2, void* p3) — a THIN styling shim over CtlText. Switch on p1[1]=msg:
- msg 4 (INSTALL_BASE): *(void**)(p2[3]) = FUN_00610c40 (install CtlText FrameProc as the parent/base), then fall through to thunk_FUN_00647170 (chain-forward). This is what wires the CtlText base into the proc chain so CtlText's own create/destroy/paint run.
- msg 9 (CREATE): FUN_0062f4b0(*p1, 3)  == FrameSetDefaultTextStyle(frameId, styleIndex=3), then thunk_FUN_00647170. NOTE: thunk_FUN_00647170 explicitly early-outs for msg 9 and 0xb, so the base CtlText instance (CtlText.cpp:0x18a) is actually allocated by the frame-create dispatch that walks every proc in the chain for msg 9 — not by the thunk. Net effect of this control = force default text style 3 at creation.
- all other msgs: thunk_FUN_00647170(p1,p2,p3) — forward to CtlText base, which implements the real protocol.

FrameSetDefaultTextStyle (FUN_0062f4b0) internals: GetFrame(frameId) [FUN_00647db0] -> CText::SetStyle(frame+0x194, 3) [FUN_00633c60] -> dispatch msg 0x39 (relayout) [FUN_00647c80(0x39,0,0)].

Effective (inherited) CtlText protocol handled by base FUN_00610c40: 4=install its own base FUN_006123a0; 8=layout/measure hook; 9=alloc instance (CtlText.cpp); 0xb=destroy (calls vtbl[0](1)); 0x38=GetLayout/measure text (style bits from FUN_0062fe20 mask 0x8000/0x10000/0x20000/0x80000); 0x39=relayout; 0x3a; 0x78=apply/refresh text to child glyph frames; 0x88/0x89/0x8a=get text/length variants; 0x8b=set a 4-byte tag/color at inst+0x30 (re-pushes to children via FUN_006641e0); 0x8c=set color at inst+0x18 then invalidate; 0x8d=set inst+0x1c ptr; 0x8e/0x8f=set text buffer (highlight index inst+0x14 = -1 vs 0). CtlText base's own base is FUN_006123a0 (installs FUN_0062c370). Chain: UiCtlLabelText(FUN_009240d0) -> CtlText(FUN_00610c40) -> FUN_006123a0 -> FUN_0062c370.

- **Create recipe:**

Created via the standard frame-create primitive with this proc. From the sole registration site (FUN_00893b70 @ 0x00894032):
FUN_0062bfc0(parent=frame[EDI+4], flags=0x0, childId=0x12, proc=FUN_009240d0, userData=EAX, 0)
where userData EAX is a localized-string/data handle from FUN_007c3be0(0xb985ac,...) and string ids 0x55a/0x55c/0x55e are pushed nearby.

Recipe to reproduce:
1. Call the create primitive FUN_0062bfc0(parentFrameId, flags, childId, FUN_009240d0, userData, 0). flags=0 is what the shipping label uses; childId is caller-chosen (0x12 here).
2. Do NOT pass CtlText (FUN_00610c40) directly — pass FUN_009240d0; it self-installs CtlText as its base in msg 4, so the full CtlText chain (and instance alloc) is set up automatically during the create dispatch.
3. On create the proc forces FrameSetDefaultTextStyle(frame, 3). To set text/color afterward, use the inherited CtlText setter messages (0x8e/0x8f set text; 0x8c set color; 0x8b set tag) via the dispatcher FUN_0062ef40.
4. Warm-ups: none beyond a valid non-zero parent frame; CtlText create also runs FUN_0062ede0(frame,0,-1), FUN_0062ccd0(frame,0,0x30), FUN_0062ef00(frame,0x4c) internally.

- **Crash gotchas:**

- Must be installed as a proc-chain entry via msg 4, NOT invoked standalone. If msg 4 doesn't install FUN_00610c40, the CtlText instance is never allocated and every subsequent CtlText message dereferences *pfVar2 (the instance ptr) => crash. This proc holds no state and relies 100% on the base.
- thunk_FUN_00647170 (FUN_00647170) early-returns for msg 9 and 0xb. So the create/destroy of the CtlText base does NOT flow through the thunk — it happens through the framework's create/destroy dispatch that walks all chained procs for msg 9/0xb. If you hand-roll a create that only calls this proc directly (bypassing that dispatch), no CtlText instance is built => later text ops crash.
- FrameSetDefaultTextStyle (FUN_0062f4b0) asserts FUN_00487a80(0xb7f) (FrApi.cpp) when frameId==0. The proc passes *p1 (the frame id) at msg 9, so the frame must already be valid at create time — it is, under normal dispatch.
- Style is applied only once, at msg 9. Re-styling at runtime requires calling FrameSetDefaultTextStyle again (which also dispatches relayout msg 0x39); the proc will not re-apply on its own.
- Do not conflate the CtlText instance (frame instance slot, offsets +0x00..+0x30 above) with the frame's CText subobject at frame+0x194 where the style index actually lives.


### UiCtlStat (IUi::UiCtlStatFrameProc)  (EXE 0x00924120, confidence: high)

- **WASM:** ram:0x814b068b
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlStat.cpp (game-layer). Display child uses engine-layer P:\Code\Engine\Controls\CtlText.cpp
- **Struct layout:**

Instance = 0x47 (71) bytes, allocated by FrameProc msg 0x09 via FUN_0047f340("...UiCtlStat.cpp",0x47), pointer stored at *(msgframe[2]); reached later as **(frame+8) through FUN_00924490.
  +0x00  dword  ownFrameHandle (copied from msgframe[0]); used as parent handle for both children and as *puVar2 target of all get/set FUN_0062cfc0 routing.
  +0x04..0x46  control state, zero-init by allocator; not written by this FrameProc directly — visible value/text lives in the CtlText display child (child id 0). The stat's displayed number/label is stored/rendered by that CtlText sub-frame (its own struct: +0x14 index, +0x1c fontsize, +0x18/+0x30 color quads, +0x0c length — see FUN_00610c40 CtlText.cpp).
This is a COMPOSITE control: a UiCtlStat instance + a CtlText display child (renders the value) + a secondary layout/measure child (FUN_00924510, clamps min width).

- **Message protocol:**

FrameProc FUN_00924120(msgframe*, payload*, out*). Switch on msg = msgframe[1]. Instance accessor FUN_00924490(frame) = **(frame+8) (asserts 0x59 if the instance frame-handle is 0).

- 0x09 CREATE/init: asserts (FUN_00487a80(0x46)) if *(msgframe[2]) already set (double-create). Allocs 0x47(=71) bytes via FUN_0047f340("...UiCtlStat.cpp",0x47); copies frame handle msgframe[0] -> inst[0]; stores inst ptr into *(msgframe[2]). Then builds TWO child frames on inst frame handle:
   (a) CtlText display child: FUN_0062bfc0(*inst, 0x80300, 0, FUN_00610c40, 0, 0); warm-ups FUN_00604aa0(child,&0xffffeab8) (color/param) + FUN_0062ede0(child,0,-1).
   (b) layout/value child: FUN_0062bfc0(*inst, 0x300, 1, FUN_00924510, 0, 0); FUN_0062ede0(child,0,-1).
- 0x0B DESTROY: if inst!=0 FUN_005acaeb(inst,4) (free); zero *(msgframe[2]).
- 0x15 (21) MEASURE/size-query: validates inst; asserts (0xC8) if out==0; writes rect out[0]=0, out[1]=_DAT_00943278, out[2]=0, out[3]=_DAT_00943278 (=0x40000000 -> 2.0f default extent).
- 0x37 (55) ARRANGE (2-arg): forwards positions to children via FUN_0062cfc0(*inst,1,0x8a,&pos,0) and (*inst,0,0x86,...); FUN_0062e8a0 commit. pos = payload[0..1].
- 0x38 (56) ARRANGE+measure (3-arg): like 0x37 with FUN_0062e700 + FUN_0062e800(_DAT_0093d950,8,...) snap; writes computed pos back into *(payload[2]).
- 0x56 (86) SET (mode 0): asserts (0x103) if payload==0; FUN_0062cfc0(*inst,0,payload); FUN_00611320.
- 0x57 (87) SET (mode 1): asserts (0x10F) if payload==0; FUN_0062cfc0(*inst,1,payload); FUN_00611320.
- 0x58 (88) SET-INT: converts signed int payload to string via FUN_007c3be0((sign)+4,1,abs,0), then mode-1 set + FUN_00611320.
- default: base-template parent-chain dispatch thunk_FUN_00647170 (this is where paint msg 0x01 and parent-install msg 0x04 are handled — UiCtlStat does not override them).

Child proc FUN_00924510 (id1, flags 0x300): msg4 installs FUN_00610c40 as proc + ORs style 0xa4000; msg9 sets color FUN_00604aa0(*self,&0xfff0f0f0), FUN_0059fee0(*self,0x40), installs layout hook FUN_0062f150(*self,FUN_009244d0,0); msg0x38 base-dispatches then clamps width to min _DAT_0095044c when below _DAT_00946578; else base dispatch. FUN_009244d0: on msg 0x15 subtracts padding _DAT_009413c8 from out height; else FUN_00879090.

- **Create recipe:**

Register FUN_00924120 as the frame proc and let the UI manager create the frame; it self-assembles its children on msg 0x09. Concretely:
1. Create the outer frame: FUN_0062bfc0(parentHandle, flags, childId, FUN_00924120, userdata, 0). The engine then dispatches msg 0x09 to this proc.
2. On 0x09 the proc allocates its 71-byte instance and spawns (a) the CtlText display child (proc FUN_00610c40, flags 0x80300, child-id 0) and (b) the layout child (proc FUN_00924510, flags 0x300, child-id 1). No caller action needed for children.
3. Sizing: default measured extent is 2.0f x 2.0f (msg 0x15). Send 0x37/0x38 to arrange within parent layout.
4. Set the displayed value: send 0x58 (SET-INT) with an integer stat value, or 0x56/0x57 with a text/string payload (mode 0 vs mode 1). Each set routes to the CtlText child and flushes via FUN_00611320.
Order: CREATE(0x09) -> [MEASURE 0x15 / ARRANGE 0x37|0x38 by parent] -> SET(0x56/0x57/0x58). Warm-ups (color FUN_00604aa0, FUN_0062ede0 enable) are done internally at create; no external warm-up required.

- **Crash gotchas:**

- Double-create: sending msg 0x09 when *(msgframe[2]) is already non-null asserts FUN_00487a80(0x46) (no-return) -> crash. Create exactly once.
- Use-before-create: EVERY get/set/measure/arrange (0x15,0x37,0x38,0x56,0x57,0x58) calls FUN_00924490 which asserts FUN_00487a80(0x59) if the instance frame-handle (inst[0]) is 0. Never send these before a successful 0x09.
- Null out on measure: msg 0x15 asserts FUN_00487a80(0xC8) if out==0.
- Null payload on set: msg 0x56 asserts 0x103, msg 0x57 asserts 0x10F if payload==0.
- 0x58 allocates a temp string from the signed int via FUN_007c3be0; passing a bogus/huge magnitude drives a large alloc.
- Free path: msg 0x0B calls FUN_005acaeb(inst,4) and zeroes the slot — must not be dispatched twice and children (created on inst frame) must still be valid; freeing the parent frame out from under the CtlText child can dangle.
- Paint (0x01) and parent-install (0x04) are NOT handled here; they fall through to base template FUN_00647170, which itself asserts (0x256/0x221/0x223/0x24b) if the frame's class/vtable table indices are inconsistent — i.e. the proc must be registered in the frame class table before any message is pumped.


### CtlUtils (GameView tap/hold/drag gesture threshold setter — FUN_0060cf40)  (EXE not-a-proc, confidence: high)  [NOT a frame proc]

- **WASM:** ? (no distinct WASM symbol resolved; static gesture-utility, not a named control class)
- **Struct layout:**

This function itself touches only two module globals (no instance struct):
  float g_tapHoldTime      @ 0x00bef490   // seconds, >=0
  float g_tapDragDistSq    @ 0x00bef494   // pre-squared distance, >=0

Gesture-tracker struct operated on by the consumer helpers (FUN_0060ce70 / FUN_0060cef0), size >= 0x1c:
  +0x00  (unused by these fns)
  +0x04  float  startX       // initial contact X
  +0x08  float  startY       // initial contact Y
  +0x0c  float  curX         // latest pointer X (written by FUN_0060ce70)
  +0x10  float  curY         // latest pointer Y (written by FUN_0060ce70)
  +0x14  float  elapsed      // accumulated hold time (accumulated by FUN_0060cef0)
  +0x18  int    state        // 1 = armed/pending, 2 = triggered (hold or drag fired)

- **Message protocol:**

NONE — this is not a control FrameProc. FUN_0060cf40 (EXE 06-14, base 0x00400000) has NO msgframe/msg switch, no case 4/9/0xb/1/0x15 dispatch, no FUN_0047f340("<Ctl>.cpp",size) instance allocation, and no paint pass. It is a two-argument static setter for touch/gamepad gesture thresholds.

Signature: void FUN_0060cf40(float tapHoldTime, float tapDragDistance)
Body:
  if (tapHoldTime  < 0.0) FUN_00487a80(0x53);   // no-return assert/fatal, code 0x53
  if (tapDragDistance < 0.0) FUN_00487a80(0x54); // no-return assert/fatal, code 0x54
  _DAT_00bef490 = tapHoldTime;                    // hold-time threshold (seconds), stored raw
  _DAT_00bef494 = tapDragDistance * tapDragDistance; // drag-distance threshold, stored SQUARED

Global producer/consumer contract (the real "protocol"):
  * 0x00bef490 (float) = tap-hold time threshold. WRITE: 0060cf8d (here). READ: FUN_0060cef0 @ 0060cf05.
  * 0x00bef494 (float) = tap-drag distance-SQUARED threshold. WRITE: 0060cf95 (here). READ: FUN_0060ce70 @ 0060cec5.

Consumer FUN_0060cef0(gesture* g, float dt) — HOLD detector:
    g->elapsed(+0x14) += dt;
    if (g->elapsed > _DAT_00bef490 && g->state(+0x18)==1) { g->state=2; return 1; } return 0;
Consumer FUN_0060ce70(gesture* g, float* pos) — DRAG detector:
    g->curX(+0x0c)=pos[0]; g->curY(+0x10)=pos[1];
    if (g->state(+0x18)==1) { dx=curX-startX(+0x04); dy=curY-startY(+0x08);
       if (dx*dx+dy*dy > _DAT_00bef494) { g->state=2; return 1; } } return 0;

Sole caller: FUN_004a2190 (GameView/gamepad input config loader) at the tail, as
  FUN_0060cf40(_DAT_00c00dd0 /*GameViewTapHoldTime*/, _DAT_00c00dd4 /*GameViewTapDragDistance*/);
alongside sibling setters FUN_0062cf10/0062ce80/00630300/0060d310 that install other input tuning constants read from the config store (keys GameViewTapHoldTime, GameViewTapDragDistance, GamepadFlickThreshold, etc.).

- **Create recipe:**

N/A — no control is created. This is a static configuration setter with no lifecycle, no parent/child frame, no proc, no flags. It is called once (or on config reload) by the GameView input-config loader FUN_004a2190 to publish two gesture thresholds into globals. To "use" it: call FUN_0060cf40(holdTimeSeconds, dragDistancePixels) with both values >= 0; the drag value is squared for you and compared against squared pointer displacement by FUN_0060ce70. Do not pre-square the drag argument yourself.

- **Crash gotchas:**

1) Both arguments are asserted non-negative: tapHoldTime<0 -> FUN_00487a80(0x53) (no-return fatal), tapDragDistance<0 -> FUN_00487a80(0x54). FUN_00487a80 does not return, so a negative config value hard-faults the client.
2) The stored drag threshold is ALREADY the square of the input (param_2*param_2). Callers/consumers must compare against squared displacement (dx*dx+dy*dy), which FUN_0060ce70 does. Passing an already-squared value here would square it twice.
3) Not a FrameProc: do NOT drive it through FUN_0062ef40 / msgframe dispatch or treat 0x00bef490/0x00bef494 as an instance pointer — they are plain float globals, and the tracker struct at +0x04..+0x18 is a separate per-gesture record owned by the GameView input layer, not allocated via FUN_0047f340.


### UiCtlWebLink::BuildLinkTarget (helper, NOT the FrameProc)  (EXE not-a-proc, confidence: high)  [NOT a frame proc]

- **WASM:** ? (not resolved — EXE-side helper; no distinct WASM symbol chased since target is not a frame proc)
- **Assertion file:** P:\Code\Gw\Ui\Controls\UiCtlWebLink.cpp
- **Struct layout:**

WebLinkData (the `this` passed in ECX to FUN_0087e250; the UiCtlWebLink instance/model):
  +0x08  int      linkType     // 0=raw web URL, 1=Quest, 2=named-map, 3=map(outpost/mission/explorable), 4=Skill, 5=profession-skills, 6=invalid(assert)
  +0x0c  wchar_t* nameString   // type 2 only: map/location display name, slugified (space->'_') into the link
  +0x1c  uint / wchar_t* arg   // %u id for Quest/Skill/Map/Profession links; also the raw URL wchar text pointer when linkType==0
  +0x20  int      mapKind      // type 3 only: 0 => Outpost link; nonzero => Explorable/Mission (disambiguated via map record FUN_005a6b00, field +0xc==2 => Explorable else Mission)
(Only offsets touched by this helper are known; full control/frame struct not enumerated here.)

- **Message protocol:**

NOT a message/frame proc. FUN_0087e250 does NOT switch on msgframe[1]=msg and takes none of the FrameProc args (frame,msg,wparam,out). Its signature is __thiscall UiCtlWebLink_BuildLinkTarget(WebLinkData* this /*ECX*/, wchar_t* outBuf, int outSize). Confirmed by the call site in FUN_0087eff0: `FUN_0087e250(local_108, 0x100)` (out=256B buffer, size=0x100, this in ECX).

It switches on this->linkType (*(int*)(this+8)) to encode the control's target into a printable link string:
  type 0 -> raw web URL: copies wchar text at this+0x1c into out via FUN_005e2e60->FUN_005e2e80(out, "%s"-fmt @DAT_00935a30, size, text). This is the http:// path.
  type 1 -> "Game_link:Quest_%u"        (id = *(this+0x1c))
  type 2 -> named-map link: slugifies wchar name at this+0x0c (spaces 0x20 -> '_' 0x5f), builds template @0x00b96228, encodes via FUN_005e2e80(0x14,...)
  type 3 -> map: id=*(this+0x1c), flag=*(this+0x20); flag==0 -> "Game_link:Outpost_%u"; else look up map record (FUN_005a6b00): rec+0xc==2 -> "Game_link:Explorable_%u" else "Game_link:Mission_%u"
  type 4 -> "Game_link:Skill_%u"                 (id = *(this+0x1c))
  type 5 -> "Game_link:Skills_for_profession_%u" (id = *(this+0x1c))
  type 6 -> hard assert (reserved/invalid)
Tail: FUN_0046c3b0(out,0x100) formats template+id, FUN_005e2e80(0x14, tmp, arg) encodes into outBuf.

THE ACTUAL FrameProc for this control is the (Ghidra-undefined) code region ~0x0087e510..0x0087eea0 — it references the same UiCtlWebLink.cpp assert-file string dozens of times and dispatches the message cases. The activation/click handler is FUN_0087eff0 (address 0x0087eff0): it calls this BuildLinkTarget helper, tests the result for a "http://" prefix (FUN_0046c250/FUN_0046bd40), validates (FUN_004a1d20), truncates at a delimiter, then OPENS THE URL by sending message 0x2000 to a frame — FUN_0062cfc0(*param_1,0) gets the frame, FUN_00630180(frame, 0x2000, callback FUN_00895bd0, url, ...). That msg-0x2000 dispatch is the "open browser" action.

- **Create recipe:**

N/A for this address — it is a leaf helper, not a control template you install as a proc. To exercise/create the UiCtlWebLink control you install its real FrameProc (undefined region ~0x0087e510; activation handler FUN_0087eff0) via the standard control pipeline (create primitive FUN_0062bfc0(parent,flags,child,proc,userdata,0); case 9 alloc via FUN_0047f340("UiCtlWebLink.cpp",size)). This helper is invoked internally when the link is clicked to produce the encoded target string; you would not call it directly. If reproducing the open-URL behavior: populate WebLinkData (linkType=0, +0x1c = wchar URL beginning "http://"), then the click path FUN_0087eff0 encodes it and dispatches frame message 0x2000 (callback FUN_00895bd0) to launch the browser.

- **Crash gotchas:**

Guarded by /GS stack cookie (DAT_00bee340) + 256-byte local buffer; several asserts via FUN_00487a80 (file @0x00b96194, class-ctx ECX=0x9404d0):
  - outBuf (param_2) NULL -> assert line 0xE2 (226)
  - outSize (param_3) NULL/0 -> assert line 0xE3 (227)
  - linkType == 6 -> assert line 0x62 (98) (reserved/invalid)
  - type 2 with nameString(+0x0c)==NULL -> assert line 0x108 (264)
  - unknown linkType (default) -> assert line 0x188 (392)
  - final produced string empty -> assert line 0x18B (395) — encoder MUST yield a non-empty string
  - type 2 uses an alloca-based slugify loop sized to the wide name length; an unbounded/huge name string can blow the stack.
  - type 0 assumes +0x1c is a valid NUL-terminated wchar URL; a bad/non-http pointer either faults here or is rejected later by the http:// check in FUN_0087eff0.


### GmCtlSkListContext (constructor / hashtable-entry state node)  (EXE not-a-proc, confidence: high)  [NOT a frame proc]

- **WASM:** ? (no WASM FrameProc; class "SkillListContext" confirmed via strings ram:00106596 "SkillListContext::SKILL_LIST_USERS != skillListUser" and ram:00117648 "skillListUser < SkillListContext::SKILL_LIST_USERS")
- **Assertion file:** ../../../../Gw/Ui/Game/Controls/GmCtlSkListContext.cpp
- **Struct layout:**

GmCtlSkListContext, size = 0x30 (48 bytes), constructed by FUN_008cbf30(this, user, category, skillId):
  0x00 int   key_user       (skillListUser; ASSERT user <= 4, i.e. < SKILL_LIST_USERS)
  0x04 int   key_category   (ASSERT category <= 7)
  0x08 int   key_skillId    (skill id)
  0x0C int   map_node/next  (NOT written by ctor; intrusive TMap linkage + stored-hash region, populated on insert by FUN_004740c0; lookup FUN_008cc4c0 reads *(obj + container.hashOffset) and *(obj + container.linkOffset+4) here)
  0x10 TLink listA.next     = &self@0x10 (self-referential; ASSERT 4-byte aligned code 0xa0, ASSERT not odd code 0xe9)
  0x14 int   listA.prev/root= (int)self + 0x11
  0x18 TLink listB.next     = &self@0x18 (self-referential)
  0x1C int   listB.prev/root= (int)self + 0x19
  0x20 int   cur_user       (copy of user; ASSERT <=4 code 0x7f)
  0x24 int   cur_category   (copy of category; ASSERT <=7 code 0x80)
  0x28 int   cur_skillId    (copy of skillId)
  0x2C int   valid_flag     = 0 iff (user==1 && category==0 && skillId < 0x33 [FUN_008c5950]) else 1; consumed as (flag==0) by FUN_008ccc70
Two embedded TLink sentinels (0x10, 0x18) make this node the head of two intrusive doubly-linked child/observer lists; the (user,category,skillId) triple at 0x00 is the map key, duplicated at 0x20 as the mutable "current" state.

- **Message protocol:**

NONE — not a control FrameProc. FUN_008cbf30 has no msgframe/switch(msg) dispatch. It is the C++ constructor SkillListContext::SkillListContext(user, category, skillId) for a per-key state node in the GmCtlSkList control. It is invoked only from the SkList control's state-mutation paths (see create recipe), never registered as a paint/dispatch proc. Therefore no case 1/4/9/0xb/0x15/0x56 protocol applies.

- **Create recipe:**

Do NOT create as a frame/window. This object is produced internally by the GmCtlSkList control state setters and lives in an intrusive hashtable keyed by (user,category,skillId):
  1. Compute skillId param via FUN_008c58d0(skillNumber,0x30).
  2. Build a 3-int stack key {user, category, skillId} and probe the map: FUN_008cc4c0(container, &key) (hash via FUN_008cc690, buckets of 0xC bytes).
  3. If not present: alloc = FUN_0046d9e0(0x30); if alloc!=0, FUN_008cbf30(alloc, user, category, skillId); hashKey = FUN_008cc690(); FUN_004740c0(alloc, hashKey) inserts it (this fills the 0x0C map-node region).
  4. Notify via FUN_008ccc70(context->valid_flag==0, targetId).
Callers: FUN_008cc730 (state-set by skillId/bitset path) and FUN_008cccd0 (state-set by agent/param_2, validates param via FUN_00808b40, id range <=0x28). Valid arg ranges are mandatory: user in 0..4, category in 0..7.

- **Crash gotchas:**

All guards are FUN_00487a80(code) fatal asserts (no return):
  - user > 4  -> assert 0x73 (ctor) / 0x7f (copy-store); must be < SKILL_LIST_USERS (5).
  - category > 7 -> assert 0x74 (ctor) / 0x80 (copy-store).
  - Misaligned embedded TLink (self ptr not 4-byte aligned) -> assert 0xa0; odd pointer -> assert 0xe9. These only fire if the object is placed at a misaligned address, so allocate via the game allocator (FUN_0046d9e0(0x30)) — do not embed unaligned.
  - Field 0x0C is left uninitialized by the ctor; it is only valid after FUN_004740c0 insertion. Reading map/next before insert reads garbage.
  - Never register FUN_008cbf30 as a control proc / paint handler — it is a plain __thiscall ctor and will corrupt the msgframe protocol if driven with (frame,msg,wparam,out).
  - valid_flag semantics: caller uses (flag==0) as "true"; flag==0 ONLY for the special key (user==1,category==0,skillId<0x33), else flag==1.


### UiCtlBtnFloating (IUi::UiCtlBtnFloatingProc)  (EXE not-a-proc, confidence: high)

- **WASM:** ram:812ab245
- **Assertion file:** NONE — this control has no .cpp assertion in either binary. It never allocs a per-instance struct (no FUN_0047f340 / FUN_00487a80 assert path), so no filename is embedded. Only UiCtlBtn.cpp / UiCtlBtnToggle.cpp / UiCtlBtnExpand.cpp exist as sibling assertions; UiCtlBtnFloating.cpp is absent in both Gw.wasm and Gw.exe.</assertion_file> <parameter name="struct_layout">No dedicated per-instance struct. UiCtlBtnFloating is a pure decorator/container frame: it never calls the instance-alloc primitive (FUN_0047f340) and never installs an instance accessor. Its entire state is:   - The standard Frame object (created by msg 9 with the wrapper proc).   - Exactly ONE child at index 0: a base CtlBtn (child proc = 0xa9d in WASM), which carries the normal CtlBtn instance data. All get/set state (label, image, pressed flag, enable, etc.) lives on that child, not on the wrapper. Because there is no wrapper instance, there is no FUN_00618aa0-style instance pointer to fetch for this frame; use FrameGetChild(self,0) to reach the state.
- **Message protocol:**

Frame proc dispatches on msg = msgframe[1] (WASM param1[1]). Base proc installed in case 4 = 0xaaa (shared reactive/tip container base; EXE analog = CTipBasic/CTipReactive family base). payload = param2, out = param3.
  - msg 4  (INSTALL BASE): *(payload[3]) = baseProc(0xaaa). Chains to the reactive container base.
  - msg 5,6,7,8 (class register / global init / free): no-op here — handled by base (no per-class instance exists).
  - msg 9  (CREATE): parent = frame[0]; flags = (msgframe.style[3] & 0xfffff000) | 0x280; wparam = payload[0]. Calls FrameCreate(parent, flags, 0, childBtnProc(0xa9d), wparam, 0) to build the inner button, then FrameSetSubclassFlags(child, childBtnProc, 1, 0).
  - msg 0xc (POST-CREATE / LAYOUT): child = FrameGetChild(self,0); FrameEnable(child, payload); FrameMouseEnable(child, (payload!=0)?0x11:0, (payload!=0)?0:-1); FrameMouseEnable(child, ...) a second time. Wires mouse/enable state onto the child.
  - msg 0x15 (SIZE/RECT query): FrameMsgCallBase first, then inset the returned rect by 2px on ALL four edges (out[0..3] -= 2.0). This is the floating 2px border/padding.
  - msg 0x31 (CHILD EVENT/NOTIFY): if payload[2] (event code) >= 7 -> FrameMsgNotifyParent(self, code=payload[2], a=payload[3], b=payload[4]). Bubbles child events with code>=7 to the parent; codes <7 are swallowed.
  - msg 0x38 (NATIVE SIZE query): child = FrameGetChild(self,0); FrameGetNativeSize(&tmp, child, coord); copy tmp (2 floats) into payload[2]. Reports the child button's native size as its own.
  - msg >= 0x56 (all control-specific get/set): child = FrameGetChild(self,0); FrameMsgSend(child, msg, payload, out) — transparent forward of every 0x56+ accessor to the inner CtlBtn.
  - default (any other msg): FrameMsgCallBase (delegate to 0xaaa base).

- **Create recipe:**

To instantiate (mirrors msg 9): create the wrapper via the create primitive, e.g. FUN_0062bfc0(parent, flags, 0, UiCtlBtnFloatingProc, userdata, 0) where flags = (desiredStyle & 0xfffff000) | 0x280 (0x280 = 0x200|0x80 forces the low style bits; high bits preserved). The wrapper's own msg 9 then auto-creates the inner CtlBtn child (proc 0xa9d) — you do NOT create the button yourself.
Warm-up order after create:
  1. Let msg 9 run (child button gets created + subclass-flagged).
  2. Send msg 0xc to enable + mouse-enable the child (pass wparam!=0 to make it interactive: mouse mode 0x11).
  3. Set label/image/state by sending the normal CtlBtn accessor msgs (0x56+) to the FLOATING frame — they are auto-forwarded to the child.
Sizing: query size with msg 0x15 (returns child rect inset by 2px) or msg 0x38 (returns child native size). Do not size the wrapper independently of the child; the wrapper derives its size from the child minus the 2px border.
NOTE: This is a WASM-only control. It is NOT present in the 06-14 EXE, so there is no EXE proc address to call; the recipe applies to the current (WASM) client.

- **Crash gotchas:**

- WASM-only: absent from EXE 06-14 (no UiCtlBtnFloating.cpp string; signature flag build (style&0xfffff000)|0x280 exists nowhere in EXE code — only AND 0xfffff000 site is __alloca_probe, and the 0x280 push at 0x00611410 belongs to CtlImageList). Do not try to hook/call an EXE address for it.
- Requires EXACTLY one child at index 0. msgs 0xc, 0x38, and every 0x56+ accessor call FrameGetChild(self,0) then forward WITHOUT null-checking. If msg 9 failed (bad parent/style) or hasn't run yet, the child id is 0/invalid and the forwarded FrameMsgSend/FrameGetNativeSize will operate on a null frame.
- No per-instance struct: there is no instance-accessor for the wrapper itself. Any code expecting **(msgframe+8)-style instance data on the floating frame will read the base/frame object, not button state — always go through the child.
- msg 9 does style = (parentStyle & 0xfffff000) | 0x280. Callers that pre-strip high style bits (expecting them preserved) or expect the low bits they passed to survive will get 0x280 forced instead.
- msg 0x31 only bubbles child event codes >= 7; codes < 7 are silently dropped (no parent notification).
- msg 0x15 unconditionally subtracts 2.0 from all four rect components after the base call; nesting two floating wrappers compounds the inset (4px), which can collapse tiny buttons.


### UiCtlTextHeader  (EXE not-a-proc, confidence: high)

- **WASM:** ram:811e887d
- **Assertion file:** None of its own. Non-allocating decorator over CtlText: base assertion file is P:\Code\Engine\Controls\CtlText.cpp (used by the CtlText base proc FUN_00610c40 at alloc, size 0x60). No UiCtlTextHeader.cpp or "UiCtlTextHeader" name string exists in EXE 06-14 (unlike UiCtlGroupHeader/UiCtlTextShy).
- **Struct layout:**

No own instance struct. It reuses the CtlText instance created by the base proc FUN_00610c40 (allocated 0x60 bytes, vtable/&PTR set; from CtlText.cpp:0x18a). Observed CtlText/CText fields (frame->CText at frame+0x194; instance pointer stored via payload[2]): +0x04 text buffer ptr, +0x0c buffer length/capacity, +0x14 cursor/text-id (0xffffffff sentinel), +0x18 color A (rgba), +0x1c height/size float, +0x20 model array ptr, +0x28 model count, +0x30 color B (rgba). TextHeader adds zero fields and stores no per-instance state; its only persistent effect is the default-text-style bit 8 set on the frame's CText during init.

- **Message protocol:**

WASM IUi::UiCtlTextHeaderProc(FrameMsgHdr&, const void*, void*) switch(msgframe[1]=msg); it is a thin CtlText decorator that only overrides 3 messages and forwards everything else via FrameMsgCallBase:
- case 4 (parent/base install): writes the base proc into *(payload[3]) = CtlText proc. In WASM the stored value is function-table token 0xa81 (indirect); the EXE equivalent base is FUN_00610c40 (CtlText). Then FrameMsgCallBase.
- case 9 (create/init): FrameSetDefaultTextStyle(frame, 8)  -> EXE FUN_0062f4b0(frame,8); style bit 8 = bold/header default text style on the frame's CText (frame+0x194). Then FrameMsgCallBase. NOTE: NO instance allocation, NO double-init assert (unlike CtlText/TextShy).
- case 0x15 (FrameMsgSizeQuery): out = Rect4f margins {left,top,right,bottom} floats. Sets left=0, top=0; h = FrameGetDefaultTextHeight(frame) (EXE reads CText at frame+0x194, CText::GetHeight); if FrameTestStyles(frame, 0x20000) (EXE FUN_0062fe20(frame,0x20000)) is set, sets top = bottom = h*0.5 (adds half-line vertical padding). Then FrameMsgCallBase so CtlText fills the actual content size.
- all other msgs (5,6,7,8, 0xa..0x14, 0x16+, control get/set 0x56+): fall straight through to FrameMsgCallBase -> CtlText base.
EXE 06-14: this proc is NOT present as a standalone registered function. The identical behavior is emitted inline at each call site (create CtlText child with FUN_00610c40, then FUN_0062f4b0(child,8)); verified in FUN_0086af80, FUN_00858940, FUN_004db610, FUN_00573f30, FUN_0058b0c0.

- **Create recipe:**

Because EXE 06-14 has no dedicated proc, reproduce UiCtlTextHeader inline (this is exactly what the game does):
1. child = FUN_0062bfc0(parentFrame, styleFlags, childId, FUN_00610c40 /*CtlText proc*/, userdata, name). Header labels use layout style flags like 0x300 / 0x2300 / 0x80300 (seen at real sites); add 0x20000 if you want the half-line vertical padding behavior.
2. FUN_0062f4b0(child, 8)  // FrameSetDefaultTextStyle -> bold header default text style. THIS is the defining TextHeader step.
3. Set the text: FUN_00604aa0(child, &hTextId) or FUN_00612900/FUN_007c3bc0 to bind a HText/string id.
Order/warm-ups: the create primitive itself drives msg 4 (install CtlText base) then msg 9 (CtlText allocates the CText instance); you MUST let those run before setting text/style. Sizing is automatic via the CtlText 0x15 handler; the extra 0x20000 vertical padding is only applied if that style bit is present.
If targeting the WASM build directly, create/register with UiCtlTextHeaderProc so msg 9 auto-applies style 8 and msg 0x15 applies the 0x20000 padding.

- **Crash gotchas:**

- Non-allocating decorator: its case 9 does NOT allocate and does NOT assert on double-init. It depends 100% on the CtlText base; if case 4 fails to install FUN_00610c40 into payload[3], or case 9 skips FrameMsgCallBase, the CText object at frame+0x194 is never created and later text ops deref null.
- Order matters: FrameSetDefaultTextStyle(frame,8) must run after the base has created the CText (i.e. after base msg 9); calling it on a frame with no CText is unsafe.
- Style 0x20000 is dual-purpose: it is BOTH the size-query padding trigger here AND a CText render flag (CtlText msg 0x56 maps 0x20000 -> text-render flag 4). Setting it changes glyph rendering as well as layout.
- Size query (msg 0x15) writes a Rect4f (4 floats) into the out buffer before delegating; passing a null/short out buffer overflows (CtlText size paths assert 0xbd on null out).
- EXE 06-14 caveat: do not look for a single TextHeader address to hook; there is none. Hook/patch the inline sites or the shared FUN_0062f4b0(frame,8) idiom instead.


