"""
Shopee JSONL Search Engine — V2  (BM25 + Semantic Boosting)
============================================================

Kiến trúc scoring:
  final_score = w1 * bm25_score
              + w2 * ai_bonus_score
              + w3 * quality_score        ← rating × log(sold+1)

Tại sao BM25 tốt hơn string match?
  - Tính IDF: từ hiếm (brand, model) có trọng số CAO hơn từ phổ biến
  - Tính TF: từ xuất hiện nhiều trong title → score cao hơn
  - Có độ dài chuẩn hóa → title ngắn gọn không bị phạt
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

# ── Score weights ──────────────────────────────────────────────────────────────
W_BM25     = 0.55   # relevance với từ khóa
W_AI_BOOST = 0.25   # bonus từ AI expansion (brands, synonyms)
W_QUALITY  = 0.20   # chất lượng sản phẩm (rating × sold)

# ── BM25 hyper-parameters (chuẩn Robertson 1994) ──────────────────────────────
BM25_K1 = 1.5       # saturation term frequency (1.2–2.0 là range chuẩn)
BM25_B  = 0.75      # length normalization (0 = off, 1 = full)


# ══════════════════════════════════════════════════════════════════════════════
# UTILS
# ══════════════════════════════════════════════════════════════════════════════

def _normalize(text: str) -> str:
    """
    Chuẩn hóa text:
      - NFKD → loại combining chars (bỏ dấu tiếng Việt)
      - lowercase
      - bỏ ký tự đặc biệt (giữ khoảng trắng)
    """
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    no_accent = "".join(c for c in nfkd if not unicodedata.combining(c))
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", no_accent.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def _tokenize(text: str) -> list[str]:
    """Tokenize sau khi normalize. Trả về list token (có thể trùng)."""
    return _normalize(text).split()


def _to_vnd(value: float) -> float:
    return round(value * USD_TO_VND_RATE, 0)


# ══════════════════════════════════════════════════════════════════════════════
# BM25 ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class BM25:
    """
    Lightweight BM25 không cần thư viện ngoài.
    Được tối ưu để build nhanh từ JSONL file.
    """

    def __init__(self, corpus_tokens: list[list[str]]):
        self.corpus_size = len(corpus_tokens)
        self.avgdl = (
            sum(len(doc) for doc in corpus_tokens) / self.corpus_size
            if self.corpus_size > 0 else 1.0
        )

        # df[term] = số document chứa term
        self.df: dict[str, int] = {}
        # tf_per_doc[doc_idx][term] = tần suất xuất hiện trong doc đó
        self.tf_per_doc: list[dict[str, int]] = []

        for doc in corpus_tokens:
            tf: dict[str, int] = {}
            for token in doc:
                tf[token] = tf.get(token, 0) + 1
            self.tf_per_doc.append(tf)
            for term in set(doc):
                self.df[term] = self.df.get(term, 0) + 1

    def idf(self, term: str) -> float:
        """IDF theo Robertson BM25 formula."""
        n = self.df.get(term, 0)
        if n == 0:
            return 0.0
        return math.log((self.corpus_size - n + 0.5) / (n + 0.5) + 1)

    def score(self, doc_idx: int, query_tokens: list[str]) -> float:
        """Tính BM25 score cho 1 document với query."""
        tf_doc = self.tf_per_doc[doc_idx]
        doc_len = sum(tf_doc.values())
        score = 0.0

        for term in query_tokens:
            if term not in tf_doc:
                continue
            tf = tf_doc[term]
            idf = self.idf(term)
            numerator   = tf * (BM25_K1 + 1)
            denominator = tf + BM25_K1 * (1 - BM25_B + BM25_B * doc_len / self.avgdl)
            score += idf * (numerator / denominator)

        return score


# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════════════════════

def _parse_product(item: dict) -> Optional[Product]:
    """Parse 1 dòng JSONL → Product. Trả về None nếu thiếu title."""
    title = (item.get("title") or item.get("name") or "").strip()
    if not title:
        return None

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

    try:
        rating = float(item.get("item_rating") or item.get("rating") or 0)
    except (ValueError, TypeError):
        rating = 0.0

    try:
        sold = int(item.get("total_sold") or item.get("sold") or 0)
    except (ValueError, TypeError):
        sold = 0

    try:
        item_id = int(item.get("id", 0))
    except (ValueError, TypeError):
        item_id = 0

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
        shop_name=item.get("seller_name") or item.get("shop_name", "Unknown"),
        location=item.get("location", "Vietnam"),
        is_official_shop=bool(item.get("is_official_shop", False)),
        score=None,
    )


def _load_all_products() -> list[Product]:
    """Đọc toàn bộ JSONL → list Product."""
    if not DATA_JSONL_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file dữ liệu tại: {DATA_JSONL_PATH}\n"
            "Hãy set biến môi trường DATA_JSONL_PATH."
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


# ══════════════════════════════════════════════════════════════════════════════
# QUALITY SCORE (độc lập với keyword)
# ══════════════════════════════════════════════════════════════════════════════

def _quality_score(p: Product, max_sold: int) -> float:
    """
    Điểm chất lượng sản phẩm — không phụ thuộc từ khóa.
      = normalized_rating * 0.5 + normalized_sold * 0.5
    """
    rating_norm = (p.rating or 0.0) / 5.0
    sold_norm   = math.log(p.sold + 1) / math.log(max_sold + 2) if max_sold > 0 else 0.0
    return 0.5 * rating_norm + 0.5 * sold_norm


# ══════════════════════════════════════════════════════════════════════════════
# MAIN SEARCH FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_top_products(
    keyword: str,
    limit: int = 10,
    sort_by: str = "relevancy",
) -> list[Product]:
    """
    Pipeline:
      1. Parse keyword → core_query, ai_expansion
      2. Load + tokenize corpus
      3. Build BM25 index
      4. Score = BM25(core) + AI_boost(expansion) + Quality
      5. Hard filter: bỏ sản phẩm có BM25 = 0 (hoàn toàn không liên quan)
      6. Sort và trả về top-K
    """

    # ── 1. Parse AI payload ────────────────────────────────────────────────
    if "|" in keyword:
        core_raw, ai_raw = keyword.split("|", 1)
    else:
        core_raw, ai_raw = keyword, ""

    core_tokens  = _tokenize(core_raw)        # từ người dùng (đã bỏ dấu)
    ai_tokens    = _tokenize(ai_raw)           # từ AI expansion
    query_tokens = core_tokens + ai_tokens     # toàn bộ query cho BM25

    print(f"\n[SEARCH V2]")
    print(f"  Core tokens : {core_tokens}")
    print(f"  AI tokens   : {ai_tokens}")

    if not core_tokens and not ai_tokens:
        return []

    # ── 2. Load corpus ─────────────────────────────────────────────────────
    all_products = _load_all_products()
    if not all_products:
        return []

    corpus_titles        = [p.name for p in all_products]
    corpus_tokens_list   = [_tokenize(t) for t in corpus_titles]

    # ── 3. Build BM25 ─────────────────────────────────────────────────────
    bm25 = BM25(corpus_tokens_list)

    max_sold = max((p.sold for p in all_products), default=0)

    # ── 4. Score mỗi sản phẩm ─────────────────────────────────────────────
    scored: list[tuple[float, Product]] = []

    for idx, product in enumerate(all_products):

        # 4a. BM25 với core query (từ người dùng gốc)
        bm25_core = bm25.score(idx, core_tokens)

        # Hard filter: nếu core hoàn toàn không match → skip
        # (trừ trường hợp core_tokens rỗng vì AI đã dịch hết)
        if core_tokens and bm25_core == 0.0:
            continue

        # 4b. AI expansion boost — BM25 với full query
        bm25_full = bm25.score(idx, query_tokens)
        ai_boost  = max(0.0, bm25_full - bm25_core)   # phần tăng thêm từ AI

        # 4c. Quality score
        quality = _quality_score(product, max_sold)

        # 4d. Normalize BM25 (soft max để đưa về [0, 1] range)
        # Dùng sigmoid-like: score / (score + 5)
        bm25_norm = bm25_core / (bm25_core + 5.0)
        ai_norm   = ai_boost  / (ai_boost  + 5.0) if ai_boost > 0 else 0.0

        final = W_BM25 * bm25_norm + W_AI_BOOST * ai_norm + W_QUALITY * quality

        scored.append((final, product))

    print(f"  Matched: {len(scored)}/{len(all_products)} products")

    # ── 5. Sort ────────────────────────────────────────────────────────────
    if sort_by in {"relevancy", "relevant"}:
        scored.sort(key=lambda x: x[0], reverse=True)
    elif sort_by == "price":
        scored.sort(key=lambda x: x[1].price if x[1].price > 0 else float("inf"))
    elif sort_by in {"sold", "sales"}:
        scored.sort(key=lambda x: x[1].sold, reverse=True)
    else:
        scored.sort(key=lambda x: x[0], reverse=True)

    # ── 6. Gán score và trả về ─────────────────────────────────────────────
    result = []
    for rank_score, product in scored[:limit]:
        product.score = round(rank_score * 100, 1)   # convert → % cho dễ đọc
        result.append(product)

    return result