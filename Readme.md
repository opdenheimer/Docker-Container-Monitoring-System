# 🩺 Container Doctor

> An autonomous AI agent that monitors Docker containers, diagnoses failures using Claude, and self-heals — zero human intervention required.

---

## What It Does

Container Doctor watches your running containers in real time. When it spots errors in logs, it sends them to Claude for diagnosis, notifies you on Slack, and — if safe — automatically restarts the container.

```
Docker Logs → Error Detection → Claude Diagnosis → Auto-Fix + Slack Alert
```

---

## Project Structure

```
container-doctor/
├── agent/
│   ├── main.py                          # Entrypoint — boots Flask + monitor loop
│   ├── Dockerfile
│   ├── requirements.txt
│   └── doctor/
│       ├── config.py                    # All env vars in one place
│       ├── core/
│       │   ├── monitor.py               # Main polling loop
│       │   ├── diagnosis.py             # Claude API integration
│       │   └── fixer.py                 # Auto-restart with safety guards
│       ├── notifications/
│       │   └── slack.py                 # Slack Block Kit alerts
│       ├── utils/
│       │   ├── docker_utils.py          # Log fetching & container restarts
│       │   ├── error_utils.py           # Pattern detection & deduplication
│       │   └── rate_limiter.py          # Hourly Claude API rate cap
│       └── api/
│           └── health.py                # /health and /history endpoints
├── docker-compose.yml
├── .env.example                         # ✅ commit this
├── .env                                 # ❌ never commit (in .gitignore)
├── .gitignore
└── README.md
```

---

## Quick Start

**1. Clone and configure**
```bash
git clone <your-repo>
cd container-doctor
cp .env.example .env
```

**2. Fill in `.env`**
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
TARGET_CONTAINERS=my_app,my_worker     # names of containers to watch
SLACK_WEBHOOK_URL=https://hooks.slack.com/...   # optional
```

**3. Run**
```bash
docker compose up -d
```

**4. Verify**
```bash
curl http://localhost:8080/health
curl http://localhost:8080/history
```

---

## How It Works

### 1. Log Polling
Every `CHECK_INTERVAL` seconds, the agent pulls the last `LOG_LINES` lines from each target container via the Docker socket.

### 2. Error Detection
Logs are scanned for 15 known patterns — `error`, `exception`, `traceback`, `oom`, `connection refused`, `timeout`, and more. Clean logs are skipped entirely.

### 3. Deduplication
The last 200 characters of logs are hashed. If the hash matches the previous check, the error is already known and skipped — eliminating alert storms.

### 4. Claude Diagnosis
Matching logs are sent to Claude with a structured prompt. Claude responds with a JSON diagnosis:

```json
{
  "root_cause": "Connection pool exhausted due to unclosed DB connections",
  "severity": "high",
  "suggested_fix": "Increase POOL_SIZE or fix connection leaks in app code",
  "auto_restart_safe": true,
  "config_suggestions": ["POOL_SIZE=20"],
  "likely_recurring": true,
  "estimated_impact": "All API requests return 500"
}
```

### 5. Auto-Fix (with safety guards)

Before restarting, three checks must pass:

| Guard | Behaviour |
|---|---|
| `AUTO_FIX=true` | Global kill switch — set to `false` to disable all restarts |
| `auto_restart_safe: true` | Claude must explicitly approve the restart |
| Restart cap | Max 3 restarts per container per hour — escalates to Slack after |

After restart, the agent waits 5 seconds and verifies the container is `running`.

### 6. Slack Alert
A formatted Block Kit alert is sent for every diagnosed issue, including severity, root cause, suggested fix, config recommendations, and whether an auto-restart was applied.

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | **Required** |
| `TARGET_CONTAINERS` | — | Comma-separated container names |
| `CHECK_INTERVAL` | `30` | Seconds between polls |
| `LOG_LINES` | `50` | Log lines pulled per check |
| `AUTO_FIX` | `true` | Master switch for auto-restarts |
| `MAX_DIAGNOSES_PER_HOUR` | `20` | Claude API rate cap |
| `SLACK_WEBHOOK_URL` | — | Slack incoming webhook (optional) |

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | Agent status, Docker connectivity, rate limit remaining |
| `GET /history` | Last 50 diagnoses with timestamps and severities |

---

## Keeping `.env` Secure

`.env` is in `.gitignore` — never commit it. Only `.env.example` (with placeholder values) goes into git.

**Local / single server**
```bash
chmod 600 .env          # restrict to owner only
```

**CI/CD (GitHub Actions)**
```yaml
- name: Deploy
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: |
    echo "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}" >> .env
    docker compose up -d
```

**Production (Docker Swarm)**
```bash
echo "sk-ant-your-key" | docker secret create anthropic_api_key -
```

**Quick checklist**
- [ ] `.env` is in `.gitignore`
- [ ] `.env.example` has only placeholder values
- [ ] `chmod 600 .env` on the server
- [ ] Health port bound to `127.0.0.1` not `0.0.0.0`
- [ ] `git log --all -- .env` returns nothing

---

## Cost

With rate limiting and deduplication, typical usage across 5 containers costs **~$3–5/month** on the Claude API.

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Diagnosis | Anthropic Claude (claude-sonnet-4) |
| Container Management | Docker SDK for Python |
| Health API | Flask |
| Alerts | Slack Block Kit |
| Runtime | Python 3.12, Docker Compose |

---

## Extending

**Add a new notification channel** (e.g. PagerDuty, email)
→ Create `doctor/notifications/pagerduty.py` and call it from `core/monitor.py`

**Add a new error pattern**
→ Append to `ERROR_PATTERNS` list in `doctor/utils/error_utils.py`

**Change the diagnosis schema**
→ Edit `DIAGNOSIS_SCHEMA` in `doctor/core/diagnosis.py`

---

## License

MIT