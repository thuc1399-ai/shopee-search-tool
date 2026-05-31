FROM python:3.11-slim
WORKDIR /app

COPY backend/requirements-render.txt backend/requirements-render.txt
RUN pip install --no-cache-dir -r backend/requirements-render.txt

COPY backend ./backend
COPY data ./data

ENV PYTHONPATH=/app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
