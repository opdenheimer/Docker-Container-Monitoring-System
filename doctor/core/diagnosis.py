import json
import logging
from datetime import datetime

from anthropic import Anthropic

from doctor.utils.rate_limiter import check_rate_limit

logger = logging.getLogger(__name__)

_client = Anthropic()

DIAGNOSIS_SCHEMA = """{
    "root_cause":         "One sentence explaining exactly what went wrong",
    "severity":           "low | medium | high",
    "suggested_fix":      "Step-by-step fix the operator should apply",
    "auto_restart_safe":  true or false,
    "config_suggestions": ["ENV_VAR=value"],
    "likely_recurring":   true or false,
    "estimated_impact":   "What breaks if this is not fixed"
}"""


def diagnose(container_name: str, logs: str, error_patterns: list[str]) -> dict | None:
    """
    Send logs to Claude and return a parsed diagnosis dict, or None on failure.
    """
    if not check_rate_limit(container_name):
        return None

    prompt = (
        f"You are a DevOps expert analyzing container logs.\n\n"
        f"Container: {container_name}\n"
        f"Timestamp: {datetime.now().isoformat()}\n"
        f"Detected patterns: {', '.join(error_patterns)}\n\n"
        f"Recent logs:\n---\n{logs}\n---\n\n"
        f"Respond with ONLY valid JSON (no markdown, no explanation):\n"
        f"{DIAGNOSIS_SCHEMA}"
    )

    try:
        message = _client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        return _parse(message.content[0].text)
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return None


def _parse(text: str) -> dict | None:
    try:
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e} | raw: {text}")
    except Exception as e:
        logger.error(f"Failed to parse diagnosis: {e}")
    return None
