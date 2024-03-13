"""
64 63                                           19     12           0
 0  00011000111000111000000101110101101101000100 1110101 000000000111

64-63: Always 0
63-19: Unix timestamp in milliseconds
19-12: Process ID
12-00: Incrementing per-process ID
"""

import datetime
import os
import time

_incrementing_id = 0


def create_snowflake(
    t: float | int | datetime.datetime | None = None,
    pid: int | None = None,
    increment: int | None = None,
) -> int:
    if t is None:
        # WARNING: this may roll back or forwards depending on system time
        t = time.time_ns() // 1000000
    elif isinstance(t, datetime.datetime):
        t = int(t.timestamp() * 1000)
    elif isinstance(t, float):
        t = int(t * 1000)

    if t.bit_length() > 44:
        raise OverflowError(f"Timestamp {t} out of bounds (are we in 2527?)")

    if pid is None:
        pid = os.getpid()

    if increment is None:
        global _incrementing_id
        increment = _incrementing_id
        _incrementing_id += 1

    pid = pid % 128
    increment = increment % 4096

    return (t << 19) + (pid << 12) + increment
