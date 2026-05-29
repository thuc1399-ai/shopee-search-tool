"""
AI Keyword Enhancer — V2
========================
Chiến lược mới:
  1. Dịch VI → EN (Google Translate, free)
  2. Multi-prompt flan-t5:  brands  +  synonyms  +  related_items
  3. Trả về payload  "original_kw|en_translation expanded_terms"
     để shopee.py dùng cho BM25 boosting.

Tại sao bỏ cách cũ?
  - Prompt "Name 2 popular brands of X" quá hẹp → bỏ sót sản phẩm
  - Không có synonyms → search kém với từ đồng nghĩa
  - Không có related_items → miss sản phẩm liên quan
"""

import asyncio
import re
from typing import Optional
from deep_translator import GoogleTranslator
from transformers import pipeline

MODEL_NAME = "google/flan-t5-small" # Sử dụng bản "google/flan-t5-large" nếu tải về để có kết quả tối ưu hơn 
_pipeline: Optional[object] = None

# ─────────────────────────────────────────────
# STOP WORDS – lọc những từ vô nghĩa ra khỏi expansion
# ─────────────────────────────────────────────
_STOP_WORDS = {
    "the", "and", "of", "popular", "famous", "brands", "are", "is",
    "some", "a", "an", "for", "in", "on", "with", "to", "or",
    "include", "includes", "such", "as", "like", "type", "types",
    "product", "products", "item", "items", "buy", "shop"
}


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        print(f"[*] Loading model {MODEL_NAME}... (cold start)")
        _pipeline = pipeline(
            "text2text-generation",
            model=MODEL_NAME,
            device=-1  # CPU; đổi thành 0 nếu có GPU
        )
    return _pipeline


def _run_prompt(gen, prompt: str, max_tokens: int = 20) -> str:
    """Chạy 1 prompt T5, trả về text đã clean."""
    try:
        out = gen(
            prompt,
            max_new_tokens=max_tokens,
            num_beams=4,
            do_sample=False,
            repetition_penalty=1.5,
            no_repeat_ngram_size=2,
        )
        return out[0].get("generated_text", "").strip()
    except Exception as e:
        print(f"  [WARN] T5 prompt failed: {e}")
        return ""


def _tokenize(text: str) -> list[str]:
    """Tách từ, lowercase, bỏ ký tự đặc biệt."""
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    return [w for w in text.split() if w and w not in _STOP_WORDS]


def _deduplicate(words: list[str], exclude: set[str]) -> list[str]:
    seen = set(exclude)
    result = []
    for w in words:
        wl = w.lower()
        if wl not in seen and len(wl) > 1:
            seen.add(wl)
            result.append(w.title())
    return result


def _enhance_sync(keyword: str) -> str:
    print(f"\n{'='*50}")
    print(f"[AI ENHANCER V2] Input: '{keyword}'")

    # ── BƯỚC 1: Dịch VI → EN ──────────────────────────
    eng_kw = keyword
    try:
        translated = GoogleTranslator(source="auto", target="en").translate(keyword)
        if translated and translated.strip():
            eng_kw = translated.strip()
    except Exception as e:
        print(f"  [WARN] Translation failed: {e}")

    eng_kw_lower = eng_kw.lower().strip()
    print(f"  [1] Translated: '{eng_kw_lower}'")

    base_words = set(_tokenize(eng_kw_lower))

    # ── BƯỚC 2: Multi-prompt T5 expansion ─────────────
    gen = _get_pipeline()
    expansion_tokens: list[str] = []

    # Prompt A: Brands / nhãn hiệu phổ biến
    raw_brands = _run_prompt(
        gen,
        f"List 3 well-known brands for: {eng_kw_lower}",
        max_tokens=25,
    )
    print(f"  [2a] Brands raw: '{raw_brands}'")

    # Prompt B: Synonyms / từ đồng nghĩa
    raw_synonyms = _run_prompt(
        gen,
        f"Synonyms and alternative names for {eng_kw_lower}:",
        max_tokens=20,
    )
    print(f"  [2b] Synonyms raw: '{raw_synonyms}'")

    # Prompt C: Related product types / sản phẩm liên quan
    raw_related = _run_prompt(
        gen,
        f"Related product categories for {eng_kw_lower}:",
        max_tokens=20,
    )
    print(f"  [2c] Related raw: '{raw_related}'")

    # ── BƯỚC 3: Post-processing ────────────────────────
    combined_raw = f"{raw_brands} {raw_synonyms} {raw_related}"
    all_tokens = _tokenize(combined_raw)
    unique_expansion = _deduplicate(all_tokens, exclude=base_words)

    # Giới hạn tối đa 8 từ expansion để tránh noise
    final_expansion = " ".join(unique_expansion[:8])
    print(f"  [3] Final expansion: '{final_expansion}'")

    # ── FORMAT OUTPUT: "keyword|en_kw expansion_terms" ──
    # shopee.py sẽ parse phần sau "|" để boost scoring
    ai_payload = f"{eng_kw_lower} {final_expansion}".strip()
    result = f"{keyword}|{ai_payload}"

    print(f"  [OUTPUT] '{result}'")
    print(f"{'='*50}\n")
    return result


async def enhance_keyword(keyword: str) -> str:
    """Entry point async cho FastAPI router."""
    try:
        return await asyncio.to_thread(_enhance_sync, keyword)
    except Exception as e:
        print(f"[ERROR enhance_keyword] {e}")
        return f"{keyword}|"
