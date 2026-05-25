"""
find_find_related_frame.py — Ghidra script to locate Ui_FindRelatedFrame in any Gw.exe version.

Run this in Ghidra's Python console (Window → Python) with Gw.exe open.

It finds the function by looking for a CALL to the relation walker (FUN_0062d1d0)
preceded by LEA ECX,[reg+0x128] — the unique FrameRelation offset pattern.
"""
from ghidra.program.model.listing import Instruction
from ghidra.program.model.symbol import Reference

FM = currentProgram.getFunctionManager()
LISTING = currentProgram.getListing()

# Step 1: Find all LEA reg,[reg+0x128] instructions
# Opcode: 8D ?? 28 01 00 00
candidates = []
min_addr = currentProgram.getMinAddress()
max_addr = currentProgram.getMaxAddress()
addr = min_addr

while addr < max_addr:
    try:
        b = getBytes(addr, 6)
        if b and len(b) == 6 and b[0] == 0x8D and b[2] == 0x28 and b[3] == 0x01 and b[4] == 0x00 and b[5] == 0x00:
            # LEA reg,[reg+0x128] = 8D ?? 28 01 00 00
            lea_addr = addr
            # Check next byte for CALL (0xE8)
            call_bytes = getBytes(addr.add(6), 1)
            if call_bytes and call_bytes[0] == 0xE8:
                candidates.append(lea_addr)
        addr = addr.add(1)
    except:
        addr = addr.add(1)

print(f"Found {len(candidates)} LEA reg,[reg+0x128]; CALL sequences")

# Step 2: For each candidate, check if it's in a function that:
#  - Has two calls to Ui_SelectFrameContext (0x006287c0-ish, will vary by version)
#  - Returns *(result + 0xBC)
# The unique indicator is XOR EAX,EAX right before the PUSH EAX; PUSH [EBP+0xC]; LEA; CALL
for lea_addr in candidates:
    # Check bytes before LEA for: 33 C0 50 FF 75 0C
    before = getBytes(lea_addr.subtract(4), 4)
    if before and len(before) == 4:
        if before[0] == 0x33 and before[1] == 0xC0 and before[2] == 0x50 and before[3] == 0xFF:
            # Check the byte before FF: should be 75 (JNZ) or FF 75 0C (PUSH [EBP+0xC])
            before2 = getBytes(lea_addr.subtract(5), 5)
            if before2 and before2[0] == 0xFF and before2[1] == 0x75 and before2[2] == 0x0C:
                func = FM.getFunctionContaining(lea_addr)
                if func:
                    func_addr = func.getEntryPoint()
                    print(f"\n✓ Found Ui_FindRelatedFrame at: 0x{func_addr.getOffset():08X}")
                    print(f"  LEA instruction at: 0x{lea_addr.getOffset():08X}")
                    print(f"  Copy this address into UIMgr.cpp:")
                    print(f"    FindRelatedFrame_Func = reinterpret_cast<FindRelatedFrame_pt>(0x{func_addr.getOffset():08X});")
                    # Also print AssertAddress string
                    print(f"  Pattern offset from function start: {lea_addr.getOffset() - func_addr.getOffset()} bytes")
