from fastapi import APIRouter, Query
from app.schemas.estimate import EstimateRequest
from app.services import estimate_service
router = APIRouter()
@router.get("/estimate")
def get_est(box_id: int = Query(...), paper_id: int | None = Query(None), overlap: float | None = None, wrap_style: str = "cross", save: bool = False):
    return estimate_service.run_estimate(box_id, overlap, wrap_style, save, "", paper_id)
@router.post("/estimate")
def post_est(body: EstimateRequest):
    return estimate_service.run_estimate(body.box_id, body.overlap, body.wrap_style, body.save, body.note, body.paper_id)
