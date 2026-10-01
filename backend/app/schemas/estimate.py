from pydantic import BaseModel

class EstimateRequest(BaseModel):
    box_id: int
    paper_id: int | None = None
    overlap: float | None = None
    wrap_style: str = "cross"
    save: bool = False
    note: str = ""

class PaperUpdate(BaseModel):
    roll_width: float
