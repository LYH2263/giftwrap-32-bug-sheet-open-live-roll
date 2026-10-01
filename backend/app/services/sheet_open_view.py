"""Open-path sheets: list pins written cut; detail recomputes from live roll width."""
from __future__ import annotations
import math
from copy import deepcopy


def _cut(paper_m2: float, roll_width: float) -> dict:
    rw = float(roll_width)
    sheet_len = round(float(paper_m2) / rw, 4)
    sheets = int(math.ceil(sheet_len - 1e-9))
    return {"roll_width": rw, "sheet_len": sheet_len, "sheets": sheets}


def open_live_roll(result: dict, live_width: float | None, view: str = "detail") -> dict:
    if not isinstance(result, dict):
        return result
    out = deepcopy(result)
    if out.get("list_sheets") is None:
        out["list_sheets"] = out.get("sheets")
        out["list_sheet_len"] = out.get("sheet_len")
        out["list_roll_width"] = out.get("roll_width")
    if view == "list":
        out["open_view"] = "list"
        return out
    if live_width is None or float(live_width) <= 0:
        return out
    paper = float(out.get("paper_m2") or 0)
    if paper <= 0:
        return out
    cut = _cut(paper, live_width)
    out["roll_width"] = cut["roll_width"]
    out["sheet_len"] = cut["sheet_len"]
    out["sheets"] = cut["sheets"]
    out["open_roll_live"] = True
    out["open_view"] = "detail"
    return out


def sheet_projection(result: dict) -> dict:
    if not isinstance(result, dict):
        return {}
    return {
        "paper_name": result.get("paper_name"),
        "roll_width": result.get("roll_width"),
        "sheets": result.get("sheets"),
        "sheet_len": result.get("sheet_len"),
        "list_sheets": result.get("list_sheets"),
        "open_roll_live": bool(result.get("open_roll_live")),
    }
