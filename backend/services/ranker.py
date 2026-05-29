from backend.models.schemas import Product

def score_product(p: Product) -> float:
    """
    Tính điểm tổng hợp cho sản phẩm dựa trên:
    - Rating (40%)
    - Lượt bán (30%)
    - Discount (15%)
    - Official shop bonus (15%)
    """
    rating_score = (p.rating or 0) / 5.0 * 40

    # Normalize sold: cap at 10000
    sold_score = min(p.sold / 10000, 1.0) * 30

    discount_score = min((p.discount_percent or 0) / 100, 1.0) * 15

    official_score = 15.0 if p.is_official_shop else 0.0

    return round(rating_score + sold_score + discount_score + official_score, 2)

def rank_products(products: list[Product]) -> list[Product]:
    for p in products:
        p.score = score_product(p)
    return sorted(products, key=lambda x: x.score, reverse=True)