import time
from fastapi import APIRouter, HTTPException
from backend.models.schemas import SearchRequest, SearchResponse
from backend.services.shopee import fetch_top_products
from backend.services.ai_enhancer import enhance_keyword


router = APIRouter()

@router.post("/search", response_model=SearchResponse)
async def search_products(req: SearchRequest):
    if not req.keyword.strip():
        raise HTTPException(status_code=400, detail="Keyword không được để trống")

    start = time.time()

    search_kw = req.keyword
    display_enhanced: str | None = None  # Chỉ dùng để hiển thị lên UI

    # ── Step 1: AI Enhance ──────────────────────────────────────────────
    if req.use_ai:
        raw_payload = await enhance_keyword(req.keyword)
        # raw_payload dạng: "tai nghe chong on|noise cancelling headphones Sony Bose"
        if "|" in raw_payload:
            original_part, ai_part = raw_payload.split("|", 1)
            ai_part = ai_part.strip()
            if ai_part and ai_part.lower() != req.keyword.lower():
                # Hiển thị phần AI thêm vào cho người dùng thấy
                display_enhanced = ai_part
                # Truyền full payload cho search engine
                search_kw = raw_payload
        else:
            search_kw = raw_payload

    # ── Step 2: Search ─────────────────────────────────────────────────
    try:
        products = await fetch_top_products(
            keyword=search_kw,
            limit=req.limit,
            sort_by=req.sort_by
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


    elapsed_ms = int((time.time() - start) * 1000)

    return SearchResponse(
        keyword_original=req.keyword,
        keyword_enhanced=display_enhanced,
        total_found=len(products),
        products=products,
        search_time_ms=elapsed_ms
    )