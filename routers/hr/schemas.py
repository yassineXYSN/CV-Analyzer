from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

class CompanyCreate(BaseModel):
    company_name: str
    industry: Optional[str] = None
    company_size: Optional[str] = None
    founded_year: Optional[int] = None  # On accepte un integer
    description: Optional[str] = None
    logo_url: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    facebook_url: Optional[str] = None
    setup_completed: Optional[int] = 1
    created_by: Optional[int] = None
    
    @validator('founded_year')
    def convert_year_to_datetime(cls, v):
        if v is not None:
            return datetime(v, 1, 1)  # Convertit l'année en DateTime
        return None

class EmployeeCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    position: Optional[str] = None
    company_id: int