# Windows CAD/3D Software Download Summary

本文档汇总 Windows 上安装 FastAPI、CadQuery/OpenCascade、FreeCAD、Assimp、Blender 的方式，并说明它们在 CAD 文件上传、解析、转换和网页预览系统里的作用。

## 推荐结论

第一版系统不需要把所有底层库都单独装全。推荐优先安装：

1. Python 3.11
2. FastAPI
3. Miniforge 或 Miniconda
4. CadQuery
5. FreeCAD
6. Blender

暂时可以不单独安装：

1. OpenCascade/OCCT：CadQuery 和 FreeCAD 通常会自带或依赖它。
2. Assimp：主要是 3D 格式导入导出开发库，等确定需要 OBJ/FBX/glTF 等格式批量转换时再装。

## 软件作用总览

| 软件 | 主要用途 | 是否必须 | 在系统里的角色 |
| --- | --- | --- | --- |
| FastAPI | Python 后端 API 框架 | 需要做网页/API 时必须 | 接收上传文件、启动转换任务、返回结果 |
| CadQuery | Python 参数化 CAD 建模库 | 做 Python CAD 处理时推荐 | 生成/处理 STEP 等 CAD 模型 |
| OpenCascade/OCCT | CAD 几何内核 | 通常不单独装 | 底层几何计算、B-Rep、STEP/IGES 读写 |
| FreeCAD | 桌面 CAD 软件，也可脚本化 | 推荐 | 打开检查 CAD 文件，辅助转换 STEP/STL/OBJ 等 |
| Assimp | 3D 模型导入导出库 | 可选 | 处理 OBJ/FBX/DAE/glTF 等网格格式 |
| Blender | 3D 建模、渲染、转换软件 | 推荐 | 查看 GLB/OBJ/STL，做渲染、材质、展示 |

## Windows 安装方式

### 1. Python 3.11

下载地址：

https://www.python.org/downloads/windows/

安装时建议勾选：

- Add python.exe to PATH
- pip

验证：

```powershell
py -3.11 --version
pip --version
```

### 2. FastAPI

用途：

FastAPI 用来写后端服务。比如网页上传 STEP 文件后，FastAPI 负责接收文件、调用 FreeCAD/CadQuery 转换、返回 GLB 或 JSON 结果。

官方文档：

https://fastapi.tiangolo.com/

安装：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install "fastapi[standard]"
```

验证：

```powershell
fastapi --version
python -c "import fastapi; print(fastapi.__version__)"
```

### 3. Miniforge / Miniconda

用途：

CadQuery、OCCT 这类 CAD/Python 包依赖复杂，Windows 上建议用 Conda 环境安装，成功率比直接 pip 更高。

推荐下载 Miniforge：

https://github.com/conda-forge/miniforge/releases

Windows 一般下载：

```text
Miniforge3-Windows-x86_64.exe
```

安装后打开 Miniforge Prompt 或 PowerShell。

### 4. CadQuery

用途：

CadQuery 是 Python CAD 建模库，可以用代码生成、修改、导出 CAD 模型。例如用 Python 生成 STEP 文件。

官方安装文档：

https://cadquery.readthedocs.io/en/stable/installation.html

推荐安装：

```powershell
conda create -n cq python=3.11
conda activate cq
mamba install cadquery
```

如果环境里没有 `mamba`：

```powershell
conda install -c conda-forge mamba
mamba install cadquery
```

验证：

```powershell
python -c "import cadquery as cq; print(cq.__version__)"
```

说明：

通常不需要单独安装 OpenCascade，因为 CadQuery 环境会安装它需要的 OCCT 相关依赖。

### 5. OpenCascade / OCCT

用途：

OpenCascade 是 CAD 几何内核，负责精确几何、曲面、实体、布尔运算、STEP/IGES 读写等底层能力。CadQuery 和 FreeCAD 都依赖类似的几何内核能力。

官方下载：

https://dev.opencascade.org/release

如果只是使用 CadQuery 或 FreeCAD，不建议一开始单独安装 OCCT。

如果你要做 C++ 开发或底层 CAD 解析，可以使用 vcpkg：

```powershell
vcpkg install opencascade
```

### 6. FreeCAD

用途：

FreeCAD 是完整桌面 CAD 软件。它可以打开 STEP、IGES、BREP、STL 等文件，也可以通过 Python 脚本做 CAD 转换。适合用来检查模型、验证转换结果。

官方下载：

https://www.freecad.org/downloads.php

Windows 一般下载：

```text
FreeCAD Windows x86_64 installer
```

安装后验证：

1. 打开 FreeCAD。
2. 用 File -> Open 打开一个 STEP/STL 文件。
3. 确认模型能正常显示。

在自动化系统中的作用：

```text
上传 STEP
    -> 后端调用 FreeCAD Python 或命令行转换
    -> 输出 STL/OBJ/GLB 或中间格式
