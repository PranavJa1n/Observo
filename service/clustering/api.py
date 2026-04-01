"""FastAPI service exposing clustering endpoints."""

from __future__ import annotations

from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .pipeline import LogClusteringPipeline
from .config import ClusteringConfig


class ClusterBatchRequest(BaseModel):
    logs: List[str] = Field(..., description="List of raw log lines")
    focus_areas: Optional[List[str]] = Field(default=None, description="Optional hints for reporting")


class ClusterBatchResponse(BaseModel):
    good_count: int
    bad_count: int
    outlier_count: int
    bad_logs: List[str]
    outlier_logs: List[str]


class TrainRequest(BaseModel):
    reload_artifacts: bool = False


class TrainResponse(BaseModel):
    stats: dict


config = ClusteringConfig()
pipeline = LogClusteringPipeline(config)

if pipeline.artifacts_exist():
    pipeline.load_artifacts()

app = FastAPI(title="Observo Clustering Service", version="1.0.0")


@app.get("/health")
def health() -> dict:
    return {"status": "healthy", "trained": pipeline.stats_dict().get("trained")}


@app.post("/train", response_model=TrainResponse)
def train(request: TrainRequest) -> TrainResponse:
    try:
        split = pipeline.train_from_dataset()
        pipeline.save_artifacts()
    except Exception as exc:  # noqa: BLE001 - we want to surface all failures to client
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    stats = pipeline.stats_dict()
    stats["last_train_summary"] = split.summary
    return TrainResponse(stats=stats)


@app.post("/cluster/batch", response_model=ClusterBatchResponse)
def cluster_batch(request: ClusterBatchRequest) -> ClusterBatchResponse:
    try:
        split = pipeline.cluster_batch(request.logs)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ClusterBatchResponse(
        good_count=len(split.good_logs),
        bad_count=len(split.bad_logs),
        outlier_count=len(split.outlier_logs),
        bad_logs=split.bad_logs,
        outlier_logs=split.outlier_logs,
    )


@app.get("/cluster/stats")
def cluster_stats() -> dict:
    return pipeline.stats_dict()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("service.clustering.api:app", host="0.0.0.0", port=5005, reload=False)
