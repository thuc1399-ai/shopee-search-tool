import time
from fastapi import APIRouter, HTTPException, Query
from backend.models.schemas import SearchRequest, SearchResponse, SuggestResponse
from backend.services.shopee import fetch_top_products, suggest_products, clear_cache
from backend.services.ai_enhancer import enhance_keyword

router = APIRouter()
@router.post("/search", response_model=SearchResponse)
async def search_products(req: SearchRequest):
    if not req.keyword.strip():
        raise HTTPException(status_code=400, detail="Keyword không được để trống")

    start = time.time()
    search_kw = req.keyword  # MẶC ĐỊNH LUÔN GIỮ TỪ KHÓA GỐC (Tiếng Việt)
    ai_terms = ""
    display_enhanced = None

    if req.use_ai:
        try:
            ai_result = await enhance_keyword(req.keyword)
            
            # Chỉ lấy kết quả AI đưa vào ai_terms, TUYỆT ĐỐI KHÔNG ghi đè search_kw
            translated = ai_result.get("translated", "")
            enhanced = ai_result.get("enhanced", "")
            
            ai_terms = f"{translated} {enhanced}".strip()
            
            if enhanced:
                display_enhanced = enhanced
        except Exception:
            pass

    try:
        products = await fetch_top_products(
            keyword=search_kw,
            ai_terms=ai_terms,
            limit=req.limit,
            sort_by=req.sort_by,
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
        search_time_ms=elapsed_ms,
    )
    
    
@router.get("/suggest", response_model=SuggestResponse)
async def suggest(
    q: str = Query(..., min_length=1, max_length=255), # Nâng từ 100 lên 255
    limit: int = Query(6, ge=1, le=10),
):
    suggestions = suggest_products(query=q, limit=limit)
    return SuggestResponse(query=q, suggestions=suggestions)


@router.delete("/cache", tags=["admin"])
async def flush_cache():
    cleared = clear_cache()
    return {"cleared": cleared, "message": f"Đã xóa {cleared} cache entries"}