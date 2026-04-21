"""端到端 HTTP 冒烟：创建 Job → 上传 ZIP → 轮询任务。

验证 slowapi `_inject_headers` 在成功路径与失败路径都能拿到合法的 Response 对象。
此脚本需要本地 uvicorn 已在 127.0.0.1:8000 监听，且 Postgres 容器已就绪。
"""
import io
import os
import sys
import time
import zipfile

import httpx as requests  # noqa: N812 (复用 requests 式调用风格)

BASE = os.environ.get("FALCON_BASE", "http://127.0.0.1:8000")
ORIGIN = "http://localhost:3000"


def _make_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("candidate1/resume.txt", "张三 13800138000 zhangsan@x.com 5 年 Python 经验")
    return buf.getvalue()


def main() -> int:
    jd = (
        "Python 后端工程师\n要求：本科，3-5 年经验，熟悉 FastAPI / Postgres / Docker"
    )
    with requests.Client(timeout=60.0) as client:
        r = client.post(
            f"{BASE}/api/jobs",
            json={"raw_jd": jd, "title": "HTTP 冒烟职位"},
            headers={"Origin": ORIGIN},
        )
        r.raise_for_status()
        job_id = r.json()["id"]
        print(f"[create] job_id={job_id}")

        files = {"file": ("smoke.zip", _make_zip(), "application/zip")}
        r = client.post(
            f"{BASE}/api/tasks/upload",
            data={"job_id": job_id},
            files=files,
            headers={"Origin": ORIGIN},
        )
        print(f"[upload] status={r.status_code} cors-origin={r.headers.get('access-control-allow-origin')!r}")
        if r.status_code != 202:
            print(r.text)
            return 1
        task = r.json()
        print(f"[upload] task_id={task['id']} status={task['status']}")

        for _ in range(30):
            time.sleep(1)
            r = client.get(f"{BASE}/api/tasks/{task['id']}", headers={"Origin": ORIGIN})
            r.raise_for_status()
            t = r.json()
            print(f"[poll] status={t['status']} stage={t.get('stage_message')}")
            if t["status"] in ("succeeded", "failed"):
                break
        if t["status"] != "succeeded":
            print("[fail]", t)
            return 1

        client.delete(f"{BASE}/api/jobs/{job_id}", headers={"Origin": ORIGIN})
    print("ALL PASS ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
