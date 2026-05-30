"""
backend/models/schemas.py  — V2 (Bug fixes)
=============================================
Bugs fixed:
  1. top_products → products  (was causing 422 ValidationError on EVERY request)
  2. keyword_enhanced: str → Optional[str]  (was crashing when AI returns None)
  3. Added missing search_time_ms field to SearchResponse
"""
from pydantic import BaseModel
from typing import List, Optional


class Product(BaseModel):
    item_id: int
    shop_id: int
    name: str
    price: float
    original_price: Optional[float] = None
    discount_percent: Optional[int] = None
    rating: float
    sold: int
    stock: int
    image_url: str
    product_url: str
    shop_name: str
    location: str
    is_official_shop: bool
    score: Optional[float] = None


class SearchRequest(BaseModel):
    keyword: str
    use_ai: Optional[bool] = True
    sort_by: Optional[str] = "relevancy"
    limit: Optional[int] = 10


class SearchResponse(BaseModel):
    keyword_original: str
    keyword_enhanced: Optional[str] = None  
    total_found: int
    products: List[Product]            
    search_time_ms: int          


class SuggestResponse(BaseModel):
    """Lightweight autocomplete response."""
    query: str
    suggestions: List[str]
