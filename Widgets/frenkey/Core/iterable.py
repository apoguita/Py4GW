
from typing import Iterable, Iterator, TypeVar


def chunked(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))