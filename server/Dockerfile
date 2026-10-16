# Alpine 的系統套件比 Debian slim 少很多，Harbor 弱點掃描結果也乾淨很多
FROM python:3.12-alpine

# pip 改從公司 Nexus 下載套件（runner 不能連外網），設定與 Harbor base_image/python 相同
# 用 ARG 只在 build 時生效，不會留在最後的 image 裡
ARG PIP_INDEX_URL=https://nexusoss.wistron.com/repository/pypi-group/simple
ARG PIP_TRUSTED_HOST=nexusoss.wistron.com

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
