from flask import Flask, jsonify

from doctor.utils.docker_utils import get_docker_client, fix_history
from doctor.utils.rate_limiter import remaining
from doctor.config import TARGET_CONTAINERS
from datetime import datetime

app = Flask(__name__)

# Imported lazily to avoid circular imports
_diagnosis_history = None


def _history():
    global _diagnosis_history
    if _diagnosis_history is None:
        from doctor.core.monitor import diagnosis_history
        _diagnosis_history = diagnosis_history
    return _diagnosis_history


@app.route("/health")
def health():
    try:
        get_docker_client().ping()
        docker_ok = True
    except Exception:
        docker_ok = False

    return jsonify({
        "status":               "healthy" if docker_ok else "degraded",
        "docker_connected":     docker_ok,
        "monitoring":           TARGET_CONTAINERS,
        "total_diagnoses":      len(_history()),
        "fixes_applied":        {k: len(v) for k, v in fix_history.items()},
        "rate_limit_remaining": remaining(),
        "uptime_check":         datetime.now().isoformat(),
    })


@app.route("/history")
def history():
    return jsonify(_history()[-50:])
