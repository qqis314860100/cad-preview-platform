from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from app.services.conversion import run_conversion


# 本地开发先用线程池模拟后台任务。
# 生产环境应替换成独立 worker 队列，例如 Celery/RQ/Arq + Redis。
executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cad-converter")


def enqueue_conversion(job_id: str, asset_id: str) -> None:
    executor.submit(run_conversion, job_id, asset_id)
