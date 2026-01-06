from typing import Optional, Any

def read_wstr(ptr: Any) -> Optional[str]:
    """Reads a wide string from a given pointer. Returns None if the pointer is null."""
    ...
    
def encoded_wstr_to_str(s: Optional[str]) -> Optional[str]:
    """
    Makes Guild Wars encoded strings visible by escaping control / non-printable characters.
    Returns None if the input string is None.
    """
    ...