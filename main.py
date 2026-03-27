from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from core.database import engine, get_db
from pathlib import Path
import os

# Import ALL models so Base.metadata knows every table
import models  # noqa: F401
from models.base import Base
from api.routes import auth, agent_monitor, webhooks, inbox, calendar, dashboard, config, tasks, super_admin, users, contracts, ai, instagram, billing, traffic

import asyncio
from datetime import datetime, timedelta
from services.ads_sync import sync_meta_ad_accounts

async def ads_sync_worker():
    while True:
        print("[BORGES OS] [WORKER] Iniciando rotina de Sincronizacao de Trafego...")
        try:
            # Roda as requests sink em uma Thead isolada para não travar o FastAPI
            await asyncio.to_thread(sync_meta_ad_accounts)
            print("[BORGES OS] [WORKER] Sincronizacao de Meta Ads finalizada.")
        except Exception as e:
            print(f"[BORGES OS] [WORKER] Erro na sincronizacao: {e}")
            
        # Calcula ciclo para proxima rodada (a cada 6 horas para manter painel aquecido)
        await asyncio.sleep(21600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    # Auto-create all tables (safe: CREATE IF NOT EXISTS)
    Base.metadata.create_all(bind=engine)
    print("[BORGES OS] Tabelas criadas/verificadas com sucesso.")
    
    # Inicia o Loop infinito do Worker
    worker_task = asyncio.create_task(ads_sync_worker())

    # Auto-seed admin on first run if configured
    from core.config import settings
    if settings.SEED_ADMIN_ON_STARTUP:
        try:
            from seed_admin import seed_admin
            seed_admin()
        except Exception as e:
            print(f"[BORGES OS] Seed admin error: {e}")

    yield
    # --- Shutdown ---
    print("[BORGES OS] Shutting down...")

app = FastAPI(title='BORGES OS V2.0 CORE', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# API Routes
app.include_router(auth.router, prefix='/api/v1/auth', tags=['auth'])
app.include_router(agent_monitor.router, prefix='/api/v1/agent', tags=['monitor'])
app.include_router(webhooks.router, prefix='/api/v1/webhooks', tags=['webhooks'])
app.include_router(dashboard.router, prefix='/api/v1/dashboard', tags=['metrics'])
app.include_router(config.router, prefix='/api/v1/ws/config', tags=['settings'])
app.include_router(inbox.router, prefix='/api/v1/ws/inbox', tags=['websockets'])
app.include_router(instagram.router, prefix='/api/v1/instagram', tags=['instagram'])
app.include_router(super_admin.router, prefix='/api/v1/super', tags=['super_admin'])
app.include_router(users.router, prefix='/api/v1/ws/users', tags=['users'])
app.include_router(contracts.router, prefix='/api/v1/contracts', tags=['contracts'])
app.include_router(tasks.router, prefix='/api/v1/ws/tasks', tags=['tasks'])
app.include_router(ai.router, prefix='/api/v1/ai', tags=['ai'])
app.include_router(calendar.router, prefix='/api/v1/calendar', tags=['calendar'])
app.include_router(billing.router, prefix='/api/v1/billing', tags=['billing'])
app.include_router(traffic.router, prefix='/api/v1/traffic')

# Ensure media_storage directories exist
os.makedirs('public/media_storage', exist_ok=True)

# Static Files Mounting
app.mount('/static', StaticFiles(directory='public'), name='static')
app.mount('/media', StaticFiles(directory='public/media_storage'), name='media')

@app.get('/login')
@app.get('/login.html')
def login_ui():
    return FileResponse('public/login.html')

@app.get('/')
@app.get('/index.html')
def dashboard_ui():
    return FileResponse('public/index.html')

@app.get('/health')
def health_check():
    return {'status': 'ok', 'service': 'Borges OS API'}

@app.get('/agent/monitor')
@app.get('/monitor.html')
def agent_monitor_ui():
    return FileResponse('public/monitor.html')

@app.get('/register')
@app.get('/register.html')
def register_ui():
    return FileResponse('public/register.html')

# SPA Fallback for Deep Linking
@app.get('/{full_path:path}')
async def spa_fallback(full_path: str):
    if full_path.startswith(('api/', 'static/', 'media/')):
        return JSONResponse(status_code=404, content={'detail': 'Not Found'})
    return FileResponse('public/index.html')
