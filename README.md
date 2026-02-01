# Observo

**Intelligent Log Analysis with AI-Powered Root Cause Detection**

Observo is a CLI tool that transforms chaotic log streams into clear, actionable insights. Instead of manually sifting through millions of log lines during incidents, Observo automatically clusters similar logs, detects anomalies, and uses AI to explain what's wrong and how to fix it.

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
- When anomalous clusters are detected, an AI agent analyzes them
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
Clusters similar log patterns
        ↓
Detects anomalies (bad clusters)
        ↓
AI analyzes bad clusters
        ↓
You get: Summary + Root Cause + Fix Suggestions
        ↓
Dashboard shows incidents + Email alerts sent
```

---

## Features

### Current Version (v1.0)

- 🎯 **Automatic log clustering** - Groups similar logs without manual configuration
- 🤖 **AI-powered analysis** - Uses AI Agent to explain incidents in plain language
- 📊 **Web dashboard** - View all detected incidents with full AI analysis
- 📧 **Email alerts** - Get notified when critical issues are detected
- 📁 **Local file monitoring** - Watch log files or directories in real-time
- 💾 **Lightweight storage** - Stores only important incidents, not all logs
- 🚀 **Simple setup** - Works out of the box with minimal configuration
- ⚙️ **Easy configuration** - Configure via intuitive CLI commands

---

## Quick Start

### Prerequisites

**Required:**
- Go 1.21+ (for running the daemon)
- Python 3.9+ (for processing service)

### Installation

### Initial Setup
```bash
# Initialize Observo (interactive setup)
observo init
```

You'll be prompted for:
- **Log source path** - Directory or file where your application writes logs
- **Alert email** (optional) - Email address for incident notifications
- **API key** - Your API key for AI analysis

**Example:**
```
Enter log directory or file path: /var/log/myapp
Alert email (optional): devops@company.com
API key: sk-ant-api03-...
✓ Configuration saved to ~/.observo/config.json
```

### Start Monitoring
```bash
# Start Observo daemon and dashboard
observo start
```

This will:
- Launch background daemon to monitor your logs
- Start Python processing service
- Start dashboard at http://localhost:6969
- Begin analyzing logs and detecting incidents

### View Status
```bash
# Check if Observo is running
observo status
```

**Output:**
```
Observo Status: Running
Uptime: 2h 15m
Logs processed: 45,230
Incidents detected: 3
Dashboard: http://localhost:6969
```

### Stop Monitoring
```bash
# Stop Observo daemon
observo stop
```

---

## Configuration

Observo stores configuration in `~/.observo/config.json`. You can update settings using the `observo config` command.

### Change Log Source

**Monitor a different directory:**
```bash
observo config --source local --path /var/log/myapp
```

**Monitor a single file:**
```bash
observo config --source local --path /var/log/myapp/app.log
```

### Update Alert Email
```bash
observo config --alert-email newemail@company.com
```

**Disable email alerts:**
```bash
observo config --alert-email ""
```

### Update API Key
```bash
observo config --api-key sk-ant-api03-new-key
```

### View Current Configuration
```bash
observo status
```

---

## Dashboard

Once Observo is running, access the dashboard at **http://localhost:6969**

### Dashboard Features

**System Status:**
- Daemon health (running/stopped)
- Python service status
- Database connection status
- Logs processed count
- Active incidents count

**Incidents View:**
- Table of all detected incidents
- Each incident shows:
  - **Timestamp** - When the issue was first detected
  - **Problem Summary** - AI-generated description of the issue
  - **Root Cause Analysis** - AI's explanation of why it happened
  - **Suggested Fixes** - Actionable steps to resolve the issue
  - **Sample Logs** - Representative logs from the problematic cluster
- Filter and sort incidents by time
- Expandable details for each incident

**Statistics:**
- Total logs processed
- Total incidents detected
- System uptime
- Processing metrics

---

## How Clustering Works

Observo uses advanced machine learning techniques to make sense of your logs:

### 1. **Template Extraction**
Converts variable log messages into reusable templates:
- `"User 12345 logged in from 192.168.1.1"` → `"User <ID> logged in from <IP>"`
- `"Order abc-123 processed in 450ms"` → `"Order <ID> processed in <TIME>"`

This groups all similar logs together regardless of specific values.

### 2. **Semantic Clustering**
Uses HDBSCAN algorithm with semantic embeddings to cluster similar templates:
- Groups logs by meaning, not just keywords
- Automatically determines optimal number of clusters
- No manual configuration needed

**Example clusters:**
```
Cluster 1: "User login successful" (Normal, 5,000 occurrences)
Cluster 2: "Database connection timeout" (Anomaly, 150 occurrences) ⚠️
Cluster 3: "API request completed" (Normal, 8,000 occurrences)
Cluster 4: "Payment processing failed" (Anomaly, 45 occurrences) ⚠️
```

### 3. **Anomaly Detection**
Classifies clusters as "good" (normal) or "bad" (problematic) using:
- **Keyword detection** - Presence of ERROR, FATAL, EXCEPTION, CRITICAL
- **Log level analysis** - High proportion of error-level logs

Only "bad" clusters trigger AI analysis, saving time and API costs.

---

## How AI Analysis Works

When Observo detects anomalous log clusters, it uses a multi-stage AI agent:

### LangGraph Workflow
```
1. Summarization
   ↓ (Takes cluster data)
   "Authentication service experiencing high failure rates"
   
