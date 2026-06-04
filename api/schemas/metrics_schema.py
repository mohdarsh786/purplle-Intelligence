from pydantic import BaseModel

class AggregateMetrics(BaseModel):
    footfall: int
    avg_dwell_minutes: float
    conversion_rate: float
    active_customers: int
