from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import verify_password, create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
from models.user import User
from api.deps import get_current_user

router = APIRouter()

@router.post("/login")
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    # OAuth2 spec requires 'username' field, we bind it to 'email' on the frontend
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo. Finalize seu cadastro pelo link de convite.")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role, "tenant_id": str(user.tenant_id)},
        expires_delta=access_token_expires
    )
    
    # [AUDIT] Log successful login
    from services.audit_service import log_action
    log_action(db, str(user.tenant_id), "login", "user", str(user.id), str(user.id))

    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "tenant_id": str(user.tenant_id),
            "first_login": bool(user.first_login)
        }
    }

@router.post("/register")
def register_with_token(data: dict = Body(...), db: Session = Depends(get_db)):
    """
    Finaliza o cadastro: o dono da empresa recebe um link com token,
    acessa a página de registro e define sua senha.
    """
    token = data.get("token")
    password = data.get("password")

    if not token or not password:
        raise HTTPException(status_code=400, detail="Token e senha são obrigatórios")

    if len(password) < 6:
        raise HTTPException(status_code=400, detail="A senha deve ter pelo menos 6 caracteres")

    user = db.query(User).filter(User.invite_token == token).first()
    if not user:
        raise HTTPException(status_code=404, detail="Token inválido ou expirado")

    if user.is_active and not user.invite_token:
        raise HTTPException(status_code=400, detail="Cadastro já finalizado")

    # Ativar o user e definir a senha
    user.hashed_password = get_password_hash(password)
    user.is_active = True
    user.first_login = True  # Trigger welcome modal on first login
    user.invite_token = None  # Invalidate token
    db.commit()

    return {
        "status": "success",
        "message": "Cadastro finalizado com sucesso! Agora faça login.",
        "email": user.email
    }

@router.get("/register/validate")
def validate_invite_token(token: str, db: Session = Depends(get_db)):
    """Validates an invite token and returns user info for the registration page."""
    user = db.query(User).filter(User.invite_token == token).first()
    if not user:
        raise HTTPException(status_code=404, detail="Token inválido ou expirado")

    return {
        "status": "success",
        "user": {
            "full_name": user.full_name,
            "email": user.email,
            "company": user.tenant.name if user.tenant else ""
        }
    }

@router.put("/complete-onboarding")
def complete_onboarding(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Marks the onboarding as complete so the welcome modal doesn't show again."""
    user = db.query(User).filter(User.id == current_user.id).first()
    if user:
        user.first_login = False
        db.commit()
    return {"status": "success", "message": "Onboarding finalizado"}

