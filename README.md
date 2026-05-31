# Shopee Search Tool

Công cụ tìm kiếm sản phẩm Shopee với khả năng tối ưu hóa từ khóa tìm kiếm, cung cấp sắp xếp theo độ liên quan, giá cả, lượng bán và trả về kết quả qua API.

## Tính năng chính

- Tối ưu hóa từ khóa tìm kiếm bằng mô hình xử lý ngôn ngữ tự nhiên (google/flan-t5-large)
- Backend API được xây dựng với FastAPI
- Frontend được phát triển bằng React
- Hỗ trợ sắp xếp theo các tiêu chí:
  - Độ liên quan (relevancy)
  - Giá thấp nhất (price)
  - Lượng bán cao nhất (sold)
- Dữ liệu mẫu định dạng JSONL, có thể cấu hình để sử dụng dữ liệu thực
- Quy đổi giá USD sang VND (cấu hình thông qua biến môi trường)

## Kiến trúc hệ thống

- Backend: FastAPI (Python)
- Frontend: React + Vite + Tailwind CSS
- Database: File JSONL (offline mode) hoặc kết nối API
- Giao tiếp: API REST

## Dữ liệu

Hệ thống mặc định sử dụng file dữ liệu mẫu: `data/shopee_sample.jsonl`

Dữ liệu được lấy từ bộ dữ liệu mẫu trên Kaggle: [Shopee Sample Data](https://www.kaggle.com/datasets/yoongsin/shopee-sample-data)

Để sử dụng dữ liệu của riêng bạn, hãy đặt biến môi trường `DATA_JSONL_PATH` trỏ đến file JSONL của bạn.

## Cài đặt cục bộ

### Yêu cầu hệ thống

- Python 3.8 hoặc cao hơn
- Node.js 16 hoặc cao hơn
- npm hoặc yarn

### Cài đặt Backend

```bash
cd backend
pip install -r requirements.txt
```

Chạy Backend:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend sẽ chạy tại: http://localhost:8000

### Cài đặt Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend sẽ chạy tại: http://localhost:3000

## Cấu hình biến môi trường

Tạo file `.env` tại thư mục gốc của dự án và điền các giá trị sau (nếu cần):

```
DATA_JSONL_PATH=
USD_TO_VND_RATE=25000
```

Giải thích chi tiết:

- `DATA_JSONL_PATH`: Đường dẫn tuyệt đối hoặc tương đối đến file dữ liệu JSONL của bạn. Nếu để trống, hệ thống sẽ sử dụng file mẫu mặc định.
- `USD_TO_VND_RATE`: Tỉ giá quy đổi từ USD sang VND (mặc định: 25000 VND = 1 USD)

## API Endpoints

### Tìm kiếm sản phẩm

**Endpoint:** `POST /api/v1/search`

**Request Body:**

```json
{
  "keyword": "ban phim",
  "limit": 5,
  "use_ai": true,
  "sort_by": "relevancy"
}
```

**Tham số:**

- `keyword` (string): Từ khóa tìm kiếm
- `limit` (integer): Số lượng kết quả trả về (tối đa)
- `use_ai` (boolean): Có sử dụng tối ưu hóa từ khóa hay không
- `sort_by` (string): Tiêu chí sắp xếp - `relevancy`, `price`, hoặc `sold`

**Response:**

```json
{
  "results": [
    {
      "name": "Tên sản phẩm",
      "price": 15000,
      "sold": 1200,
      "rating": 4.5
    }
  ],
  "total": 5
}
```

## Chạy ứng dụng bằng Docker

Để chạy toàn bộ ứng dụng (Backend + Frontend) bằng Docker Compose:

```bash
docker compose up --build
```

Sau đó, truy cập:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

## Kiểm tra nhanh API

Sử dụng curl để kiểm tra API:

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"keyword":"Apple Pencil","limit":5,"use_ai":true,"sort_by":"relevancy"}'
```

## Demo trực tuyến

Truy cập ứng dụng demo tại: https://shopee-search-frontend.onrender.com/

## Video hướng dẫn

[Screencast from 29-05-2026 12:38:34.webm](https://github.com/user-attachments/assets/dd14a6bd-3fae-4e65-927a-f18fb5c04e54)

## Lưu ý kỹ thuật

- Mô hình ngôn ngữ `google/flan-t5-large` sẽ được tải xuống lần đầu tiên, kích thước khoảng 3.1GB. Thời gian tải lần đầu có thể mất vài phút.
- Dữ liệu mẫu đã được quy đổi từ USD sang VND trước khi lưu trữ trong backend.
- Khi khởi động lần đầu, backend sẽ chuẩn bị dữ liệu và mô hình, vui lòng chờ một lúc.

## Cấu trúc dự án

```
shopee-search-tool/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
├── data/
│   └── shopee_sample.jsonl
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## Giấy phép

Dự án này được cấp phép dưới MIT License.

## Hỗ trợ

Nếu bạn gặp vấn đề hoặc có câu hỏi, vui lòng mở một issue trên GitHub repository này.
