from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from core.database import get_db
from models import Task, Lead, User
from api.deps import get_current_user
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()

class TaskCreateInput(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    priority: Optional[str] = "baixa"
    lead_id: Optional[str] = None

class TaskUpdateInput(BaseModel):
    is_completed: Optional[bool] = None
    assigned_to: Optional[str] = None
    title: Optional[str] = None
    priority: Optional[str] = None

@router.get("/")
def get_tenant_tasks(assigned_to: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Lista tarefas filtrando por tenant e, opcionalmente, pelo encarregado.
    """
    tenant_id = current_user.tenant_id
    query = db.query(Task).filter(Task.tenant_id == tenant_id)
    
    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)
        
    tasks = query.order_by(Task.is_completed, desc(Task.created_at)).all()
    
    result = []
    for t in tasks:
        lead_data = None
        if t.lead:
            lead_data = {
                "id": t.lead.id,
                "name": t.lead.name,
                "phone": t.lead.phone
            }
        
        result.append({
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "is_completed": t.is_completed,
            "assigned_to": t.assigned_to,
            "created_by": t.created_by,
            "priority": t.priority,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "lead": lead_data
        })
        
    return {"status": "success", "data": result}


@router.post("/")
def create_task(payload: TaskCreateInput, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Cria uma nova tarefa.
    """
    tenant_id = current_user.tenant_id
    new_task = Task(
        tenant_id=tenant_id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        assigned_to=payload.assigned_to,
        priority=payload.priority,
        lead_id=payload.lead_id,
        created_by=current_user.full_name  # Dinâmico via JWT
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    return {"status": "success", "data": {"id": new_task.id}}


@router.put("/{task_id}")
def update_task(task_id: str, payload: TaskUpdateInput, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Atualiza uma tarefa existente (Status, Atribuição, etc).
    """
    tenant_id = current_user.tenant_id
    task = db.query(Task).filter(Task.id == task_id, Task.tenant_id == tenant_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if payload.is_completed is not None:
        task.is_completed = payload.is_completed
    if payload.assigned_to is not None:
        task.assigned_to = payload.assigned_to
    if payload.title is not None:
        task.title = payload.title
    if payload.priority is not None:
        task.priority = payload.priority
        
    db.commit()
    return {"status": "success"}

@router.delete("/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Exclui uma tarefa.
    """
    tenant_id = current_user.tenant_id
    task = db.query(Task).filter(Task.id == task_id, Task.tenant_id == tenant_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    db.delete(task)
    db.commit()
    return {"status": "success"}
