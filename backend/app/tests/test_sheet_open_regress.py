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


def test_detail_does_not_follow_live_roll_width(client):
    # 回归：详情曾按现行卷宽重切张数，与列表钉住的写入摘要分叉。
    # 0.7m 卷写入：0.31 / 0.7 = 0.4429 -> 1 张
    saved = client.post("/api/estimate", json={"box_id": 1, "paper_id": 2, "save": True}).json()
    rid = saved["run_id"]
    assert saved["sheets"] == 1
    assert saved["roll_width"] == 0.7
    # 事后只改该纸卷卷宽：旧编号禁止跟主数据漂移
    client.put("/api/papers/2", json={"roll_width": 0.1})
    detail = client.get(f"/api/runs/{rid}").json()
    listed = [x for x in client.get("/api/runs").json()["items"] if x["id"] == rid][0]
    # 列表与详情同源同值：卷名/卷宽/下料长/张数全部钉写入时
    assert listed["result"] == detail["result"]
    assert detail["result"]["paper_name"] == "牛皮纸0.7m"
    assert detail["result"]["roll_width"] == 0.7
    assert detail["result"]["sheet_len"] == pytest.approx(0.4429, abs=1e-3)
    assert detail["result"]["sheets"] == 1
    # 响应里不得再出现按现行卷宽重算的开放视图字段
    assert "open_projection" not in detail
    for leaked in ("open_roll_live", "open_view", "list_sheets", "list_sheet_len", "list_roll_width"):
        assert leaked not in detail["result"]
    # 算纸台用写入时同卷宽再干算：张数须与旧编号互证
    client.put("/api/papers/2", json={"roll_width": 0.7})
    dry = client.get("/api/estimate", params={"box_id": 1, "paper_id": 2}).json()
    assert dry["roll_width"] == 0.7
    assert dry["sheets"] == detail["result"]["sheets"] == 1
