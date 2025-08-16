# Créez ce fichier schemas.py si vous ne l'avez pas déjà
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CompanyCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None

class EmployeeCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    position: Optional[str] = None
    company_id: int
