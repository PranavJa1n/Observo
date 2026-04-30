"""
Observo Python Service — FastAPI entrypoint.

Started automatically by the Go CLI via:
    python service/main.py

Runs on port 5000 (hardcoded in internal/python_client/python_client.go).

Endpoints consumed by the Go CLI:
  POST /process  — receives a batch of raw log lines, classifies them,
                   and calls the agentic AI on the bad logs.
  GET  /health   — liveness probe used by WaitForPython().

Additional utility endpoints:
  GET  /status   — current pipeline stats (good/bad counts, model info).
  POST /analyze  — direct AI analysis without clustering (for testing).
"""

from __future__ import annotations

import importlib
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import dotenv
dotenv.load_dotenv()

# Ensure the project root (d:\Observo) is on sys.path so that
# `from service.clustering...` and `from service.agentic...` resolve
# correctly regardless of how this file is invoked.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("observo.service")

# ---------------------------------------------------------------------------
# Clustering pipeline — loaded once at startup
# ---------------------------------------------------------------------------
_pipeline = None

def _load_pipeline():
    """Load or train the clustering pipeline at startup."""
    global _pipeline
    try:
        from service.clustering.pipeline import LogClusteringPipeline
        _pipeline = LogClusteringPipeline()
        if _pipeline.artifacts_exist():
            logger.info("Loading existing clustering artifacts...")
            _pipeline.load_artifacts()
            logger.info("Clustering pipeline loaded successfully.")
        else:
            logger.warning(
                "No trained model found. Run train_pipeline first: "
                "python -m service.clustering.train_pipeline"
            )
            _pipeline = None
    except Exception as exc:
        logger.error("Failed to load clustering pipeline: %s", exc)
        _pipeline = None

# ---------------------------------------------------------------------------
# Agentic AI — selected by AI_PROVIDER env var (default: claude)
# ---------------------------------------------------------------------------
_agent = None

def _get_agent(model_name: str = "gemini"):
    """Lazily load the AI agent based on the requested model name."""
    model_name = model_name.lower()
    
    # Map user input to provider and class
    if model_name in ["sonnet", "claude"]:
        provider = "claude"
    elif model_name in ["chatgpt", "openai", "gpt-4"]:
        provider = "openai"
    elif model_name in ["perplexity"]:
        provider = "perplexity"
    else:
        provider = "gemini"
        
    provider_map = {
        "claude":    ("service.agentic.claude_agentic",    "LogAnalysisAgent", "CLAUDE_API_KEY"),
        "gemini":    ("service.agentic.gemini_agentic",    "LogAnalysisAgent", "GEMINI_API_KEY"),
        "openai":    ("service.agentic.openai_agentic",    "LogAnalysisAgent", "OPENAI_API_KEY"),
        "perplexity":("service.agentic.perplexity_agentic","LogAnalysisAgent", "PERPLEXITY_API_KEY"),
    }
    
    if provider not in provider_map:
        return None

    module_path, class_name, env_key = provider_map[provider]
    api_key = os.getenv(env_key)
    if not api_key:
        logger.warning("No %s found. Agent disabled.", env_key)
        return None

    try:
        module = importlib.import_module(module_path)
        agent_cls = getattr(module, class_name)
        return agent_cls(api_key=api_key)
    except Exception as exc:
        logger.error("Failed to load agent for %s: %s", provider, exc)
        return None

# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Observo Python Service starting on port 5000...")
    _load_pipeline()
    logger.info("Service ready.")
    yield
    logger.info("Observo Python Service shutting down.")

