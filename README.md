# CAD 在线预览平台

这是一个面向 CAD 大文件在线预览的前后端分离项目。它的目标不是让浏览器直接解析 `.step/.x_t/.sldprt` 源文件，而是把源文件交给后端保存、排队、转换，再把浏览器友好的 `GLB / 3D Tiles / metadata.json` 作为产物分发给前端。

```text
用户上传 CAD 文件
  -> FastAPI 后端分块保存源文件
  -> 后台任务提取 metadata.json
  -> 后台任务转换 GLB 或 3D Tiles
  -> React 前端按 URL 加载预览产物
```

## 功能说明

- 上传：支持大文件分块落盘，避免一次性把几百 MB / GB 文件读进内存。
- 任务：上传后创建 `asset` 和 `job`，前端轮询任务状态。
- 预览：浏览器优先加载 `GLB`，后续可扩展到 `3D Tiles`。
- 结构化数据：每个上传文件都会生成 `metadata.json`。
- STL：可直接统计网格并转换为 GLB。
- STEP / STP：可用 CadQuery/OCP 开发版转换器生成 GLB，并提取 HEADER、实体统计、颜色、产品名。
- X_T / SolidWorks：需要外部 CAD 转换器；未配置时会明确显示阻塞原因，但仍会尝试提取可读 metadata。
- 转换器状态：前端会显示当前环境哪些转换器可用。

## 需要安装的软件

必需：

- Git：管理代码版本。
- Python 3.11：运行 FastAPI 后端和 CAD 处理依赖。
- Node.js 20 或更新版本：运行 React / Vite 前端。
- npm：安装前端依赖，通常随 Node.js 一起安装。

项目依赖：

- 后端 Python 包来自 `backend/requirements.txt`。
- 前端 npm 包来自 `frontend/package.json`。

可选：

- CAD Exchanger / HOOPS Exchange / Autodesk Platform Services 代理 / 内部 CAD 转换服务：用于生产处理 X_T、SolidWorks、超大 STEP 和 3D Tiles。
- 本地 mock 转换器：没有商业转换器时，可用 `scripts/mock_external_converter.py` 验证外部转换链路。

## 快速启动

下面假设项目路径是：

```bash
cd /Users/tomtong/Software/python/cad-preview-platform
```

### 1. 启动后端

```bash
cd /Users/tomtong/Software/python/cad-preview-platform
cp .env.example .env
cd backend
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd ..
backend/.venv/bin/uvicorn app.main:app --app-dir backend --reload --port 8800
```

后端地址：

```text
http://127.0.0.1:8800
```

健康检查：

```bash
curl http://127.0.0.1:8800/api/health
```

### 2. 启动前端

打开另一个终端：

