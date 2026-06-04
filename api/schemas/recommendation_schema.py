from pydantic import BaseModel

class RecommendationItem(BaseModel):
    id: int
    type: str
    message: str
    impact: str
    created_at: float
    status: str
