def simplify(item):
    return {
        "id":    item.get("itemid") or item.get("id"),
        "name":  item.get("name") or item.get("title") or "",

        # shopee.py dùng "price_actual" trước, nên đặt tên đúng
        # để tránh bị nhân đôi với USD_TO_VND_RATE
        "price_actual": float(item.get("price") or 0),

        "rating": float(
            (item.get("item_rating") or {}).get("rating_star")
            or item.get("rating") or 0
        ),
        "total_sold": int(
            item.get("historical_sold") or item.get("sold") or 0
        ),

        # Map "shop" → "shop_name" để shopee.py đọc đúng
        "shop_name": (
            item.get("shop_name") or
            item.get("shop", {}).get("name") or ""
        ),

        "image_url":   item.get("image") or item.get("image_url") or "",
        "product_url": item.get("item_url") or "",
        "location":    item.get("shop_location") or "Vietnam",
    }