import asyncio
import re
import os
from typing import Optional, Dict
from deep_translator import GoogleTranslator

# Hỗ trợ các giá trị: "lite", "small", "base", "large"
AI_MODE = os.getenv("AI_MODE", "lite").lower()

_pipeline: Optional[object] = None

_STOP_WORDS = {
    "the", "and", "of", "popular", "famous", "brands", "are", "is",
    "some", "a", "an", "for", "in", "on", "with", "to", "or",
    "include", "includes", "such", "as", "like", "type", "types",
    "product", "products", "item", "items", "buy", "shop"
}

def _get_pipeline():
    global _pipeline
    
    if AI_MODE == "lite":
        return None

    try:
        from transformers import pipeline
        if _pipeline is None:
            # Tự động chọn mô hình dựa trên biến môi trường
            model_name = f"google/flan-t5-{AI_MODE}"
            # Fallback nếu nhập sai tên
            if AI_MODE not in ["small", "base", "large", "xl", "xxl"]:
                model_name = "google/flan-t5-small"
                
            print(f"[STARTUP] Loading local AI model: {model_name}...")
            _pipeline = pipeline(
                "text2text-generation",
                model=model_name,
                device=-1
            )
            print(f"[STARTUP] {model_name} ready.")
        return _pipeline
    except ImportError:
        print("[WARNING] Thư viện 'transformers' hoặc 'torch' chưa được cài đặt. Tự động chuyển về AI LITE.")
        return None
    except Exception as e:
        print(f"[ERROR] Lỗi khi load AI model: {e}. Tự động chuyển về AI LITE.")
        return None

def _run_prompt(gen, prompt: str, max_tokens: int = 50) -> str:
    if gen is None:
        return ""
    try:
        out = gen(
            prompt,
            max_length=max_tokens,
            num_beams=4,
            do_sample=False,
            repetition_penalty=1.5,
            no_repeat_ngram_size=2,
        )
        return out[0].get("generated_text", "").strip()
    except Exception:
        return ""

def _tokenize(text: str) -> list[str]:
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

def _enhance_sync(keyword: str) -> Dict[str, str]:
    eng_kw = keyword
    try:
        translated = GoogleTranslator(source="auto", target="en").translate(keyword)
        if translated and translated.strip():
            eng_kw = translated.strip()
    except Exception:
        pass

    eng_kw_lower = eng_kw.lower().strip()
    base_words = set(_tokenize(eng_kw_lower))

    gen = _get_pipeline()
    
    if gen is not None:
        # Chế độ FULL (Chạy bằng Model flan-t5)
        raw_brands = _run_prompt(gen, f"List 3 well-known brands for: {eng_kw_lower}", 25)
        raw_synonyms = _run_prompt(gen, f"Synonyms and alternative names for {eng_kw_lower}:", 20)
        raw_related = _run_prompt(gen, f"Related product categories for {eng_kw_lower}:", 20)

        combined_raw = f"{raw_brands} {raw_synonyms} {raw_related}"
        all_tokens = _tokenize(combined_raw)
        unique_expansion = _deduplicate(all_tokens, exclude=base_words)

        final_expansion = " ".join(unique_expansion[:8])
        print(f"[AI ENHANCER - FULL] Translated: '{eng_kw_lower}' | Expanded: '{final_expansion}'")
    else:
        # Chế độ LITE (Chỉ dịch và làm sạch từ khoá - Dùng cho Render)
        all_tokens = _tokenize(eng_kw_lower)
        unique_expansion = _deduplicate(all_tokens, exclude=set())
        
        final_expansion = " ".join(unique_expansion[:8])
        print(f"[AI ENHANCER - LITE] Translated: '{eng_kw_lower}' | Expanded: '{final_expansion}'")
    
    return {
        "original": keyword,
        "enhanced": final_expansion,
        "translated": eng_kw_lower
    }

async def enhance_keyword(keyword: str) -> Dict[str, str]:
    try:
        return await asyncio.to_thread(_enhance_sync, keyword)
    except Exception:
        return {"original": keyword, "enhanced": "", "translated": keyword.lower()}
