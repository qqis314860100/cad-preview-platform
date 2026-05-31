#!/usr/bin/env bash
set -euo pipefail

# 这个脚本只负责提示两个服务如何启动。
# 前后端分离项目通常需要两个终端：一个跑 API，一个跑页面。

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cat <<EOF
请分别在两个终端启动：

后端：
  cd "$ROOT/backend"
  .venv/bin/uvicorn app.main:app --reload --port 8800

前端：
  cd "$ROOT/frontend"
  npm run dev -- --host 127.0.0.1 --port 5173

打开：
  http://127.0.0.1:5173
EOF
