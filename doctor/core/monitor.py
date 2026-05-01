import time
import logging
from datetime import datetime

from doctor.config import TARGET_CONTAINERS, CHECK_INTERVAL, AUTO_FIX, MAX_DIAGNOSES_PER_HOUR
from doctor.utils.docker_utils import get_container_logs
from doctor.utils.error_utils import detect_errors, is_new_error
from doctor.core.diagnosis import diagnose
from doctor.core.fixer import attempt_fix
from doctor.notifications.slack import send_alert

logger = logging.getLogger(__name__)

# Shared diagnosis history (also exposed via health endpoint)
diagnosis_history: list[dict] = []


def run() -> None:
    logger.info("Container Doctor starting up")
    logger.info(f"  Monitoring:  {TARGET_CONTAINERS}")
    logger.info(f"  Interval:    {CHECK_INTERVAL}s")
    logger.info(f"  Auto-fix:    {AUTO_FIX}")
    logger.info(f"  Rate limit:  {MAX_DIAGNOSES_PER_HOUR}/hour")

    while True:
        for container_name in TARGET_CONTAINERS:
            _check(container_name)
        time.sleep(CHECK_INTERVAL)


def _check(container_name: str) -> None:
    logs = get_container_logs(container_name)
    if not logs:
        return

    patterns = detect_errors(logs)
    if not patterns:
        return

    if not is_new_error(container_name, logs):
        return

    logger.warning(f"[{container_name}] Error patterns detected: {patterns}")

    diagnosis = diagnose(container_name, logs, patterns)
    if not diagnosis:
        logger.error(f"[{container_name}] Could not obtain diagnosis. Skipping.")
        return

    diagnosis_history.append({
        "container": container_name,
        "timestamp": datetime.now().isoformat(),
        "diagnosis": diagnosis,
        "patterns":  patterns,
    })

    logger.info(
        f"[{container_name}] severity={diagnosis.get('severity')} | "
        f"cause={diagnosis.get('root_cause')}"
    )

    fixed = False
    if diagnosis.get("severity") == "high":
        fixed = attempt_fix(container_name, diagnosis)

    send_alert(container_name, diagnosis, extra="Auto-restarted ✅" if fixed else "")
