import os

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def hello():
    return {"message": "Hello World"}


@app.get("/version")
def version():
    # BUILD_ID：build image 時寫入；APP_VERSION：部署時由 helm 設定（例如 v1.0.0）
    return {
        "build": os.getenv("BUILD_ID", "local"),
        "version": os.getenv("APP_VERSION", "unknown"),
    }
