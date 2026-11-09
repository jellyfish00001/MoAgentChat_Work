# build context 是 scheduler/（CI：docker build -f scheduler/AiPrepare.Scheduler.Job/Dockerfile ./scheduler）
# ---------- 第一階段：restore／publish ----------
FROM harbor.wistron.com/base_image/dotnetsdk:10.0 AS build

# runner 不能連外網，NuGet 改從公司 Nexus 下載；Nexus 憑證是公司內部 CA 簽的
ARG NUGET_SOURCE=https://nexusoss.wistron.com/repository/nuget.org-proxy/index.json
COPY certs/wistron-root-ca.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates

WORKDIR /src
COPY . .
RUN dotnet publish AiPrepare.Scheduler.Job/AiPrepare.Scheduler.Job.csproj \
    -c Release -o /app --source ${NUGET_SOURCE} -p:UseAppHost=false

# ---------- 第二階段：只放執行需要的檔案 ----------
FROM harbor.wistron.com/base_image/aspnet:10.0

WORKDIR /app
COPY --from=build /app ./

# build 編號（CI 傳入），label 讓 PRD 推廣時能沿用同一個編號
ARG BUILD_ID=local
ENV BUILD_ID=${BUILD_ID}
LABEL build-id=${BUILD_ID}

# SQLite 放 /data（k8s 掛 PVC，與 Api 同一個檔）；Program.cs 讀 urls（ASPNETCORE_URLS）決定監聽位址
ENV ASPNETCORE_URLS=http://+:8080 \
    SCHEDULE_DB_PATH=/data/schedules.sqlite

USER 1000
EXPOSE 8080

ENTRYPOINT ["dotnet", "AiPrepare.Scheduler.Job.dll"]
