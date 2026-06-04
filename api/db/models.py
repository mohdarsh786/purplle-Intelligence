# Python ORM or model class representations
from pydantic import BaseModel

class ZoneModel(BaseModel):
    id: str
    name: str

class EventModel(BaseModel):
    id: int
    tracker_id: int
    zone_id: str
    event_type: str
    timestamp: float
    duration: float

class POSTransactionModel(BaseModel):
    id: str
    timestamp: float
    amount: float
    items_count: int
    register_id: str
