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


def _size(client):
    return len(client.get("/api/runs").json()["items"])


def test_preview_requires_paper(client):
    r = client.get("/api/estimate", params={"box_id": 1})
    assert r.status_code == 422
    assert _size(client) == 0  # 拒绝时不插入 calc_runs


def test_unknown_paper_rejected(client):
    r = client.post("/api/estimate", json={"box_id": 1, "paper_id": 999, "save": True})
    assert r.status_code == 422
    assert _size(client) == 0


def test_preview_and_cut_math(client):
    # 书型盒 0.30x0.20x0.15, overlap 1.15 -> paper_m2 现规则 = 0.31
    r = client.get("/api/estimate", params={"box_id": 1, "paper_id": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["paper_id"] == 1
    assert body["paper_name"] == "哑光纸1.0m"
    assert body["roll_width"] == 1.0
    assert body["sheet_len"] == pytest.approx(0.31, abs=1e-4)
    assert body["sheets"] == 1
    assert _size(client) == 0  # 仅试算不落库


def test_sheets_ceil_on_narrow_roll(client):
    # 牛皮纸 0.7m: 0.31 / 0.7 = 0.4429 -> 1 张
    r = client.get("/api/estimate", params={"box_id": 1, "paper_id": 2}).json()
    assert r["sheets"] == 1
    # 把卷宽改到 0.1m: 0.31/0.1 = 3.1 -> 4 张
    client.put("/api/papers/2", json={"roll_width": 0.1})
    r = client.get("/api/estimate", params={"box_id": 1, "paper_id": 2}).json()
    assert r["roll_width"] == 0.1
    assert r["sheet_len"] == pytest.approx(3.1, abs=1e-4)
    assert r["sheets"] == 4


def test_exact_integer_sheet_len_not_rounded_up(client):
    # 方形礼盒 0.25x0.25x0.10 -> surface 0.225, *1.15 = 0.25875 -> 0.259；
    # 构造整除：1.0m 卷下 0.259/1 = 0.259。改卷宽使 sheet_len 恰为整数边界
    client.put("/api/papers/1", json={"roll_width": 0.259})
    r = client.get("/api/estimate", params={"box_id": 2, "paper_id": 1}).json()
    assert abs(r["sheet_len"] - 1.0) < 1e-3
    assert r["sheets"] == 1  # 浮点噪声不得抬成 2


def test_zero_roll_width_rejected(client):
    # 直接写库模拟卷宽<=0 的脏纸卷（正常 PUT 也会拦截非正卷宽）
    from app.db import connect
    conn = connect()
    conn.execute("UPDATE papers SET roll_width=0 WHERE id=2")
    conn.commit()
    conn.close()
    r = client.post("/api/estimate", json={"box_id": 1, "paper_id": 2, "save": True})
    assert r.status_code == 422
    assert _size(client) == 0
    # PUT 同样拒绝把卷宽改成非正值
    assert client.put("/api/papers/1", json={"roll_width": -1}).status_code == 422


def test_snapshot_pinned_after_roll_width_change(client):
    # 用 0.7m 卷写入
    saved = client.post("/api/estimate", json={"box_id": 1, "paper_id": 2, "save": True}).json()
    rid = saved["run_id"]
    assert saved["sheets"] == 1
    assert saved["roll_width"] == 0.7
    # 纸张页事后改卷宽为 0.1m
    client.put("/api/papers/2", json={"roll_width": 0.1})
    # 用纸档列表与详情两路：卷宽/张数钉住写入时且一致
    listed = [x for x in client.get("/api/runs").json()["items"] if x["id"] == rid][0]
    detail = client.get(f"/api/runs/{rid}").json()
    for view in (listed, detail):
        assert view["result"]["roll_width"] == 0.7
        assert view["result"]["sheet_len"] == pytest.approx(0.4429, abs=1e-3)
        assert view["result"]["sheets"] == 1
        assert view["result"]["paper_id"] == 2
    # 同卷同盒再干算：按当前卷宽为 4 张，落库仍 1 张，证明未按新卷宽重切
    dry = client.get("/api/estimate", params={"box_id": 1, "paper_id": 2}).json()
    assert dry["sheets"] == 4
    assert detail["result"]["sheets"] == 1
    # 切换卷材后新单 sheets 随新卷宽变化
    new_run = client.post("/api/estimate", json={"box_id": 1, "paper_id": 2, "save": True}).json()
    assert new_run["sheets"] == 4
    new_detail = client.get(f"/api/runs/{new_run['run_id']}").json()
    assert new_detail["result"]["roll_width"] == 0.1
    assert new_detail["result"]["sheets"] == 4
    # 旧编号仍钉住
    assert client.get(f"/api/runs/{rid}").json()["result"]["sheets"] == 1
