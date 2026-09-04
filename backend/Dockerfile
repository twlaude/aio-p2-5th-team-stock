# 빌드 컨텍스트는 backend/가 아니라 저장소 루트다.
# shared/supported_companies.json을 이미지에 담아야 하기 때문이다.
#   docker build -f backend/Dockerfile -t stock-backend .
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY shared/supported_companies.json ./data/supported_companies.json

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
