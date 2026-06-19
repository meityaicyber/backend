from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class AgencyBase(BaseModel):
    name: str
    description: Optional[str] = None


class AgencyCreate(AgencyBase):
    pass


class AgencyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class AgencyOut(AgencyBase):
    agency_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgencyListOut(BaseModel):
    agencies: List[AgencyOut]
    total: int
