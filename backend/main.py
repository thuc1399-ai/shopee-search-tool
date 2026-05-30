"""
backend/main.py — V2 (Lifespan + Health)
==========================================
Changes:
  1. Added lifespan context manager:
     - Builds BM25 index at startup (not per-request)
     - Warms up the flan-t5 model in a thread (cold start happens at boot,
       not on the first user request)
  2. Enhanced /health endpoint with index status and uptime
"""

import time
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.search import router
from backend.services.shopee import build_index, index_status
from backend.services.ai_enhancer import _get_pipeline

_APP_START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: build search index + warm AI model.
    All heavy work runs in a thread pool so the event loop stays responsive.
    """
    loop = asyncio.get_event_loop()

    # 1. Build BM25 index (sync, blocking — run in thread)
    print("[STARTUP] Building search index...")
    await loop.run_in_executor(None, build_index)

    # 2. Warm up flan-t5 model (downloads weights on first run ~3GB)
    #    Runs in background so server comes up immediately.
    async def _warm_model():
        print("[STARTUP] Warming AI model (background)...")
        await loop.run_in_executor(None, _get_pipeline)
        print("[STARTUP] AI model ready.")

    asyncio.create_task(_warm_model())

    yield   # ← application runs here

    # Shutdown (nothing to clean up for now)
    print("[SHUTDOWN] Bye.")


app = FastAPI(
    title="Shopee Search Tool",
    description="Top 10 sản phẩm nổi bật với AI-powered BM25 ranking",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["search"])


@app.get("/health", tags=["system"])
def health():
    """
    Enhanced health check — shows index status and uptime.
    Useful for Docker healthcheck and monitoring dashboards.
    """
    idx = index_status()
    uptime_s = int(time.time() - _APP_START_TIME)
    return {
        "status":  "ok" if idx["ready"] else "degraded",
        "service": "shopee-search-tool",
        "version": "2.0.0",
        "uptime_seconds": uptime_s,
        "index": idx,
    }