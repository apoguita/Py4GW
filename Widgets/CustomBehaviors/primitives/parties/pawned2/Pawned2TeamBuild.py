from __future__ import annotations

import base64
import re
from typing import List, Dict, Any


class Pawned2TeamBuild:
    """
    Encoder/decoder for paw·ned² team build templates based on PwndTemplate.php.

    Primary API:
      - encode(templates: list[str]) -> str
          Accepts a list of Guild Wars template strings (base64, unpadded; e.g., skill templates)
          and emits a full paw·ned² text with header, >payload<, and 80-char line wrapping.

      - decode(pwnd: str) -> list[str]
          Parses a paw·ned² text and returns the list of skill template strings in order.

    Notes:
      - This mirrors the PHP implementation: length-prefixed base64 chunks using a single base64 char
        as the length for skills/equipment/weaponsets/flags/player and two base64 chars for description length.
      - "player" and "description" are stored in the paw·ned² format as base64(no padding) of raw bytes.
        For encode(), we leave them empty except for a minimal description ("\r\n") like the PHP default.
    """

    BASE64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    PWND_PREFIX = "pwnd0001"
    PWND_HEADER = "pwnd-encoder by @codemasher: https://github.com/build-wars/gw-templates"

    # ------------------------ helpers ------------------------
    @classmethod
    def _base64_ord(cls, ch: str) -> int:
        if len(ch) != 1:
            raise ValueError("expected single base64 character")
        idx = cls.BASE64.find(ch)
        if idx == -1:
            raise ValueError(f"invalid base64 character: {ch!r}")
        return idx

    @classmethod
    def _base64_chr(cls, n: int) -> str:
        if not (0 <= n < 64):
            raise ValueError(f"ordinal out of range: {n}")
        return cls.BASE64[n]

    @staticmethod
    def _check_charset(s: str) -> str:
        s2 = s.replace("=", "")  # no padding in this format
        if not re.fullmatch(r"[A-Za-z0-9+/]*", s2):
            raise ValueError("Base64 must match RFC3548 character set (A-Za-z0-9+/)")
        return s2

    @staticmethod
    def _b64_encode_nopad(data: bytes) -> str:
        return base64.b64encode(data).decode("ascii").rstrip("=")

    @staticmethod
    def _b64_decode_nopad(s: str) -> bytes:
        # add padding to multiple of 4
        pad = (-len(s)) % 4
        if pad:
            s = s + ("=" * pad)
        return base64.b64decode(s)

    # ------------------------ public: decode ------------------------
    def decode(self, pwnd: str) -> List[str]:
        """Return the list of skill template strings from a full paw·ned² string."""
        builds = self.decode_full(pwnd)
        return [b["skills"] for b in builds]

    def decode_full(self, pwnd: str) -> List[Dict[str, Any]]:
        """
        Parse a paw·ned² string into a list of build dicts matching the PHP keys:
          { skills: str, equipment: str, weaponsets: [str,str,str], flags: str,
            player: bytes, description: bytes }
        """
        s = pwnd.strip()
        # mirror PHP: remove CR/LF only; and later we look between > and <
        s = s.replace("\r", "").replace("\n", "")

        # Validate header and find payload delimiters
        start = s.rfind(">")
        end_pos = s.find("<", start)
        if not s.startswith("pwnd000"):
            raise ValueError("invalid pwnd template (missing prefix)")
        if start == -1 or end_pos == -1 or end_pos <= start:
            raise ValueError("invalid pwnd template (missing >...< payload)")

        # Extract payload and normalize spaces to '+' as in PHP
        b64 = s[start + 1 : end_pos].replace(" ", "+")
        total = len(b64)
        offset = 0

        def read(n: int) -> str:
            nonlocal offset
            chunk = b64[offset : offset + n]
            offset += n
            return chunk

        def read_len_prefixed() -> str:
            length = self._base64_ord(read(1))
            return read(length)

        builds: List[Dict[str, Any]] = []
        while offset < total:
            build: Dict[str, Any] = {
                "skills": "",
                "equipment": "",
                "weaponsets": [],
                "player": b"",
                "description": b"",
                "flags": "",
            }

            build["skills"] = read_len_prefixed()
            build["equipment"] = read_len_prefixed()

            wsets: List[str] = []
            for _ in range(3):
                wsets.append(read_len_prefixed())
            build["weaponsets"] = wsets

            build["flags"] = read_len_prefixed()  # ignored semantics

            player_b64 = read_len_prefixed()
            build["player"] = self._b64_decode_nopad(player_b64) if player_b64 else b""

            if offset >= total:
                # no room for description length -> stop (robustness)
                break

            len_hi = self._base64_ord(read(1))
            len_lo = self._base64_ord(read(1))
            desc_len = len_hi * 64 + len_lo
            desc_b64 = read(desc_len)
            build["description"] = self._b64_decode_nopad(desc_b64) if desc_b64 else b""

            builds.append(build)

        return builds

    # ------------------------ public: encode ------------------------
    def encode(self, templates: List[str]) -> str:
        """
        Build a paw·ned² string from a list of GW template strings.
        For each template we emit:
          skills=<template>, equipment='', 3x weaponsets='', flags='', player='', description='\r\n'.
        """
        # Pre-normalize/validate all skill templates
        skills_list = [self._check_charset(t or "") for t in templates]

        # Minimal defaults (as per PHP addBuild())
        player_b64 = ""  # empty
        description_b64 = self._b64_encode_nopad(b"\r\n")

        def write_field(s: str) -> str:
            return self._base64_chr(len(s)) + s

        payload_parts: list[str] = []
        for skills in skills_list:
            payload_parts.append(write_field(skills))            # skills
            payload_parts.append(write_field(""))               # equipment
            payload_parts.append(write_field(""))               # weaponset 1
            payload_parts.append(write_field(""))               # weaponset 2
            payload_parts.append(write_field(""))               # weaponset 3
            payload_parts.append(write_field(""))               # flags (zero-length)
            payload_parts.append(write_field(player_b64))       # player (empty)
            # description length = 2 base64 chars (hi, lo) of len(description_b64)
            hi = len(description_b64) // 64
            lo = len(description_b64) % 64
            payload_parts.append(self._base64_chr(hi))
            payload_parts.append(self._base64_chr(lo))
            payload_parts.append(description_b64)

        payload = "".join(payload_parts)

        # Wrap with >payload< and split lines at 80 chars, prepend header line
        bracketed = ">" + payload + "<"
        lines = [bracketed[i : i + 80] for i in range(0, len(bracketed), 80)]
        header = f"{self.PWND_PREFIX}?{self.PWND_HEADER}"
        return "\r\n".join([header, *lines])

