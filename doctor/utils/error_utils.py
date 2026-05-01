Error_log_state: dict[str, int] = {}   # container_name → last log hash

ERROR_PATTERNS = [
    "error", "exception", "traceback", "failed", "crash",
    "fatal", "panic", "segmentation fault", "out of memory",
    "killed", "oomkiller", "connection refused", "timeout",
    "permission denied", "no such file", "errno",
]


def detect_errors(logs: str) -> list[str]:
    """Return every error pattern found in the log string."""
    lower = logs.lower()
    return [p for p in ERROR_PATTERNS if p in lower]


def is_new_error(container_name: str, logs: str) -> bool:
    """
    Deduplicate: return False if we've already seen this exact error tail.
    Hashing only the last 200 chars keeps it lightweight.
    """
    log_hash = hash(logs[-200:]) if len(logs) > 200 else logs
    if Error_log_state.get(container_name) == log_hash:
        return False
    Error_log_state[container_name] = log_hash
    return True