```bash
cd /Users/tomtong/Software/python/cad-preview-platform/frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

前端地址：

```text
http://127.0.0.1:5173
```

### 3. 验证项目

```bash
cd /Users/tomtong/Software/python/cad-preview-platform
python3.11 scripts/smoke_check.py
cd frontend
npm run build
```

`npm run build` 如果提示 chunk 较大，通常是因为 `<model-viewer>` 体积较大；这不影响当前开发验证。

## 外部转换器配置

复制 `.env.example` 后，可以在 `.env` 里配置：

```bash
CAD_STORAGE_DIR=backend/storage
CAD_DATABASE_PATH=backend/storage/cad_preview.sqlite3
CAD_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
CAD_EXTERNAL_CONVERTER_COMMAND=
CAD_EXTERNAL_CONVERTER_TIMEOUT_SECONDS=3600
```

外部转换器命令支持这些占位符：

```text
{source}        上传后的源文件路径
{artifact_dir}  当前 asset 的产物目录
{output_glb}    推荐输出 GLB 文件路径
```

示例：

```bash
CAD_EXTERNAL_CONVERTER_COMMAND="/opt/cad-converter/bin/convert --input {source} --output {output_glb}"
```

没有商业转换器时，可用 mock 验证链路：

```bash
CAD_EXTERNAL_CONVERTER_COMMAND="/Users/tomtong/Software/python/cad-preview-platform/backend/.venv/bin/python /Users/tomtong/Software/python/cad-preview-platform/scripts/mock_external_converter.py --input {source} --output {output_glb}"
```

## API 说明

- `POST /api/assets`：上传源文件，并创建转换任务。
- `GET /api/assets/{asset_id}`：查看源文件信息。
- `GET /api/jobs/{job_id}`：查看转换任务状态。
- `GET /api/assets/{asset_id}/artifacts`：查看生成的产物列表。
- `GET /api/artifacts/{asset_id}/{filename}`：下载或预览产物文件。
- `GET /api/converters`：查看当前转换器可用状态。

## 结构化数据提取

上传文件后，后台任务会先生成 `metadata.json`。它不是完整 CAD 内核解析结果，而是从源文件中安全提取“能明文读出来、能用于业务判断”的信息：

- STL：编码、三角面数量、顶点引用数量、包围盒。
- STEP / STP：`HEADER` 字段、实体类型统计、`COLOUR_RGB` 颜色、产品名。
- X_T：前 80 行明文片段、行数、数字 token 估算、常见关键词。
- GLB：GLB 版本、chunk、mesh / material 数量。
- SolidWorks：标记为需要外部转换器。

详细说明见 `docs/METADATA.md`。

## 项目结构

```text
backend/
  app/api/                         HTTP 接口
  app/core/                        配置读取
  app/models/                      API 数据模型
  app/services/converters/         GLB / STEP / STL / 外部转换器适配器
  app/services/metadata_extractors/结构化数据提取器，每种格式独立一个文件
  app/services/storage.py          上传文件保存和格式识别
  app/services/repository.py       SQLite 读写
  app/workers/                     后台任务入口

frontend/
  src/api/                         调后端 API
  src/components/                  页面组件
  src/hooks/                       上传、轮询、metadata 加载流程
  src/utils/                       格式化工具
  src/styles/                      页面样式
  src/App.tsx                      页面组装入口

docs/
  ARCHITECTURE.md                  架构说明
  CONVERTERS.md                    外部转换器接入说明
  LEARNING_PYTHON.md               给前端开发者的 Python 学习导览
  METADATA.md                      结构化数据提取说明
  decisions/                       关键技术决策记录
```

## 如果你是前端开发者

建议先读 `docs/LEARNING_PYTHON.md`。它会按前端视角解释：

- FastAPI 和 Express/Koa 怎么类比。
- Pydantic 模型和 TypeScript interface 怎么类比。
- Python 的 `.venv / pip / requirements.txt` 和 Node 的 `node_modules / npm / package.json` 怎么类比。
- 当前项目应该按什么顺序读代码。

## 维护原则

- HTTP 上传接口只负责保存文件和创建任务，不同步转换大 CAD 文件。
- 前端只加载 artifact URL，不把大型 mesh 塞进 JSON。
- 新增源格式时，优先增加一个独立 extractor 或 converter，不把逻辑堆回主流程。
- X_T、SolidWorks 等专有格式必须走外部转换器，不手写完整 B-Rep 解析器。
- 生产环境需要把 SQLite、本地磁盘、进程内线程池替换为 PostgreSQL、对象存储和独立任务队列。

## 面向大文件的下一步

- 用 Redis + Celery/RQ/Arq 替换进程内线程池。
- 用 S3 / MinIO / OSS 替换本地磁盘存储。
- 接入商业 CAD 转换器，处理大文件 STEP、X_T、SolidWorks。
- 生成 GLB 时加入 Draco / Meshopt 压缩。
- 对超大装配生成 3D Tiles 和多级 LOD。
- 加入用户权限、配额、任务取消、失败重试、文件保留策略。
