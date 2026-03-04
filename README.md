## BORGES OS - Guia Rápido

O Backend do BORGES OS foi inicializado com a estrutura para:
- FastAPI (Rotas API Webhooks e WebSockets)
- PostgreSQL (Banco Crítico de CRM)
- Redis + Celery (Fila para mensagens demoradas/picotadas)

Para rodá-lo (assumindo Docker instalado):
```bash
docker-compose up -d
```
E para rodar a aplicação:
```bash
.\venv\Scripts\activate
uvicorn main:app --reload
```
