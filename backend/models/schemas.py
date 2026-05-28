from pydantic import BaseModel
from typing import Optional

class SearchRequest(BaseModel):
    keyword: str
    limit: int = 10
    use_ai: bool = True          # AI keyword enhancement toggle
    sort_by: str = "relevancy"   # relevancy | price | sold

class Product(BaseModel):
    item_id: int
    shop_id: int
    name: str
    price: float                 # VND
    original_price: Optional[float]
    discount_percent: Optional[int]
    rating: Optional[float]
    sold: int
    stock: int
    image_url: str
    product_url: str
    shop_name: str
    location: str
    is_official_shop: bool
    score: Optional[float]       # AI ranking score

class SearchResponse(BaseModel):
    keyword_original: str
    keyword_enhanced: Optional[str]
    total_found: int
    products: list[Product]
    search_time_ms: int