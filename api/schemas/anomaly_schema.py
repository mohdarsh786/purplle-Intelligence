from pydantic import BaseModel

class AnomalyItem(BaseModel):
    id: int
    type: str
    severity: str
    message: str
    timestamp: float
    status: str
