import logging
from datetime import datetime, timedelta
from collections import defaultdict

from doctor.config import MAX_DIAGNOSES_PER_HOUR

logger = logging.getLogger(__name__)

_counter: dict[str, int] = defaultdict(int)
_reset_at: datetime = datetime.now() + timedelta(hours=1)


def check_rate_limit(container_name: str) -> bool:
    """
    Returns True if a Claude call is allowed.
    Increments the counter for this container on approval.
    Resets the entire counter every hour.
    """
    global _counter, _reset_at

    if datetime.now() > _reset_at:
        _counter.clear()
        _reset_at = datetime.now() + timedelta(hours=1)

    total = sum(_counter.values())
    if total >= MAX_DIAGNOSES_PER_HOUR:
        logger.warning(f"Rate limit reached ({total}/{MAX_DIAGNOSES_PER_HOUR}/hr). Skipping '{container_name}'.")
        return False

    _counter[container_name] += 1
    return True


def remaining() -> int:
    return max(0, MAX_DIAGNOSES_PER_HOUR - sum(_counter.values()))
