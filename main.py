from __future__ import annotations

"""(MSC) Morphological Source Code: pyword.c v0.0.12
================================================================================
<https://github.com/Morphological-Source-Code/pyword.c> • MSC: Morphological Source Code © 2025 by Phovos
Imports only 3.12+ stdlibs."""
import re
import sys
import math
import enum
import logging
import logging.config
import argparse
import platform
import multiprocessing
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from collections.abc import Iterable
from functools import reduce
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Set, Type
try:
    from pyword import PyWord          # type: ignore
except ImportError as e:               # pragma: no cover
    print(f"Cannot import C extension: {e}", file=sys.stderr)
    sys.exit(2)
try:
    if platform.system() == "Windows":
        from ctypes import windll, byref, wintypes

        # from ctypes.wintypes import HANDLE, DWORD, LPWSTR, LPVOID, BOOL
        from pathlib import PureWindowsPath

        class WindowsConsole:
            """Enable ANSI escape sequences on Windows consoles."""

            @staticmethod
            def enable_ansi() -> None:
                STD_OUTPUT_HANDLE = -11
                ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
                kernel32 = windll.kernel32
                handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
                mode = wintypes.DWORD()
                if kernel32.GetConsoleMode(handle, byref(mode)):
                    new_mode = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
                    kernel32.SetConsoleMode(handle, new_mode)
                else:
                    raise RuntimeError("Failed to get console mode for enabling ANSI.")

        try:
            WindowsConsole.enable_ansi()
        except Exception as e:
            print(
                f"Failed to enable ANSI escape codes on Windows console: {e}",
                file=sys.stderr,
            )
            sys.exit(1)
except (ImportError, OSError, RuntimeError) as e:
    # If enabling ANSI fails (e.g., not a real console), print a warning
    # but don't exit. The program can run, just without colors.
    print(
        f"Warning: Failed to enable ANSI escape codes on Windows: {e}", file=sys.stderr
    )


@dataclass
class LogAdapter:
    """
    Sets up console + file + broadcast + (optional) queue handlers, and exposes a correlation-aware logger instance. You can customize handler levels and output filenames at instantiation time.
    ---
    | Token             | Meaning                                      |
    | ----------------- | -------------------------------------------- |
    | `%(asctime)s`     | Timestamp                                    |
    | `%(name)s`        | Logger name (`__name__`)                     |
    | `%(levelname)s`   | Log level name                               |
    | `%(message)s`     | The actual message                           |
    | `%(filename)s`    | File name where the log is emitted           |
    | `%(lineno)d`      | Line number of the log statement             |
    | `%(funcName)s`    | Function name                                |
    | `%(threadName)s`  | Thread name (super useful w/ `threading`)    |
    | `%(processName)s` | Process name (helpful for `multiprocessing`) |
    ---

    """

    console_level: str = "INFO"
    file_filename: str = "app.log"
    file_level: str = "INFO"
    broadcast_filename: str = "broadcast.log"
    broadcast_level: str = "INFO"
    queue_size: Optional[int] = (
        None  # Set to -1 for infinite, or a positive int for a sized queue
    )
    correlation_id: str = "SYSTEM"
    LOGGING_CONFIG: dict = field(init=False)
    logger: logging.Logger = field(init=False)

    def __post_init__(self):
        self.LOGGING_CONFIG = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'default': {
                    'format': '[%(levelname)s] %(asctime)s | [%(filename)s:%(lineno)d]: %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S',
                },
                'color': {
                    '()': self.ColorFormatter,
                    'format': '[%(levelname)s] %(asctime)s | [%(filename)s:%(lineno)d]: %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S',
                },
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': self.console_level,
                    'formatter': 'color',
                    'stream': 'ext://sys.stdout',
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': self.file_level,
                    'formatter': 'default',
                    'filename': self.file_filename,
                    'maxBytes': 10 * 1024 * 1024,
                    'backupCount': 5,
                    'encoding': 'utf-8',
                },
                'broadcast': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': self.broadcast_level,
                    'formatter': 'default',
                    'filename': self.broadcast_filename,
                    'maxBytes': 10 * 1024 * 1024,
                    'backupCount': 5,
                    'encoding': 'utf-8',
                },
            },
            'root': {
                'level': 'INFO',
                # This will be determined by whether a queue is used or not
                'handlers': [],
            },
        }
        # The list of handlers that do the actual work (writing to console/file)
        destination_handlers = ['console', 'file', 'broadcast']
        if self.queue_size is not None:
            # If a queue is used, configure it and make it the ONLY handler for the root logger.
            # The QueueHandler itself will then dispatch to the destination handlers.
            self.LOGGING_CONFIG['handlers']['queue'] = {
                'class': 'logging.handlers.QueueHandler',
                # This is the crucial missing piece:
                'handlers': destination_handlers,
                'queue': multiprocessing.Queue(self.queue_size),
            }
            self.LOGGING_CONFIG['root']['handlers'] = ['queue']
        else:
            # If no queue is used, the root logger sends directly to the destination handlers.
            self.LOGGING_CONFIG['root']['handlers'] = destination_handlers

        logging.config.dictConfig(self.LOGGING_CONFIG)
        base_logger = logging.getLogger(__name__)
        self.logger = self.CorrelationLogger(base_logger, {"cid": self.correlation_id})

        self.logger.info("Logger initialized.")

    class CorrelationLogger(logging.LoggerAdapter):
        def process(self, msg: str, kwargs: Any) -> tuple[str, Any]:
            cid = self.extra.get("cid", "SYSTEM")
            return f"[{cid}] {msg}", kwargs

    class ColorFormatter(logging.Formatter):
        _COLORS = {
            logging.DEBUG: "\033[34m",  # Blue
            logging.INFO: "\033[32m",  # Green
            logging.WARNING: "\033[33m",  # Yellow
            logging.ERROR: "\033[31m",  # Red
            logging.CRITICAL: "\033[41m",  # Red background
        }
        _RESET = "\033[0m"

        def format(self, record: logging.LogRecord) -> str:
            base = super().format(record)
            color = self._COLORS.get(record.levelno, self._COLORS[logging.DEBUG])
            return f"{color}{base}{self._RESET}"


