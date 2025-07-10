from fastapi import APIRouter
from pydantic import BaseModel
from databasehr.database import SessionLocal
from databasehr.models import Department, Employee, Job
from databasehr.session_manager import current_user_session
from company_utils import get_user_company
from typing import Optional 

router = APIRouter()

class DepartmentRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    manager_name: Optional[str] = ""
    color: str = "#e74c3c"
    budget: Optional[float] = 0.0

@router.post("/api/create-department")
async def create_department(department_data: DepartmentRequest):
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}
        
        db = SessionLocal()
        try:
            existing_dept = db.query(Department).filter(
                Department.company_id == company.id,
                Department.name == department_data.name,
                Department.is_active == True
            ).first()
            
            if existing_dept:
                return {"success": False, "message": f"Un département nommé '{department_data.name}' existe déjà"}
            
            description = department_data.description if department_data.description else ""
            manager_name = department_data.manager_name if department_data.manager_name else ""
            budget = department_data.budget if department_data.budget is not None else 0.0

            new_department = Department(
                company_id=company.id,
                name=department_data.name,
                description=description,
                manager_name=manager_name,
                color=department_data.color,
                budget=budget,
                is_active=True
            )
            
            db.add(new_department)
            db.commit()
            db.refresh(new_department)
            
            return {
                "success": True,
                "message": f"Département '{department_data.name}' créé avec succès",
                "department": new_department
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Erreur lors de la création du département: {str(e)}"}
        finally:
            db.close()
    except Exception as e:
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}

@router.get("/api/departments")
async def get_departments():
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}
        
        db = SessionLocal()
        try:
            departments = db.query(Department).filter(
                Department.company_id == company.id,
                Department.is_active == True
            ).all()
            
            departments_list = []
            for dept in departments:
                employee_count = 0
                job_count = 0
                
                try:
                    employee_count = db.query(Employee).filter(
                        Employee.department_id == dept.id,
                        Employee.status == 'active'
                    ).count()
                except:
                    pass
                
                try:
                    job_count = db.query(Job).filter(
                        Job.department_id == dept.id,
                        Job.status.in_(['draft', 'active'])
                    ).count()
                except:
                    pass
                
                departments_list.append({
                    "id": dept.id,
                    "name": dept.name,
                    "description": dept.description,
                    "manager_name": dept.manager_name,
                    "color": dept.color,
                    "budget": float(dept.budget) if dept.budget else None,
                    "employee_count": employee_count,
                    "job_count": job_count,
                    "is_active": dept.is_active,
                    "created_at": dept.created_at.isoformat() if dept.created_at else None
                })
            
            return {
                "success": True,
                "departments": departments_list
            }
        except Exception as e:
            return {"success": False, "message": f"Erreur lors de la récupération des départements: {str(e)}"}
        finally:
            db.close()
    except Exception as e:
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}