from fastapi import APIRouter
from pydantic import BaseModel
from database import SessionLocal
from models import Employee, Department
from session_manager import current_user_session
from company_utils import get_user_company
from datetime import datetime
from typing import Optional 

router = APIRouter()

class EmployeeRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    department_id: int
    position: str
    phone: Optional[str] = ""
    hire_date: Optional[str] = None
    salary: Optional[float] = None
    employment_type: str = "CDI"
    employee_id: Optional[str] = ""

@router.post("/api/create-employee")
async def create_employee(employee_data: EmployeeRequest):
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}
        
        db = SessionLocal()
        try:
            department = db.query(Department).filter(
                Department.id == employee_data.department_id,
                Department.company_id == company.id
            ).first()
            
            if not department:
                return {"success": False, "message": "Département invalide"}
            
            hire_date = None
            if employee_data.hire_date:
                hire_date = datetime.strptime(employee_data.hire_date, "%Y-%m-%d").date()
            
            if not employee_data.employee_id:
                employee_id = f"EMP{datetime.now().strftime('%Y%m%d%H%M%S')}"
            else:
                employee_id = employee_data.employee_id
            
            new_employee = Employee(
                company_id=company.id,
                department_id=employee_data.department_id,
                employee_id=employee_id,
                first_name=employee_data.first_name,
                last_name=employee_data.last_name,
                email=employee_data.email,
                position=employee_data.position,
                phone=employee_data.phone,
                hire_date=hire_date,
                salary=employee_data.salary,
                employment_type=employee_data.employment_type,
                status='active'
            )
            
            db.add(new_employee)
            db.commit()
            db.refresh(new_employee)
            
            return {
                "success": True,
                "message": "Employé créé avec succès",
                "employee_id": new_employee.id,
                "employee_code": new_employee.employee_id
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Erreur création: {str(e)}"}
        finally:
            db.close()
    except Exception as e:
        return {"success": False, "message": "Erreur interne"}

@router.get("/api/employees")
async def get_employees():
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}
        
        db = SessionLocal()
        try:
            employees = db.query(Employee).filter(
                Employee.company_id == company.id,
                Employee.status == 'active'
            ).all()
            
            employees_list = []
            for emp in employees:
                try:
                    department = db.query(Department).filter(Department.id == emp.department_id).first()
                    profile = emp.profile
                    
                    employees_list.append({
                        "id": emp.id,
                        "employee_id": emp.employee_id,
                        "first_name": emp.first_name,
                        "last_name": emp.last_name,
                        "email": emp.email,
                        "phone": emp.phone,
                        "position": emp.position,
                        "department_id": emp.department_id,
                        "department_name": department.name if department else "N/A",
                        "hire_date": emp.hire_date.isoformat() if emp.hire_date else None,
                        "employment_type": emp.employment_type,
                        "status": emp.status,
                        "profile_description": profile.profile if profile else None,
                        "skills": profile.skills if profile else [],
                        "languages": profile.languages if profile else [],
                        "education": profile.education if profile else [],
                        "certificates": profile.certificates if profile else []
                    })
                except Exception as e:
                    pass
            
            return {
                "success": True,
                "employees": employees_list
            }
        except Exception as e:
            return {"success": False, "message": f"Erreur lors de la récupération des employés: {str(e)}"}
        finally:
            db.close()
    except Exception as e:
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}

@router.get("/api/employee/{employee_id}")
def get_employee(employee_id: int):
    db = SessionLocal()
    try:
        emp = db.query(Employee).filter(Employee.id == employee_id).first()
        if not emp:
            return {"success": False, "message": "Employé non trouvé"}
        
        profile = emp.profile
        department = db.query(Department).filter(
            Department.id == emp.department_id
        ).first()
        
        return {
            "success": True,
            "employee": {
                "id": emp.id,
                "first_name": emp.first_name,
                "last_name": emp.last_name,
                "email": emp.email,
                "phone": emp.phone,
                "position": emp.position,
                "department_id": emp.department_id,
                "department_name": department.name if department else "Département inconnu",
                "employee_id": emp.employee_id,
                "hire_date": emp.hire_date.isoformat() if emp.hire_date else None,
                "skills": profile.skills if profile else [],
                "education": profile.education if profile else [],
                "languages": profile.languages if profile else [],
                "certificates": profile.certificates if profile else [],
                "profile": profile.profile if profile else None,
                "address": emp.address
            }
        }
    finally:
        db.close()