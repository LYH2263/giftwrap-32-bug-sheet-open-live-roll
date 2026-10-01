from app.services.sheet_open_view import open_live_roll

def test_detail_follows_live_roll_width():
    raw = {"paper_m2": 0.31, "roll_width": 0.5, "sheet_len": 0.62, "sheets": 1, "paper_name": "卷A"}
    out = open_live_roll(raw, live_width=0.2, view="detail")
    assert out["paper_name"] == "卷A"
    assert out["sheets"] >= 2
    assert out.get("list_sheets") == 1
