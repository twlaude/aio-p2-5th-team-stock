FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY server.py .

EXPOSE 8023

CMD ["python", "server.py"]
