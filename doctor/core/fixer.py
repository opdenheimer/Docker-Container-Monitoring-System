import logging

from doctor.utils.docker_utils import restart_container, fix_history
from doctor.notifications.slack import send_alert

logger = logging.getLogger(__name__)


def attempt_fix(container_name: str, diagnosis: dict) -> bool:
    """
    Try to auto-fix a high-severity issue.
    Sends a repeated-failure alert if the restart cap is hit.
    """
    from datetime import datetime, timedelta

    # Check restart cap before attempting — send escalation alert if needed
    recent = [
        t for t in fix_history[container_name]
        if t > datetime.now() - timedelta(hours=1)
    ]
    if len(recent) >= 3:
        logger.warning(f"'{container_name}' has been restarted 3+ times this hour.")
        send_alert(
            container_name, diagnosis,
            extra="⚠️ REPEATED FAILURE: Restarted 3+ times this hour. Manual intervention needed.",
        )
        return False

    return restart_container(container_name, diagnosis)
