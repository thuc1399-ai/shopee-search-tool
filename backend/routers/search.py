import time
from fastapi import APIRouter, HTTPException
from backend.models.schemas import SearchRequest, SearchResponse
from backend.services.shopee import fetch_top_products
from backend.services.ai_enhancer import enhance_keyword
from backend.services.ranker import rank_products

router = APIRouter()

@router.post("/search", response_model=SearchResponse)
async def search_products(req: SearchRequest):
    if not req.keyword.strip():
        raise HTTPException(status_code=400, detail="Keyword không được để trống")

    start = time.time()

    # Step 1: AI enhance keyword (optional)
    enhanced = None
    search_kw = req.keyword
    if req.use_ai:
        enhanced = await enhance_keyword(req.keyword)
        if enhanced != req.keyword:
            search_kw = enhanced

    # Step 2: Fetch from Shopee
    try:
        products = await fetch_top_products(
            keyword=search_kw,
            limit=req.limit,
            sort_by=req.sort_by
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Step 3: AI-powered re-ranking (only for relevancy)
    if req.sort_by == "relevancy":
        products = rank_products(products)

    elapsed_ms = int((time.time() - start) * 1000)

    return SearchResponse(
        keyword_original=req.keyword,
        keyword_enhanced=enhanced if enhanced != req.keyword else None,
        total_found=len(products),
        products=products,
        search_time_ms=elapsed_ms
    )