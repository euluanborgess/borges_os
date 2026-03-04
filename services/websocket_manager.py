from typing import Dict, List, Any
from fastapi import WebSocket
import json

class ConnectionManager:
    """
    Gerencia as conexões ativas de WebSockets dos atendentes no Painel.
    Permite enviar atualizações (mensagens novas, leads novos) em tempo real agrupadas por Tenant.
    """
    def __init__(self):
        # Dicionário organizando: { "tenant_id": [WebSocket1, WebSocket2, ...] }
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, tenant_id: str):
        if tenant_id not in self.active_connections:
            self.active_connections[tenant_id] = []
        self.active_connections[tenant_id].append(websocket)
        print(f"[WS] Novo usuário conectado no tenant {tenant_id}")

    def disconnect(self, websocket: WebSocket, tenant_id: str):
        if tenant_id in self.active_connections:
            self.active_connections[tenant_id].remove(websocket)
            if not self.active_connections[tenant_id]:
                del self.active_connections[tenant_id]
        print(f"[WS] Usuário desconectado do tenant {tenant_id}")

    async def broadcast_to_tenant(self, tenant_id: str, message: dict):
        """
        Envia uma mensagem (JSON) para todos os atendentes conectados daquele tenant.
        """
        if tenant_id in self.active_connections:
            text_data = json.dumps(message)
            for connection in self.active_connections[tenant_id]:
                try:
                    await connection.send_text(text_data)
                except Exception as e:
                    print(f"[WS Erro] Falha ao enviar broadcast: {e}")

# Instância global do gerenciador para ser importada nas rotas
manager = ConnectionManager()
