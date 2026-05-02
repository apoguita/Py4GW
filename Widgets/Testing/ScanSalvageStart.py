import time

import PyScanner


MODULE_NAME = "ScanSalvageStart"

TEXT = 0
RUN_ONCE = True
RESCAN_INTERVAL_SECONDS = 30.0

_last_run_time = 0.0
_has_run = False


def _scanner():
    return PyScanner.PyScanner


def _fmt_addr(addr):
    try:
        addr = int(addr or 0)
    except Exception:
        addr = 0
    return f"0x{addr:08X}"


def _is_text(addr):
    try:
        return bool(_scanner().IsValidPtr(int(addr or 0), TEXT))
    except Exception:
        return False


def _ensure_scanner_ready():
    try:
        _scanner().Initialize("")
    except Exception as exc:
        print(f"[{MODULE_NAME}] scanner_initialize_error: {type(exc).__name__}: {exc}")
        return False
    print(f"[{MODULE_NAME}] scanner initialized")
    return True


def _function_start(addr, scan_range=0x1200):
    addr = int(addr or 0)
    if not _is_text(addr):
        return 0
    try:
        func = int(_scanner().ToFunctionStart(addr, int(scan_range)) or 0)
    except Exception as exc:
        print(f"[{MODULE_NAME}] to_function_start_error addr={_fmt_addr(addr)}: {type(exc).__name__}: {exc}")
        return 0
    return func if _is_text(func) else 0


def _scan_pattern(name, pattern, mask, offset=0):
    try:
        addr = int(_scanner().Find(pattern, mask, int(offset), TEXT) or 0)
    except Exception as exc:
        print(f"[{MODULE_NAME}] pattern_error {name}: {type(exc).__name__}: {exc}")
        return 0, 0

    func = _function_start(addr)
    print(
        f"[{MODULE_NAME}] pattern {name}: "
        f"addr={_fmt_addr(addr)} func={_fmt_addr(func)} "
        f"delta={addr - func if addr and func else 'n/a'}"
    )
    return addr, func


def _scan_assertion(file_name, message):
    try:
        addr = int(_scanner().FindAssertion(file_name, message, 0, 0) or 0)
    except Exception as exc:
        print(
            f"[{MODULE_NAME}] assertion_error file={file_name!r} "
            f"msg={message!r}: {type(exc).__name__}: {exc}"
        )
        return 0, 0

    func = _function_start(addr)
    print(
        f"[{MODULE_NAME}] assertion file={file_name!r} msg={message!r}: "
        f"addr={_fmt_addr(addr)} func={_fmt_addr(func)} "
        f"delta={addr - func if addr and func else 'n/a'}"
    )
    return addr, func


def _print_scan_status():
    try:
        status = _scanner().GetScanStatus()
    except Exception as exc:
        print(f"[{MODULE_NAME}] scan_status_error: {type(exc).__name__}: {exc}")
        return

    scans = status.get("scans", {}) if isinstance(status, dict) else {}
    hooks = status.get("hooks", {}) if isinstance(status, dict) else {}
    print(f"[{MODULE_NAME}] scan_status counts: scans={len(scans)} hooks={len(hooks)}")

    interesting = []
    for name, addr in scans.items():
        lname = str(name).lower()
        if "salvage" in lname or "identify" in lname:
            interesting.append((str(name), addr))

    if not interesting:
        print(f"[{MODULE_NAME}] scan_status interesting scans: none")
        return

    for name, addr in sorted(interesting):
        print(f"[{MODULE_NAME}] scan_status scan {name}={_fmt_addr(addr)}")


def _scan_itcli_candidate():
    print(f"[{MODULE_NAME}] itcli_candidate begin")
    checks = [
        "targetInventoryId",
        "targetItemId",
        "context->inventoryTable.Get(targetInventoryId)",
        "context->itemTable.Get(targetItemId)",
        "context->itemTable.Get(sourceItemId)",
    ]
    results = []
    for message in checks:
        addr, func = _scan_assertion("ItCliApi.cpp", message)
        results.append((message, addr, func))

    primary_func = results[0][2] if results else 0
    support = [message for message, _, func in results if primary_func and func == primary_func]
    print(f"[{MODULE_NAME}] itcli_candidate primary_func={_fmt_addr(primary_func)} support={support}")
    for message, addr, func in results:
        print(
            f"[{MODULE_NAME}] itcli_candidate check msg={message!r} "
            f"addr={_fmt_addr(addr)} func={_fmt_addr(func)} "
            f"matches_primary={bool(primary_func and func == primary_func)}"
        )
    print(f"[{MODULE_NAME}] itcli_candidate end")


def _run_scan():
    print(f"[{MODULE_NAME}] begin safe_scan_version=3")
    if not _ensure_scanner_ready():
        print(f"[{MODULE_NAME}] scanner is not ready; skipping scan")
        return

    _print_scan_status()

    _scan_pattern(
        "old_exact_line_0638_plus_ba_9c7c",
        b"\x75\x14\x68\x38\x06\x00\x00\xBA\x7C\x9C",
        "xxxxxxxxxx",
    )
    _scan_pattern(
        "old_line_0625",
        b"\x75\x14\x68\x25\x06\x00\x00",
        "xxxxxxx",
    )
    _scan_pattern(
        "old_line_0638",
        b"\x75\x14\x68\x38\x06\x00\x00",
        "xxxxxxx",
    )
    _scan_pattern(
        "loose_jnz14_push_any_imm32_mov_edx",
        b"\x75\x14\x68\x00\x00\x00\x00\xBA",
        "xxx????x",
    )
    _scan_pattern(
        "loose_jnz14_push_line_06xx_mov_edx",
        b"\x75\x14\x68\x00\x06\x00\x00\xBA",
        "xxx?xxxx",
    )

    _scan_assertion("InvSalvage.cpp", "m_toolId")
    _scan_itcli_candidate()

    print(f"[{MODULE_NAME}] end")


def main():
    global _has_run, _last_run_time

    now = time.time()
    if RUN_ONCE and _has_run:
        return
    if not RUN_ONCE and now - _last_run_time < RESCAN_INTERVAL_SECONDS:
        return

    _has_run = True
    _last_run_time = now
    try:
        _run_scan()
    except Exception as exc:
        print(f"[{MODULE_NAME}] ERROR: {type(exc).__name__}: {exc}")
