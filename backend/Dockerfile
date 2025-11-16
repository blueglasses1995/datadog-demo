FROM python:3.11-slim

WORKDIR /app

# 依存パッケージのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# Flaskアプリケーションを起動
CMD ["ddtrace-run", "flask", "run", "--host=0.0.0.0", "--port=5000"]