2. Root Cause Analysis
   ↓ (Analyzes patterns)
   "Database connection pool exhausted - 150 timeout errors in 5 minutes"
   
3. Suggestion Generation
   ↓ (Proposes fixes)
   ["Scale auth service to 5 replicas",
    "Check database connection limits",
    "Review recent deployment for config changes"]
```

### AI Agent Features

- **Context-aware analysis** - Understands log patterns and relationships
- **Plain language output** - No technical jargon, clear explanations
- **Actionable suggestions** - Specific steps to resolve the issue
- **Confidence scoring** - Indicates how certain the AI is about its analysis

### Example AI Output

**Input:** 150 logs clustered as "Database connection timeout"

**AI Analysis:**
```
Summary:
The authentication service is experiencing a high rate of database 
connection timeouts, affecting user login attempts.

Root Cause:
Database connection pool appears exhausted based on timeout patterns. 
This coincides with a 3x traffic spike detected in the logs. Possible 
contributing factors:
- Insufficient connection pool size (currently 20 connections)
- Long-running queries holding connections
- Recent deployment may have introduced connection leak

Suggested Actions:
1. Immediate: Increase database connection pool from 20 to 50
2. Investigate: Review recent code changes for connection leaks
3. Monitor: Add connection pool metrics to observability dashboard
4. Scale: Consider adding database read replicas if reads are bottleneck

Confidence: 85%
```

---

## Example Workflow

### Real-World Scenario: Application Error Spike

**1. Your application encounters issues**
```
2026-02-01 10:30:15 ERROR [auth-service] Database connection timeout
2026-02-01 10:30:16 ERROR [auth-service] Failed to authenticate user
2026-02-01 10:30:17 ERROR [auth-service] Database connection timeout
... (150 similar errors in 5 minutes)
```

**2. Observo detects and clusters**
- File watcher picks up new log lines
- After 60 seconds, batch is sent for processing
- Clustering identifies "Database connection timeout" pattern
- Classified as "bad" cluster (ERROR keyword + high frequency)

**3. AI analyzes the incident**
- LangGraph agent receives cluster data
- Generates summary, root cause, and suggestions
- Stores incident in database

**4. You get notified**
- Email alert sent to your configured address
- Dashboard updates with new incident

**5. You view and act**
- Open dashboard at http://localhost:6969
- See incident with full AI analysis
- Follow suggested fixes:
  - Scale authentication service
  - Check database connection pool
  - Review recent deployments

**6. Problem resolved**
- Apply fixes based on AI suggestions
- Incident automatically logged with timestamp and details

**Total time from error to insight: ~2 minutes**

---

## Architecture
```
┌──────────────────────────┐
│    Observo CLI (Go)      │
│  Commands & Config Mgmt  │
└────────────┬─────────────┘
             │