app = FastAPI(
    title="Observo Python Service",
    description="Log clustering + AI analysis backend for the Observo CLI.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class BatchRequest(BaseModel):
    """Payload sent by the Go CLI's SendBatch()."""
    logs: List[str]
    model: Optional[str] = "gemini"

class AnalysisResult(BaseModel):
    root_cause: str
    severity: str
    recommendations: List[str]
    affected_components: List[str]
    timestamp: str
    summary: str

class ProcessResponse(BaseModel):
    status: str
    total: int
    good_count: int
    bad_count: int
    analysis: Optional[AnalysisResult] = None
    message: str = ""

class StatusResponse(BaseModel):
    running: bool
    pipeline_loaded: bool
    agent_loaded: bool
    pipeline_stats: Optional[Dict[str, Any]] = None

class DirectAnalyzeRequest(BaseModel):
    logs: List[str]
    context: Optional[str] = None
    diagnostics: Optional[List[str]] = None
    model: Optional[str] = "gemini"

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    """
    Liveness probe polled by Go's WaitForPython().
    Must return HTTP 200 for the CLI to proceed.
    """
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/process", response_model=ProcessResponse)
def process(request: BatchRequest):
    """
    Main endpoint called by the Go CLI every 60 seconds.

    Go sends a batch of raw log lines. This endpoint:
    1. Runs the clustering pipeline to split logs into good / bad.
    2. If bad logs exist, calls the AI agent to analyse them.
    3. Returns the counts + AI analysis to Go so it can store the incident.
    """
    logs = [log.strip() for log in request.logs if log.strip()]
    if not logs:
        return ProcessResponse(
            status="ok",
            total=0,
            good_count=0,
            bad_count=0,
            message="No logs in batch.",
        )

    # --- 1. Clustering ---
    good_logs: List[str] = []
    bad_logs: List[str] = []

    if _pipeline is not None:
        try:
            split = _pipeline.cluster_batch(logs)
            good_logs = split.good_logs
            bad_logs = split.bad_logs
            logger.info(
                "Batch processed: total=%d good=%d bad=%d",
                len(logs), len(good_logs), len(bad_logs),
            )
        except Exception as exc:
            logger.error("Clustering failed: %s — falling back to keyword-only mode.", exc)
            # Graceful fallback: use keyword classifier directly
            from service.clustering.cluster_classifier import _is_bad_log
            for log in logs:
                (bad_logs if _is_bad_log(log) else good_logs).append(log)
    else:
        # No model loaded — use keyword classifier directly
        try:
            from service.clustering.cluster_classifier import _is_bad_log
            for log in logs:
                (bad_logs if _is_bad_log(log) else good_logs).append(log)
        except Exception:
            good_logs = logs  # absolute fallback

    # --- 2. AI analysis on bad logs ---
    ai_result: Optional[AnalysisResult] = None

    if bad_logs:
        agent = _get_agent(request.model)
        if agent is not None:
            try:
                bad_text = "\n".join(bad_logs[-200:])  # cap at 200 lines to stay within token limits
                result = agent.analyze_logs(logs=bad_text)
                ai_result = AnalysisResult(
                    root_cause=result.root_cause,
                    severity=result.severity,
                    recommendations=result.recommendations,
                    affected_components=result.affected_components,
                    timestamp=result.timestamp,
                    summary=result.raw_analysis,
                )
                logger.info("AI analysis complete: severity=%s", result.severity)
                try:
                    with open("ai_results.json", "a") as f:
                        f.write(ai_result.model_dump_json() + "\n")
                except Exception as e:
                    logger.error("Failed to write to ai_results.json: %s", e)
            except Exception as exc:
                logger.error("AI agent failed: %s", exc)

    return ProcessResponse(
        status="ok",
        total=len(logs),
        good_count=len(good_logs),
        bad_count=len(bad_logs),
        analysis=ai_result,
        message="Analysis complete." if ai_result else (
            "Bad logs found but no AI agent loaded." if bad_logs else "All logs normal."
        ),
    )


@app.get("/status", response_model=StatusResponse)
def status():
    """Returns the current state of the pipeline and agent for debugging."""
    stats = None
    if _pipeline is not None:
        try:
            stats = _pipeline.stats_dict()
        except Exception:
            pass

    return StatusResponse(
        running=True,
        pipeline_loaded=_pipeline is not None,
        agent_loaded=True, # Agent is loaded lazily per request
        pipeline_stats=stats,
    )


@app.post("/analyze", response_model=AnalysisResult)
def analyze(request: DirectAnalyzeRequest):
    """
    Direct AI analysis endpoint — bypasses clustering.
    Useful for testing the AI agent independently.
    """
    agent = _get_agent(request.model)
    if agent is None:
        raise HTTPException(
            status_code=503,
            detail=f"AI agent not loaded. Check the API key env var for the {request.model} model.",
        )
    try:
        result = agent.analyze_logs(
            logs="\n".join(request.logs),
            context=request.context,
            diagnostics=request.diagnostics,
        )
        return AnalysisResult(
            root_cause=result.root_cause,
            severity=result.severity,
            recommendations=result.recommendations,
            affected_components=result.affected_components,
            timestamp=result.timestamp,
            summary=result.raw_analysis,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Pass the app object directly (not a string) so uvicorn doesn't need to
    # re-import 'service.main' — this makes `python service/main.py` work
    # from the project root without needing PYTHONPATH to be set.
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info",
    )
