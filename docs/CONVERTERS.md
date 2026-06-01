# 外部 CAD 转换器接入说明

## 为什么需要外部转换器

STL 已经是三角网格，后端可以直接转 GLB。

STEP 可以用 CadQuery/OCP 做开发版转换，但它更适合中小文件或本地验证。

X_T、SolidWorks 这类格式依赖专有 CAD 内核或商业转换库。正式系统不应该手写解析器，而应该接：

- CAD Exchanger CLI / SDK
- HOOPS Exchange
- Autodesk Platform Services
- 内部 CAD 转换服务
- SolidWorks / NX / Creo 自动化导出服务

## 配置方式

后端通过环境变量读取外部转换命令：

```bash
CAD_EXTERNAL_CONVERTER_COMMAND="/path/to/converter --input {source} --output {output_glb}"
CAD_EXTERNAL_CONVERTER_TIMEOUT_SECONDS=3600
```

可用占位符：

```text
{source}        上传后的源文件路径
{artifact_dir}  当前 asset 的产物目录
{output_glb}    推荐输出 GLB 文件路径
```

转换器只要最终生成以下任意产物，平台就会收集：

- `{artifact_dir}/{源文件名}.glb`
- 任意子目录下的 `tileset.json`

## 示例：CAD Exchanger CLI 形态

实际命令需要按你安装的软件调整，这里只展示形态：

```bash
CAD_EXTERNAL_CONVERTER_COMMAND="/opt/cadexchanger/bin/ExchangerConv -i {source} -e {output_glb}"
```

## 示例：内部 HTTP 转换代理

如果你把 HOOPS / APS / SolidWorks 自动化封装成内部服务，可以写一个本地脚本：

```bash
CAD_EXTERNAL_CONVERTER_COMMAND="python scripts/call_internal_converter.py --input {source} --output {output_glb}"
```

这个脚本内部再去调用 HTTP 服务，平台仍然只关心输出产物。

## 本地 mock 验证

没有商业转换器时，可以用 mock 脚本验证链路：

```bash
CAD_EXTERNAL_CONVERTER_COMMAND="/Users/tomtong/Software/python/cad-preview-platform/backend/.venv/bin/python /Users/tomtong/Software/python/cad-preview-platform/scripts/mock_external_converter.py --input {source} --output {output_glb}"
```

注意：mock 只生成一个占位 GLB，用来验证 job / artifact / 前端加载流程，不代表真实 CAD 转换。

## 当前限制

- 外部命令在后端机器上执行，因此生产环境必须做安全隔离。
- 大文件转换应放到独立 worker，不建议长期使用进程内线程池。
- 3D Tiles 生成需要专业 tiler 或商业转换链路。
- 颜色、装配树、PMI、BOM 等信息需要转换器显式输出，不能靠平台凭空恢复。

