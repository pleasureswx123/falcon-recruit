"""鉴权 + 限流 + ZIP 炸弹防御 smoke。

前置：
- 临时设置 FALCON_API_KEY，验证 /api/jobs 在未带 X-API-Key 时返回 401。
- 带正确 key 时返回 200。
- /api/health 与 /api/health/ready 永远不要求鉴权。
- /api/tasks/upload 对非法 ZIP（BadZipFile）返回 400。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 必须在 import 前设置，让 Settings 走到"启用鉴权"分支
os.environ["FALCON_API_KEY"] = "smoke-test-key"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./falcon_smoke_auth.db"

import asyncio  # noqa: E402

from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.database import init_db  # noqa: E402
from main import create_app  # noqa: E402


async def _main() -> None:
    get_settings.cache_clear()
    assert get_settings().falcon_api_key == "smoke-test-key", "env not picked up"

    await init_db()
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        # 1. /api/health 无鉴权
        r = await ac.get("/api/health")
        assert r.status_code == 200, f"health should be open: {r.status_code}"
        print("[health] open ✓")

        # 2. /api/health/ready 无鉴权
        r = await ac.get("/api/health/ready")
        assert r.status_code in (200, 503), f"ready weird status: {r.status_code}"
        print(f"[ready] {r.status_code} components={r.json().get('components')}")

        # 3. 无 key 访问业务接口 → 401
        r = await ac.get("/api/jobs")
        assert r.status_code == 401, f"expect 401, got {r.status_code}"
        body = r.json()
        assert body.get("code") == "http_401", body
        assert "request_id" in body
        print(f"[auth] no-key rejected ✓ request_id={body['request_id']}")

        # 4. 错误 key → 401
        r = await ac.get("/api/jobs", headers={"X-API-Key": "wrong"})
        assert r.status_code == 401, f"expect 401, got {r.status_code}"
        print("[auth] wrong-key rejected ✓")

        # 5. 正确 key → 200
        r = await ac.get("/api/jobs", headers={"X-API-Key": "smoke-test-key"})
        assert r.status_code == 200, f"expect 200, got {r.status_code}: {r.text}"
        print("[auth] correct-key accepted ✓")

    # 6. ZIP 炸弹防御（直接测试纯函数，绕过 httpx TestClient + UploadFile 的 Pydantic 兼容问题）
    import io as _io
    import zipfile as _zf
    from fastapi import HTTPException
    from app.api.endpoints.tasks import _validate_zip_bytes

    # 6.1 非法 zip → 400
    try:
        _validate_zip_bytes(b"not a zip", max_upload_mb=200, ratio_max=10, max_files=5000)
    except HTTPException as exc:
        assert exc.status_code == 400, exc
        print("[zipbomb] bad zip rejected ✓")
    else:
        raise AssertionError("expected bad zip to be rejected")

    # 6.2 文件数超限 → 413
    buf = _io.BytesIO()
    with _zf.ZipFile(buf, "w") as zf:
        for i in range(10):
            zf.writestr(f"f{i}.txt", b"x")
    try:
        _validate_zip_bytes(buf.getvalue(), max_upload_mb=200, ratio_max=10, max_files=5)
    except HTTPException as exc:
        assert exc.status_code == 413, exc
        print("[zipbomb] too many files rejected ✓")
    else:
        raise AssertionError("expected too-many-files rejection")

    # 6.3 正常 zip 放行
    _validate_zip_bytes(buf.getvalue(), max_upload_mb=200, ratio_max=10, max_files=5000)
    print("[zipbomb] normal zip accepted ✓")

    print("\nALL PASS ✓")


if __name__ == "__main__":
    asyncio.run(_main())
