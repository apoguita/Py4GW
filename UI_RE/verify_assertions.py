"""
Assertion String Verification (2026-06-04)
==========================================
Tests each Scanner::FindAssertion call that the new C++ Create
functions use. Runs in injected Python, no DLL rebuild needed.
All output via print().
"""
from Py4GWCoreLib.Scanner import Scanner


ASSERTIONS = [
    ("DropdownFrame", "UiCtlDropMenu.cpp",
     "!FrameGetChild(thisFrame, CTL_LIST_ENTRIES)"),
    ("SliderFrame", "CtlSlider.cpp",
     "value >= m_range.min"),
    ("EditableTextFrame", "UiCtlEditBox.cpp",
     "!s_editCaretMaterial"),
    ("ProgressBar", "UiCtlProgress.cpp",
     "!sm_rateArrowImageList"),
    ("TabsFrame", "CtlPage.cpp",
     "!IsBtnCode(pageCode)"),
]


def main():
    print("=" * 60)
    print("ASSERTION STRING VERIFICATION")
    print("Tests Scanner::FindAssertion for 5 new callbacks")
    print("=" * 60)

    for name, file, msg in ASSERTIONS:
        print(f"\n── {name} ──")
        print(f"  FindAssertion('{file}', '{msg}', 0, 0)")

        addr = Scanner.FindAssertion(file, msg, 0, 0)
        if not addr:
            print(f"  FAIL: FindAssertion returned 0 — string not found!")
            continue

        print(f"  Found at: 0x{addr:08X}")

        func_start = Scanner.ToFunctionStart(addr, 0xFFF)
        if not func_start:
            print(f"  FAIL: ToFunctionStart returned 0 — can't find function start!")
            continue

        print(f"  Function at: 0x{func_start:08X}")
        print(f"  RESULT: OK")

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("If all 5 show 'OK', the assertion strings are valid")
    print("and the crash is elsewhere (CreateUIComponent, flags, etc.)")
    print("=" * 60)


if __name__ == "__main__":
    main()
