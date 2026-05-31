import json
import math
import os
import re
import time
import unicodedata
import threading
from pathlib import Path
from typing import Optional, List, Tuple

from dotenv import load_dotenv
from backend.models.schemas import Product

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[2]

DATA_JSONL_PATH = REPO_ROOT / "data" / "shopee_sample.jsonl"

USD_TO_VND_RATE = float(os.getenv("USD_TO_VND_RATE", "25000"))
_MAX_USD_PRICE = 50_000.0

BM25_K1 = 1.5
BM25_B = 0.75

W_BM25 = 0.60
W_AI_BOOST = 0.20
W_QUALITY = 0.20

TTL_SECONDS = 300
_cache: dict[str, Tuple[float, List[Product]]] = {}
_cache_lock = threading.Lock()

class _Index:
    products: List[Product] = []
    bm25: Optional["BM25"] = None
    max_sold: int = 0
    built_at: float = 0.0
    is_ready: bool = False

_IDX = _Index()

def build_index() -> None:
    try:
        products = _load_all_products()
    except FileNotFoundError as e:
        print(f"[INDEX ERROR] {e}")
        return

    corpus = [_tokenize(p.name) for p in products]

    _IDX.products = products
    _IDX.bm25 = BM25(corpus)
    _IDX.max_sold = max((p.sold for p in products), default=0)
    _IDX.built_at = time.time()
    _IDX.is_ready = True

def index_status() -> dict:
    return {
        "ready": _IDX.is_ready,
        "products": len(_IDX.products),
        "built_at": _IDX.built_at,
    }

def _normalize(text: str) -> str:
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    no_accent = "".join(c for c in nfkd if not unicodedata.combining(c))
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", no_accent.lower())
    return re.sub(r"\s+", " ", cleaned).strip()

def _tokenize(text: str) -> List[str]:
    return [t for t in _normalize(text).split() if t]

def _to_vnd(value: float) -> float:
    if value <= 0:
        return 0.0
    if value > _MAX_USD_PRICE:
        return round(value, 0)
    return round(value * USD_TO_VND_RATE, 0)

class BM25:
    def __init__(self, corpus_tokens: List[List[str]]):
        self.n = len(corpus_tokens)
        self.avgdl = sum(len(d) for d in corpus_tokens) / self.n if self.n > 0 else 1.0
        self.df: dict[str, int] = {}
        self.tf_per_doc: List[dict[str, int]] = []

        for doc in corpus_tokens:
            tf: dict[str, int] = {}
            for tok in doc:
                tf[tok] = tf.get(tok, 0) + 1
            self.tf_per_doc.append(tf)
            for term in set(doc):
                self.df[term] = self.df.get(term, 0) + 1

    def idf(self, term: str) -> float:
        n = self.df.get(term, 0)
        if n == 0:
            return 0.0
        return math.log((self.n - n + 0.5) / (n + 0.5) + 1)

    def score(self, doc_idx: int, query_tokens: List[str]) -> float:
        if not query_tokens:
            return 0.0
        tf_doc = self.tf_per_doc[doc_idx]
        doc_len = sum(tf_doc.values())
        s = 0.0
        for term in query_tokens:
            if term not in tf_doc:
                continue
            tf = tf_doc[term]
            idf = self.idf(term)
            num = tf * (BM25_K1 + 1)
            den = tf + BM25_K1 * (1 - BM25_B + BM25_B * doc_len / self.avgdl)
            s += idf * (num / den)
        return s

def _parse_product(item: dict) -> Optional[Product]:
    title = (item.get("title") or item.get("name") or "").strip()
    if not title:
        return None

    try:
        price = float(item.get("price_actual") or item.get("price") or 0)
    except (ValueError, TypeError):
        price = 0.0
    price = _to_vnd(price)

    try:
        orig = float(item.get("price_ori") or item.get("original_price") or 0)
        original_price: Optional[float] = _to_vnd(orig) if orig > 0 else None
    except (ValueError, TypeError):
        original_price = None

    try:
        rating_raw = item.get("item_rating") or item.get("rating") or 0
        if isinstance(rating_raw, dict):
            rating_raw = rating_raw.get("rating_star", 0)
        rating = float(rating_raw)
    except (ValueError, TypeError):
        rating = 0.0

    try:
        sold = int(item.get("historical_sold") or item.get("total_sold") or item.get("sold") or 0)
    except (ValueError, TypeError):
        sold = 0

    try:
        item_id = int(item.get("itemid") or item.get("id") or 0)
    except (ValueError, TypeError):
        item_id = 0
        
    try:
        shop_id = int(item.get("shopid") or item.get("shop_id") or 0)
    except (ValueError, TypeError):
        shop_id = 0
        
    try:
        stock = int(item.get("stock") or 999)
    except (ValueError, TypeError):
        stock = 999

    shop_raw = item.get("seller_name") or item.get("shop_name") or item.get("shop") or "Unknown"
    shop_name = shop_raw.get("name") or "Unknown" if isinstance(shop_raw, dict) else str(shop_raw)

    image_url = str(item.get("pict_link") or item.get("image_url") or item.get("image") or "")
    if image_url and not image_url.startswith("http"):
        image_url = f"https://down-vn.img.susercontent.com/file/{image_url}"

    product_url = str(item.get("link_ori") or item.get("product_url") or "")
    if not product_url and item_id:
        product_url = f"https://shopee.vn/product/{shop_id}/{item_id}"

    discount_percent: Optional[int] = None
    if original_price and price > 0 and price < original_price:
        discount_percent = int(round((1 - price / original_price) * 100))

    return Product(
        item_id=item_id,
        shop_id=shop_id,
        name=title,
        price=price,
        original_price=original_price,
        discount_percent=discount_percent,
        rating=round(rating, 1),
        sold=sold,
        stock=stock,
        image_url=image_url,
        product_url=product_url,
        shop_name=shop_name,
        location=str(item.get("shop_location") or item.get("location") or "Vietnam"),
        is_official_shop=bool(item.get("is_official_shop", False)),
        score=None,
    )

