# 架构说明

## 总体目标

这个项目的目标不是“在浏览器里直接解析 CAD 源文件”，而是构建一条适合大文件的在线预览链路：

```text
源 CAD 文件
  -> 后端保存
  -> 后台转换
  -> 生成浏览器友好的预览产物
  -> 前端加载产物
```

浏览器适合加载 GLB、3D Tiles 这种图形产物，不适合直接吃几百 MB 的 STEP、X_T、SolidWorks 源文件。

## 模块边界

```text
frontend/
  React 前端。负责上传、显示任务状态、轮询转换结果、加载 3D 预览。

backend/app/api/
  HTTP 接口层。只接收请求、返回响应，不直接写 CAD 转换逻辑。

backend/app/services/
  业务服务层。负责文件存储、数据库访问、产物记录、转换调度。

backend/app/services/converters/
  预览产物转换器。每个转换器只负责一种或一类输入格式。

backend/app/services/metadata_extractors/
  结构化数据提取器。每种格式独立一个文件，避免把 STEP、STL、X_T 规则混在一起。

backend/app/workers/
  后台任务层。当前用线程池做本地开发版本，后续可替换成 Celery/RQ。

backend/storage/
  运行时数据目录。保存上传文件、转换产物和 SQLite 数据库，不提交到 git。
```

## 数据流

```text
用户上传文件
  -> 后端分块写入 backend/storage/assets/{asset_id}/source/
  -> 数据库写入 asset 记录
  -> 数据库写入 job 记录
  -> 后台 worker 先生成 metadata.json
  -> 后台 worker 开始转换
  -> 转换器写入 backend/storage/assets/{asset_id}/artifacts/
  -> 前端轮询 job 状态
  -> 前端拿 artifact URL 加载 GLB / 3D Tiles / metadata.json
```

## 产物优先策略

正式系统不应该把大量三角网格塞进 JSON 响应。正确做法是生成“文件产物”：

- 小模型：生成 `.glb`。
- 大模型：生成 `tileset.json` 和 3D Tiles 分块文件。
- 元数据：生成 `metadata.json`，例如 STEP HEADER、实体类型统计、颜色、STL 网格统计。

这样前端可以按 URL 加载，而不是一次性解析巨大响应。

## 结构化数据策略

结构化数据不是完整 CAD 几何重建。它的目标是回答这些问题：

- 这个文件是什么格式、大小、什么时候被处理？
- STEP 里声明了哪些 `FILE_SCHEMA`、产品名、颜色和主要实体类型？
- STL 有多少三角面，模型大概占多大空间？
- X_T 明文里能看到哪些片段，但为什么仍需要 Parasolid 兼容转换器？

因此后台 job 会先写出 `metadata.json`，再运行 GLB / 3D Tiles 转换。即使几何转换被阻塞，前端仍然可以展示已提取的结构化数据，便于判断下一步应该接哪个外部转换器。

## 转换器策略

后端把转换器当成“可替换适配器”：

```text
本地开源转换器
商业 CLI 转换器
云转换服务
CAD 软件自动化服务
```

当前已实现：

- STL -> GLB：本地转换，适合验证 artifact-first 流程。
- STEP/STP -> GLB：CadQuery/OCP 开发版转换器，适合本地验证和中小文件 fallback。

计划接入：

- X_T -> GLB / STEP：CAD Exchanger、HOOPS Exchange、Parasolid 兼容转换器。
- SolidWorks -> GLB / STEP：商业转换器或 SolidWorks 自动化服务。
- 大文件 STEP/STP -> 3D Tiles：CAD Exchanger、HOOPS Exchange 或专门 tiler 服务。

外部转换器接入细节见 `docs/CONVERTERS.md`。

## 为什么不能同步转换

几百 MB / GB 级 CAD 文件转换可能需要几十秒到数分钟，内存可能达到数 GB。如果放在 HTTP 请求里同步执行，会带来：

- 请求超时。
- 用户无法看到进度。
- 转换失败无法重试。
- 同一个文件重复上传重复转换。
- 服务进程容易被单个大文件拖死。

所以转换必须是 job。

## 后续生产化清单

- 上传改成分片上传和断点续传。
- 本地 storage 替换成对象存储。
- SQLite 替换成 PostgreSQL。
- 线程池替换成独立 worker 队列。
- 产物加 CDN 或静态文件服务。
- 增加 3D Tiles、LOD、压缩、权限、配额、审计日志。
