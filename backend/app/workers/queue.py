from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from app.services.conversion import run_conversion


# 本地开发先用线程池模拟后台任务。
#
# 为什么不用上传接口直接转换？
# - CAD 转换可能需要几十秒甚至几分钟；
# - HTTP 请求一直不返回，前端和网关都容易超时；
# - 用户也看不到进度。
#
# ThreadPoolExecutor 可以先把“上传”和“转换”拆开：上传接口快速返回 job_id，
# 转换任务在另一个线程里慢慢执行。生产环境应替换成 Celery/RQ/Arq + Redis。
executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cad-converter")


def enqueue_conversion(job_id: str, asset_id: str) -> None:
    """把转换任务提交到后台线程池。

    submit 不会等待 run_conversion 执行完成，它只是把任务排进去。
    这和前端 setTimeout / Promise 异步执行有点像：先安排任务，当前函数继续返回。
    """

    executor.submit(run_conversion, job_id, asset_id)
