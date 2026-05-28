import httpx
import asyncio
from typing import Optional
from models.schemas import Product
from utils.headers import get_headers

SHOPEE_SEARCH_URL = "https://shopee.vn/api/v4/search/search_items"
SHOPEE_ITEM_BASE = "https://shopee.vn/product/{shop_id}/{item_id}"
SHOPEE_IMAGE_BASE = "https://down-vn.img.susercontent.com/file/{image}"

async def fetch_top_products(
    keyword: str,
    limit: int = 10,
    sort_by: str = "relevancy"
) -> list[Product]:
    params = {
        "by": sort_by,
        "keyword": keyword,
        "limit": limit,
        "newest": 0,
        "order": "desc",
        "page_type": "search",
        "scenario": "PAGE_GLOBAL_SEARCH",
        "version": 2,
        "fe_categoryids": "",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(
                SHOPEE_SEARCH_URL,
                params=params,
                headers=get_headers()
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Shopee API error: {e}")

    items = data.get("items", []) or []
    products = []

    for raw in items[:limit]:
        item = raw.get("item_basic", {})
        price_raw = item.get("price", 0)
        price_max_raw = item.get("price_max", 0)
        original_raw = item.get("price_before_discount", 0)

        price = price_raw / 100000         # Shopee prices in units/100000
        original = original_raw / 100000 if original_raw else None
        discount = item.get("discount", None)
        if discount:
            try:
                discount = int(discount.replace("%", ""))
            except Exception:
                discount = None

        images = item.get("images", [])
        image_url = (
            f"{SHOPEE_IMAGE_BASE.format(image=images[0])}"
            if images else ""
        )

        products.append(Product(
            item_id=item.get("itemid", 0),
            shop_id=item.get("shopid", 0),
            name=item.get("name", ""),
            price=price,
            original_price=original,
            discount_percent=discount,
            rating=round(item.get("item_rating", {}).get("rating_star", 0), 1),
            sold=item.get("historical_sold", 0),
            stock=item.get("stock", 0),
            image_url=image_url,
            product_url=SHOPEE_ITEM_BASE.format(
                shop_id=item.get("shopid", 0),
                item_id=item.get("itemid", 0)
            ),
            shop_name=item.get("shop_name", ""),
            location=item.get("shop_location", ""),
            is_official_shop=bool(item.get("is_official_shop", False)),
            score=None
        ))

    return products