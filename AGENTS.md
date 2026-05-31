# 项目 Agent 指南

## 项目是什么

这是一个 CAD 在线预览平台。目标是支持几百 MB / GB 级 CAD 文件上传、后台转换和浏览器预览。项目采用前后端分离：

- `backend/`：FastAPI 后端，负责上传、任务、产物分发。
- `frontend/`：React 前端，负责用户界面和 3D 预览。

## 开始看哪里

- 先读 `README.md`，了解如何运行。
- 再读 `docs/ARCHITECTURE.md`，了解为什么这样分层。
- 后端入口：`backend/app/main.py`。
- 前端入口：`frontend/src/App.tsx`。

## 硬性规则

- 不要在 HTTP 请求里同步转换大 CAD 文件。
- 不要把大 mesh 作为 JSON 返回给前端。
- 上传源文件、临时文件、转换产物只能放在 storage 目录。
- X_T、SolidWorks 这类专有格式必须走外部转换器，不要手写完整解析器。
- 删除用户上传文件前，必须先有明确的保留策略。

## 常用命令

后端安装：

```bash
cd backend
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

后端启动：

```bash
cd backend
.venv/bin/uvicorn app.main:app --reload --port 8800
```

前端安装：

```bash
cd frontend
npm install
```

前端启动：

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

检查：

```bash
python3.11 scripts/smoke_check.py
```

## 修改时注意

- 改上传逻辑时，要确认仍然是分块写入磁盘。
- 改转换逻辑时，要确认仍然通过 job 状态反馈结果。
- 改前端预览时，要确认加载的是 artifact URL，不是大 JSON。
- 改架构决策时，需要更新 `docs/ARCHITECTURE.md` 或 `docs/decisions/`。
