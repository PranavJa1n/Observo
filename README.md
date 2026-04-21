# Observo

**Intelligent Log Analysis with AI-Powered Root Cause Detection**

Observo is a CLI tool that transforms chaotic log streams into clear, actionable insights. Instead of manually sifting through millions of log lines during incidents, Observo automatically clusters similar logs, detects anomalies, and uses AI to explain what's wrong and how to fix it.

---

🌐 **Landing Page:** [https://pranavja1n.github.io/Observo](https://pranavja1n.github.io/Observo)

---

## The Problem

Modern applications generate massive amounts of logs:
- **Expensive to store and index** - Traditional log management systems cost thousands per month
- **Noisy and repetitive** - 95% of logs are normal operations, making real issues hard to spot
- **Hard to interpret during incidents** - SREs waste hours searching logs, trying filters, guessing root causes

When something goes wrong, teams face:
- Overwhelming log volume (millions of lines per hour)
- Difficulty identifying which errors actually matter
- No clear path from "I see errors" to "I understand the problem"
- Precious time lost during outages manually analyzing logs

---

## The Solution

Observo uses a two-step approach to turn log chaos into clarity:

### 1. **Intelligent Log Clustering**
- Automatically groups similar log messages into distinct behavioral patterns
- Learns what's "normal" vs "anomalous" using keyword-based classification
- Reduces millions of log lines into a handful of meaningful clusters
- Highlights problematic clusters that represent real issues

**Result:** Instead of searching through endless logs, you see a concise summary of what your system is actually doing.

### 2. **AI-Powered Root Cause Analysis**
- When anomalous clusters are detected, a LangGraph AI agent analyzes them
- Generates plain-language explanations of what's going wrong
- Proposes likely root causes based on error patterns
- Suggests concrete remediation steps

**Result:** Move from "errors detected" to "here's the problem and how to fix it" in seconds.

---

## How It Works
```
Your Application Logs (Local Files)
        ↓
Observo watches log files/directories
        ↓
Batches logs every 60 seconds
        ↓
Go daemon sends batch → Python service (localhost:5000)
        ↓
Python clusters logs using HDBSCAN
        ↓
Detects anomalies (bad clusters)
        ↓
LangGraph AI agent analyzes bad clusters
        ↓
You get: Summary + Root Cause + Fix Suggestions
        ↓
Dashboard shows incidents + Email alerts sent
```

---

## Features

### Current Version (v1.0)

- 🎯 **Automatic log clustering** - Groups similar logs without manual configuration
- 🤖 **AI-powered analysis** - LangGraph agent explains incidents in plain language (Gemini, OpenAI, Claude, Perplexity)
- 📊 **Web dashboard** - React frontend at `localhost:6969` with dark/light theme
- 📧 **Email alerts** - Get notified when critical issues are detected
- 📁 **Local file monitoring** - Watch log files or directories in real-time
- 💾 **SQLite storage** - Lightweight local database, no external dependencies
- 🚀 **Simple CLI** - Five commands to control everything
- 🌐 **Landing page** - Public-facing page with interactive log animation and install guide

---

## Architecture
```
┌──────────────────────────┐
│    Observo CLI (Go)      │
│  cobra — 5 commands      │
└────────────┬─────────────┘
             │
┌────────────▼──────────────────────────────────┐
│         Observo Daemon (Go)                   │
│                                               │
│  ┌─────────────────────────────────────┐      │
│  │  File Watcher (fsnotify)            │      │
│  │  (Monitors local files/directories) │      │
│  └──────────────┬──────────────────────┘      │
│                 │                             │
│  ┌──────────────▼──────────────────────┐      │
│  │  60-Second Batch Buffer             │      │
│  └──────────────┬──────────────────────┘      │
│                 │                             │
│  ┌──────────────▼──────────────────────┐      │
│  │  Python Service Client (HTTP)       │──────┼──→ Python Service (FastAPI)
│  │  POST /process  GET /health         │      │    service/main.py
│  └──────────────┬──────────────────────┘      │    • HDBSCAN Clustering
│                 │                             │    • Anomaly Classification
│  ┌──────────────▼──────────────────────┐      │    • LangGraph AI Agent
│  │  Incident Storage (SQLite/GORM)     │      │
│  └──────────────┬──────────────────────┘      │
│                 │                             │
│  ┌──────────────▼──────────────────────┐      │
│  │  Email Alerts (SMTP)                │      │
│  └─────────────────────────────────────┘      │
│                                               │
│  ┌─────────────────────────────────────┐      │
│  │  Dashboard API (gorilla/mux)        │      │
│  │  GET /api/stats                     │      │
│  │  GET /api/incidents                 │      │
│  │  http://localhost:6969              │      │
│  └─────────────────────────────────────┘      │
└───────────────────────────────────────────────┘
             │
             ▼
      ┌──────────────┐
      │  SQLite DB   │
      │ ~/.observo/  │
      └──────────────┘
```

---

## Project Structure

```
Observo/
├── cmd/
│   └── main.go              # CLI entry point (cobra — init, start, stop, status, config)
├── internal/
│   ├── buffer/              # 60s batch buffer
│   ├── config/              # Config load/save (~/.observo/config.json)
│   ├── daemon/              # Daemon start/stop/PID management
│   ├── models/              # SQLite models (GORM)
│   ├── python_client/       # HTTP client → Python service
│   ├── server/              # Dashboard API server (gorilla/mux)
│   └── watcher/             # File watcher (fsnotify)
├── service/
│   ├── main.py              # Python FastAPI server (POST /process, GET /health)
│   └── agentic/
│       ├── gemini_agentic.py      # LangGraph agent — Google Gemini
│       ├── openai_agentic.py      # LangGraph agent — OpenAI GPT-4
│       ├── claude_agentic.py      # LangGraph agent — Anthropic Claude
│       └── perplexity_agentic.py  # LangGraph agent — Perplexity
├── frontend/
│   ├── main/                # React dashboard (Vite, port 6969 via Go proxy)
│   └── landingPage/         # React landing page (Vite, port 5173)
├── requirements.txt         # Python dependencies
├── go.mod                   # Go module
└── README.md
```

---

## Quick Start

### Prerequisites

- **Go 1.21+**
- **Python 3.9+**
- **Google Gemini API key** (or OpenAI / Anthropic / Perplexity)

### Installation

**Clone and build:**
```bash
git clone https://github.com/PranavJa1n/Observo.git
cd Observo
go build -o observo ./cmd/main.go
sudo mv observo /usr/local/bin/   # or add to PATH
```

**Install Python dependencies:**
```bash
pip install -r requirements.txt
```

### Initial Setup
```bash
# Initialize Observo (interactive setup)
observo init
```

You'll be prompted for:
- **Log source path** - Directory or file where your application writes logs
- **Alert email** (optional) - Email address for incident notifications
- **API key** - Your Google Gemini API key (or other provider)

**Example:**
```
Enter log file or directory path: /var/log/myapp
Enter alert email (optional, press Enter to skip): devops@company.com
Enter Google API key: AIza...
✓ Configuration saved to ~/.observo/config.json
```

### Start Monitoring
```bash
observo start
```

This will:
- Launch the Python processing service (`service/main.py`) on port 5000
- Start the Go daemon (file watcher + batch buffer)
- Start the dashboard API at `http://localhost:6969`
- Begin analyzing logs and detecting incidents

### Other Commands
```bash
observo status           # Check if Observo is running
observo stop             # Stop the daemon
observo config --path /new/log/path      # Change log source
observo config --alert-email me@mail.com # Update email
observo config --api-key AIza...         # Update API key
```

---

## Dashboard

Once Observo is running, access the dashboard at **http://localhost:6969**

### Dashboard Features

**System Status cards:**
- Daemon health (Running / Stopped)
- Total incidents detected
- System uptime

**Incidents View:**
- Expandable list of all detected incidents
- Each incident shows:
  - **Timestamp** — When the issue was first detected
  - **Problem Summary** — AI-generated description
  - **Root Cause Analysis** — AI's explanation of why it happened
  - **Sample Logs** — Representative logs from the anomalous cluster

**Theme:**
- Dark mode (charcoal/gray) and light mode (warm orange) — toggle in header

---

## Configuration

Stored in `~/.observo/config.json`. Manage with `observo config`:

```bash
# Change log source
observo config --source local --path /var/log/myapp

# Monitor a single file
observo config --source local --path /var/log/myapp/app.log

# Update alert email
observo config --alert-email newemail@company.com

# Disable email alerts
observo config --alert-email ""

# Update API key
observo config --api-key AIza...
```

---

## File Locations

| File | Path |
|---|---|
| Configuration | `~/.observo/config.json` |
| Database | `~/.observo/observo.db` |
| Daemon PID | `~/.observo/daemon.pid` |
| Daemon logs | `~/.observo/daemon.log` |

---

## How Clustering Works

### 1. Template Extraction
Converts variable log messages into reusable templates:
- `"User 12345 logged in from 192.168.1.1"` → `"User <ID> logged in from <IP>"`
- `"Order abc-123 processed in 450ms"` → `"Order <ID> processed in <TIME>"`

### 2. Semantic Clustering (HDBSCAN)
Uses HDBSCAN algorithm with semantic embeddings:
- Groups logs by meaning, not just keywords
- Automatically determines optimal number of clusters
- No manual configuration required

### 3. Anomaly Detection
Classifies clusters as "good" or "bad" using:
- **Keyword detection** — ERROR, FATAL, EXCEPTION, CRITICAL
- **Log level analysis** — High proportion of error-level logs

Only "bad" clusters trigger AI analysis, saving API costs.

---

## How AI Analysis Works

The LangGraph agent runs a two-stage workflow on anomalous clusters:

```
1. analyze node
   ↓ (sends cluster logs to LLM)
   Returns JSON: root_cause, severity, recommendations, affected_components

2. format node
   ↓ (structures the response)
   Returns LogAnalysisResult object → stored in SQLite
```

### Supported AI Providers

| Provider | File | Model |
|---|---|---|
| Google Gemini | `service/agentic/gemini_agentic.py` | gemini-pro |
| OpenAI | `service/agentic/openai_agentic.py` | gpt-4 |
| Anthropic Claude | `service/agentic/claude_agentic.py` | claude-3 |
| Perplexity | `service/agentic/perplexity_agentic.py` | sonar |

---

## Troubleshooting

### Observo won't start

```bash
observo status          # Check if already running
tail -f ~/.observo/daemon.log   # View daemon logs
```

**Common issues:**
- Port 6969 already in use → stop conflicting service
- Python service fails → check `pip install -r requirements.txt` completed
- Invalid config → run `observo init` again

### No logs being processed

```bash
ls -la /your/log/path   # Verify path exists
chmod 644 /your/log/*.log  # Ensure readable
```

> **Remember:** Logs are batched every 60 seconds — wait at least one minute after starting.

### AI analysis not working

- Invalid API key → `observo config --api-key YOUR_KEY`
- Rate limit exceeded → wait or upgrade plan
- Wrong provider → ensure `service/main.py` uses the correct agentic module

### Dashboard not loading

```bash
curl http://localhost:6969/api/stats   # Check API is up
observo status                         # Verify daemon running
```

---

## Performance

### Resource Usage

| Component | RAM |
|---|---|
| Go daemon | ~50 MB |
| Python service | ~200–500 MB (depends on model) |
| SQLite database | ~1 MB per 1,000 incidents |

### Throughput

- **Log processing:** ~10,000 logs/second
- **Batch interval:** 60 seconds (hardcoded)
- **Clustering time:** ~2–5 seconds per batch
- **AI analysis:** ~3–7 seconds per incident
- **Total latency:** ~70–75 seconds from log written to incident displayed

---

## Supported Log Formats

**Plain text:**
```
2026-02-01 10:30:15 ERROR [auth-service] Database connection failed
2026-02-01 10:30:16 INFO  [auth-service] Retrying connection...
```

**JSON logs:**
```json
{"timestamp":"2026-02-01T10:30:15Z","level":"ERROR","service":"auth","message":"Database connection failed"}
```

Observo auto-detects format and extracts: timestamp, log level, service name, message.

---

## Future Implementations

### Phase 2: Advanced Log Sources
- AWS S3 / Azure Blob / GCP Storage monitoring
- Multiple simultaneous sources
- Elasticsearch, Grafana Loki, CloudWatch connectors

### Phase 3: Enhanced Analytics
- Historical trend analysis and time-series visualization
- Statistical baseline learning (Z-score, IQR)
- Predictive analytics and capacity planning

### Phase 4: Incident Management
- Mark incidents resolved with notes, track MTTR
- Incident correlation and root cause propagation

### Phase 5: Dashboard Enhancements
- Real-time log streaming in dashboard
- Interactive trend charts and cluster heatmaps
- Multi-user support with RBAC

### Phase 6: Configuration & Flexibility
- YAML configuration files
- Tunable HDBSCAN parameters (min_cluster_size, batch interval)
- Custom classification rules

### Phase 7–11: Integrations, Enterprise, AI
- Slack, PagerDuty, Jira integrations
- Prometheus metrics export / OpenTelemetry
- PostgreSQL support, horizontal scaling
- Multi-model AI, feedback learning, runbook generation

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

---

## License

[To be determined — planned: MIT or Apache 2.0]

---

## Project Background

- **Type:** College Mini Project — AI & Machine Learning
- **Developers:** Pranav Jain & Madhav Garg
- **Focus:** HDBSCAN log clustering + LangGraph AI agent design + production-grade Go CLI

---

## Contact

- **Email:** [pranav.avlok@gmail.com]
- **Repository:** [https://github.com/PranavJa1n/Observo]

---

**Observo** — Turn log chaos into clarity with AI

*Built for the DevOps and SRE community*
