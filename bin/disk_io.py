"""Random 4K disk reads with best-effort unbuffered I/O (Windows/Linux)."""

from __future__ import annotations

import ctypes
import mmap
import os
import platform
import random
import time
from typing import Callable, Optional

BLOCK_SIZE = 4096


def _latencies_cached(
    path: str,
    file_size: int,
    iterations: int,
    check_cancel: Optional[Callable[[], None]] = None,
) -> list[float]:
    latencies: list[float] = []
    with open(path, "rb") as f:
        for i in range(iterations):
            if check_cancel and i % 500 == 0:
                check_cancel()
            offset = random.randint(0, max(0, file_size - BLOCK_SIZE))
            offset -= offset % BLOCK_SIZE
            t0 = time.perf_counter()
            f.seek(offset)
            chunk = f.read(BLOCK_SIZE)
            t1 = time.perf_counter()
            if not chunk:
                break
            latencies.append((t1 - t0) * 1000.0)
    return latencies


def _latencies_unbuffered_linux(
    path: str,
    file_size: int,
    iterations: int,
    check_cancel: Optional[Callable[[], None]] = None,
) -> list[float]:
    o_direct = getattr(os, "O_DIRECT", 0)
    if not o_direct:
        raise OSError("O_DIRECT not available")
    fd = os.open(path, os.O_RDONLY | o_direct)
    latencies: list[float] = []
    try:
        buf = mmap.mmap(-1, BLOCK_SIZE)
        try:
            for i in range(iterations):
                if check_cancel and i % 500 == 0:
                    check_cancel()
                offset = random.randint(0, max(0, file_size - BLOCK_SIZE))
                offset -= offset % BLOCK_SIZE
                t0 = time.perf_counter()
                n = os.preadv(fd, [buf], offset)
                t1 = time.perf_counter()
                if n != BLOCK_SIZE:
                    break
                latencies.append((t1 - t0) * 1000.0)
        finally:
            buf.close()
    finally:
        os.close(fd)
    return latencies


def _latencies_unbuffered_windows(
    path: str,
    file_size: int,
    iterations: int,
    check_cancel: Optional[Callable[[], None]] = None,
) -> list[float]:
    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
    GENERIC_READ = 0x80000000
    FILE_SHARE_READ = 0x00000001
    OPEN_EXISTING = 3
    FILE_FLAG_NO_BUFFERING = 0x20000000
    FILE_FLAG_RANDOM_ACCESS = 0x10000000
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
    FILE_BEGIN = 0

    handle = kernel32.CreateFileW(
        path,
        GENERIC_READ,
        FILE_SHARE_READ,
        None,
        OPEN_EXISTING,
        FILE_FLAG_NO_BUFFERING | FILE_FLAG_RANDOM_ACCESS,
        None,
    )
    if handle == INVALID_HANDLE_VALUE or handle is None:
        raise OSError(ctypes.get_last_error(), "CreateFileW NO_BUFFERING failed")

    latencies: list[float] = []
    raw = bytearray(BLOCK_SIZE * 2)
    addr = ctypes.addressof(ctypes.c_char.from_buffer(raw))
    align_off = (BLOCK_SIZE - (addr % BLOCK_SIZE)) % BLOCK_SIZE
    buf = (ctypes.c_char * BLOCK_SIZE).from_buffer(raw, align_off)
    read = ctypes.c_ulong(0)
    distance = ctypes.c_longlong(0)
    new_pos = ctypes.c_longlong(0)
    try:
        for i in range(iterations):
            if check_cancel and i % 500 == 0:
                check_cancel()
            offset = random.randint(0, max(0, file_size - BLOCK_SIZE))
            offset -= offset % BLOCK_SIZE
            distance.value = offset
            t0 = time.perf_counter()
            if not kernel32.SetFilePointerEx(handle, distance, ctypes.byref(new_pos), FILE_BEGIN):
                break
            ok = kernel32.ReadFile(handle, buf, BLOCK_SIZE, ctypes.byref(read), None)
            t1 = time.perf_counter()
            if not ok or read.value != BLOCK_SIZE:
                break
            latencies.append((t1 - t0) * 1000.0)
    finally:
        kernel32.CloseHandle(handle)
    return latencies


def measure_random_read_latencies(
    path: str,
    file_size: int,
    iterations: int,
    check_cancel: Optional[Callable[[], None]] = None,
) -> tuple[list[float], str]:
    """
    Best-effort unbuffered random 4K reads.
    Returns (latencies_ms, mode) with mode 'unbuffered' or 'cached'.
    """
    system = platform.system().lower()
    try:
        if system == "windows":
            lat = _latencies_unbuffered_windows(path, file_size, iterations, check_cancel)
        elif system == "linux":
            lat = _latencies_unbuffered_linux(path, file_size, iterations, check_cancel)
        else:
            lat = []
        if lat:
            return lat, "unbuffered"
    except (OSError, AttributeError, ValueError):
        pass
    return _latencies_cached(path, file_size, iterations, check_cancel), "cached"