def _load_all_products() -> List[Product]:
    if not DATA_JSONL_PATH.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_JSONL_PATH}")
    products: List[Product] = []
    with open(DATA_JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                p = _parse_product(json.loads(line))
                if p is not None:
                    products.append(p)
            except (json.JSONDecodeError, Exception):
                continue
    return products

def _quality_score(p: Product, max_sold: int) -> float:
    rating_norm = (p.rating or 0.0) / 5.0
    sold_norm = math.log(p.sold + 1) / math.log(max_sold + 2) if max_sold > 0 else 0.0
    return 0.5 * rating_norm + 0.5 * sold_norm

def _cache_key(keyword: str, ai_terms: str, limit: int, sort_by: str) -> str:
    return f"{keyword.lower().strip()}|{ai_terms.lower().strip()}|{limit}|{sort_by}"

def _cache_get(key: str) -> Optional[List[Product]]:
    with _cache_lock:
        entry = _cache.get(key)
        if entry is None:
            return None
        ts, results = entry
        if time.time() - ts > TTL_SECONDS:
            del _cache[key]
            return None
        return results

def _cache_set(key: str, results: List[Product]) -> None:
    with _cache_lock:
        if len(_cache) >= 200:
            oldest = min(_cache.items(), key=lambda x: x[1][0])
            del _cache[oldest[0]]
        _cache[key] = (time.time(), results)

def clear_cache() -> int:
    with _cache_lock:
        size = len(_cache)
        _cache.clear()
        return size

def suggest_products(query: str, limit: int = 6) -> List[str]:
    if not _IDX.is_ready or not query.strip():
        return []

    q_tokens = _tokenize(query)
    if not q_tokens:
        return []

    scored: List[Tuple[float, str]] = []
    for idx, product in enumerate(_IDX.products):
        s = _IDX.bm25.score(idx, q_tokens)
        if s > 0:
            scored.append((s, product.name))

    scored.sort(key=lambda x: x[0], reverse=True)

    seen: set[str] = set()
    suggestions: List[str] = []
    for _, name in scored:
        key = name[:40].lower()
        if key not in seen:
            seen.add(key)
            suggestions.append(name)
            if len(suggestions) >= limit:
                break
    return suggestions

async def fetch_top_products(
    keyword: str,
    ai_terms: str = "",
    limit: int = 10,
    sort_by: str = "relevancy",
) -> List[Product]:
    cache_key = _cache_key(keyword, ai_terms, limit, sort_by)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    if not _IDX.is_ready:
        build_index()
        if not _IDX.is_ready:
            raise FileNotFoundError("Search index unavailable.")

    core_tokens = _tokenize(keyword.strip())
    ai_tokens = _tokenize(ai_terms.strip())
    all_tokens = core_tokens + ai_tokens

    if not core_tokens and not ai_tokens:
        return []

    has_ai = bool(ai_tokens)
    scored: List[Tuple[float, Product]] = []

    for idx, product in enumerate(_IDX.products):
        bm25_core = _IDX.bm25.score(idx, core_tokens) if core_tokens else 0.0
        bm25_ai_core = _IDX.bm25.score(idx, ai_tokens) if ai_tokens else 0.0

        if core_tokens and bm25_core == 0.0:
            if not has_ai or bm25_ai_core == 0.0:
                continue

        effective_core = max(bm25_core, bm25_ai_core)
        bm25_full = _IDX.bm25.score(idx, all_tokens)
        ai_boost = max(0.0, bm25_full - effective_core)
        quality = _quality_score(product, _IDX.max_sold)

        core_norm = effective_core / (effective_core + 5.0)
        ai_norm = ai_boost / (ai_boost + 5.0) if ai_boost > 0 else 0.0

        final = W_BM25 * core_norm + W_AI_BOOST * ai_norm + W_QUALITY * quality
        scored.append((final, product))

    if sort_by in {"relevancy", "relevant"}:
        scored.sort(key=lambda x: x[0], reverse=True)
    elif sort_by == "price":
        scored.sort(key=lambda x: x[1].price if x[1].price > 0 else float("inf"))
    elif sort_by in {"sold", "sales"}:
        scored.sort(key=lambda x: x[1].sold, reverse=True)
    else:
        scored.sort(key=lambda x: x[0], reverse=True)

    result: List[Product] = []
    for rank_score, product in scored[:limit]:
        p = product.model_copy()
        p.score = round(rank_score * 100, 1)
        result.append(p)

    _cache_set(cache_key, result)
    return result