# Global Registry for Morphological Classes and Functions
MSC_REGISTRY: Dict[str, Set[str]] = {'classes': set(), 'functions': set()}


# Exception for Morphodynamic Collapse
class MorphodynamicCollapse(Exception):
    """Raised when a morph object destabilizes."""

    pass


# MorphSpec Blueprint for Morphological Classes
@dataclass
class MorphSpec:
    """Blueprint for morphological classes."""

    entropy: float
    trigger_threshold: float
    memory: dict
    signature: str


# Morphology Decorator for Class Registration and Validation
def morphology(source_model: Type) -> Callable[[Type], Type]:
    """Decorator: register & validate a class against a MorphSpec."""

    def decorator(target: Type) -> Type:
        target.__msc_source__ = source_model
        # Ensure target has all annotated fields from source_model
        for field_name in getattr(source_model, '__annotations__', {}):
            if field_name not in getattr(target, '__annotations__', {}):
                raise TypeError(f"{target.__name__} missing field '{field_name}'")
        MSC_REGISTRY['classes'].add(target.__name__)
        return target

    return decorator

BENCH_SIZE   = 64          # bytes per PyWord / bytearray
ROUNDS       = 1_000_000   # iterations
WARMUP       = 10_000
# ------------------------------------------------------------------
def _warmup(logger: logging.Logger) -> None:
    """Touch the code path so branch-predictor settles."""
    w = PyWord()                      # import added below
    dummy = bytearray(BENCH_SIZE)
    for _ in range(WARMUP):
        w.set_bytes(dummy)
        _ = w.get_bytes()
    logger.debug("Warm-up complete")

def _bench_c_ext(logger: logging.Logger) -> tuple[float, float]:
    """Return (bandwidth MB/s, latency ns/op)."""
    import time
    w = PyWord()
    payload = bytes(range(BENCH_SIZE))
    logger.info("Starting C-extension benchmark …")
    t0 = time.perf_counter()
    for _ in range(ROUNDS):
        w.set_bytes(payload)          # copy in
        _ = w.get_bytes()             # copy out
    t1 = time.perf_counter()
    elapsed = t1 - t0
    bytes_total = ROUNDS * BENCH_SIZE * 2        # in + out
    bandwidth = bytes_total / elapsed / 1e6      # MB/s
    latency   = (elapsed / ROUNDS) * 1e9         # ns
    return bandwidth, latency

def _bench_python(logger: logging.Logger) -> tuple[float, float]:
    """Same loop with pure-Python bytearray for comparison."""
    import time
    buf = bytearray(BENCH_SIZE)
    payload = bytes(range(BENCH_SIZE))
    logger.info("Starting pure-Python bytearray baseline …")
    t0 = time.perf_counter()
    for _ in range(ROUNDS):
        buf[:] = payload              # copy in
        _ = bytes(buf)                # copy out
    t1 = time.perf_counter()
    elapsed = t1 - t0
    bytes_total = ROUNDS * BENCH_SIZE * 2
    bandwidth = bytes_total / elapsed / 1e6
    latency   = (elapsed / ROUNDS) * 1e9
    return bandwidth, latency

# ------------------------------------------------------------------
def main(argv: list[str] | None = None) -> None:
    global ROUNDS, BENCH_SIZE
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(description="PyWord micro-benchmark")
    parser.add_argument("-r", "--rounds", type=int, default=ROUNDS,
                        help="Iterations (default 1 000 000)")
    parser.add_argument("-s", "--size", type=int, default=BENCH_SIZE,
                        help="Payload bytes (default 64)")
    args = parser.parse_args(argv)

    ROUNDS   = args.rounds
    BENCH_SIZE = args.size

    log = LogAdapter(correlation_id="BENCH").logger
    log.info("PyWord benchmark started")
    _warmup(log)

    c_bw, c_lat = _bench_c_ext(log)
    py_bw, py_lat = _bench_python(log)

    # pretty report
    def colour(v, good, bad): return f"\033[32m{v:.2f}\033[0m" if v > good else f"\033[31m{v:.2f}\033[0m"
    log.info("Results -------------------------------------------------")
    log.info(f"C ext  bandwidth : {colour(c_bw,  5000, 2000)} MB/s")
    log.info(f"C ext  latency    : {colour(c_lat,  5,   15)} ns/op")
    log.info(f"Python baseline  : {py_bw:.2f} MB/s  |  {py_lat:.2f} ns/op")
    log.info(f"Speed-up         : {c_bw/py_bw:.1f}× bandwidth  |  {py_lat/c_lat:.1f}× latency")

if __name__ == "__main__":
    main()