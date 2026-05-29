"""
Shopee JSONL Search Engine — V2.1
===================================
"""

import json
import math
import os
import re
import unicodedata
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from backend.models.schemas import Product

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_JSONL_PATH = Path(
    os.getenv("DATA_JSONL_PATH", str(REPO_ROOT / "data" / "shopee_sample.jsonl"))
)
USD_TO_VND_RATE = float(os.getenv("USD_TO_VND_RATE", "25000"))

# ── Score weights ──────────────────────────────────────────────────────
W_BM25     = 0.60
W_AI_BOOST = 0.20
W_QUALITY  = 0.20

# ── BM25 params ───────────────────────────────────────────────────────
BM25_K1 = 1.5
BM25_B  = 0.75


# ══════════════════════════════════════════════════════════════════════
# UTILS
# ══════════════════════════════════════════════════════════════════════

def _normalize(text: str) -> str:
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    no_accent = "".join(c for c in nfkd if not unicodedata.combining(c))
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", no_accent.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def _tokenize(text: str) -> list[str]:
    return [t for t in _normalize(text).split() if t]


def _to_vnd(value: float) -> float:
    return round(value * USD_TO_VND_RATE, 0)


# BM25 ENGINE

class BM25:
    def __init__(self, corpus_tokens: list[list[str]]):
        self.corpus_size = len(corpus_tokens)
        self.avgdl = (
            sum(len(d) for d in corpus_tokens) / self.corpus_size
            if self.corpus_size > 0 else 1.0
        )
        self.df: dict[str, int] = {}
        self.tf_per_doc: list[dict[str, int]] = []

        for doc in corpus_tokens:
            tf: dict[str, int] = {}
            for token in doc:
                tf[token] = tf.get(token, 0) + 1
            self.tf_per_doc.append(tf)
            for term in set(doc):
                self.df[term] = self.df.get(term, 0) + 1

    def idf(self, term: str) -> float:
        n = self.df.get(term, 0)
        if n == 0:
            return 0.0
        return math.log((self.corpus_size - n + 0.5) / (n + 0.5) + 1)

    def score(self, doc_idx: int, query_tokens: list[str]) -> float:
        if not query_tokens:
            return 0.0
        tf_doc = self.tf_per_doc[doc_idx]
        doc_len = sum(tf_doc.values())
        score = 0.0
        for term in query_tokens:
            if term not in tf_doc:
                continue
            tf = tf_doc[term]
            idf = self.idf(term)
            num = tf * (BM25_K1 + 1)
            den = tf + BM25_K1 * (1 - BM25_B + BM25_B * doc_len / self.avgdl)
            score += idf * (num / den)
        return score


# DATA LOADING 

def _parse_product(item: dict) -> Optional[Product]:
    # Tên sản phẩm — hỗ trợ cả "title", "name", "text"
    title = (
        item.get("title") or
        item.get("name") or
        ""
    ).strip()
    if not title:
        return None

    # Giá
    try:
        price = float(item.get("price_actual") or item.get("price") or 0)
    except (ValueError, TypeError):
        price = 0.0

    try:
        original_price = float(
            item.get("price_ori") or item.get("original_price") or 0
        )
        original_price = original_price if original_price > 0 else None
    except (ValueError, TypeError):
        original_price = None

    if price > 0:
        price = _to_vnd(price)
    if original_price:
        original_price = _to_vnd(original_price)

    # Rating
    try:
        rating_raw = item.get("item_rating") or item.get("rating") or 0
        # Nếu là dict (format gốc Shopee), lấy rating_star
        if isinstance(rating_raw, dict):
            rating_raw = rating_raw.get("rating_star", 0)
        rating = float(rating_raw)
    except (ValueError, TypeError):
        rating = 0.0

    # Sold
    try:
        sold = int(
            item.get("total_sold") or
            item.get("historical_sold") or
            item.get("sold") or 0
        )
    except (ValueError, TypeError):
        sold = 0

    # Item ID
    try:
        item_id = int(item.get("itemid") or item.get("id") or 0)
    except (ValueError, TypeError):
        item_id = 0

    # Shop name — FIX: thêm "shop" field từ test_ai.py
    shop_name = (
        item.get("seller_name") or
        item.get("shop_name") or
        item.get("shop") or      # ← field từ test_ai.py
        "Unknown"
    )

    # Discount
    discount_percent: Optional[int] = None
    if original_price and price > 0 and price < original_price:
        discount_percent = int(round((1 - price / original_price) * 100))

    return Product(
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
        shop_name=shop_name,
        location=item.get("location", "Vietnam"),
        is_official_shop=bool(item.get("is_official_shop", False)),
        score=None,
    )


