import json
import os
from pathlib import Path

from dotenv import load_dotenv

from backend.models.schemas import Product

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_JSONL_PATH = Path(
    os.getenv("DATA_JSONL_PATH", str(REPO_ROOT / "data" / "shopee_sample.jsonl"))
)
USD_TO_VND_RATE = float(os.getenv("USD_TO_VND_RATE", "25000"))


def _to_vnd(value: float) -> float:
    return round(value * USD_TO_VND_RATE, 0)


def _sort_products(products: list[Product], sort_by: str) -> list[Product]:
    if sort_by == "price":
        return sorted(
            products,
            key=lambda p: p.price if p.price and p.price > 0 else float("inf")
        )
    if sort_by in {"sold", "sales"}:
        return sorted(products, key=lambda p: p.sold, reverse=True)
    return products

async def fetch_top_products(
    keyword: str,
    limit: int = 10,
    sort_by: str = "relevancy"
) -> list[Product]:
    
    products: list[Product] = []

    if not DATA_JSONL_PATH.exists():
        raise FileNotFoundError(
            "Không tìm thấy file dữ liệu. Hãy set DATA_JSONL_PATH hoặc kiểm tra file mẫu."
        )

    with open(DATA_JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
                
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue

            title = item.get("title", "") or item.get("name", "")
            
            if keyword and keyword.lower() not in title.lower():
                continue

            try:
                price = float(item.get("price_actual") or item.get("price") or 0)
            except ValueError:
                price = 0.0

            try:
                original_price = float(item.get("price_ori") or item.get("original_price") or 0)
                original_price = original_price if original_price > 0 else None
            except ValueError:
                original_price = None

            # Source data is USD, convert to VND for output
            if price > 0:
                price = _to_vnd(price)
            if original_price:
                original_price = _to_vnd(original_price)

            try:
                rating = float(item.get("item_rating") or item.get("rating") or 0)
            except ValueError:
                rating = 0.0

            try:
                sold = int(item.get("total_sold") or item.get("sold") or 0)
            except ValueError:
                sold = 0
                
            try:
                item_id = int(item.get("id", 0))
            except ValueError:
                item_id = 0

            discount_percent = None
            if original_price and price < original_price:
                discount_percent = int(round((1 - price / original_price) * 100))

            product = Product(
                item_id=item_id,
                shop_id=0, 
                name=title,
                price=price,
                original_price=original_price,
                discount_percent=discount_percent,
                rating=round(rating, 1),
                sold=sold,
                stock=999,
                image_url=item.get("pict_link") or item.get("image_url", ""),
                product_url=item.get("link_ori") or item.get("product_url", ""),
                shop_name=item.get("seller_name") or item.get("shop_name", "Unknown Shop"),
                location=item.get("location", "Vietnam"),
                is_official_shop=False,
                score=None
            )
            
            products.append(product)

            if sort_by == "relevancy" and len(products) >= limit:
                break
    products = _sort_products(products, sort_by)
    return products[:limit]