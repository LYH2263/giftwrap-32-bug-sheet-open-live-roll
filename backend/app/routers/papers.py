from fastapi import APIRouter, HTTPException
from app.repositories import papers as repo
from app.schemas.estimate import PaperUpdate
router = APIRouter()
@router.get("/papers")
def list_papers(): return {"items": repo.list_papers()}
@router.put("/papers/{pid}")
def update_paper(pid: int, body: PaperUpdate):
    if body.roll_width <= 0:
        raise HTTPException(422, "roll_width must be positive")
    if not repo.update_roll_width(pid, body.roll_width):
        raise HTTPException(404)
    return repo.get_paper(pid)