```

注意：

FreeCAD 对 STEP/STL/IGES 比较友好，但对 SolidWorks 原生 `.sldprt/.sldasm` 和 Parasolid `.x_t/.x_b` 不一定可靠。更稳的做法是让用户先导出 STEP。

### 7. Blender

用途：

Blender 更偏网格建模、渲染、材质和动画，不是传统工程 CAD 软件。它适合检查 GLB、OBJ、STL 的显示效果，也可以做模型压缩、材质处理和渲染。

官方下载：

https://www.blender.org/download/

Windows 安装说明：

https://docs.blender.org/manual/en/latest/getting_started/installing/windows.html

也可以用 winget：

```powershell
winget install BlenderFoundation.Blender
```

在系统中的作用：

```text
CAD/STEP 转出 GLB/OBJ/STL
    -> Blender 检查、优化、渲染
    -> 网页用 Three.js 显示 GLB
```

### 8. Assimp

用途：

Assimp 是 3D 网格格式导入导出库，支持 OBJ、FBX、DAE、3DS、glTF 等很多格式。它更适合开发者集成到程序里，不是普通用户每天打开的软件。

官方仓库：

https://github.com/assimp/assimp

Windows 推荐通过 vcpkg 安装：

```powershell
vcpkg install assimp
```

如果只是第一版做 STEP 上传和 GLB 网页预览，Assimp 可以先不装。

## 关于网页预览 CAD 文件

浏览器通常不能直接渲染 STEP、x_t、sldprt 这类 CAD 实体文件。实际系统通常这样做：

```text
用户上传 CAD 文件
    -> 后端保存原始文件
    -> 后端用 FreeCAD/CadQuery/OpenCascade 解析或转换
    -> 生成 GLB/STL/OBJ 等网页可显示格式
    -> 前端用 Three.js/Babylon.js/model-viewer 显示
```

GLB 是网页显示用的可视化副本，不应该替代原始 CAD 文件。

原始 CAD 文件用于：

- 精确几何
- 二次 CAD 编辑
- 工程测量
- 加工制造
- 后端再次转换

GLB 用于：

- 网页旋转预览
- 展示外观
- 选中零件
- 批注和协作
- 快速加载

## 对 x_t / SolidWorks 文件的建议

`.x_t` 是 Parasolid 文本格式，`.x_b` 是 Parasolid 二进制格式。它们不是普通网页或 Three.js 可以直接读取的格式。

`.sldprt` 和 `.sldasm` 是 SolidWorks 原生格式，解析难度更高，通常需要 SolidWorks 本身、商业 CAD SDK 或先导出 STEP。

第一版建议支持：

- STEP / STP
- STL
- OBJ
- GLB

暂时不要承诺直接支持：

- x_t / x_b
- sldprt / sldasm

更稳的业务流程：

```text
SolidWorks / NX / 专业 CAD 软件
    -> 导出 STEP
    -> 上传 STEP
    -> 后端解析 STEP
    -> 生成 JSON + GLB
    -> 网页显示 GLB
```

## 推荐安装顺序

1. 安装 Python 3.11。
2. 安装 FastAPI。
3. 安装 Miniforge。
4. 用 Miniforge 安装 CadQuery。
5. 安装 FreeCAD。
6. 安装 Blender。
7. 等确实需要格式转换开发时，再安装 Assimp。
8. 等确实需要底层 C++ CAD 开发时，再单独安装 OpenCascade/OCCT。

## 最小可行组合

如果只是先验证 CAD 上传、转换和网页预览，最小组合是：

```text
Windows 开发机：
- Python 3.11
- FastAPI
- Miniforge
- CadQuery
- FreeCAD

前端：
- Three.js
```

这个组合可以先完成：

```text
上传 STEP
    -> 后端保存
    -> 转成 GLB/STL
    -> 网页预览
    -> 保留原始 STEP 做精确数据来源
```

