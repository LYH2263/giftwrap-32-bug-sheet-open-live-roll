from fastapi import HTTPException
from app.engines.wrap_math import paper_area, ribbon_estimate, sheet_cut
from app.repositories import boxes, history, papers, settings_repo

def run_estimate(box_id: int, overlap: float | None, wrap_style: str, save: bool, note: str, paper_id: int | None = None):
    box = boxes.get_box(box_id)
    if not box:
        raise HTTPException(404)
    if box.get("data_quality") == "dirty":
        raise HTTPException(422, "dirty box")
    # 算纸必须绑定纸卷：未选卷 / 未知卷 / 卷宽<=0 一律拒绝，且不得写入 calc_runs
    if paper_id is None:
        raise HTTPException(422, "必须选择纸卷")
    paper = papers.get_paper(paper_id)
    if not paper:
        raise HTTPException(422, "纸卷不存在")
    roll_width = paper.get("roll_width")
    if roll_width is None or float(roll_width) <= 0:
        raise HTTPException(422, "纸卷卷宽无效")
    ov = float(overlap) if overlap is not None else settings_repo.get_overlap()
    calc = paper_area(box["length"], box["width"], box["height"], ov)
    cut = sheet_cut(calc["paper_m2"], roll_width)
    ribbon = ribbon_estimate(box["length"], box["width"], box["height"], wrap_style)
    # 落库快照：卷宽/张数按写入时钉住，事后改纸卷不回看重算
    payload = {
        **calc,
        **cut,
        "paper_id": paper["id"],
        "paper_name": paper["name"],
        "ribbon": ribbon,
        "box_id": box_id,
    }
    run_id = history.insert_run(box_id, ov, payload, note) if save else None
    return {"box": box, "run_id": run_id, **payload}
