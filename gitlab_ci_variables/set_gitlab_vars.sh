#!/usr/bin/env bash
# 把 gitlab_ci_variables/.env 裡的 HARBOR_* 變數一次寫進 GitLab CI/CD Variables（已存在就更新）
#
# 用法：
#   cp gitlab_ci_variables/.env.example gitlab_ci_variables/.env   # 第一次使用，填好 .env
#   bash gitlab_ci_variables/set_gitlab_vars.sh
set -euo pipefail

ENV_FILE="$(dirname "$0")/.env"
[ -f "$ENV_FILE" ] || { echo "找不到 $ENV_FILE，請先 cp gitlab_ci_variables/.env.example gitlab_ci_variables/.env 並填值"; exit 1; }
set -a; source "$ENV_FILE"; set +a

# 沒填的機密資料，執行時再問（輸入不會顯示）
[ -n "${GITLAB_TOKEN:-}" ]    || { read -rsp "GITLAB_TOKEN: " GITLAB_TOKEN; echo; }
[ -n "${HARBOR_PASSWORD:-}" ] || { read -rsp "HARBOR_PASSWORD: " HARBOR_PASSWORD; echo; }

API="$GITLAB_URL/api/v4/projects/${GITLAB_PROJECT//\//%2F}/variables"

set_var() { # key value
  local masked=false
  [[ $1 =~ PASSWORD|TOKEN|SECRET ]] && masked=true
  local args=(-s -o /dev/null -w "%{http_code}" -H "PRIVATE-TOKEN: $GITLAB_TOKEN"
    --form "key=$1" --form "value=$2" --form "masked=$masked" --form "protected=false"
    --form "raw=true") # robot 帳號含 $，不 raw 會被 GitLab 當成變數展開
  local code
  code=$(curl -X PUT "${args[@]}" "$API/$1")              # 先嘗試更新
  [ "$code" = "404" ] && code=$(curl -X POST "${args[@]}" "$API")  # 不存在就新增
  case "$code" in 200|201) echo "✅ $1" ;; *) echo "❌ $1（HTTP $code）" ;; esac
}

for key in HARBOR_URL HARBOR_PROJECT HARBOR_USER HARBOR_PASSWORD; do
  [ -n "${!key:-}" ] || { echo "❌ $key 沒有填，請檢查 $ENV_FILE"; continue; }
  set_var "$key" "${!key}"
done
