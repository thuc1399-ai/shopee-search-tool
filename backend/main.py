from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.search import router

app = FastAPI(
    title="Shopee Search Tool",
    description="Top 10 sản phẩm nổi bật với AI-powered ranking",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["search"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "shopee-search-tool"}