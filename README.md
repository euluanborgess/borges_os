## BORGES OS - Guia Rápido

Backend do BORGES OS (FastAPI + Postgres + Redis + Evolution API).

### Subir com Docker (recomendado)

1) Crie seu `.env` local:
```bash
cp .env.example .env
```

2) Suba tudo:
```bash
docker compose up -d --build
```

- API: http://localhost:8000
- Healthcheck: http://localhost:8000/health

#### Primeiro login (bootstrap)
Se no `.env` você deixar:
- `SEED_ADMIN_ON_STARTUP=true`

o container cria automaticamente um tenant + usuário admin na primeira subida.

Configure no `.env` (troque a senha!):
- `DEFAULT_ADMIN_EMAIL`
- `DEFAULT_ADMIN_PASSWORD`

### Rodar local rápido (DEV) sem Docker

- por padrão o backend usa **SQLite** (`sqlite:///./borges_os.db`)
- copie `.env.example` para `.env` e ajuste o que precisar

Rodar a aplicação:
```bash
uvicorn main:app --reload
```

### Seeds manuais (opcional)
Se preferir criar manualmente:
```bash
python seed_admin.py
```