┌────────────▼──────────────────────────────────┐
│         Observo Daemon (Go)                   │
│                                               │
│  ┌─────────────────────────────────────┐      │
│  │  File Watcher                       │      │
│  │  (Monitors local files/directories) │      │
│  └──────────────┬──────────────────────┘      │
│                 │                             │
│  ┌──────────────▼──────────────────────┐      │
│  │  60-Second Batch Buffer             │      │
│  └──────────────┬──────────────────────┘      │
│                 │                             │
│  ┌──────────────▼──────────────────────┐      │
│  │  Python Service Client              │──────┼──→ Python Processing
│  │  (HTTP calls to Python service)     │      │    Service (FastAPI)
│  └──────────────┬──────────────────────┘      │    • Preprocessing
│                 │                             │    • Clustering (HDBSCAN)
│  ┌──────────────▼──────────────────────┐      │    • Classification
│  │  Incident Storage                   │      │    • AI Agent (LangGraph)
│  │  (SQLite database)                  │      │
│  └──────────────┬──────────────────────┘      │
│                 │                             │
│  ┌──────────────▼──────────────────────┐      │
│  │  Email Alerts                       │      │
│  │  (SMTP sender)                      │      │
│  └─────────────────────────────────────┘      │
│                                               │
│  ┌─────────────────────────────────────┐      │
│  │  Dashboard API                      │      │
│  │  + React Frontend                   │      │
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

## File Locations

Observo stores all data in your home directory under `.observo/`:

- **Configuration:** `~/.observo/config.json`
- **Database:** `~/.observo/observo.db`
- **Daemon PID:** `~/.observo/daemon.pid`
- **Daemon logs:** `~/.observo/daemon.log`

---

## Troubleshooting

### Observo won't start

**Check if already running:**
```bash
observo status
```

**View daemon logs:**
```bash
tail -f ~/.observo/daemon.log
```

**Common issues:**
- Port 6969 already in use → Stop conflicting service or change port
- Python service not starting → Check Python dependencies installed
- Invalid configuration → Run `observo config` to verify settings

### No logs being processed

**Verify log path exists:**
```bash
ls -la /var/log/myapp
```

**Check file permissions:**
```bash
# Ensure Observo can read the log files
chmod 644 /var/log/myapp/*.log
```

**Check daemon logs for errors:**
```bash
grep ERROR ~/.observo/daemon.log
```

**Remember:** Logs are batched every 60 seconds, wait at least one minute after starting.

### AI analysis not working

**Common issues:**
- Invalid API key → Update with `observo config --api-key`
- Rate limit exceeded → Wait or upgrade API plan
- Network connectivity → Check firewall settings

### Email alerts not sending

**Verify email configured:**
```bash
observo status
# Check that alert email is set
```

