import logging
import requests

from doctor.config import SLACK_WEBHOOK_URL

logger = logging.getLogger(__name__)

SEVERITY_EMOJI = {"low": "🟡", "medium": "🟠", "high": "🔴"}


def send_alert(container_name: str, diagnosis: dict, extra: str = "") -> None:
    """Send a formatted Slack Block Kit alert. Silently skips if no webhook is set."""
    if not SLACK_WEBHOOK_URL:
        return

    severity = diagnosis.get("severity", "unknown")
    emoji    = SEVERITY_EMOJI.get(severity, "⚪")

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} Container Doctor — {container_name}",
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Severity:* {severity}"},
                {"type": "mrkdwn", "text": f"*Container:* `{container_name}`"},
                {"type": "mrkdwn", "text": f"*Root Cause:* {diagnosis.get('root_cause', 'Unknown')}"},
                {"type": "mrkdwn", "text": f"*Suggested Fix:* {diagnosis.get('suggested_fix', 'N/A')}"},
            ],
        },
    ]

    if diagnosis.get("estimated_impact"):
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Impact:* {diagnosis['estimated_impact']}"},
        })

    if diagnosis.get("config_suggestions"):
        suggestions = "\n".join(f"• `{s}`" for s in diagnosis["config_suggestions"])
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Config Suggestions:*\n{suggestions}"},
        })

    if diagnosis.get("likely_recurring"):
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "⚠️ *This issue is likely to recur.* Root cause fix needed."},
        })

    if extra:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*{extra}*"},
        })

    try:
        resp = requests.post(SLACK_WEBHOOK_URL, json={"blocks": blocks}, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"Slack notification failed: {e}")
