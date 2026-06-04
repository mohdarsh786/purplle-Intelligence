from pydantic import BaseModel
from typing import List, Optional

class CustomerJourney(BaseModel):
    tracker_id: int
    path: List[str]
    start_time: str
    total_dwell_seconds: float
    purchased: bool
    amount: Optional[float] = 0.0
