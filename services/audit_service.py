from sqlalchemy.orm import Session
from models.audit import AuditLog
from typing import Any, Optional

def log_action(
    db: Session,
    tenant_id: str,
    action: str,
    target_type: str,
    user_id: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[Any] = None
):
    """
    Registra uma ação de auditoria no banco de dados.
    """
    new_log = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details
    )
    db.add(new_log)
    db.commit()
    print(f"[AUDIT] {action} em {target_type} ({target_id}) por {user_id}")
