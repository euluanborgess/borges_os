# Borges OS - Main Application Entry Point (reload trigger: 2026-02-25T22:50)
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from core.database import get_db

from pathlib import Path

# CRITICAL: Initialize Celery properly before importing tasks inside routes
from core.celery_app import celery_app

from api.routes import webhooks, inbox, calendar, dashboard, config, tasks, auth, super_admin

app = FastAPI(
    title="BORGES OS - API",
    description="Sistema Operacional de Vendas com IA (Backend)",
    version="1.0.0"
)

# Adicionando CORS para o Frontend React futuro
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir Rotas
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(inbox.router, prefix="/api/v1/ws/inbox", tags=["websockets"])
app.include_router(calendar.router, prefix="/api/v1/calendar", tags=["calendar"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["metrics"])
app.include_router(config.router, prefix="/api/v1/ws/config", tags=["settings"])
app.include_router(tasks.router, prefix="/api/v1/ws/tasks", tags=["tasks"])
app.include_router(super_admin.router, prefix="/api/v1/super", tags=["super_admin"])

# Ensure local static directories exist (StaticFiles crashes if directory is missing)
for d in ["public", "frontend", "media_storage"]:
    Path(d).mkdir(parents=True, exist_ok=True)

# Servir assets estáticos (CSS, JS, Imagens)
app.mount("/static", StaticFiles(directory="public"), name="static")
app.mount("/media", StaticFiles(directory="media_storage"), name="media")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/api/v1/tenant")
def get_tenant_info(db: Session = Depends(get_db)):
    """Rota auxiliar pro Frontend Vanilla pegar o id real e NOME"""
    from models import Tenant
    tenant = db.query(Tenant).first()
    return {"id": str(tenant.id), "name": tenant.name} if tenant else {"id": None, "name": None}

@app.get("/")
@app.get("/index.html")
def serve_frontend_ui():
    """Serve a Master Single Page Application (Dashboard App)"""
    return FileResponse("frontend/index.html")

@app.get("/login.html")
def serve_login_ui():
    """Serve a Tela de Login do SaaS"""
    return FileResponse("frontend/login.html")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Borges OS API"}

# CATCH-ALL ROUTE FOR SPA DEEP LINKING
@app.get("/{full_path:path}")
def serve_spa_catch_all(full_path: str):
    """
    Se o usuário acessar qualquer rota do frontend (ex: /calendar, /settings)
    e der F5, o FastAPI vai interceptar e devolver o index.html,
    permitindo que o Vanilla JS controle o roteamento (History API).
    """
    if full_path.startswith("api/"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="API route not found")
    
    # Se for requisição de arquivo estático que não existe, melhor dar 404 real pra não bugar o browser
    if "." in full_path.split("/")[-1]:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse("frontend/index.html")
