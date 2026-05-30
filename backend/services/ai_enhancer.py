import asyncio
import re
from typing import Optional, Dict
from deep_translator import GoogleTranslator
from transformers import pipeline

MODEL_NAME = "google/flan-t5-small"
_pipeline: Optional[object] = None

_STOP_WORDS = {
    "the", "and", "of", "popular", "famous", "brands", "are", "is",
    "some", "a", "an", "for", "in", "on", "with", "to", "or",
    "include", "includes", "such", "as", "like", "type", "types",
    "product", "products", "item", "items", "buy", "shop"
}

def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = pipeline(
            "text2text-generation",
            model=MODEL_NAME,
            device=-1
        )
    return _pipeline

def _run_prompt(gen, prompt: str, max_tokens: int = 50) -> str:
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
    except Exception as e:
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
    
    raw_brands = _run_prompt(gen, f"List 3 well-known brands for: {eng_kw_lower}", 25)
    raw_synonyms = _run_prompt(gen, f"Synonyms and alternative names for {eng_kw_lower}:", 20)
    raw_related = _run_prompt(gen, f"Related product categories for {eng_kw_lower}:", 20)

    combined_raw = f"{raw_brands} {raw_synonyms} {raw_related}"
    all_tokens = _tokenize(combined_raw)
    unique_expansion = _deduplicate(all_tokens, exclude=base_words)

    final_expansion = " ".join(unique_expansion[:8])
    
    print(f"[AI ENHANCER] Translated: '{eng_kw_lower}' | Expanded: '{final_expansion}'")
    
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