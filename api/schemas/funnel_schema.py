from pydantic import BaseModel

class FunnelStage(BaseModel):
    stage: str
    count: int
    percentage: float
