# ---------- 第一階段：安裝套件並 build ----------
FROM node:22-alpine AS build

# runner 不能連外網，npm 套件改從公司 Nexus 下載
ARG NEXUS=https://nexusoss.wistron.com/repository
ARG NPM_REGISTRY=${NEXUS}/npm-group/

# Nexus 的憑證是公司內部 CA 簽的，讓 Node.js 信任 Wistron 根憑證
COPY certs/wistron-root-ca.crt /usr/local/share/ca-certificates/
ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/wistron-root-ca.crt

WORKDIR /app

# 版本和 package.json 的 packageManager 一致
RUN npm install -g pnpm@10.5.1 --registry=${NPM_REGISTRY}

# 先只複製套件清單：程式碼改了但套件沒變時，可以沿用這層的 cache
COPY package.json pnpm-lock.yaml ./
RUN pnpm config set registry ${NPM_REGISTRY} && pnpm install --frozen-lockfile

COPY . .

# NEXT_PUBLIC_* 會在 build 時寫死進前端，所以只放「所有環境都一樣」的值：
# - /api：瀏覽器打同網域的 /api，再由 Next.js 轉給後端（後端網址在執行時用 LANGGRAPH_API_URL 設定）
# - agent：server/langgraph.json 裡 graph 的名稱
# - /schedule-api：排程 API 一樣走同網域 proxy（Scheduler 網址在執行時用 SCHEDULE_API_URL 設定）
ENV NEXT_PUBLIC_API_URL=/api \
    NEXT_PUBLIC_SCHEDULE_API_URL=/schedule-api \
    NEXT_PUBLIC_ASSISTANT_ID=agent \
    NEXT_TELEMETRY_DISABLED=1
RUN pnpm build

# ---------- 第二階段：只放執行需要的檔案 ----------
FROM node:22-alpine

ARG NEXUS=https://nexusoss.wistron.com/repository

COPY certs/wistron-root-ca.crt /usr/local/share/ca-certificates/
RUN cat /usr/local/share/ca-certificates/wistron-root-ca.crt >> /etc/ssl/certs/ca-certificates.crt

# apk 改用 Nexus 上對應 Alpine 版本的 mirror，再套用最新的系統安全性更新
RUN ALPINE_VERSION=$(cut -d. -f1,2 /etc/alpine-release) \
    && printf "%s\n" \
        "${NEXUS}/apk-alpine${ALPINE_VERSION}-proxy/main" \
        "${NEXUS}/apk-alpine${ALPINE_VERSION}-proxy/community" \
        > /etc/apk/repositories \
    && apk upgrade --no-cache

# 執行時用不到 npm／corepack，移除可以減少 Harbor 掃到的弱點
RUN rm -rf /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/corepack \
    /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack

WORKDIR /app

COPY --from=build --chown=1000:1000 /app/.next/standalone ./
COPY --from=build --chown=1000:1000 /app/.next/static ./.next/static

# build 編號（CI 傳入），label 讓 PRD 推廣時能沿用同一個編號
ARG BUILD_ID=local
ENV BUILD_ID=${BUILD_ID}
LABEL build-id=${BUILD_ID}

# LANGGRAPH_API_URL／SCHEDULE_API_URL：後端在 k8s 裡的網址，部署時設定（例如 http://mo-agentchat-server:8000）
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000

# node image 內建的 node 使用者就是 uid 1000
USER 1000
EXPOSE 3000

CMD ["node", "server.js"]
