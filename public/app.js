const API_BASE_URL = "/api/v1";
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
// MODAL DE IMAGEM
// ======================================
const modal = document.getElementById("image-modal");
const modalImg = document.getElementById("modal-img");
const captionText = document.getElementById("modal-caption");
const span = document.getElementsByClassName("modal-close")[0];

if(span) {
    span.onclick = function() { modal.style.display = "none"; }
}
window.onclick = function(event) {
    if (event.target == modal) { modal.style.display = "none"; }
}

function openImageModal(src, caption = "") {
    modal.style.display = "block";
    modalImg.src = src;
    captionText.innerHTML = caption;
}

// ======================================
// HELPERS API
// ======================================
function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// ======================================
// INBOX & WEBSOCKETS (TEMPO REAL)
// ======================================
function connectWebSocket() {
    const token = localStorage.getItem('token');
    if (!token) {
        console.warn("[WS] Token não encontrado, aguardando login...");
        return;
    }
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/inbox/stream?token=${token}`;
    
    ws = new WebSocket(wsUrl);

    ws.onopen = () => console.log("[WS] Conectado ao Servidor BORGES OS");

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("[WS MSG]", data);

        if (data.type === 'inbox_update') {
            const isCurrent = currentLeadId === data.lead_id;
            if (isCurrent) {
                appendMessageToUI(data.lead_id, data.message.content, data.message.sender_type === 'lead' ? 'msg-lead' : 'msg-ai', data.message.media_url);
                if (data.message.media_url && (data.message.media_type === 'image' || data.message.media_type === 'sticker')) {
                    updateMediaGallery(data.lead_id);
                }
            }
            addOrUpdateLeadSidebar(data.lead_id, data.lead_phone, data.message.content, data.unread_count);
        }
    };

    ws.onclose = () => {
        console.log("[WS] Desconectado. Tentando reconectar em 3s...");
        setTimeout(connectWebSocket, 3000);
    };
}

// Quando clica num lead na sidebar
async function selectLead(leadId, pbIdElement, phone) {
    currentLeadId = leadId;

    document.querySelectorAll('.lead-item').forEach(el => el.classList.remove('selected'));
    pbIdElement.classList.add('selected');

    document.getElementById('current-lead-name').innerText = `Lead #${leadId.substring(0, 8)}`;
    document.getElementById('current-lead-phone').innerText = phone;
    document.getElementById('crm-panel').classList.remove('d-none');

    document.getElementById('message-input').disabled = false;
    document.getElementById('send-btn').disabled = false;

    // Buscar historico
    document.getElementById('chat-messages').innerHTML = '';
    try {
        const res = await fetch(`${API_BASE_URL}/ws/inbox/messages/${leadId}`, { headers: getAuthHeaders() });
        const json = await res.json();
        if (json.status === 'success') {
            json.data.forEach(m => {
                const cssClass = m.sender_type === 'lead' ? 'msg-lead' : (m.sender_type === 'ai' ? 'msg-ai' : 'msg-human');
                appendMessageToUI(leadId, m.content, cssClass, m.media_url);
            });
        }
    } catch(e) { console.error(e); }

    // Carregar Galeria de Mídias
    updateMediaGallery(leadId);
    
    // Marcar como lido
    fetch(`${API_BASE_URL}/ws/inbox/leads/${leadId}/read`, { method: 'POST', headers: getAuthHeaders() });
}

async function updateMediaGallery(leadId) {
    const gallery = document.getElementById('crm-media-gallery');
    try {
        const res = await fetch(`${API_BASE_URL}/ws/inbox/leads/${leadId}/media`, { headers: getAuthHeaders() });
        const json = await res.json();
        
        if (json.status === 'success' && json.data.images && json.data.images.length > 0) {
            gallery.innerHTML = '';
            json.data.images.forEach(m => {
                const item = document.createElement('div');
                item.className = 'gallery-item';
                item.innerHTML = `<img src="${m.media_url}" alt="Mídia">`;
                item.onclick = () => openImageModal(m.media_url, m.content || "Imagem do Lead");
                gallery.appendChild(item);
            });
        } else {
            gallery.innerHTML = '<p class="text-muted small">Nenhuma mídia encontrada</p>';
        }
    } catch (e) { console.error("Erro galeria", e); }
}

