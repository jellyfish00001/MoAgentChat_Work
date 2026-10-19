# Alpine 的系統套件比 Debian slim 少很多，Harbor 弱點掃描結果也乾淨很多
FROM python:3.12-alpine

# runner 不能連外網，apk 和 pip 都改從公司 Nexus 下載
ARG NEXUS=https://nexusoss.wistron.com/repository
# 用 ARG 只在 build 時生效，不會留在最後的 image 裡
ARG PIP_INDEX_URL=${NEXUS}/pypi-group/simple
ARG PIP_CERT=/etc/ssl/certs/ca-certificates.crt

# Nexus 的憑證是公司內部 CA 簽的，先把 Wistron 根憑證加進系統信任清單
COPY certs/wistron-root-ca.crt /usr/local/share/ca-certificates/
RUN cat /usr/local/share/ca-certificates/wistron-root-ca.crt >> /etc/ssl/certs/ca-certificates.crt

# apk 改用 Nexus 上對應 Alpine 版本的 mirror，再套用最新的系統安全性更新
RUN ALPINE_VERSION=$(cut -d. -f1,2 /etc/alpine-release) \
    && printf "%s\n" \
        "${NEXUS}/apk-alpine${ALPINE_VERSION}-proxy/main" \
        "${NEXUS}/apk-alpine${ALPINE_VERSION}-proxy/community" \
        > /etc/apk/repositories \
    && apk upgrade --no-cache

WORKDIR /app

COPY requirements.txt .
# 裝完套件就移除 pip：執行時用不到，也避免 pip 本身的弱點被掃到
RUN pip install --no-cache-dir -r requirements.txt && pip uninstall -y pip

COPY main.py .

# build 編號（CI 傳入），/version 會回傳；label 讓 PRD 推廣時能沿用同一個編號
ARG BUILD_ID=local
ENV BUILD_ID=${BUILD_ID}
LABEL build-id=${BUILD_ID}

USER 1000
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
