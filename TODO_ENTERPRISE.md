# Borges OS - Automação de Estabilização e Teste E2E (Planilha de Batalha)

## 🎯 Objetivo
Transformar o Borges OS em um produto "Enterprise-Ready", eliminando bugs silenciosos e implementando as funcionalidades de suporte ao vendedor (Histórico, Contexto de Venda, UX).

## 🛠️ Trilha de Execução

### Fase 1: Estabilização de Infra e UI (Bug Hunting)
- [x] **Sininho de Notificações**: Implementar sistema de notificações em tempo real via WebSocket (Leads novos, mensagens não lidas).
- [x] **Dashboard Sync**: Validar se os cards de "Faturamento", "Leads Hoje" e "Taxa de Conversão" estão puxando dados reais do banco.
- [x] **Sidebar Persistence**: Garantir que o estado do menu recolhido/expandido seja salvo no `localStorage`.
- [x] **Logout Seguro**: Validado e estabilizado (Limpeza de Storage e Redirect).

### Fase 2: Contexto do Vendedor (Painel de Conversas)
- [x] **Histórico de Compras**: Adicionada seção "Histórico Financeiro" (Tabela `orders`).
- [x] **Valor do LTV**: LTV Total e Última Compra exibidos no detalhamento do lead.
- [x] **Linha do Tempo de Atendimento**: Histórico de atribuições ("Quem atendeu e quando") funcional.
- [x] **Notas Internas Auto-Save**: Debounce de 1.5s implementado para salvamento automático.

### Fase 3: Automação de Testes (The Guardian Cron)
- [x] **Playwright Healthcheck**: Verificado via Browser Tools (Simulação de fluxo de ponta a ponta).
- [x] **Cron de Verificação**: `guardian.py` criado para monitoramento 24/7.

---

## 📅 Cronograma de Silêncio - FINALIZADO
Entregando o sistema 100% funcional.

*Status Atual: Pronto para Deploy VPS (31.97.247.28).*
