import asyncio
import unicodedata
from typing import Optional

from transformers import pipeline

SYSTEM_PROMPT = """Tối ưu từ khóa tìm kiếm Shopee.
Yêu cầu: chỉ trả về từ khóa đã tối ưu, tối đa 5 từ.
Nếu keyword quá chung chung, thêm thuộc tính (hãng, dòng, kích thước, chất liệu, đối tượng).
Ví dụ: "điện thoại" → "điện thoại samsung chính hãng".
"""

MODEL_NAME = "google/flan-t5-large"  # Model lớn, tải lần đầu sẽ lâu
_text2text: Optional[object] = None


def _get_pipeline():
    global _text2text
    if _text2text is None:
        _text2text = pipeline("text2text-generation", model=MODEL_NAME)
    return _text2text


def _normalize_text(text: str) -> str:
    return "".join(
        ch
        for ch in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(ch) != "Mn"
    )


def _clean_output(text: str, fallback: str) -> str:
    cleaned = text.replace("\n", " ").strip().strip("\"").strip("'")

    for sep in [
        "Keyword tối ưu:",
        "Từ khóa tối ưu:",
        "Optimized keyword:",
        "Keyword:",
        "Tu khoa toi uu:",
    ]:
        if sep in cleaned:
            cleaned = cleaned.split(sep)[-1].strip()

    if not cleaned:
        return fallback

    lowered = cleaned.lower()
    if lowered.startswith("ban la") or lowered.startswith("bạn là") or lowered.startswith("you are"):
        return fallback

    normalized = _normalize_text(cleaned)
    if "tu khoa" in normalized or "keyword" in normalized or "optimiz" in normalized:
        return fallback

    words = cleaned.split()
    if len(words) > 5:
        cleaned = " ".join(words[:5])

    return cleaned


def _enhance_sync(keyword: str) -> str:
    generator = _get_pipeline()
    prompt = f"{SYSTEM_PROMPT}\nKeyword: {keyword}\nTừ khóa tối ưu:"
    output = generator(
        prompt,
        max_new_tokens=16,
        num_beams=4,
        no_repeat_ngram_size=2,
        do_sample=False,
    )
    if not output:
        return keyword
    text = output[0].get("generated_text", "").strip()
    return _clean_output(text, keyword)

async def enhance_keyword(keyword: str) -> str:
    try:
        return await asyncio.to_thread(_enhance_sync, keyword)
    except Exception as e:
        print(f"[ERROR] {e}")
        return keyword


# 👇 MAIN để test
async def main():
    test_keywords = [
        "điện thoại",
        "tai nghe",
        "laptop",
        "giày thể thao"
    ]

    print("=== TEST FLAN-T5 AI ENHANCER ===")

    for kw in test_keywords:
        print(f"\n[INPUT ] {kw}")
        result = await enhance_keyword(kw)
        print(f"[OUTPUT] {result}")


if __name__ == "__main__":
    asyncio.run(main())