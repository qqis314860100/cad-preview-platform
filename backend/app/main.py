from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.services.repository import init_db


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用。

    对前端同学可以这样类比：
    - FastAPI 类似 Express/Koa 的 app 实例；
    - middleware 类似 Express 的 app.use(...)；
    - include_router 类似把一组路由挂到 /api 前缀下。

    这里写成函数，而不是直接在全局堆配置，是为了以后测试时也能重新创建
    一个干净的 app。
    """

    # 确保存储目录存在。用户上传的源文件、转换产物、SQLite 数据库都放在这里。
    # parents=True 表示中间目录不存在也一起创建；exist_ok=True 表示目录已存在时不报错。
    settings.storage_dir.mkdir(parents=True, exist_ok=True)

    # 初始化 SQLite 表。CREATE TABLE IF NOT EXISTS 是幂等的：
    # 第一次启动会建表，后续启动发现表已存在就跳过。
    init_db()

    app = FastAPI(title="CAD Preview Platform API", version="0.1.0")

    # CORS 解决“前端 5173 端口调用后端 8800 端口”时的浏览器跨域限制。
    # 这不是后端访问不到前端，而是浏览器为了安全拦截跨源请求。
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 所有业务 API 都统一挂到 /api 下，例如 /api/assets、/api/jobs/{id}。
    # 这样前端代理、网关转发和未来版本管理都会更清晰。
    app.include_router(router, prefix="/api")
    return app


# uvicorn 启动时会寻找这个 app 变量：
#   uvicorn app.main:app --reload --port 8800
# 其中 app.main 表示 backend/app/main.py，最后的 app 就是下面这个对象。
app = create_app()
