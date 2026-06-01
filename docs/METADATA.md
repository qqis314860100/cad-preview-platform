# 结构化数据提取说明

## 这一步解决什么问题

在线预览需要 GLB 或 3D Tiles，但业务系统通常还需要“可读数据”：

- 文件是什么格式、大小是多少。
- STEP 里声明了什么 schema、产品名和颜色。
- STL 有多少三角面、包围盒大概多大。
- X_T 里能看到哪些明文片段，以及为什么不能靠平台直接还原完整几何。

所以后台任务会为每个上传文件生成一个 `metadata.json` 产物。前端把它作为普通 artifact 加载和展示。

## 存放位置

```text
backend/storage/assets/{asset_id}/artifacts/metadata.json
```

数据库里的 artifact 类型是：

```text
metadata
```

前端通过接口拿到 URL：

```text
GET /api/assets/{asset_id}/artifacts
GET /api/artifacts/{asset_id}/metadata.json
```

## 当前能提取什么

### STL

- ASCII / Binary 编码判断。
- 三角面数量。
- 顶点引用数量。
- 包围盒 `min/max`。

STL 本身就是三角网格，所以这部分统计比较可靠。

### STEP / STP

- `HEADER` 中的 `FILE_DESCRIPTION`、`FILE_NAME`、`FILE_SCHEMA`。
- `DATA` 中的实体类型统计，例如 `ADVANCED_FACE`、`CARTESIAN_POINT`。
- `COLOUR_RGB` 颜色列表。
- `PRODUCT` 产品名。

注意：这些是轻量结构化提取，不等于完整 OpenCascade / Parasolid 级别的 B-Rep 拓扑解析。

### Parasolid XT

- 前 80 行明文片段。
- 行数。
- 数字 token 数量估算。
- 高频英文关键词。

注意：X_T 是 Parasolid 专有格式。`metadata.json` 可以帮助判断文件内容，但完整几何仍需要 Parasolid 兼容转换器或商业 CAD 转换库。

### GLB

- GLB 版本。
- chunk 列表。
- glTF JSON 中的 scene / mesh / material 数量。

### SolidWorks

当前只标记为“需要外部转换器”。`.sldprt/.sldasm` 的几何和装配数据不应该由本项目手写解析。

## 为什么不把所有数据直接放进接口响应

大文件场景下，接口响应要保持小而稳定。正确做法是：

```text
接口返回 artifact 列表
前端按需加载 metadata.json
前端按需加载 GLB / 3D Tiles
```

这样未来接对象存储、CDN、权限签名 URL 时，接口模型不用大改。

## 下一步可以扩展

- 把 `metadata.json` 拆成“基础元数据”和“业务元数据”两类。
- 外部转换器输出装配树、BOM、PMI、材质贴图，再由平台登记为独立 artifact。
- 为 STEP 实体统计加白名单和阈值，避免超大文件扫描时间过长。
- 把 metadata 写入 PostgreSQL / 搜索引擎，支持按产品名、颜色、格式、尺寸检索。
