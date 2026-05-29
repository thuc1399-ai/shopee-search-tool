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
    keyword_enhanced: str
    total_found: int
    top_products: List[Product]
