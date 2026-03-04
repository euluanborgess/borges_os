const API_BASE_URL = "http://localhost:8000/api/v1";
let currentTenantId = null;
let currentLeadId = null;
let ws = null;

// ======================================
// NAVEGAÇÃO ENTRE ABAS
// ======================================
document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', (e) => {
        document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');

        const targetId = e.target.getAttribute('data-target');
        document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));
        document.getElementById(targetId).classList.add('active');

        if (targetId === 'view-dashboard') loadDashboard();
        if (targetId === 'view-calendar') loadCalendar();
    });
});

// ======================================
// INBOX & WEBSOCKETS (TEMPO REAL)
// ======================================
function connectWebSocket() {
    // ws://localhost:8000/api/v1/ws/inbox/{tenant_id}
    const wsUrl = `ws://localhost:8000/api/v1/ws/inbox/${currentTenantId}`;
    ws = new WebSocket(wsUrl);

    ws.onopen = () => console.log("[WS] Conectado ao Servidor BORGES OS");

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("[WS MSG]", data);

        // Se for mensagem de um Lead enviada no whats
        if (data.type === 'new_message' && data.sender_type === 'lead') {
            appendMessageToUI(data.lead_id, data.content, 'msg-lead');
            addOrUpdateLeadSidebar(data.lead_id, data.lead_phone, data.content);
        }

        // Se a propria IA ou outro sistema enviou
        if (data.event === 'message_sent_by_human') {
            appendMessageToUI(data.lead_id, data.content, 'msg-human');
        }
    };

    ws.onclose = () => {
        console.log("[WS] Desconectado. Tentando reconectar em 3s...");
        setTimeout(connectWebSocket, 3000);
    };
}

// Quando clica num lead na sidebar
function selectLead(leadId, pbIdElement, phone) {
    currentLeadId = leadId;

    // UI Update
    document.querySelectorAll('.lead-item').forEach(el => el.classList.remove('selected'));
    pbIdElement.classList.add('selected');

    document.getElementById('current-lead-name').innerText = `Lead #${leadId.substring(0, 8)}`;
    document.getElementById('current-lead-phone').innerText = phone;

    document.getElementById('crm-panel').classList.remove('d-none');

    // Inputs ativados
    document.getElementById('message-input').disabled = false;
    document.getElementById('send-btn').disabled = false;

    // Buscar historico do banco de dados
    document.getElementById('chat-messages').innerHTML = '';
    fetch(`${API_BASE_URL}/ws/inbox/messages/${currentTenantId}/${leadId}`)
        .then(res => res.json())
        .then(json => {
            if (json.status === 'success') {
                json.data.forEach(m => {
                    // Se for IA, trata visualmente como msg do atendente pra ficar à direita
                    const cssClass = m.sender_type === 'lead' ? 'msg-lead' : 'msg-human';
                    appendMessageToUI(leadId, m.content, cssClass);
                });
            }
        });
}

// Carregar lista de leads com conversas anteriores no boot
async function loadInboxLeads() {
    try {
        const res = await fetch(`${API_BASE_URL}/ws/inbox/leads/${currentTenantId}`);
        const json = await res.json();
        if (json.status === 'success') {
            document.getElementById('leads-list').innerHTML = '';
            // Ordem reversa pois addOrUpdate dá prepend (joga pra cima)
            json.data.reverse().forEach(l => {
                addOrUpdateLeadSidebar(l.id, l.phone, l.last_message);
            });
        }
    } catch (e) { console.error("Erro ao carregar leads", e); }
}

function addOrUpdateLeadSidebar(leadId, phone, lastMsg) {
    const list = document.getElementById('leads-list');
    let item = document.getElementById(`sidebar-lead-${leadId}`);

    if (!item) {
        item = document.createElement('div');
        item.id = `sidebar-lead-${leadId}`;
        item.className = 'lead-item';
        item.innerHTML = `<h5>${phone}</h5><p class="truncate"></p>`;
        item.onclick = () => selectLead(leadId, item, phone);
        list.prepend(item);
    }

    item.querySelector('p').innerText = lastMsg;
}

function appendMessageToUI(msgLeadId, content, cssClass) {
    // Só renderiza se for a conversa aberta agora
    if (currentLeadId !== msgLeadId) return;

    const chat = document.getElementById('chat-messages');

    // Remover o empty state
    const empty = chat.querySelector('.empty-state');
    if (empty) empty.remove();

    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${cssClass}`;
    msgDiv.innerText = content;

    chat.appendChild(msgDiv);
    chat.scrollTop = chat.scrollHeight; // Auto-scroll
}

// Enviar msg manual cortando a IA
document.getElementById('send-btn').addEventListener('click', () => {
    const input = document.getElementById('message-input');
    const text = input.value.trim();
    if (!text || !currentLeadId || !ws) return;

    // Envia o payload via websockets para o Backend lidar
    const payload = {
        action: "send_message",
        lead_id: currentLeadId,
        content: text
    };

    ws.send(JSON.stringify(payload));

    // Adiciona na propria tela ja
    appendMessageToUI(currentLeadId, text, 'msg-human');

    // Mudar UI do Robô para Humano
    const indicator = document.getElementById('ai-indicator');
    indicator.className = "status-badge human";
    indicator.innerText = "🕵️ Humano";

    input.value = "";
});

// ======================================
// DASHBOARD VIEW
// ======================================
async function loadDashboard() {
    try {
        const res = await fetch(`${API_BASE_URL}/dashboard/metrics?tenant_id=${currentTenantId}`);
        const json = await res.json();

        if (json.status === 'success') {
            const data = json.data;
            const grid = document.getElementById('metrics-grid');
            grid.innerHTML = `
                <div class="metric-card">
                    <h5>Pendências Manuais</h5>
                    <div class="value">${data.leads_waiting_human || 0}</div>
                </div>
                <div class="metric-card">
                    <h5>Agendamentos Totais</h5>
                    <div class="value">${data.total_events || 0}</div>
                </div>
                <div class="metric-card">
                    <h5>Tarefas da Equipe</h5>
                    <div class="value">${data.pending_activities || 0}</div>
                </div>
            `;
        }
    } catch (e) {
        console.error("Erro dashboard", e);
    }
}

// ======================================
// CALENDAR VIEW
// ======================================
async function loadCalendar() {
    try {
        const res = await fetch(`${API_BASE_URL}/calendar/?tenant_id=${currentTenantId}`);
        const json = await res.json();

        const list = document.getElementById('events-list');
        list.innerHTML = '';

        if (json.events && json.events.length > 0) {
            json.events.forEach(ev => {
                const dateStart = new Date(ev.start_time).toLocaleString();
                list.innerHTML += `
                    <div class="metric-card" style="margin-bottom: 12px">
                        <h5>${dateStart}</h5>
                        <p style="font-weight: 500">${ev.title}</p>
                    </div>
                `;
            });
        } else {
            list.innerHTML = 'Nenhum evento agendado ainda. Deixe a IA vender por você!';
        }
    } catch (e) {
        console.error("Erro calendário", e);
    }
}

// ======================================
// INICIALIZAÇÃO
// ======================================
async function initApp() {
    try {
        const res = await fetch(`${API_BASE_URL}/tenant`);
        const data = await res.json();
        if (data.id) {
            currentTenantId = data.id;
            console.log("Tenant Ativo:", currentTenantId);
            connectWebSocket();
            loadInboxLeads();
        } else {
            console.error("Nenhum Tenant encontrado no banco de dados.");
        }
    } catch (e) {
        console.error("Erro ao buscar tenant", e);
    }
}

initApp();
