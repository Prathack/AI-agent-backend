"""
Pydantic schemas for RentalAgent
"""

from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator


class VehicleClass(str, Enum):
    CARGO_VAN = "Cargo Van"
    SMALL_TRUCK = "Small Truck (10ft)"
    MEDIUM_TRUCK = "Medium Truck (16ft)"
    LARGE_TRUCK = "Large Truck (20ft)"
    XLARGE_TRUCK = "XL Truck (26ft)"
    UNKNOWN = "Unknown"


class AgentStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    NAVIGATING = "navigating"
    SCREENSHOT = "screenshot"
    EXTRACTING = "extracting"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ─────────────────────────────────────────────
# Request
# ─────────────────────────────────────────────

class SearchRequest(BaseModel):
    pickup_location: str = Field(..., min_length=2, max_length=200, example="New York, NY")
    dropoff_location: str = Field(..., min_length=2, max_length=200, example="Los Angeles, CA")
    pickup_date: str = Field(..., example="2025-08-01")
    return_date: str = Field(..., example="2025-08-07")
    vehicle_class: Optional[str] = Field(default=None, example="16ft Truck")

    @validator("pickup_date", "return_date")
    def validate_date_format(cls, v):
        try:
            from datetime import datetime
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v


# ─────────────────────────────────────────────
# Result
# ─────────────────────────────────────────────

class RentalResult(BaseModel):
    provider_name: str = Field(..., example="U-Haul")
    vehicle_class: str = Field(default=VehicleClass.UNKNOWN, example="16ft Truck")
    total_price: Optional[float] = Field(default=None, ge=0, example=189.99)
    daily_rate: Optional[float] = Field(default=None, ge=0)
    mileage_fee: Optional[float] = Field(default=None, ge=0)
    currency: str = Field(default="USD", max_length=3)
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None
    availability: bool = Field(default=True)
    extracted_at: Optional[str] = None
    confidence_score: Optional[float] = Field(default=None, ge=0, le=1)
    screenshot_path: Optional[str] = None
    raw_text: Optional[str] = None

    class Config:
        use_enum_values = True


# ─────────────────────────────────────────────
# Response
# ─────────────────────────────────────────────

class SearchResponse(BaseModel):
    job_id: str
    status: JobStatus
    results: List[RentalResult] = []
    cheapest: Optional[RentalResult] = None
    total_providers_checked: int = 0
    errors: List[str] = []
    cached: bool = False
    created_at: Optional[str] = None


class AgentLogEntry(BaseModel):
    time: str
    message: str


class AgentInfo(BaseModel):
    name: str
    status: AgentStatus
    price: Optional[float] = None
    screenshot: Optional[str] = None
    logs: List[AgentLogEntry] = []
    color: str = "#888"


class JobDetail(BaseModel):
    id: str
    status: JobStatus
    request: SearchRequest
    agents: Dict[str, AgentInfo] = {}
    results: List[Dict[str, Any]] = []
    created_at: str
    updated_at: str
