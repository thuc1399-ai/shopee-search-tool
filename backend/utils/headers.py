import random

HEADERS_POOL = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
        "Referer": "https://shopee.vn/",
        "x-api-source": "pc",
        "x-shopee-language": "vi",
        "x-csrftoken": "placeholder",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
        "Accept-Language": "vi-VN,vi;q=0.9",
        "Referer": "https://shopee.vn/",
        "x-api-source": "pc",
        "x-shopee-language": "vi",
    }
]

def get_headers():
    return random.choice(HEADERS_POOL)