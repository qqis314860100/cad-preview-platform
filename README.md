# CAD 在线预览平台

这是一个面向“几百 MB / GB 级 CAD 文件在线预览”的工程化项目骨架。它替代原来的同步解析 demo，改成更接近生产系统的前后端分离架构。

核心思路：

```text
React 前端
  -> FastAPI 后端
  -> 流式上传并保存源文件
  -> 后台转换任务
  -> 生成预览产物：当前先支持 GLB，后续扩展 3D Tiles
  -> 浏览器按 URL 加载预览产物
```

## 当前已经实现

- 前后端分离：`frontend/` 是 React，`backend/` 是 FastAPI。
- 上传接口会把文件分块写入磁盘，不再一次性塞进内存。
- 后端会创建 asset 和 job，转换任务在后台线程执行。
- STL 文件可以转换成 GLB 预览产物。
- STEP / STP 文件可以通过 CadQuery/OCP 开发版转换器生成 GLB。
- X_T / SolidWorks 文件会进入明确的“需要外部 CAD 转换器”状态。
- 前端支持上传、上传进度、任务轮询、产物列表、GLB 预览。
- 项目已准备好 Git、架构文档和基础检查脚本。

## 为什么要这样改

原型项目把上传、解析、转换、预览数据返回都放在一次请求里。这对小文件能跑，但遇到几百 MB 或 GB 级 CAD 会有问题：

- 请求容易超时。
- Python 进程内存容易爆。
- 前端接收巨大 JSON 会卡死。
- 没法做任务进度、重试、取消、排队。
- 后续很难扩展到 3D Tiles 分块加载。

所以正式架构要把“文件上传”和“转换预览”拆开：

```text
上传：只负责安全落盘
转换：后台慢慢处理
预览：加载转换后的 GLB / 3D Tiles 产物
```

## 运行后端

```bash
cd /Users/tomtong/Software/python/cad-preview-platform/backend
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --port 8800
```

后端地址：

```text
http://127.0.0.1:8800
```

## 运行前端

```bash
cd /Users/tomtong/Software/python/cad-preview-platform/frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

前端地址：

```text
http://127.0.0.1:5173
```

## API 说明

- `POST /api/assets`：上传源文件，并创建转换任务。
- `GET /api/assets/{asset_id}`：查看源文件信息。
- `GET /api/jobs/{job_id}`：查看转换任务状态。
- `GET /api/assets/{asset_id}/artifacts`：查看生成的预览产物。
- `GET /api/artifacts/{asset_id}/{filename}`：下载或预览产物文件。

## 面向大文件的下一步

当前第一版已经把架构切对，但还不是完整生产系统。继续往生产走，需要补这些能力：

- 用 Redis + Celery/RQ/Arq 替换进程内线程池。
- 用 S3 / MinIO / OSS 替换本地磁盘存储。
- 接入商业 CAD 转换器，处理大文件 STEP、X_T、SolidWorks。
- 生成 GLB 时加入 Draco / Meshopt 压缩。
- 对超大装配生成 3D Tiles 和多级 LOD。
- 加入用户权限、配额、任务取消、失败重试、文件保留策略。

## 文件结构

```text
backend/
  app/api/          HTTP 接口
  app/services/     上传、存储、转换、数据库逻辑
  app/workers/      后台任务入口

frontend/
  src/api/          调后端 API
  src/App.tsx       主界面
  src/styles/       页面样式

docs/
  ARCHITECTURE.md   架构说明
  decisions/        关键技术决策记录
```