**Test email connectivity:**
- Ensure ports 587 (TLS) or 465 (SSL) are not blocked
- For Gmail: Use [app-specific password](https://support.google.com/accounts/answer/185833)

**Check daemon logs:**
```bash
grep -i "email\|alert" ~/.observo/daemon.log
```

### Dashboard not loading

**Check if daemon is running:**
```bash
observo status
```

**Verify port 8080 is accessible:**
```bash
curl http://localhost:6969/api/health
```

**Check browser console for errors:**
- Open browser DevTools (F12)
- Look for network or JavaScript errors

---

## Performance (Suspected not Tested)

### Resource Usage

- **Go daemon:** ~50MB RAM
- **Python service:** ~200-500MB RAM (depends on model size)
- **SQLite database:** ~1MB per 1,000 incidents

### Throughput

- **Log processing:** ~10,000 logs/second on modern hardware
- **Batch interval:** 60 seconds (hardcoded)
- **Clustering time:** ~2-5 seconds per batch
- **AI analysis:** ~3-7 seconds per incident
- **Total latency:** ~70-75 seconds from log written to incident displayed

### Scalability

Current version is designed for single-machine deployments processing up to:
- **100,000 logs/minute**
- **~1,000 incidents/day**

For higher volumes, see Future Implementations section.

---

## Supported Log Formats

### Current Support

**Plain text logs:**
```
2026-02-01 10:30:15 ERROR [service] Database connection failed
2026-02-01 10:30:16 INFO [service] Retrying connection...
```

**JSON logs:**
```json
{"timestamp":"2026-02-01T10:30:15Z","level":"ERROR","service":"auth","message":"Database connection failed"}
```

### Format Detection

Observo automatically detects log format and extracts:
- Timestamp
- Log level (ERROR, WARN, INFO, DEBUG)
- Service/component name (if present)
- Message content

---

## Future Implementations

The following features were scoped out of v1.0 to deliver a focused MVP, but are planned for future releases:

### Phase 2: Advanced Log Sources
- **Cloud storage support**
  - AWS S3 bucket monitoring
  - Azure Blob Storage integration
  - Google Cloud Storage support
  - Automatic credential detection from cloud CLIs
- **Multiple simultaneous sources**
  - Monitor local files + S3 + Azure at the same time
  - Aggregate logs from different sources
- **Log aggregator integration**
  - Elasticsearch/OpenSearch
  - Grafana Loki
  - AWS CloudWatch Logs
  - Datadog, Splunk connectors

### Phase 3: Enhanced Analytics
- **Historical trend analysis**
  - Track cluster frequency changes over time
  - Detect gradual degradation patterns
  - Identify cyclical issues (e.g., "errors spike every Monday")
  - Time-series visualization of cluster evolution
- **Advanced anomaly detection**
  - Statistical baseline learning (Z-score, IQR methods)
  - Frequency spike detection beyond keyword matching
  - New cluster detection (previously unseen patterns)
  - Disappearing cluster alerts (normal patterns suddenly absent)
- **Predictive analytics**
  - Forecast potential issues before they occur
  - Capacity planning based on log patterns

### Phase 4: Incident Management
- **Resolution workflow**
  - Mark incidents as resolved with notes
  - Track resolution time (MTTR)
  - Link related incidents
  - Incident postmortem generation
- **Incident correlation**
  - Automatic linking of related incidents
  - Root cause propagation across services
  - Impact analysis (which services affected)

### Phase 5: Dashboard Enhancements
- **Real-time log streaming**
  - Live log feed in dashboard
  - Filter and search live logs
  - Tail specific services or log levels
- **Advanced visualization**
  - Interactive trend charts with drill-down
  - Cluster evolution heatmaps
  - Service dependency graphs
  - Custom dashboard layouts
- **Multi-user support**
  - User authentication and authorization
  - Role-based access control
  - Team collaboration features

### Phase 6: Configuration & Flexibility
- **YAML configuration files**
  - Full configuration via `observo.yaml`
  - Environment-specific configs (dev, staging, prod)
  - Configuration templates and presets
- **Tunable clustering parameters**
  - Adjust batch interval (currently hardcoded at 60s)
  - Configure HDBSCAN parameters (min_cluster_size, min_samples)
  - Choose clustering algorithm (HDBSCAN, DBSCAN, K-Means)
  - Embedding model selection
- **Custom classification rules**
  - User-defined "good" vs "bad" criteria
  - Regex-based pattern matching
  - Service-specific thresholds
  - Machine learning model training on labeled data

### Phase 7: Advanced Log Parsing
- **Multi-format support**
  - Apache/Nginx access logs
  - Syslog formats
  - Application-specific formats
  - Custom regex patterns
- **Structured log extraction**
  - Extract custom fields from logs
  - Parse stack traces
  - Extract metrics from logs

### Phase 8: Integrations
- **Alert channels**
  - Slack notifications
  - Microsoft Teams webhooks
  - PagerDuty integration
  - SMS alerts via Twilio
  - Custom webhook support
- **Ticketing systems**
  - Jira issue creation
  - ServiceNow incidents
  - GitHub Issues
- **Observability platforms**
  - Prometheus metrics export
  - OpenTelemetry integration
  - Grafana datasource plugin

### Phase 9: Enterprise Features
- **Distributed deployment**
  - Horizontal scaling for high log volumes
  - Load balancing across multiple instances
  - Centralized coordination
- **Advanced storage**
  - PostgreSQL support for better performance
  - Time-series databases (InfluxDB, TimescaleDB)
  - Object storage for long-term archival
- **High availability**
  - Failover and redundancy
  - Zero-downtime upgrades
  - Backup and disaster recovery

### Phase 10: Extensibility
- **Plugin system**
  - Custom log parsers
  - Custom classification algorithms
  - Custom AI analysis prompts
  - Third-party integrations
- **API for external tools**
  - REST API for programmatic access
  - Webhooks for event streaming
  - GraphQL endpoint
- **SDK for custom integrations**
  - Python SDK
  - Go SDK
  - JavaScript SDK

### Phase 11: AI Enhancements
- **Multi-model support**
  - GPT-4, Gemini, Llama integration
  - Model selection per incident type
  - Ensemble analysis (multiple models)
- **Learning from feedback**
  - User feedback on AI suggestions
  - Improve accuracy over time
  - Custom training on organization's incidents
- **Advanced AI features**
  - Code-level fix suggestions
  - Automatic runbook generation
  - Incident playbook recommendations

### Community & Open Source
- **Open source release**
  - MIT or Apache 2.0 license
  - Public GitHub repository
  - Community contributions welcome
- **Documentation**
  - API reference
  - Plugin development guide
  - Architecture deep-dive
  - Video tutorials
- **Community features**
  - Plugin marketplace
  - Shared classification rules
  - Pre-trained models for common frameworks

---

### How to Contribute
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request
5. Participate in code review

---

## License

[To be determined - planned: MIT or Apache 2.0]

## Project Background

### Academic Context
- **Project Type:** College Mini Project
- **Specialization:** Artificial Intelligence & Machine Learning
- **Focus Areas:** 
  - Log clustering using HDBSCAN and semantic embeddings
  - AI agent design with LangGraph for root cause analysis
  - Production-grade software engineering

### Team
- **Developers:** Pranav Jain & Madhav Garg

### Technical Highlights
- **Clustering Innovation:** Semantic understanding of logs using transformer embeddings
- **AI Agent Design:** Multi-stage LangGraph workflow for structured analysis
- **Production Ready:** Real-world applicable tool, not just academic exercise

---

## Acknowledgments

- **LogHub** - Public log dataset for testing and validation
- **Open Source Community** - Libraries and frameworks that made this possible

---

## Contact & Support

### During Development
- **Primary Contact:** [pranav.avlok@gmail.com]
- **Project Repository:** [https://github.com/PranavJa1n/Observo]

### After Open Source Release
- **GitHub Issues:** Bug reports and feature requests
- **Discussions:** Community forum for questions
- **Documentation:** Comprehensive wiki and guides

---

## Roadmap

- Open source release
- Community feedback integration
- Documentation improvements
- Cloud storage support (AWS S3, Azure, GCP)
- Trend analysis and visualization
- YAML configuration system
- Advanced anomaly detection
- Multi-user dashboard
- Incident management workflow
- Additional integrations (Slack, PagerDuty)
- Plugin system foundation
- Advanced AI capabilities
- Comprehensive plugin ecosystem

---

**Observo** - Turn log chaos into clarity with AI

*Built for the DevOps and SRE community*