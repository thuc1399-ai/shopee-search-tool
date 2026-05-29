# Shopee Search Tool

Tìm kiếm sản phẩm Shopee với AI tối ưu từ khóa, sắp xếp theo độ liên quan/giá/bán chạy và trả về Top N kết quả qua API.

## Tính năng
- Tối ưu từ khóa bằng `google/flan-t5-large` (có thể đổi model trong code).
- API tìm kiếm FastAPI + frontend React.
- Sắp xếp theo:
	- `relevancy` (xếp hạng AI)
	- `price` (giá thấp nhất)
	- `sold` (bán chạy nhất)
- Dữ liệu mẫu dạng JSONL, có thể trỏ tới dữ liệu thật qua env.
- Quy đổi giá USD → VND (cấu hình qua env).

## Kiến trúc
- Backend: FastAPI
- Frontend: React + Vite + Tailwind
- Data: JSONL (offline) → API → UI

## Dataset
Mặc định sử dụng file mẫu: `data/shopee_sample.jsonl`.
Nếu bạn có dữ liệu thật, đặt biến môi trường `DATA_JSONL_PATH` trỏ tới file JSONL của bạn.

## Cài đặt nhanh (Local)
### Backend
```bash
conda activate shopee-ai
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Mở trình duyệt: http://localhost:3000

## Biến môi trường
Tạo file `.env` ở thư mục root và điền các biến sau nếu cần:
```
DATA_JSONL_PATH=
USD_TO_VND_RATE=25000
```

Giải thích:
- `DATA_JSONL_PATH`: đường dẫn tới file JSONL dữ liệu thực.
- `USD_TO_VND_RATE`: tỉ giá quy đổi.

## API
`POST /api/v1/search`
```json
{
	"keyword": "ban phim",
	"limit": 5,
	"use_ai": true,
	"sort_by": "relevancy"
}
```

## Docker
```bash
docker compose up --build
```

## Test nhanh
```bash
curl -X POST http://localhost:8000/api/v1/search \
	-H "Content-Type: application/json" \
	-d '{"keyword":"Apple Pencil","limit":5,"use_ai":true,"sort_by":"relevancy"}'
```

## Ghi chú
- `google/flan-t5-large` tải lần đầu khoảng 3.1GB.
- Dữ liệu mẫu đã được quy đổi USD → VND trong backend.
