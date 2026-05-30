"""
backend/routers/search.py — V3
================================
New additions:
  1. GET /suggest?q=... — fast autocomplete (< 5ms, no AI)
  2. GET /cache/clear   — admin endpoint to flush search cache
"""

import time
from fastapi import APIRouter, HTTPException, Query

from backend.models.schemas import SearchRequest, SearchResponse, SuggestResponse
from backend.services.shopee import fetch_top_products, suggest_products, _cache
from backend.services.ai_enhancer import enhance_keyword

router = APIRouter()


def _extract_display(enhanced: str, original: str) -> str | None:
    """Extract human-readable AI expansion from 'keyword|en_payload' string."""
    if "|" not in enhanced:
        return None
    ai_part = enhanced.split("|", 1)[1].strip()
    if not ai_part or ai_part.lower() == original.lower():
        return None
    return ai_part


# ── POST /search ───────────────────────────────────────────────────────────

@router.post("/search", response_model=SearchResponse)
async def search_products(req: SearchRequest):
    """
    Main search endpoint.
    - Optionally enhances the keyword with flan-t5 (AI expand → brands, synonyms)
    - Runs BM25 search on the pre-built index
    - Returns top-N products ranked by relevance + quality
    """
    if not req.keyword.strip():
        raise HTTPException(status_code=400, detail="Keyword không được để trống")

    start = time.time()

    # ── Step 1: AI Keyword Enhancement ────────────────────────────────
    search_kw      = req.keyword
    display_enhanced: str | None = None

    if req.use_ai:
        try:
            enhanced_raw = await enhance_keyword(req.keyword)
            if enhanced_raw and enhanced_raw != f"{req.keyword}|":
                search_kw        = enhanced_raw
                display_enhanced = _extract_display(enhanced_raw, req.keyword)
        except Exception as e:
            print(f"[WARN] AI enhancer failed, using original. Error: {e}")

    # ── Step 2: BM25 Search (uses pre-built index + cache) ────────────
    try:
        products = await fetch_top_products(
            keyword=search_kw,
            limit=req.limit,
            sort_by=req.sort_by,
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Dữ liệu chưa sẵn sàng: {e}",
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    elapsed_ms = int((time.time() - start) * 1000)

    return SearchResponse(
        keyword_original  = req.keyword,
        keyword_enhanced  = display_enhanced,
        total_found       = len(products),
        products          = products,
        search_time_ms    = elapsed_ms,
    )


# ── GET /suggest ───────────────────────────────────────────────────────────

@router.get("/suggest", response_model=SuggestResponse)
async def suggest(
    q: str = Query(..., min_length=1, max_length=100, description="Partial search query"),
    limit: int = Query(6, ge=1, le=10),
):
    """
    Lightweight autocomplete endpoint.
    Returns up to `limit` product name suggestions for the given partial query.
    No AI enhancement — pure BM25 for < 5ms response time.

    Example: GET /api/v1/suggest?q=tai+nghe&limit=5
    """
    suggestions = suggest_products(query=q, limit=limit)
    return SuggestResponse(query=q, suggestions=suggestions)


# ── DELETE /cache ──────────────────────────────────────────────────────────

@router.delete("/cache", tags=["admin"])
async def clear_cache():
    """Flush the in-memory search cache. Useful after re-importing product data."""
    size = len(_cache)
    _cache.clear()
    return {"cleared": size, "message": f"Đã xóa {size} cache entries"}