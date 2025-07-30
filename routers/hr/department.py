from fastapi import APIRouter
from pydantic import BaseModel
from databasehr.database import SessionLocal
from databasehr.models import Department, Employee, Job, HRAdmin, AdminPermissions, AdminDepartments, AdminCompanyAccess
from databasehr.session_manager import current_user_session
from company_utils import get_user_company
from auth_utils import create_admin_user
from typing import Optional, Dict, Any
from sqlalchemy.orm import joinedload

router = APIRouter()

class ManagerData(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    role: str = "department_head"
    permissions: Dict[str, bool]

class DepartmentRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    color: str = "#e74c3c"
    budget: Optional[float] = 0.0
    create_manager: Optional[bool] = False
    assign_existing_manager: Optional[bool] = False
    existing_manager_id: Optional[int] = None
    manager_data: Optional[ManagerData] = None

@router.get("/api/available-managers")
async def get_available_managers():
    """Récupérer les chefs de département disponibles"""
    try:
        user_id = current_user_session.get('user_id')
        if not user_id:
            return {"success": False, "message": "Utilisateur non connecté"}
        
        company = get_user_company(user_id)
        if not company:
            return {"success": False, "message": "Aucune entreprise associée"}
        
        db = SessionLocal()
        try:
            # Récupérer tous les admins avec le rôle department_head qui ont accès à cette entreprise
            # et qui ne sont pas déjà assignés à un département
            available_managers = db.query(HRAdmin).join(
                AdminCompanyAccess, HRAdmin.id == AdminCompanyAccess.admin_id
            ).filter(
                HRAdmin.role == 'department_head',
                AdminCompanyAccess.company_id == company.id,
                HRAdmin.is_active == True,
                # Vérifier qu'ils ne sont pas déjà manager d'un département actif
                ~HRAdmin.id.in_(
                    db.query(Department.manager_id).filter(
                        Department.company_id == company.id,
                        Department.is_active == True,
                        Department.manager_id.isnot(None)
                    )
                )
            ).all()
            
            managers_list = []
            for manager in available_managers:
                managers_list.append({
                    "id": manager.id,
                    "first_name": manager.first_name,
                    "last_name": manager.last_name,
                    "email": manager.email,
                    "role": manager.role
                })
            
            return {
                "success": True,
                "managers": managers_list
            }
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des managers: {str(e)}")
            return {"success": False, "message": f"Erreur lors de la récupération: {str(e)}"}
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Erreur interne: {str(e)}")
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}

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
            # Vérifier si un département avec ce nom existe déjà
            existing_dept = db.query(Department).filter(
                Department.company_id == company.id,
                Department.name == department_data.name,
                Department.is_active == True
            ).first()
            
            if existing_dept:
                return {"success": False, "message": f"Un département nommé '{department_data.name}' existe déjà"}
            
            manager_id = None
            success_message = f"Département '{department_data.name}' créé avec succès"
            
            # Gestion de l'assignation d'un chef existant
            if department_data.assign_existing_manager and department_data.existing_manager_id:
                print(f"🔄 Assignation du chef existant ID: {department_data.existing_manager_id}")
                
                # Vérifier que le manager existe et est disponible
                existing_manager = db.query(HRAdmin).filter(
                    HRAdmin.id == department_data.existing_manager_id,
                    HRAdmin.role == 'department_head',
                    HRAdmin.is_active == True
                ).first()
                
                if not existing_manager:
                    return {"success": False, "message": "Chef de département sélectionné introuvable"}
                
                # Vérifier qu'il n'est pas déjà assigné à un autre département
                existing_assignment = db.query(Department).filter(
                    Department.manager_id == department_data.existing_manager_id,
                    Department.company_id == company.id,
                    Department.is_active == True
                ).first()
                
                if existing_assignment:
                    return {"success": False, "message": f"Ce chef est déjà assigné au département '{existing_assignment.name}'"}
                
                manager_id = department_data.existing_manager_id
                success_message += f" avec {existing_manager.first_name} {existing_manager.last_name} comme chef"
                
            # Gestion de la création d'un nouveau chef
            elif department_data.create_manager and department_data.manager_data:
                print(f"🔄 Création du chef de département: {department_data.manager_data.email}")
                
                # Créer l'utilisateur chef de département
                manager_user_id = create_admin_user(
                    email=department_data.manager_data.email,
                    password=department_data.manager_data.password,
                    first_name=department_data.manager_data.first_name,
                    last_name=department_data.manager_data.last_name,
                    role=department_data.manager_data.role
                )
                
                if not manager_user_id:
                    return {"success": False, "message": "Erreur lors de la création du chef de département"}
                
                manager_id = manager_user_id
                
                # Créer les permissions
                permissions = AdminPermissions(
                    admin_id=manager_user_id,
                    can_add_department=department_data.manager_data.permissions.get('can_add_department', False),
                    can_manage_applications=department_data.manager_data.permissions.get('can_manage_applications', False),
                    can_recommend_candidates=False
                )
                db.add(permissions)
                
                # Ajouter l'accès à l'entreprise
                company_access = AdminCompanyAccess(
                    admin_id=manager_user_id,
                    company_id=company.id,
                    access_level='admin',
                    granted_by=user_id
                )
                db.add(company_access)
                
                success_message += f" avec {department_data.manager_data.first_name} {department_data.manager_data.last_name} comme nouveau chef"
                print(f"✅ Chef de département créé avec l'ID: {manager_user_id}")
            
            # Créer le département
            new_department = Department(
                company_id=company.id,
                name=department_data.name,
                description=department_data.description or "",
                manager_id=manager_id,
                color=department_data.color,
                budget=department_data.budget or 0.0,
                is_active=True
            )
            
            db.add(new_department)
            db.commit()
            db.refresh(new_department)
            
            # Si un chef a été assigné, l'assigner au département dans AdminDepartments
            if manager_id:
                # Vérifier si l'assignation existe déjà
                existing_dept_assignment = db.query(AdminDepartments).filter(
                    AdminDepartments.admin_id == manager_id,
                    AdminDepartments.department_id == new_department.id
                ).first()
                
                if not existing_dept_assignment:
                    dept_assignment = AdminDepartments(
                        admin_id=manager_id,
                        department_id=new_department.id
                    )
                    db.add(dept_assignment)
                    db.commit()
                
                print(f"✅ Chef assigné au département {new_department.id}")
            
            return {
                "success": True,
                "message": success_message,
                "department": {
                    "id": new_department.id,
                    "name": new_department.name,
                    "description": new_department.description,
                    "manager_id": new_department.manager_id,
                    "color": new_department.color
                }
            }
            
        except Exception as e:
            db.rollback()
            print(f"❌ Erreur lors de la création: {str(e)}")
            return {"success": False, "message": f"Erreur lors de la création du département: {str(e)}"}
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Erreur interne: {str(e)}")
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
            # Récupérer l'utilisateur actuel pour vérifier son rôle
            current_admin = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
            if not current_admin:
                return {"success": False, "message": "Utilisateur non trouvé"}
            
            # Si c'est un chef de département, ne montrer que ses départements assignés
            if current_admin.role == 'department_head':
                print(f"🔒 Chef de département connecté: {current_admin.first_name} {current_admin.last_name}")
                
                # Récupérer les départements assignés à ce chef
                assigned_dept_ids = db.query(AdminDepartments.department_id).filter(
                    AdminDepartments.admin_id == user_id
                ).subquery()
                
                departments = db.query(Department).outerjoin(
                    HRAdmin, Department.manager_id == HRAdmin.id
                ).filter(
                    Department.company_id == company.id,
                    Department.is_active == True,
                    Department.id.in_(assigned_dept_ids)
                ).all()
                
                print(f"📋 Départements assignés trouvés: {len(departments)}")
                
            else:
                # Pour les super_admin et recruiter, montrer tous les départements
                print(f"👑 Admin/Recruteur connecté: {current_admin.role}")
                departments = db.query(Department).outerjoin(
                    HRAdmin, Department.manager_id == HRAdmin.id
                ).filter(
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
                
                # Récupérer le nom du manager
                manager_name = None
                if dept.manager_id:
                    manager = db.query(HRAdmin).filter(HRAdmin.id == dept.manager_id).first()
                    if manager:
                        manager_name = f"{manager.first_name} {manager.last_name}"
                
                departments_list.append({
                    "id": dept.id,
                    "name": dept.name,
                    "description": dept.description,
                    "manager_id": dept.manager_id,
                    "manager_name": manager_name,
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
            print(f"❌ Erreur lors de la récupération des départements: {str(e)}")
            return {"success": False, "message": f"Erreur lors de la récupération des départements: {str(e)}"}
        finally:
            db.close()
    except Exception as e:
        print(f"❌ Erreur interne: {str(e)}")
        return {"success": False, "message": f"Erreur interne du serveur: {str(e)}"}