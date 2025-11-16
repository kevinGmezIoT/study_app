# metrics.py
import time
from contextlib import contextmanager
from fastapi import APIRouter, Request, Response
from prometheus_client import (
    Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
)

router = APIRouter()

# ---- App-wide HTTP metrics ----
HTTP_REQUESTS = Counter(
    "http_requests_total", "HTTP requests", ["method", "path", "status"]
)
HTTP_LATENCY = Histogram(
    "http_request_latency_seconds", "Request latency (seconds)", ["path"]
)

# ---- Domain metrics (optional, for your class demo) ----
ATTEMPTS_TOTAL = Counter(
    "attempts_total", "Grading attempts by topic/model/outcome",
    ["topic", "model", "outcome"]  # outcome: correct|incorrect
)
LLM_LATENCY = Histogram("llm_latency_seconds", "LLM grading latency (seconds)")
BASELINE_LATENCY = Histogram("baseline_latency_seconds", "Baseline grading latency (seconds)")

@router.get("/metrics")
def metrics_endpoint():
    # Exposes all metrics in Prometheus text format
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

def instrument_app(app):
    """Attach middleware and /metrics endpoint to the app."""
    @app.middleware("http")
    async def _metrics_middleware(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start

        # Keep label cardinality low: use raw path only (no IDs in path)
        path = request.url.path
        HTTP_LATENCY.labels(path=path).observe(elapsed)
        HTTP_REQUESTS.labels(
            method=request.method,
            path=path,
            status=str(response.status_code),
        ).inc()
        return response

    app.include_router(router)

def record_attempt(topic: str | None, model: str, correct: bool):
    ATTEMPTS_TOTAL.labels(
        topic=(topic or "unknown"),
        model=model,
        outcome=("correct" if correct else "incorrect"),
    ).inc()

@contextmanager
def track_llm_latency():
    t = time.perf_counter()
    try:
        yield
    finally:
        LLM_LATENCY.observe(time.perf_counter() - t)

@contextmanager
def track_baseline_latency():
    t = time.perf_counter()
    try:
        yield
    finally:
        BASELINE_LATENCY.observe(time.perf_counter() - t)