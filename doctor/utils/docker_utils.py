import time
import logging
import docker
from datetime import datetime, timedelta
from collections import defaultdict

from doctor.config import AUTO_FIX, LOG_LINES

logger = logging.getLogger(__name__)

_docker_client = None
fix_history: dict[str, list[datetime]] = defaultdict(list)


def get_docker_client():
    global _docker_client
    if _docker_client is None:
        _docker_client = docker.from_env()
    return _docker_client


def get_container_logs(container_name: str) -> str | None:
    """Fetch the last LOG_LINES lines from a container."""
    try:
        container = get_docker_client().containers.get(container_name)
        return container.logs(tail=LOG_LINES, timestamps=True).decode("utf-8")
    except docker.errors.NotFound:
        logger.warning(f"Container '{container_name}' not found. Skipping.")
    except docker.errors.APIError as e:
        logger.error(f"Docker API error for '{container_name}': {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching logs for '{container_name}': {e}")
    return None


def restart_container(container_name: str, diagnosis: dict) -> bool:
    """
    Restart a container with safety guards:
      - AUTO_FIX global toggle
      - Claude's auto_restart_safe flag
      - Max 3 restarts per container per hour
      - Post-restart health verification
    """
    if not AUTO_FIX:
        logger.info("Auto-fix is disabled globally. Skipping restart.")
        return False

    if not diagnosis.get("auto_restart_safe"):
        logger.info(f"Claude flagged restart as unsafe for '{container_name}'. Skipping.")
        return False

    recent = [t for t in fix_history[container_name] if t > datetime.now() - timedelta(hours=1)]
    if len(recent) >= 3:
        logger.warning(f"'{container_name}' restarted {len(recent)}x this hour. Needs manual review.")
        return False

    try:
        container = get_docker_client().containers.get(container_name)
        logger.info(f"Restarting '{container_name}'...")
        container.restart(timeout=30)
        fix_history[container_name].append(datetime.now())

        time.sleep(5)
        container.reload()
        if container.status != "running":
            logger.error(f"'{container_name}' did not come back up after restart.")
            return False

        logger.info(f"'{container_name}' restarted successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to restart '{container_name}': {e}")
        return False
