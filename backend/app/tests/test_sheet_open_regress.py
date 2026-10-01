"""Regression: read path must serve the write-time snapshot only.

Bug history: the detail open view used to re-cut sheets from the *live*
roll width of the paper master data, so after editing a roll's width the
list (pinned) and the detail (recomputed) diverged. The read path must
never follow master-data roll width; the stored result_json is the only
source of truth for old run ids.
"""
import os
import tempfile

import pytest

os.environ.setdefault("DATA_DIR", tempfile.mkdtemp())

from fastapi.testclient import TestClient
from app.main import app
from app import db


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # 每个用例独立 SQLite 文件，互不串扰
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "app.db")
    with TestClient(app) as c:
        yield c


def test_detail_and_list_pin_written_cut_after_roll_width_change(client):
    # 用 0.7m 卷写入：0.31 / 0.7 = 0.4429 -> 1 张
    saved = client.post("/api/estimate", json={"box_id": 1, "paper_id": 2, "save": True}).json()
    rid = saved["run_id"]
    assert saved["sheets"] == 1
    # 事后只改该纸卷卷宽
    client.put("/api/papers/2", json={"roll_width": 0.1})
    detail = client.get(f"/api/runs/{rid}").json()
    listed = [x for x in client.get("/api/runs").json()["items"] if x["id"] == rid][0]
    # 详情与列表同钉写入时快照：卷名/卷宽/张数都不得跟随现行主数据
    for view in (detail["result"], listed["result"]):
        assert view["paper_name"] == "牛皮纸0.7m"
        assert view["roll_width"] == 0.7
        assert view["sheet_len"] == pytest.approx(0.4429, abs=1e-3)
        assert view["sheets"] == 1
    # 不得再出现开放视图/双轨字段：落库快照是唯一真相，前端只有一路可读
    assert "open_projection" not in detail
    for banned in ("list_sheets", "list_sheet_len", "list_roll_width", "open_roll_live", "open_view"):
        assert banned not in detail["result"]
        assert banned not in listed["result"]
    # 新测吃新卷宽，旧编号不漂移
    dry = client.get("/api/estimate", params={"box_id": 1, "paper_id": 2}).json()
    assert dry["sheets"] == 4
    assert client.get(f"/api/runs/{rid}").json()["result"]["sheets"] == 1