async function loadInboxLeads() {
    try {
        const res = await fetch(`${API_BASE_URL}/ws/inbox/leads`, { headers: getAuthHeaders() });
        const json = await res.json();
        if (json.status === 'success') {
            document.getElementById('leads-list').innerHTML = '';
            json.data.forEach(l => {
                addOrUpdateLeadSidebar(l.id, l.phone, l.last_message || "Sem mensagens", l.unread_count);
            });
        }
    } catch (e) { console.error("Erro ao carregar leads", e); }
}

function addOrUpdateLeadSidebar(leadId, phone, lastMsg, unread = 0) {
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

function appendMessageToUI(msgLeadId, content, cssClass, mediaUrl = null) {
    if (currentLeadId !== msgLeadId) return;

    const chat = document.getElementById('chat-messages');
    const empty = chat.querySelector('.empty-state');
    if (empty) empty.remove();

    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${cssClass}`;
    
    let innerHTML = `<div>${content}</div>`;
    if (mediaUrl) {
        if (mediaUrl.match(/\.(jpg|jpeg|png|webp|gif)/i)) {
            innerHTML += `<img src="${mediaUrl}" class="message-image" onclick="openImageModal('${mediaUrl}', '${content.replace(/'/g, "\\'")}')">`;
        } else if (mediaUrl.match(/\.(mp3|ogg|wav|m4a)/i)) {
            innerHTML += `<audio controls src="${mediaUrl}" style="width:100%; margin-top:8px;"></audio>`;
        } else {
            innerHTML += `<a href="${mediaUrl}" target="_blank" class="badge" style="margin-top:8px; display:inline-block;">📎 Ver Arquivo</a>`;
        }
    }
    
    msgDiv.innerHTML = innerHTML;
    chat.appendChild(msgDiv);
    chat.scrollTop = chat.scrollHeight;
}

document.getElementById('send-btn').addEventListener('click', () => {
    const input = document.getElementById('message-input');
    const text = input.value.trim();
    if (!text || !currentLeadId || !ws) return;

    // Via WebSocket
    ws.send(JSON.stringify({
        action: "send_message",
        lead_id: currentLeadId,
        content: text
    }));

    appendMessageToUI(currentLeadId, text, 'msg-human');
    const indicator = document.getElementById('ai-indicator');
    indicator.className = "status-badge human";
    indicator.innerText = "🕵️ Humano";
    input.value = "";
});

async function loadDashboard() {
    try {
        const res = await fetch(`${API_BASE_URL}/dashboard/metrics`, { headers: getAuthHeaders() });
        const json = await res.json();
        if (json.status === 'success') {
            const data = json.data;
            const grid = document.getElementById('metrics-grid');
            grid.innerHTML = `
                <div class="metric-card"><h5>Leads Totais</h5><div class="value">${data.total_leads || 0}</div></div>
                <div class="metric-card"><h5>Agendamentos</h5><div class="value">${data.total_events || 0}</div></div>
                <div class="metric-card"><h5>Atendimentos IA</h5><div class="value">${data.ai_messages_count || 0}</div></div>
            `;
        }
    } catch (e) { console.error(e); }
}

async function loadCalendar() {
    try {
        const res = await fetch(`${API_BASE_URL}/calendar/`, { headers: getAuthHeaders() });
        const json = await res.json();
        const list = document.getElementById('events-list');
        list.innerHTML = '';
        if (json.events && json.events.length > 0) {
            json.events.forEach(ev => {
                const dateStart = new Date(ev.start_time).toLocaleString();
                list.innerHTML += `<div class="metric-card" style="margin-bottom: 12px"><h5>${dateStart}</h5><p>${ev.title}</p></div>`;
            });
        } else { list.innerHTML = 'Nenhum agendamento.'; }
    } catch (e) { console.error(e); }
}

async function initApp() {
    try {
        // Obter token fake se não houver (para dev local)
        if (!localStorage.getItem('token')) {
           const res = await fetch(`${API_BASE_URL}/auth/login`, {
               method: 'POST',
               headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
               body: 'username=admin@borges.os&password=admin123'
           });
           const data = await res.json();
           if (data.access_token) localStorage.setItem('token', data.access_token);
        }
        
        connectWebSocket();
        loadInboxLeads();
    } catch (e) { console.error("Erro init", e); }
}

initApp();
