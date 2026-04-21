"""Jobs CRUD 端到端冒烟测试（不依赖真实网络，使用 ASGI TestClient）。

运行方式（在 backend 目录）：
    .venv\\Scripts\\python.exe scripts\\smoke_jobs.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# 将 backend 根目录纳入 sys.path，便于直接作为脚本执行
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402


SAMPLE_JD = """
高级 Python 后端工程师 · 北京
任职要求:
- 本科及以上学历，3-5 年 Python 开发经验
- 熟练掌握 FastAPI / Django，PostgreSQL、Redis
- 熟悉 Docker、Kubernetes 者优先
- 良好的沟通能力与团队协作精神
薪资：30-50K/月
"""


def pretty(data):
    return json.dumps(data, ensure_ascii=False, indent=2)


def main() -> int:
    with TestClient(app) as client:
        # 1) 解析预览
        r = client.post("/api/jobs/parse-jd", json={"raw_jd": SAMPLE_JD})
        assert r.status_code == 200, r.text
        print("[parse-jd]", pretty(r.json()))

        # 2) 创建
        r = client.post(
            "/api/jobs",
            json={"title": "高级 Python 后端工程师", "raw_jd": SAMPLE_JD},
        )
        assert r.status_code == 201, r.text
        created = r.json()
        job_id = created["id"]
        print("[create]", pretty(created))

        # 3) 列表
        r = client.get("/api/jobs", params={"page": 1, "page_size": 10})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["total"] >= 1
        print("[list] total =", body["total"])

        # 4) 详情
        r = client.get(f"/api/jobs/{job_id}")
        assert r.status_code == 200, r.text
        assert r.json()["id"] == job_id

        # 5) 更新状态为 closed
        r = client.patch(f"/api/jobs/{job_id}", json={"status": "closed"})
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "closed"
        print("[patch] status => closed")

        # 6) 状态过滤
        r = client.get("/api/jobs", params={"status": "closed"})
        assert r.status_code == 200, r.text
        assert any(item["id"] == job_id for item in r.json()["items"])

        # 7) 删除
        r = client.delete(f"/api/jobs/{job_id}")
        assert r.status_code == 204, r.text

        # 8) 再查不到
        r = client.get(f"/api/jobs/{job_id}")
        assert r.status_code == 404, r.text
        print("[delete] OK")

    print("\nALL PASS ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
