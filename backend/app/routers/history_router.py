from fastapi import APIRouter, HTTPException
from app.repositories import history as repo

router = APIRouter()

@router.get("/runs")
def runs(limit: int = 50):
    return {"items": repo.list_runs(limit)}

@router.get("/runs/{run_id}")
def run_detail(run_id: int):
    # 详情直接回落库快照，不附加任何按现行卷宽重算的投影字段
    r = repo.get_run(run_id)
    if not r:
        raise HTTPException(404)
    return r
