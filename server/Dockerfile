# Alpine 的系統套件比 Debian slim 少很多，Harbor 弱點掃描結果也乾淨很多
FROM python:3.12-alpine

# 套用最新的系統安全性更新
RUN apk upgrade --no-cache

WORKDIR /app

COPY requirements.txt .
# 裝完套件就移除 pip：執行時用不到，也避免 pip 本身的弱點被掃到
RUN pip install --no-cache-dir -r requirements.txt && pip uninstall -y pip

COPY main.py .

USER 1000
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
