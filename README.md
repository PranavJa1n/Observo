# Observo - Intelligent Log Clustering & Causal Root Cause Analysis

[![GitHub stars](https://img.shields.io/github/stars/PranavJa1n/observo?style=social)](https://github.com/PranavJa1n/observo)
[![License](https://img.shields.io/github/license/PranavJa1n/observo)](https://github.com/PranavJa1n/observo/blob/main/LICENSE)

**Observo** is a next-generation observability platform that transforms raw application logs into **actionable intelligence** through intelligent clustering, causal inference, and agentic AI analysis.

## 🎯 The Problem

**Logs are the most expensive and hardest observability signal to manage at scale:**

```
❌ 10TB+/day log volume → $50K+/month storage & indexing costs
❌ 99% noise → SREs miss real incidents in log floods  
❌ Manual triage → hours debugging simple configuration issues
❌ Correlation ≠ causation → wrong root cause fixes waste engineering time
❌ Noisy alerts → alert fatigue kills operational effectiveness
```

## 🚀 What Observo Solves

**Observo converts log noise into causal clarity:**

```
Raw Logs → Intelligent Clusters → Causal Root Causes → Actionable Fixes
    ↓              ↓                 ↓                 ↓
"ERROR: DB conn" → "DB Exhaustion" → "Pool=20→50" → "kubectl apply"
```

## 🎯 Core Capabilities

1. **Intelligent Log Clustering**
   - Groups semantically similar log patterns into stable, interpretable clusters
   - Learns "good" vs "bad" patterns from public datasets (OpenLog) + your logs
   - Density-based clustering (HDBSCAN) preserves rare anomalies

2. **Anomaly Detection**
   - Identifies "bad" clusters that deviate from normal system behavior
   - Temporal-aware detection captures sequence patterns over time
   - Adaptive thresholds adjust for time-of-day and system load patterns

3. **Causal Inference Engine**
   - Ranks root causes by **actual treatment effect**, not correlation
   - Computes: "Fixing X reduces errors by 73%" (not just "X correlates with errors")
   - Builds causal graphs from log patterns + system topology

4. **Agentic AI Analysis**
   - LangGraph-powered agent generates human-readable explanations
   - Outputs concrete remediation steps (kubectl patches, config changes, rollbacks)
   - Integrates SRE domain knowledge through feedback loops

5. **Explainable Intelligence**
   - SHAP values explain which log patterns drove each diagnosis
   - Confidence intervals for every root cause recommendation
   - Counterfactual analysis: "If log X were absent, anomaly probability drops 40%"

## 🏗️ How Observo Works

```
                    +-------------------+
Raw Logs ──────────▶│ 1. Log Parsing    │
                    │ (Drain3 + BERT)   │
                    +-------------------+
                           ↓
                    +-------------------+
                    │ 2. Vectorization  │  
                    │ (Sentence-BERT +  │
                    │  GNN Embeddings)  │
                    +-------------------+
                           ↓
                    +-------------------+
    Feedback ──────▶│ 3. Clustering     │
    Loop            │ (HDBSCAN + GNN)  │
                    +-------------------+
                           ↓
                    +-------------------+
                    │ 4. Anomaly Score  │
                    │ (Temporal LSTM +  │
                    │  Causal Discovery)│
                    +-------------------+
                           ↓ (Bad Clusters)
                    +-------------------+
                    │ 5. Causal Agent   │
                    │ (LangGraph +      │
                    │  DoWhy Inference) │
                    +-------------------+
                           ↓
"Root cause: DB pool exhaustion (73% causal impact)
 Fix: Increase pool from 20→50. Confidence: 87%"
```

## 🎯 Key Differentiators

| Capability | Observo | Traditional Log Tools |
|------------|---------|---------------------|
| **Root Cause** | Causal treatment effect ranking | Correlation alerts |
| **Intelligence** | GNN clustering + agentic AI | Simple pattern matching |
| **Explainability** | SHAP + confidence intervals | Black box decisions |
| **Training Data** | OpenLog public dataset | Cold start on your logs |
| **Human Loop** | Causal graph refinement UI | Static rules |
| **Actionability** | Concrete kubectl/config fixes | "Investigate manually" |

## 🎓 Data Foundation

**Pre-trained on OpenLog dataset:**
- **10M+ log lines** from production systems (web servers, databases, containers)
- Covers **Hadoop, Spark, Zookeeper, OpenStack** and more
- Labeled normal vs anomalous patterns for supervised fine-tuning
- Community-driven dataset updates

## 🔮 Technical Roadmap

```
Phase 1: Core Pipeline (Clustering + Causal Agent)
  ↓
Phase 2: Temporal Modeling + Explainability  
  ↓
Phase 3: User-in-Loop Causal Refinement
  ↓
Phase 4: Federated Learning (Privacy-preserving)
  ↓
Phase 5: Multi-modal Fusion (Logs + Metrics + Traces)
  ↓
Phase 6: Kubernetes Operator (Production deployment)
```

## 🎯 Expected Impact

```
Before Observo:                    After Observo:
├── 10TB logs → $50K/month         ├── 90% log noise reduction
├── 2hr MTTR → manual hunting      ├── 2hr → 15min MTTR
├── 30% wrong fixes                ├── 73% causal accuracy
└── Alert fatigue                  └── Actionable recommendations
```

## 🚀 Get Involved

1. **⭐ Star the repo** to track development
2. **🐛 Open issues** with your use cases
3. **🤝 Join discussions** on causal log analysis
4. **📬 Watch for v0.1.0 release**

## 📄 License

[Apache 2.0](LICENSE) © 2026 Observo Authors

---

**Observo: From log chaos to causal clarity. Engineering intelligence for SREs.**