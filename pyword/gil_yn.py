#!/usr/bin/env -S uv run
# /* script
# requires-python = ">=3.14"
# dependencies = [
#     "uv==*.*",
# ]
# -*- coding: utf-8 -*-
#------------------------------
# 3.14 std libs **ONLY**      |
# Platform(s):                |
# Win11 (dev*, prod) *Sandbox |
# Ubuntu-22.04 (prod, staging)|
#------------------------------
import sys
import sysconfig
import threading
import time

def solve_row(n, cols=0, diags1=0, diags2=0, row=0):
    if row == n:
        return 1
    count = 0
    free = (~(cols | diags1 | diags2)) & ((1 << n) - 1)
    while free:
        bit = free & -free
        free -= bit
        count += solve_row(
            n, cols | bit, (diags1 | bit) << 1, (diags2 | bit) >> 1, row + 1
        )
    return count

def solve_threaded(n, n_threads):
    first_row = [(1 << c) for c in range(n)]
    chunks = [first_row[i::n_threads] for i in range(n_threads)]
    total = 0
    lock = threading.Lock()

    def work(chunk):
        nonlocal total
        local = 0
        for bit in chunk:
            local += solve_row(
                n, cols=bit, diags1=bit << 1, diags2=bit >> 1, row=1
            )
        with lock:
            total += local

    threads = [threading.Thread(target=work, args=(c,)) for c in chunks]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return total

def main():
    # Detect GIL mode
    gil_disabled = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))
    mode = "free-threaded" if gil_disabled else "GIL-enabled"
    print(f"Python {sys.version}")
    print(f"Mode: {mode}")
    print("-" * 40)

    for threads in (1, 2, 4, 8):
        t0 = time.perf_counter()
        result = solve_threaded(14, threads)
        dt = time.perf_counter() - t0
        print(f"threads={threads:<2}  time={dt:.2f}s  result={result}")

if __name__ == "__main__":
    main()