import os


# ── Anthropic ──────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ── Monitoring ─────────────────────────────────────────────────────────────
TARGET_CONTAINERS = [c.strip() for c in os.getenv("TARGET_CONTAINERS", "").split(",") if c.strip()]
CHECK_INTERVAL    = int(os.getenv("CHECK_INTERVAL", "30"))
LOG_LINES         = int(os.getenv("LOG_LINES", "50"))
AUTO_FIX          = os.getenv("AUTO_FIX", "true").lower() == "true"

# ── Rate limiting ──────────────────────────────────────────────────────────
MAX_DIAGNOSES_PER_HOUR = int(os.getenv("MAX_DIAGNOSES_PER_HOUR", "20"))

# ── Slack ──────────────────────────────────────────────────────────────────
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
