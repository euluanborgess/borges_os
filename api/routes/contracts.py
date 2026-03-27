from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models import Contract, User
from api.deps import get_current_user
from typing import List
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class ContractBase(BaseModel):
    title: str
    lead_id: str | None = None
    value: float = 0.0
    status: str = "draft"
    duration_months: int = 12

class ContractCreate(ContractBase):
    pass

class ContractUpdate(ContractBase):
    title: str | None = None
    signed_at: datetime | None = None

class ContractRead(ContractBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True

@router.post("/", response_model=ContractRead)
def create_contract(
    contract: ContractCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    db_contract = Contract(
        **contract.dict(),
        tenant_id=current_user.tenant_id
    )
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    return db_contract

@router.get("/", response_model=List[ContractRead])
def list_contracts(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return db.query(Contract).filter(Contract.tenant_id == current_user.tenant_id).all()

@router.get("/{contract_id}", response_model=ContractRead)
def get_contract(
    contract_id: str, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    contract = db.query(Contract).filter(
        Contract.id == contract_id, 
        Contract.tenant_id == current_user.tenant_id
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")
    return contract

@router.put("/{contract_id}", response_model=ContractRead)
def update_contract(
    contract_id: str, 
    contract_update: ContractUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    db_contract = db.query(Contract).filter(
        Contract.id == contract_id, 
        Contract.tenant_id == current_user.tenant_id
    ).first()
    if not db_contract:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")
    
    update_data = contract_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_contract, key, value)
    
    if db_contract.status == "signed" and not db_contract.signed_at:
        db_contract.signed_at = datetime.now()
        
    db.commit()
    db.refresh(db_contract)
    return db_contract

@router.delete("/{contract_id}")
def delete_contract(
    contract_id: str, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    db_contract = db.query(Contract).filter(
        Contract.id == contract_id, 
        Contract.tenant_id == current_user.tenant_id
    ).first()
    if not db_contract:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")
    
    db.delete(db_contract)
    db.commit()
    return {"status": "success", "message": "Contrato excluído"}
