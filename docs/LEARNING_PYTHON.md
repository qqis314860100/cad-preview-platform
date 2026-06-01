# 给前端开发者的 Python 学习导览

这份文档不是 Python 语法大全，而是帮助你用当前项目入门 Python 后端。你可以按下面顺序读代码，不需要一次看完所有文件。

## 先建立类比

```text
前端 / Node                  Python / FastAPI
------------------------------------------------------------
package.json                 requirements.txt
node_modules/                .venv/
npm install                  pip install -r requirements.txt
Express/Koa app              FastAPI app
TypeScript interface         Pydantic BaseModel
fetch("/api")                @router.get / @router.post
setInterval 轮询             前端定时请求 job 状态
dist 构建产物                artifacts 预览产物
localStorage / IndexedDB     SQLite 本地数据库
```

## 推荐阅读顺序

### 1. 应用入口

文件：

```text
backend/app/main.py
```

你要理解：

- `FastAPI(...)` 创建后端应用。
- `CORSMiddleware` 允许前端 `5173` 端口调用后端 `8800` 端口。
- `include_router(router, prefix="/api")` 把所有接口挂到 `/api` 下。

### 2. API 路由

文件：

```text
backend/app/api/routes.py
```

你要理解：

- `@router.post("/assets")` 类似定义一个 POST 接口。
- `UploadFile` 是 FastAPI 接收上传文件的类型。
- 上传接口只保存文件和创建任务，不直接做耗时转换。
- 前端拿到 `job_id` 后，通过 `/api/jobs/{job_id}` 轮询进度。

### 3. 数据模型

文件：

```text
backend/app/models/schemas.py
```

你要理解：

- `BaseModel` 类似 TypeScript interface，但它运行时也会校验数据。
- `StrEnum` 用来限制状态字段只能是固定值。
- `AssetOut`、`JobOut`、`ArtifactOut` 就是接口返回结构。

### 4. 文件上传和存储

文件：

```text
backend/app/services/storage.py
```

你要理解：

- 大文件不能一次性读进内存，所以要分块保存。
- `Path` 是 Python 处理文件路径的标准方式。
- `source/` 放原始文件，`artifacts/` 放后端生成的结果。

### 5. 数据库

文件：

```text
backend/app/services/repository.py
```

你要理解：

- SQLite 是一个本地单文件数据库，适合学习和原型。
- `assets` 表记录上传文件。
- `jobs` 表记录后台任务。
- `artifacts` 表记录生成的 GLB、metadata.json 等产物。

### 6. 后台任务

文件：

```text
backend/app/workers/queue.py
backend/app/services/conversion.py
```

你要理解：

- 上传接口不能一直等 CAD 转换结束。
- `ThreadPoolExecutor` 让转换在后台线程执行。
- `conversion.py` 是任务主流程：提取 metadata -> 找转换器 -> 写产物 -> 更新状态。

### 7. 结构化数据提取

目录：

```text
backend/app/services/metadata_extractors/
```

你要理解：

- `service.py` 是统一入口。
- `stl.py` 处理 STL。
- `step.py` 处理 STEP。
- `xt.py` 处理 X_T 的明文片段。
- 这里做的是“轻量可读信息提取”，不是完整 CAD 内核解析。

### 8. 前端如何串起来

文件：

```text
frontend/src/hooks/useCadUpload.ts
frontend/src/api/client.ts
```

你要理解：

- `client.ts` 是前端 API 封装。
- `useCadUpload.ts` 管理上传、轮询、产物列表、metadata 加载。
- 页面组件只负责展示，不直接关心接口细节。

## 可以练习的小任务

这些任务适合边学边改：

1. 给 `/api/health` 增加版本号字段。
2. 给上传接口增加文件后缀白名单错误提示。
3. 新增 `GET /api/assets`，返回最近上传的文件列表。
4. 给 `metadata.json` 增加文件 MD5。
5. 在前端 artifact 表里给 `metadata.json` 增加“查看”按钮。
6. 把 job 进度文案改成中文。

## 学习时不要急着懂所有细节

这个项目里有 CAD、文件、数据库、后台任务、前端轮询。初学 Python 时，不需要一次把它们全吃透。

建议先抓住主线：

```text
前端上传文件
  -> 后端保存文件
  -> 数据库写 asset/job
  -> 后台线程转换
  -> 数据库写 artifacts
  -> 前端轮询并展示
```

只要这条线理解了，后面的 STL、STEP、X_T、GLB 都只是不同格式的处理细节。
