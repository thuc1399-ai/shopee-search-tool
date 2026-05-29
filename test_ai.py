import json
from datasets import load_dataset

def simplify(item):
    return {
        "id": item.get("itemid") or item.get("id"),

        "name": item.get("name") 
                or item.get("title") 
                or "",

        "price": float(item.get("price") or 0),

        "rating": float(
            item.get("item_rating", {}).get("rating_star")
            or item.get("rating")
            or 0
        ),

        "sold": int(
            item.get("historical_sold")
            or item.get("sold")
            or 0
        ),

        "shop": (
            item.get("shop_name")
            or item.get("shop", {}).get("name")
            or ""
        ),

        "ctime": str(item.get("ctime") or ""),

        # text để search
        "text": " ".join(filter(None, [
            item.get("name"),
            item.get("title"),
            item.get("shop_name"),
            item.get("shop", {}).get("name")
        ]))
    }


def export_to_jsonl(output_path="shopee_clean.jsonl", limit=10000):
    print("Loading dataset...")

    ds = load_dataset("rebrowser/shopee-dataset", split="train")

    count = 0
    valid = 0

    with open(output_path, "w", encoding="utf-8") as f:
        for item in ds:
            data = simplify(item)

            # ❗ lọc dữ liệu rác
            if not data["name"]:
                continue

            f.write(json.dumps(data, ensure_ascii=False) + "\n")

            valid += 1
            count += 1

            if valid >= limit:
                break

    print(f"Done! Valid items: {valid}")


if __name__ == "__main__":
    export_to_jsonl(limit=10000)