def _load_all_products() -> list[Product]:
    if not DATA_JSONL_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file dữ liệu: {DATA_JSONL_PATH}\n"
            "Set biến môi trường DATA_JSONL_PATH."
        )
    products = []
    with open(DATA_JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                p = _parse_product(item)
                if p is not None:
                    products.append(p)
            except json.JSONDecodeError:
                continue
    return products


# ══════════════════════════════════════════════════════════════════════
# QUALITY SCORE
# ══════════════════════════════════════════════════════════════════════

def _quality_score(p: Product, max_sold: int) -> float:
    rating_norm = (p.rating or 0.0) / 5.0
    sold_norm = (
        math.log(p.sold + 1) / math.log(max_sold + 2)
        if max_sold > 0 else 0.0
    )
    return 0.5 * rating_norm + 0.5 * sold_norm


# ══════════════════════════════════════════════════════════════════════
# MAIN SEARCH
# ══════════════════════════════════════════════════════════════════════

async def fetch_top_products(
    keyword: str,
    limit: int = 10,
    sort_by: str = "relevancy",
) -> list[Product]:


    # ── 1. Parse payload ──────────────────────────────────────────────
    if "|" in keyword:
        original_kw, ai_expansion = keyword.split("|", 1)
    else:
        original_kw, ai_expansion = keyword, ""

    original_kw    = original_kw.strip()
    ai_expansion   = ai_expansion.strip()

    # Tokens từ query gốc (VI, đã bỏ dấu)
    vi_tokens  = _tokenize(original_kw)

    # Tokens từ AI (EN translation + brands + synonyms)
    ai_tokens  = _tokenize(ai_expansion)

    # Primary = AI nếu có (EN → khớp EN titles); fallback = VI
    primary_tokens  = ai_tokens  if ai_tokens  else vi_tokens
    fallback_tokens = vi_tokens  if ai_tokens  else []

    print(f"\n[SEARCH V2.1]")
    print(f"  VI tokens       : {vi_tokens}")
    print(f"  AI tokens       : {ai_tokens}")
    print(f"  Primary (BM25)  : {primary_tokens}")

    if not primary_tokens:
        return []

    # ── 2. Load corpus ────────────────────────────────────────────────
    all_products = _load_all_products()
    if not all_products:
        return []

    corpus_tokens = [_tokenize(p.name) for p in all_products]
    bm25 = BM25(corpus_tokens)

    max_sold = max((p.sold for p in all_products), default=0)

    # ── 3. Score ──────────────────────────────────────────────────────
    scored: list[tuple[float, Product]] = []

    for idx, product in enumerate(all_products):

        # BM25 primary (AI English tokens)
        score_primary = bm25.score(idx, primary_tokens)

        # BM25 fallback (VI tokens — hữu ích khi data tiếng Việt)
        score_fallback = bm25.score(idx, fallback_tokens) if fallback_tokens else 0.0

        # Hard filter: cả 2 đều = 0 → không liên quan
        if score_primary == 0.0 and score_fallback == 0.0:
            continue

        # Lấy score tốt hơn làm base
        bm25_base = max(score_primary, score_fallback)

        # AI boost = phần điểm tăng thêm từ AI tokens (nếu primary > fallback)
        ai_boost = max(0.0, score_primary - score_fallback) if fallback_tokens else 0.0

        # Quality
        quality = _quality_score(product, max_sold)

        # Normalize [0, 1]
        bm25_norm  = bm25_base / (bm25_base + 5.0)
        ai_norm    = ai_boost  / (ai_boost  + 5.0) if ai_boost > 0 else 0.0

        final = W_BM25 * bm25_norm + W_AI_BOOST * ai_norm + W_QUALITY * quality

        scored.append((final, product))

    print(f"  Matched: {len(scored)}/{len(all_products)}")

    # ── 4. Sort ───────────────────────────────────────────────────────
    if sort_by in {"relevancy", "relevant"}:
        scored.sort(key=lambda x: x[0], reverse=True)
    elif sort_by == "price":
        scored.sort(key=lambda x: x[1].price if x[1].price > 0 else float("inf"))
    elif sort_by in {"sold", "sales"}:
        scored.sort(key=lambda x: x[1].sold, reverse=True)
    else:
        scored.sort(key=lambda x: x[0], reverse=True)

    # ── 5. Gán score hiển thị ─────────────────────────────────────────
    result = []
    for rank_score, product in scored[:limit]:
        product.score = round(rank_score * 100, 1)
        result.append(product)

    return result