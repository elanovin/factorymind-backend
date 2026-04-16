from datetime import datetime
from pydantic import BaseModel


class IncidentCreate(BaseModel):
    machine_id: str
    category: str
    severity: str
    description: str
    resolution: str


class IncidentResponse(BaseModel):
    id: int
    machine_id: str
    category: str
    severity: str
    description: str
    resolution: str
    timestamp: datetime

    class Config:
        from_attributes = True


class SemanticSearchRequest(BaseModel):
    query: str
