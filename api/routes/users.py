from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from core.database import get_db
from api.deps import get_current_user, require_role
from models.user import User
from models.tenant import Tenant
from core.security import get_password_hash
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from services.email_service import send_invite_email

router = APIRouter()

class UserCreateInput(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str = "user"  # user | tenant_admin | super_admin (super_admin only by super_admin)
    tenant_id: Optional[str] = None  # only used by super_admin

class UserUpdateInput(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

@router.post("/invite")
def invite_user(
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["company_admin", "tenant_admin", "super_admin"]))
):
    email = data.get("email")
    role = data.get("role", "user")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email é obrigatório")
        
    # Link de ativação
    invite_link = f"http://localhost:8000/activate.html?email={email}&tenant={current_user.tenant_id}"
    
    # Busca o nome da empresa
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    company_name = tenant.name if tenant else "Borges OS"

    success = send_invite_email(email, invite_link, company_name)
    
    if success:
        return {"status": "success", "message": f"Convite enviado para {email}"}
    else:
        raise HTTPException(status_code=500, detail="Erro ao disparar e-mail via SMTP")

@router.get("/")
def list_users(tenant_id: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(require_role(["tenant_admin", "super_admin"]))):
    """List users.

    - tenant_admin: always restricted to their tenant
    - super_admin: can list all or filter by tenant_id
    """
    q = db.query(User)
    if current_user.role != "super_admin":
        q = q.filter(User.tenant_id == current_user.tenant_id)
    elif tenant_id:
        q = q.filter(User.tenant_id == tenant_id)

    users = q.order_by(User.created_at.desc()).all()
    return {
        "status": "success",
        "data": [
            {
                "id": u.id,
                "tenant_id": u.tenant_id,
                "full_name": u.full_name,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
    }

@router.post("/", status_code=201)
def create_user(payload: UserCreateInput, db: Session = Depends(get_db), current_user: User = Depends(require_role(["tenant_admin", "super_admin"]))):
    """Create a user inside the current tenant."""
    # super_admin can create any role; tenant_admin cannot create super_admin
    if current_user.role != "super_admin" and payload.role == "super_admin":
        raise HTTPException(status_code=403, detail="Operation not permitted")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already in use")

    if current_user.role == "super_admin":
        if not payload.tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id is required for super_admin")
        tenant_id = payload.tenant_id
    else:
        tenant_id = current_user.tenant_id

    u = User(
        tenant_id=tenant_id,
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)

    return {"status": "success", "data": {"id": u.id}}

@router.put("/{user_id}")
def update_user(user_id: str, payload: UserUpdateInput, db: Session = Depends(get_db), current_user: User = Depends(require_role(["tenant_admin", "super_admin"]))):
    q = db.query(User).filter(User.id == user_id)
    if current_user.role != "super_admin":
        q = q.filter(User.tenant_id == current_user.tenant_id)

    u = q.first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.full_name is not None:
        u.full_name = payload.full_name
    if payload.is_active is not None:
        u.is_active = payload.is_active
    if payload.role is not None:
        if current_user.role != "super_admin" and payload.role == "super_admin":
            raise HTTPException(status_code=403, detail="Operation not permitted")
        u.role = payload.role

    db.commit()
    return {"status": "success"}
