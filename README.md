## BORGES OS - Guia Rápido

O Backend do BORGES OS foi inicializado com a estrutura para:
- FastAPI (Rotas API Webhooks e WebSockets)
- PostgreSQL (Banco Crítico de CRM)
- Redis + Celery (Fila para mensagens demoradas/picotadas)

Para rodar com Postgres/Redis/Evolution (produção ou dev completo, assumindo Docker instalado):
```bash
docker compose up -d --build
```

A API sobe em: http://localhost:8000

Para rodar local rápido (DEV) sem Docker:
- por padrão o backend usa **SQLite** (`sqlite:///./borges_os.db`)
- copie `.env.example` para `.env` e ajuste o que precisar

Rodar a aplicação:
```bash
uvicorn main:app --reload
```
