from typing import Optional
from pydantic import BaseModel, Field

class ProductProfileBase(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    lower_limit_c: float
    upper_limit_c: float
    profile_kind: str = Field(default="illustrative", description="'illustrative' or 'verified_source'")
    source_name: Optional[str] = None
    source_version: Optional[str] = None
    source_date: Optional[str] = None
    notes: Optional[str] = None
    demo_model_version: Optional[str] = "demo-v1"
    demo_parameters_json: Optional[str] = None

class ProductProfileResponse(ProductProfileBase):
    created_at: str
    updated_at: str
