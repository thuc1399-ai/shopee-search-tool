import os
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """Bạn là chuyên gia tối ưu từ khóa tìm kiếm trên Shopee (sàn TMĐT Việt Nam).
Nhiệm vụ: Nhận keyword đầu vào → trả về keyword được tối ưu hơn để tìm đúng sản phẩm hơn.
- Giữ ngắn gọn (tối đa 5 từ)
- Dùng tiếng Việt hoặc Anh tùy loại sản phẩm
- Chỉ trả về keyword đã tối ưu, không giải thích
- Ví dụ: "điện thoại" → "điện thoại samsung chính hãng"
"""

async def enhance_keyword(keyword: str) -> str:
    """Dùng Claude để tối ưu từ khóa tìm kiếm."""
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=50,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Keyword: {keyword}"}]
        )
        enhanced = message.content[0].text.strip()
        return enhanced if enhanced else keyword
    except Exception:
        return keyword  # fallback to original if AI fails