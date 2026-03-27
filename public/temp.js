
        let currentTenantId = null;
        let activeLeadId = null;
        let ws = null;
        let inboxChannelFilter = 'todos';
        let inboxSearchQuery = '';
        let allInboxLeads = [];

        document.addEventListener('DOMContentLoaded', async () => {
            await initializeApp();
            handleInitialRoute(); // SPA Deep Linking
            initAIBrain(); // Base 44 Feature
            initInboxEvents(); // Inbox Real time bindings
            
            // [SUPER ADMIN FIX] - Ensure tenants are fetched if starting on super-admin
            if (window.location.pathname.includes('super')) {
                fetchTenants();
            }

            // Start Dashboard polling mock (animates numbers)
            setInterval(fetchDashboardMock, 5000);
        });

        /* --- SPA ROUTING (HISTORY API) --- */
        window.addEventListener('popstate', (e) => {
            if (e.state && e.state.viewId) {
                switchView(e.state.viewId, null, false);
            } else {
                handleInitialRoute();
            }
        });

        function handleInitialRoute() {
            const path = window.location.pathname.replace(/\/$/, ''); // Remove trailing slash
            let viewId = 'dashboard';

            if (path.includes('pipeline') || path.includes('leads')) viewId = 'pipeline';
            else if (path.includes('inbox') || path.includes('conversas')) viewId = 'inbox';
            else if (path.includes('calendar') || path.includes('agendamentos')) viewId = 'calendar';
            else if (path.includes('tasks') || path.includes('tarefas')) viewId = 'tasks';
            else if (path.includes('contracts') || path.includes('contratos')) viewId = 'contracts';
            else if (path.includes('ai') || path.includes('borges')) viewId = 'ai';
            else if (path.includes('reports') || path.includes('relatorios')) viewId = 'reports';
            else if (path.includes('audit') || path.includes('logs')) viewId = 'audit';
            else if (path.includes('super')) viewId = 'super-admin';
            else if (path.includes('settings') || path.includes('config')) viewId = 'settings';

            // Set initial state silently and switch UI
            window.history.replaceState({ viewId }, "", path || '/');
            switchView(viewId, null, false);
        }

        function switchView(viewId, btnEl = null, updateUrl = true) {
            // Hide all views
            document.querySelectorAll('.app-view').forEach(el => {
                el.classList.remove('active');
            });
            
            // Remove active classes from nav items
            document.querySelectorAll('.nav-item').forEach(el => {
                el.classList.remove('nav-active', 'text-white');
                el.classList.add('text-[#8b8b9e]', 'hover:text-white', 'hover:bg-[#1c1c28]');
                const icon = el.querySelector('i');
                if (icon) icon.classList.remove('text-cyan-400');
            });

            // Show target view
            const target = document.getElementById('view-' + viewId);
            if (target) {
                target.classList.add('active');
            }

            // Highlight nav button dynamically
            const targetBtn = btnEl || document.querySelector(`.nav-item[onclick*="switchView('${viewId}'"]`);
            if (targetBtn && targetBtn.classList.contains('nav-item')) {
                targetBtn.classList.remove('text-[#8b8b9e]', 'hover:text-white', 'hover:bg-[#1c1c28]');
                targetBtn.classList.add('nav-active', 'text-white');
                const icon = targetBtn.querySelector('i');
                if (icon) icon.classList.add('text-cyan-400');
            }

            if (updateUrl) {
                let pathName = '/' + viewId;
                if (viewId === 'dashboard') pathName = '/';
                if (viewId === 'pipeline') pathName = '/leads';
                if (viewId === 'super-admin') pathName = '/super';
                window.history.pushState({ viewId }, "", pathName);
            }

            // Route-specific side-effects
            if (viewId === 'pipeline' || viewId === 'inbox') fetchKanbanData();
            if (viewId === 'inbox') fetchInboxLeads();
            if (viewId === 'calendar') fetchAppointments();
            if (viewId === 'contracts') fetchContracts();
            if (viewId === 'reports') initReports();
            if (viewId === 'audit') fetchAuditLogs();
            if (viewId === 'settings') initSettings();
            if (viewId === 'super-admin') fetchTenants();
        }

        /* --- API CALLS --- */
        async function fetchWithAuth(url, options = {}) {
            if (!window.authHeaders) return fetch(url, options); // fallback

            const newOptions = { ...options };
            newOptions.headers = {
                ...window.authHeaders,
                ...(options.headers || {})
            };

            const res = await fetch(url, newOptions);
            if (res.status === 401) {
                localStorage.removeItem('borges_token');
                localStorage.removeItem('borges_user');
                window.location.href = '/login.html';
            }
            return res;
        }

        async function initializeApp() {
            // [SAAS SECURITY] - Auth Guard
            const token = localStorage.getItem('borges_token');
            const userStr = localStorage.getItem('borges_user');

            if (!token || !userStr) {
                window.location.href = '/login.html';
                return;
            }

            const user = JSON.parse(userStr);
            console.log("Usuário Autenticado:", user.full_name, "| Role:", user.role);

            // [SAAS RBAC] - Hiding Master Menus from regular users
            if (user.role === 'user') {
                const settingsBtn = document.getElementById('nav-btn-settings');
                const aiBtn = document.getElementById('nav-btn-ai');
                if (settingsBtn) settingsBtn.style.display = 'none';
                if (aiBtn) aiBtn.style.display = 'none';
            }
            if (user.role === 'super_admin') {
                const superAdminBtn = document.getElementById('nav-btn-superadmin');
                if (superAdminBtn) superAdminBtn.style.display = 'flex';
            }

            // Exibir Nome do Usuário na Sidebar
            const elSidebarName = document.getElementById('sidebar-name');
            if (elSidebarName) elSidebarName.innerText = user.full_name;
            const elSidebarAvatar = document.getElementById('sidebar-avatar');
            if (elSidebarAvatar) elSidebarAvatar.innerText = user.full_name.charAt(0).toUpperCase();

            // Set global auth headers for specific functions if needed
            window.authHeaders = {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            };

            try {
                const res = await fetchWithAuth('/api/v1/tenant');
                if (!res.ok) {
                    if (res.status === 401) {
                        localStorage.removeItem('borges_token');
                        window.location.href = '/login.html';
                        return;
                    }
                    throw new Error("API not ok");
                }
                const t = await res.json();

                fetchDashboardMock();
                connectWebSocket();
            } catch (e) { console.error(" Init Error", e); }
        }

        async function fetchDashboardMock() {

            try {
                const res = await fetchWithAuth(`/api/v1/dashboard/metrics`);
                if (!res.ok) throw new Error("API not ok");
                const metrics = await res.json();
                if (metrics.status === 'success') {
                    const data = metrics.data;
                    let tCount = 0;
                    for (const s in data.pipeline_breakdown) {
                        tCount += data.pipeline_breakdown[s];
                    }

                    const elTotalLeads = document.getElementById('metric-total-leads');
                    const elMeetings = document.getElementById('metric-meetings');
                    const elInteractions = document.getElementById('metric-interactions');

                    if (elTotalLeads) animateValue("metric-total-leads", parseInt(elTotalLeads.innerText) || 0, tCount, 1000);
                    if (elMeetings) animateValue("metric-meetings", parseInt(elMeetings.innerText) || 0, data.total_events || 0, 1000);
                    if (elInteractions) animateValue("metric-interactions", parseInt(elInteractions.innerText) || 0, data.waiting_human || 0, 1000);

                    // Dashboard Base 44 Pipeline Overview Mocks Baseados no tCount real
                    const closedRev = Math.floor((data.total_events || 0) * 1250);
                    const estRev = Math.floor(tCount * 4500);
                    const convRate = tCount > 0 ? ((data.total_events / tCount) * 100).toFixed(1) : 0;

                    const elStatTotal = document.getElementById('stat-total-leads');
                    const elStatHot = document.getElementById('stat-hot-leads');
                    const elStatEstRev = document.getElementById('stat-estimated-revenue');
                    const elStatClosedRev = document.getElementById('stat-closed-revenue');
                    const elStatConvRate = document.getElementById('stat-conversion-rate');
                    const elStatTodayMet = document.getElementById('stat-today-meetings');
                    const elStatPendingTasks = document.getElementById('stat-pending-tasks');
                    const elStatActiveConvs = document.getElementById('stat-active-convs');
                    const elStatNoReply = document.getElementById('stat-no-reply');

                    if (elStatTotal) animateValue("stat-total-leads", parseInt(elStatTotal.innerText) || 0, tCount, 1000);
                    if (elStatHot) animateValue("stat-hot-leads", parseInt(elStatHot.innerText) || 0, Math.floor(tCount * 0.4), 1000);
                    if (elStatEstRev) elStatEstRev.innerText = `R$ ${estRev.toLocaleString('pt-BR')}`;
                    if (elStatClosedRev) elStatClosedRev.innerText = `R$ ${closedRev.toLocaleString('pt-BR')}`;
                    if (elStatConvRate) elStatConvRate.innerText = `${convRate}% conversão`;
                    if (elStatTodayMet) animateValue("stat-today-meetings", parseInt(elStatTodayMet.innerText) || 0, data.total_events || 0, 1000);
                    if (elStatPendingTasks) animateValue("stat-pending-tasks", parseInt(elStatPendingTasks.innerText) || 0, (data.waiting_human || 0) * 2, 1000);
                    if (elStatActiveConvs) animateValue("stat-active-convs", parseInt(elStatActiveConvs.innerText) || 0, tCount > 0 ? tCount - (data.waiting_human || 0) : 0, 1000);
                    if (elStatNoReply) animateValue("stat-no-reply", parseInt(elStatNoReply.innerText) || 0, Math.floor(tCount * 0.2), 1000);
                }
            } catch (e) { }
        }

        function animateValue(id, start, end, duration) {
            if (start === end) return;
            const obj = document.getElementById(id);
            if (!obj) return;
            let startTimestamp = null;
            const step = (timestamp) => {
                if (!startTimestamp) startTimestamp = timestamp;
                const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                obj.innerHTML = Math.floor(progress * (end - start) + start);
                if (progress < 1) window.requestAnimationFrame(step);
            };
            window.requestAnimationFrame(step);
        }

        /* --- KANBAN LOGIC --- */
        const stageConfig = {
            novo: { label: "Novo", color: "#8b5cf6", emoji: "🆕" },
            contato: { label: "Contato", color: "#3b82f6", emoji: "📞" },
            qualificacao: { label: "Qualificação", color: "#06b6d4", emoji: "🎯" },
            agendamento: { label: "Agendamento", color: "#22c55e", emoji: "📅" },
            reuniao: { label: "Reunião", color: "#f59e0b", emoji: "🤝" },
            proposta: { label: "Proposta", color: "#f97316", emoji: "📋" },
            fechado: { label: "Fechado", color: "#10b981", emoji: "✅" },
            perdido: { label: "Perdido", color: "#ef4444", emoji: "❌" },
            desqualificado: { label: "Desqualificado", color: "#6b7280", emoji: "⛔" },
        };

        // Adicionar aliases para compatibilidade com a IA
        const stageAliases = {
            "qualificado": "qualificacao",
            "venda": "fechado",
            "fechada": "fechado",
            "reunião": "reuniao",
            "prospecção": "contato"
        };

        function getBadgeCol(temp) {
            let t = (temp || 'frio').toLowerCase();
            if (t.includes('quente') || t.includes('alta')) return 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30';
            if (t.includes('morno') || t.includes('media')) return 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30';
            return 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30';
        }

        function buildCard(lead) {
            const letter = (lead.name && lead.name !== "Desconhecido") ? lead.name.charAt(0) : "W";
            const nome = (lead.name && lead.name !== "Desconhecido") ? lead.name : lead.phone;
            const badgeCls = getBadgeCol(lead.temperature);

            const stage = (lead.pipeline_stage || "novo").toLowerCase();
            const isClosed = stage === "fechado";
            const isLost = stage === "perdido";
            const isDisqualified = stage === "desqualificado";

            const hoverBorder = isClosed
                ? "hover:border-green-500/30 hover:shadow-[0_0_20px_rgba(34,197,94,0.08)]"
                : isLost ? "hover:border-red-500/30 hover:shadow-[0_0_20px_rgba(239,68,68,0.08)]"
                    : isDisqualified ? "hover:border-gray-400/30 hover:shadow-[0_0_20px_rgba(200,200,200,0.06)]"
                        : "hover:border-cyan-500/30 hover:shadow-[0_0_20px_rgba(6,182,212,0.08)]";

            const avatarBg = isClosed
                ? "bg-gradient-to-br from-green-600/30 to-green-600/30"
                : isLost ? "bg-gradient-to-br from-red-600/30 to-red-600/30"
                    : isDisqualified ? "bg-gradient-to-br from-gray-500/30 to-gray-500/30"
                        : "bg-gradient-to-br from-cyan-600/30 to-cyan-600/30";

            const nameHover = isClosed
                ? "group-hover:text-green-300"
                : isLost ? "group-hover:text-red-300"
                    : isDisqualified ? "group-hover:text-gray-300"
                        : "group-hover:text-cyan-300";

            const leadStr = JSON.stringify(lead).replace(/'/g, "&apos;").replace(/"/g, "&quot;");
            const txt = (lead.last_message && lead.last_message !== "Conversa iniciada") ? lead.last_message.substring(0, 70) + '...' : 'Aguardando processamento de linguagem...';

            return `
                <div class="lead-card p-4 rounded-xl cursor-pointer transition-all duration-200 group ${hoverBorder}" 
                    draggable="true" ondragstart="onLeadDragStart(event, '${lead.id}')" 
                    onclick='openLeadModal(${leadStr})' 
                    style="background: rgba(255,255,255,0.04); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.07); box-shadow: 0 2px 12px rgba(0,0,0,0.2);">
                    
                    <div class="flex items-start justify-between mb-3">
                        <div class="flex items-center gap-2">
                            <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white ${avatarBg} overflow-hidden">
                                ${(lead.profile_data && lead.profile_data.picture) ? `<img src="${lead.profile_data.picture}" class="w-full h-full object-cover" />` : letter.toUpperCase()}
                            </div>
                            <div>
                                <p class="text-sm font-semibold text-white transition-colors ${nameHover}">${nome}</p>
                            </div>
                        </div>
                        ${(lead.score > 70) ? '<i class="fa-solid fa-star text-yellow-400 text-sm"></i>' : ''}
                    </div>

                    <div class="flex items-center gap-2 mb-3">
                        <span class="px-2 py-0.5 rounded text-[10px] uppercase font-medium border ${badgeCls}">${lead.temperature === "quente" ? "Alta" : lead.temperature === "morno" ? "Média" : "Baixa"}</span>
                        <span class="text-[10px] text-[#5a5a6e]">🔗</span>
                    </div>

                    ${lead.phone ? `
                    <div class="flex items-center gap-1.5 text-xs text-[#8b8b9e] mb-1">
                        <i class="fa-solid fa-phone w-3 h-3 flex items-center justify-center text-[10px]"></i>
                        <span>${lead.phone}</span>
                    </div>` : ''}

                    ${lead.email ? `
                    <div class="flex items-center gap-1.5 text-xs text-[#8b8b9e] mb-2">
                        <i class="fa-solid fa-envelope w-3 h-3 flex items-center justify-center text-[10px]"></i>
                        <span class="truncate">${lead.email}</span>
                    </div>` : ''}

                    <p class="text-[11px] text-[#5a5a6e] mb-3 line-clamp-2 italic">
                        RESUMO: ${txt}
                    </p>

                    <div class="flex items-center justify-between pt-2 border-t border-[#1e1e2e]">
                        <div class="flex-1">
                            <div class="flex items-center justify-between mb-1">
                                <span class="text-[9px] text-[#5a5a6e] uppercase font-bold">Score</span>
                                <span class="text-[9px] text-cyan-400 font-bold">${lead.score || 0}%</span>
                            </div>
                            <div class="w-full h-1 bg-[#1e1e2e] rounded-full overflow-hidden">
                                <div class="h-full bg-gradient-to-r from-cyan-600 to-cyan-400 rounded-full transition-all duration-500" style="width: ${lead.score || 0}%"></div>
                            </div>
                        </div>
                        <div class="flex items-center gap-2 ml-3">
                            ${(lead.estimated_value && lead.estimated_value > 0) ? `<span class="text-xs text-green-400 font-medium">R$ ${lead.estimated_value.toLocaleString('pt-BR')}</span>` : ''}
                        </div>
                    </div>
                </div>
            `;
        }

        function initKanbanLayout() {
            const container = document.getElementById("kanban-columns-container");
            if (!container) return;
            container.innerHTML = "";
            Object.keys(stageConfig).forEach(stage => {
                const conf = stageConfig[stage];
                container.innerHTML += `
                    <div class="flex-shrink-0 w-[280px] flex flex-col rounded-2xl p-3" 
                        style="height: calc(100vh - 64px - 160px); min-height: 0; background: rgba(255,255,255,0.03); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.06); box-shadow: 0 4px 24px rgba(0,0,0,0.25);">
                        
                        <!-- Header -->
                        <div class="mb-3">
                            <div class="flex items-center justify-between mb-2">
                                <div class="flex items-center gap-2">
                                    <div class="w-2 h-2 rounded-full" style="background-color: ${conf.color}"></div>
                                    <span class="text-sm font-semibold text-white">${conf.label}</span>
                                    <span class="text-xs px-2 py-0.5 rounded-full bg-[#1e1e2e] text-[#8b8b9e]" id="kanban-count-${stage}">0</span>
                                </div>
                                <button class="p-1 rounded-md text-[#5a5a6e] hover:text-white hover:bg-[#1c1c28] transition-colors"><i class="fa-solid fa-plus w-3 h-3"></i></button>
                            </div>
                            
                            <div class="flex items-center gap-3 text-[10px] text-[#5a5a6e]">
                                <span id="kanban-est-${stage}">R$ 0 Est.</span>
                                <span id="kanban-paid-${stage}">0 Pagos</span>
                            </div>
                            <div class="mt-1.5 flex items-center gap-2">
                                <div class="flex-1 h-1 bg-[#1e1e2e] rounded-full overflow-hidden">
                                    <div class="h-full rounded-full transition-all" id="kanban-bar-${stage}" style="width: 0%; background-color: ${conf.color}"></div>
                                </div>
                                <span class="text-[10px] text-[#5a5a6e]" id="kanban-perc-${stage}">0.0%</span>
                            </div>
                        </div>

                        <!-- Cards -->
                        <div class="flex-1 overflow-y-auto space-y-3 pr-1 content-area custom-scroll" style="min-height: 0;" id="kanban-stage-${stage}" ondragover="onStageDragOver(event)" ondrop="onStageDrop(event, '${stage}')">
                            <!-- Skeleton wait before real data... -->
                        </div>
                    </div>
                `;
            });
        }

        // --- Drag & drop Kanban (manual stage changes) ---
        let draggedLeadId = null;

        function onLeadDragStart(ev, leadId) {
            draggedLeadId = leadId;
            try { ev.dataTransfer.setData('text/plain', leadId); } catch (e) {}
        }

        function onStageDragOver(ev) {
            ev.preventDefault();
        }

        async function onStageDrop(ev, stage) {
            ev.preventDefault();
            const leadId = (ev.dataTransfer && ev.dataTransfer.getData('text/plain')) || draggedLeadId;
            if (!leadId) return;

            try {
                await fetchWithAuth(`/api/v1/ws/inbox/leads/${leadId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ pipeline_stage: stage })
                });
            } catch (e) {}

            // Refresh both views
            fetchKanbanData();
            fetchInboxLeads();
        }

        async function fetchKanbanData() {

            try {
                const res = await fetchWithAuth(`/api/v1/ws/inbox/leads`);
                if (!res.ok) throw new Error("API not ok");
                const payload = await res.json();
                if (payload && payload.data) {

                    // Initialization the first time if needed, layout will be injected here.
                    const container = document.getElementById("kanban-columns-container");
                    if (container && container.children.length === 0) {
                        initKanbanLayout();
                    }

                    let stats = { total_est: 0, total_leads: payload.data.length, closed_leads: 0 };
                    let stageData = {};
                    Object.keys(stageConfig).forEach(s => stageData[s] = { leads: [], est: 0, converted: 0 });

                    payload.data.forEach(lead => {
                        let st = (lead.pipeline_stage || "novo").toLowerCase();
                        let targetStage = (st in stageConfig) ? st : (stageAliases[st] || "novo");
                        console.log(`Lead ${lead.id} stage ${st} -> target ${targetStage}`);

                        stageData[targetStage].leads.push(lead);
                        stageData[targetStage].est += (lead.estimated_value || 0);
                        if (lead.is_converted || lead.pipeline_stage === "fechado") {
                            stageData[targetStage].converted++;
                            stats.closed_leads++;
                        }

                        stats.total_est += (lead.estimated_value || 0);
                    });

                    // Update globals stats header
                    const elTotal = document.getElementById('crm-total-leads');
                    const elEst = document.getElementById('crm-total-est');
                    const elConv = document.getElementById('crm-conv-rate');
                    if (elTotal) elTotal.innerText = stats.total_leads;
                    if (elEst) elEst.innerText = "R$ " + stats.total_est.toLocaleString('pt-BR');
                    if (elConv) elConv.innerText = stats.total_leads > 0 ? ((stats.closed_leads / stats.total_leads) * 100).toFixed(1) + "%" : "0.0%";

                    // Render cards into stages
                    Object.keys(stageConfig).forEach(stage => {
                        const sData = stageData[stage];
                        const area = document.getElementById(`kanban-stage-${stage}`);
                        const cBadge = document.getElementById(`kanban-count-${stage}`);
                        const estBadge = document.getElementById(`kanban-est-${stage}`);
                        const paidBadge = document.getElementById(`kanban-paid-${stage}`);
                        const bar = document.getElementById(`kanban-bar-${stage}`);
                        const perc = document.getElementById(`kanban-perc-${stage}`);

                        if (cBadge) cBadge.innerText = sData.leads.length;
                        if (estBadge) estBadge.innerText = `R$ ${sData.est.toLocaleString('pt-BR')} Est.`;
                        if (paidBadge) paidBadge.innerText = `${sData.converted} Pagos`;

                        let cvRate = sData.leads.length > 0 ? ((sData.converted / sData.leads.length) * 100).toFixed(1) : "0.0";
                        if (bar) bar.style.width = `${cvRate}%`;
                        if (perc) perc.innerText = `${cvRate}%`;

                        if (area) {
                            if (sData.leads.length > 0) {
                                area.innerHTML = "";
                                sData.leads.forEach(l => area.innerHTML += buildCard(l));
                            } else {
                                area.innerHTML = `
                                    <div class="flex flex-col items-center justify-center py-10 text-[#3a3a4e]">
                                        <span class="text-3xl mb-2">📭</span>
                                        <p class="text-xs">Vazio</p>
                                    </div>
                                `;
                            }
                        }
                    });

                    // (Legacy code to update Inbox list from Kanban was here, removed to use dedicated fetchInboxLeads)
                }
            } catch (e) { }
        }

        /* --- INBOX SPECIFIC LOGIC --- */
        async function fetchInboxLeads() {
            const list = document.getElementById('inbox-leads-list');
            if (!list) return;

            try {
                const res = await fetchWithAuth(`/api/v1/ws/inbox/leads`);
                if (!res.ok) throw new Error("API not ok");
                const payload = await res.json();
                allInboxLeads = payload.data || [];
                renderInboxList();
            } catch (e) {
                list.innerHTML = `<div class="text-xs text-red-500 p-4">Erro ao carregar conversas</div>`;
            }
        }

        function renderInboxList() {
            const list = document.getElementById('inbox-leads-list');
            if (!list) return;

            // Filtrar por canal
            let filtered = allInboxLeads;
            if (inboxChannelFilter !== 'todos') {
                filtered = filtered.filter(l => (l.channel || 'whatsapp') === inboxChannelFilter);
            }
            // Filtrar por busca
            if (inboxSearchQuery) {
                const q = inboxSearchQuery.toLowerCase();
                filtered = filtered.filter(l =>
                    (l.name || '').toLowerCase().includes(q) ||
                    (l.phone || '').includes(q)
                );
            }

            // Contagem no header
            const countEl = document.getElementById('inbox-count-badge');
            if (countEl) countEl.innerText = `(${allInboxLeads.length})`;

            list.innerHTML = '';
            if (filtered.length === 0) {
                list.innerHTML = `<div class="flex flex-col items-center justify-center p-8 text-[#5a5a6e] text-center"><i class="fa-regular fa-comments text-3xl mb-2"></i><span class="text-xs">Nenhum chat encontrado</span></div>`;
                return;
            }

            filtered.forEach(lead => {
                const name = (lead.name && lead.name !== "Desconhecido") ? lead.name : lead.phone;
                const letter = name.charAt(0).toUpperCase();
                const leadStr = JSON.stringify(lead).replace(/'/g, "&apos;").replace(/"/g, "&quot;");

                const isSelected = window.activeLeadId === lead.id;
                const bgClass = isSelected ? "bg-[#111118] border-l-2 border-cyan-400" : "bg-transparent border-l-2 border-transparent hover:bg-[#111118]/50";

                const lastMsg = lead.last_message || "Iniciar conversa";
                // Preview com ícone de mídia
                let previewMsg = lastMsg;
                if (lead.last_message_media_type === 'audio') previewMsg = '🎤 Áudio';
                else if (lead.last_message_media_type === 'image') previewMsg = '📷 Imagem';
                else if (lead.last_message_media_type === 'document') previewMsg = '📄 Documento';
                else if (lead.last_message_media_type === 'video') previewMsg = '🎥 Vídeo';
                else if (lead.last_message_media_type === 'sticker') previewMsg = '🏷️ Sticker';

                const unread = lead.unread_count || 0;
                const unreadBadge = unread > 0
                    ? `<span class="bg-emerald-500 text-white text-[10px] font-bold w-5 h-5 rounded-full flex items-center justify-center shadow-[0_0_8px_rgba(16,185,129,0.4)]">${unread > 99 ? '99+' : unread}</span>`
                    : '';

                const channelIcon = (lead.channel || 'whatsapp') === 'instagram'
                    ? `<i class="fa-brands fa-instagram text-[10px] text-pink-500"></i>`
                    : `<i class="fa-brands fa-whatsapp text-[10px] text-emerald-500"></i>`;

                list.innerHTML += `
                    <div class="${bgClass} px-3 py-3 border-b border-[#1e1e2e] cursor-pointer transition-colors" onclick='openInboxMaster(${leadStr})'>
                        <div class="flex items-center gap-3">
                            <div class="relative shrink-0">
                                <div class="w-10 h-10 rounded-full bg-cyan-500 flex items-center justify-center text-white font-semibold shadow-[0_0_10px_rgba(6,182,212,0.3)] overflow-hidden">
                                    ${(lead.profile_data && lead.profile_data.picture) ? `<img src="${lead.profile_data.picture}" class="w-full h-full object-cover" onerror="this.outerHTML='${letter}'" />` : letter}
                                </div>
                                <div class="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-[#0a0a0f] flex items-center justify-center border-[1.5px] border-[#0a0a0f]">
                                    ${channelIcon}
                                </div>
                            </div>
                            <div class="flex-1 min-w-0">
                                <div class="flex justify-between items-start mb-0.5">
                                    <h4 class="text-gray-200 text-sm font-semibold truncate leading-tight flex-1">${name}</h4>
                                    <span class="text-[10px] text-[#5a5a6e] whitespace-nowrap ml-2">${timeAgoBr(lead.last_message_at || lead.updated_at)}</span>
                                </div>
                                <div class="flex justify-between items-center mt-1">
                                    <span class="text-xs text-[#8b8b9e] truncate pr-2 flex-1">${previewMsg}</span>
                                    ${unreadBadge}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
        }

        function filterInboxByChannel(channel) {
            inboxChannelFilter = channel;
            // Update button styles
            document.querySelectorAll('.inbox-filter-btn').forEach(btn => {
                if (btn.dataset.channel === channel) {
                    btn.className = 'inbox-filter-btn bg-cyan-500/15 text-cyan-400 px-3 py-1.5 rounded text-xs font-semibold border border-cyan-500/30 transition-all';
                } else {
                    btn.className = 'inbox-filter-btn bg-transparent text-[#5a5a6e] hover:text-white px-3 py-1.5 rounded text-xs transition-all border border-transparent';
                }
            });
            renderInboxList();
        }

        /* --- TASKS V2 --- */
        let currentTaskTab = 'me'; // 'me' or 'team'
        let allTasksCache = [];

        async function initTasks() {

            switchTasksTab('me');
        }

        function switchTasksTab(tab) {
            currentTaskTab = tab;
            document.getElementById('task-tab-me').className = tab === 'me' ? "px-4 py-2 rounded-lg text-sm font-semibold transition-all border bg-cyan-500/15 text-cyan-300 border-cyan-500/30" : "px-4 py-2 rounded-lg text-sm font-semibold transition-all border bg-transparent text-[#5a5a6e] border-transparent hover:text-white";
            document.getElementById('task-tab-team').className = tab === 'team' ? "px-4 py-2 rounded-lg text-sm font-semibold transition-all border bg-cyan-500/15 text-cyan-300 border-cyan-500/30" : "px-4 py-2 rounded-lg text-sm font-semibold transition-all border bg-transparent text-[#5a5a6e] border-transparent hover:text-white";

            fetchTasks();
        }

        async function fetchTasks() {
            const list = document.getElementById('tasks-board-list');
            if (!list) return;
            list.innerHTML = `<div class="flex flex-col items-center justify-center py-20 text-[#5a5a6e]"><i class="fa-solid fa-circle-notch fa-spin text-3xl mb-3"></i><p>Carregando tarefas...</p></div>`;

            try {
                const userStr = localStorage.getItem('borges_user');
                const user = userStr ? JSON.parse(userStr) : null;
                const me = (user && user.full_name) ? encodeURIComponent(user.full_name) : "";

                const url = currentTaskTab === 'me' && me ? `/api/v1/ws/tasks/?assigned_to=${me}` : `/api/v1/ws/tasks/`;
                const res = await fetchWithAuth(url);
                if (res.ok) {
                    const payload = await res.json();
                    allTasksCache = payload.data || [];
                    renderTasks();
                }
            } catch (e) { list.innerHTML = `<p class="text-sm text-red-500 text-center py-10">Erro de conexão</p>`; }
        }

        function renderTasks() {
            const list = document.getElementById('tasks-board-list');
            if (!list) return;
            list.innerHTML = "";
            if (allTasksCache.length === 0) {
                list.innerHTML = `
                    <div class="flex flex-col items-center justify-center py-24 text-[#3a3a4e]">
                        <i class="fa-solid fa-clipboard-check text-5xl mb-4 opacity-50"></i>
                        <h3 class="text-lg font-bold text-[#5a5a6e]">Nenhuma tarefa no momento</h3>
                        <p class="text-sm mt-1">Você está em dia com suas atividades!</p>
                    </div>`;
                return;
            }

            allTasksCache.forEach(t => {
                const priorityCol = t.priority === 'alta' ? 'text-red-400 bg-red-500/10 border-red-500/30' : (t.priority === 'media' ? 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30' : 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30');
                const isComp = t.is_completed;
                const statusIcon = isComp ? '<i class="fa-solid fa-circle-check text-emerald-500 text-xl"></i>' : '<i class="fa-regular fa-circle text-[#5a5a6e] hover:text-cyan-400 transition-colors text-xl"></i>';
                const opacityClass = isComp ? 'opacity-50 grayscale-[50%]' : 'opacity-100';

                list.innerHTML += `
                    <div class="glass-panel p-4 rounded-xl border-[#1e1e2e] bg-[#0a0a0f] flex items-start gap-4 hover:border-cyan-500/30 transition-all shadow-[0_4px_20px_rgba(0,0,0,0.2)] ${opacityClass} mb-3 group">
                        <button onclick="toggleTaskComplete('${t.id}', ${!isComp})" class="mt-0.5 shrink-0 focus:outline-none">
                            ${statusIcon}
                        </button>
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-3 mb-1.5">
                                <h3 class="font-bold text-gray-200 text-[15px] truncate ${isComp ? 'line-through text-[#5a5a6e]' : ''}">${t.title}</h3>
                                <span class="px-2 py-0.5 rounded text-[9px] uppercase font-bold tracking-wider border shrink-0 ${priorityCol}">${t.priority}</span>
                            </div>
                            ${t.description ? `<p class="text-xs text-[#8b8b9e] line-clamp-2 mb-3 leading-relaxed">${t.description}</p>` : ''}
                            
                            <div class="flex items-center gap-3 mt-2">
                                <div class="flex items-center gap-1.5 text-[10px] uppercase font-semibold text-[#8b8b9e] bg-[#111118] px-2.5 py-1 rounded border border-[#1e1e2e]">
                                    <i class="fa-regular fa-calendar"></i> ${t.due_date ? new Date(t.due_date).toLocaleDateString('pt-BR') : 'Sem prazo'}
                                </div>
                                <div class="flex items-center gap-1.5 text-[10px] uppercase font-semibold text-cyan-500/80 bg-cyan-500/10 px-2.5 py-1 rounded border border-cyan-500/20">
                                    <i class="fa-solid fa-user-tag text-[9px]"></i> ${t.assigned_to || 'Ninguém'}
                                </div>
                                ${t.lead ? `
                                <div class="flex items-center gap-1.5 text-[10px] font-semibold text-emerald-500/80 bg-emerald-500/10 px-2.5 py-1 rounded border border-emerald-500/20 cursor-pointer hover:bg-emerald-500/20 transition-colors">
                                    <i class="fa-brands fa-whatsapp text-[10px]"></i> ${t.lead.name || t.lead.phone}
                                </div>
                                ` : ''}
                            </div>
                        </div>
                        <button onclick="deleteTask('${t.id}')" class="text-[#5a5a6e] hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all shrink-0">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </div>
                `;
            });
        }

        async function toggleTaskComplete(id, complete) {
            try {
                await fetchWithAuth(`/api/v1/ws/tasks/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ is_completed: complete })
                });
                fetchTasks();
            } catch (e) { }
        }

        async function deleteTask(id) {
            if (!confirm('Excluir tarefa permanentemente da lista?')) return;
            try {
                await fetchWithAuth(`/api/v1/ws/tasks/${id}`, { method: 'DELETE' });
                fetchTasks();
            } catch (e) { }
        }

        function openTaskModal() {
            const m = document.getElementById('modal-new-task');
            if (m) {
                m.classList.remove('hidden');
                m.classList.add('flex');
            }
        }
        function closeTaskModal() {
            const m = document.getElementById('modal-new-task');
            if (m) {
                m.classList.add('hidden');
                m.classList.remove('flex');
                document.getElementById('form-new-task').reset();
            }
        }

        async function submitTask(e) {
            e.preventDefault();
            const btn = document.getElementById('btn-save-task');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Salvando...';
            btn.disabled = true;

            const payload = {
                title: document.getElementById('task-input-title').value,
                description: document.getElementById('task-input-desc').value,
                assigned_to: document.getElementById('task-input-assignee').value,
                priority: document.getElementById('task-input-priority').value,
                due_date: document.getElementById('task-input-date').value || null
            };

            try {
                await fetchWithAuth(`/api/v1/ws/tasks/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                closeTaskModal();
                fetchTasks(); // Reloads the board
            } catch (e) { console.error('Error saving task', e); }

            btn.innerHTML = originalText;
            btn.disabled = false;
        }

        /* --- END TASKS V2 --- */

        /* --- DRAWER (HUD) --- */
        async function openDrawer(lead) {
            activeLeadId = lead.id;
            const nome = (lead.name && lead.name !== "Desconhecido") ? lead.name : lead.phone;

            const dName = document.getElementById('draw-name');
            if (dName) dName.innerText = nome;
            const dPhone = document.getElementById('draw-phone');
            if (dPhone) dPhone.innerText = lead.phone;
            const dAvatar = document.getElementById('draw-avatar');
            if (dAvatar) dAvatar.innerText = nome.charAt(0).toUpperCase();
            const dStage = document.getElementById('draw-stage-txt');
            if (dStage) dStage.innerText = lead.pipeline_stage || "PROSPECÇÃO";

            const dTags = document.getElementById('draw-tags-container');
            if (dTags) {
                dTags.innerHTML = `<span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${getBadgeCol(lead.temperature)}">${lead.temperature || 'FRIO'}</span>`;
            }

            const score = lead.score || 0;
            const dScore = document.getElementById('draw-score-txt');
            if (dScore) dScore.innerText = score + " pts";
            const bar = document.getElementById('draw-score-bar');
            if (bar) setTimeout(() => { bar.style.width = score + "%"; }, 100);

            let tmr = lead.temperature || 'frio';
            const dSummary = document.getElementById('draw-ai-summary');
            if (dSummary) dSummary.innerText = `O lead trocou mensagens no estágio atual.Temperatura calculada como "${tmr}".Probabilidade de fechamento em análise algorítmica.`;

            const dOverlay = document.getElementById('drawer-overlay');
            if (dOverlay) dOverlay.classList.add('open');
            const dPanel = document.getElementById('drawer-panel');
            if (dPanel) setTimeout(() => { dPanel.classList.add('open'); }, 10);

            await loadChat(lead.id);
        }

        function closeDrawer(e) {
            if (e && e.target.id !== 'drawer-overlay' && e.target.tagName !== 'BUTTON' && !e.target.closest('button')) return;
            const dPanel = document.getElementById('drawer-panel');
            if (dPanel) dPanel.classList.remove('open');
            const dOverlay = document.getElementById('drawer-overlay');
            if (dOverlay) setTimeout(() => { dOverlay.classList.remove('open'); }, 300);

            toggleHandoff(false);
        }

        /* --- OLD DRAWER CHAT (Used when clicking from KanBan) --- */
        function toggleHandoff(isActive) {
            const inp = document.getElementById('msg-input');
            const btn = document.getElementById('btn-send');
            const handoffBtn = document.getElementById('btn-handoff');
            const resumeBtn = document.getElementById('btn-resume-ai');

            if (!inp || !btn) return;

            if (isActive) {
                inp.disabled = false; btn.disabled = false;
                inp.placeholder = "Modo Humano ON. Digite sua mensagem de WPP...";
                if (handoffBtn) handoffBtn.classList.add('hidden');
                if (resumeBtn) resumeBtn.classList.remove('hidden');
                inp.focus();
            } else {
                inp.disabled = true; btn.disabled = true;
                inp.placeholder = "Assuma o controle (Handoff) para enviar manuais...";
                if (handoffBtn) handoffBtn.classList.remove('hidden');
                if (resumeBtn) resumeBtn.classList.add('hidden');
                inp.value = '';
            }
        }

        async function loadChat(leadId) {
            const chatDiv = document.getElementById('chat-history');
            if (!chatDiv) return;
            chatDiv.innerHTML = '<div class="text-center text-brand-500 mt-20"><i class="fa-solid fa-circle-notch fa-spin text-2xl mb-2"></i></div>';
            toggleHandoff(false);

            try {
                const res = await fetchWithAuth(`/api/v1/ws/inbox/messages/sages / ${currentTenantId} / ${leadId}`);
                if (!res.ok) throw new Error("API not ok");
                const payload = await res.json();
                chatDiv.innerHTML = '';

                if (payload && payload.data && payload.data.length > 0) {
                    payload.data.forEach(m => drawMsg(m.sender_type, m.content));
                    scrollToBottom();
                } else {
                    chatDiv.innerHTML = '<div class="text-center text-gray-500 mt-20 text-xs"><i class="fa-regular fa-comments text-2xl mb-2"></i><br>Nenhuma mensagem trocada.</div>';
                }
            } catch (e) { }
        }

        function drawMsg(sender, text) {
            const d = document.getElementById('chat-history');
            if (!d) return;
            const w = document.createElement('div');

            if (sender === 'ai' || sender === 'human' || sender === 'agent') {
                w.className = "flex justify-end";
                const isH = sender === 'human';
                w.innerHTML = `
                <div class="max-w-[80%] text-[13px] ${isH ? 'bg-orange-900/40 border-orange-500/50' : 'bg-ui-800 border-ui-700/70'} px-4 py-3 text-gray-200 rounded-2xl border ${isH ? 'rounded-br-sm' : 'rounded-br-sm'} shadow-lg relative glow-effect">
                ${text.replace(/\n/g, '<br>')}
                <div class="text-[9px] ${isH ? 'text-orange-400' : 'text-brand-400/50'} text-right mt-1.5 flex justify-end items-center uppercase font-bold tracking-wider">
                ${isH ? '<i class="fa-solid fa-user mr-1"></i> Staff' : '<i class="fa-solid fa-robot mr-1"></i> IA'}
                        </div>
                    </div>
                    `;
            } else {
                w.className = "flex justify-start";
                w.innerHTML = `
                    <div class="max-w-[80%] text-[13px] bg-ui-700/50 px-4 py-3 text-white rounded-2xl border border-ui-600/30 rounded-bl-sm shadow-md">
                        ${text.replace(/\n/g, '<br>')}
                <div class="text-[9px] text-gray-400 text-left mt-1.5 flex items-center uppercase font-bold tracking-wider">
                    <i class="fa-brands fa-whatsapp mr-1 text-emerald-500"></i> Cliente
                </div>
                    </div>
                    `;
            }
            d.appendChild(w);
        }

        function scrollToBottom() {
            const d = document.getElementById('chat-history');
            if (d) d.scrollTop = d.scrollHeight;
        }

        const sendMsgForm = document.getElementById('send-msg-form');
        if (sendMsgForm) {
            sendMsgForm.onsubmit = (e) => {
                e.preventDefault();
                const i = document.getElementById('msg-input');
                const txt = i.value.trim();
                if (!txt || !activeLeadId) return;

                drawMsg('human', txt);
                scrollToBottom();

                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ action: "send_message", lead_id: activeLeadId, content: txt }));
                }
                i.value = '';
            };
        }

        /* --- THE INBOX M (3-COLUMNS) --- */

        // ----------- UTILIDADE: Tempo relativo em Português -----------
        function timeAgoBr(isoStr) {
            if (!isoStr) return '--';
            const date = new Date(isoStr);
            const now = new Date();
            const diffMs = now - date;
            const diffSec = Math.floor(diffMs / 1000);
            const diffMin = Math.floor(diffSec / 60);
            const diffHour = Math.floor(diffMin / 60);
            const diffDay = Math.floor(diffHour / 24);

            if (diffSec < 60) return 'Agora mesmo';
            if (diffMin < 2) return 'Há 1 minuto';
            if (diffMin < 60) return `Há ${diffMin} minutos`;
            if (diffHour < 2) return 'Há 1 hora';
            if (diffHour < 24) return `Há ${diffHour} horas`;
            if (diffDay < 2) return 'Há 1 dia';
            if (diffDay < 30) return `Há ${diffDay} dias`;
            // Se for mais que 30 dias, usar data formatada
            return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
        }

        function resetInboxEmptyState() {
            activeLeadId = null;

            // Show empty watermark
            const ce = document.getElementById('chat-master-empty');
            if (ce) ce.classList.remove('hidden');

            // Hide interaction panels
            const ch = document.getElementById('chat-master-header');
            if (ch) ch.classList.add('hidden');
            const cf = document.getElementById('chat-master-footer');
            if (cf) cf.classList.add('hidden');
            const chm = document.getElementById('chat-history-master');
            if (chm) chm.classList.add('hidden');
            const cmd = document.getElementById('chat-master-details');
            if (cmd) cmd.classList.add('hidden');

            // Re-draw list to clear active styles, relying on fetchKanbanData 
            // since it runs concurrently and will re-paint with activeLeadId = null. 
            // Ensures safety against stale active styles hovering.
        }

        async function openInboxMaster(lead) {
            const vInbox = document.getElementById('view-inbox');
            if (vInbox && !vInbox.classList.contains('active')) {
                switchView('inbox');
            }
            activeLeadId = lead.id;
            const nome = (lead.name && lead.name !== "Desconhecido") ? lead.name : lead.phone;

            // Re-render sidebar to show active state
            renderInboxList();

            const ce = document.getElementById('chat-master-empty');
            if (ce) ce.classList.add('hidden');
            const ch = document.getElementById('chat-master-header');
            if (ch) ch.classList.remove('hidden');
            const cf = document.getElementById('chat-master-footer');
            if (cf) cf.classList.remove('hidden');
            const chm = document.getElementById('chat-history-master');
            if (chm) chm.classList.remove('hidden');
            // Show details COLUMN + inner content
            const detailsCol = document.getElementById('inbox-details-column');
            if (detailsCol) detailsCol.classList.remove('hidden');
            const cmd = document.getElementById('chat-master-details');
            if (cmd) cmd.classList.remove('hidden');

            const mn = document.getElementById('chat-master-name');
            if (mn) mn.innerText = nome;
            const mp = document.getElementById('chat-master-phone');
            if (mp) mp.innerText = lead.phone;
            const ma = document.getElementById('chat-master-avatar');
            if (ma) {
                if (lead.profile_data && lead.profile_data.picture) {
                    ma.innerHTML = `<img src="${lead.profile_data.picture}" class="w-full h-full object-cover rounded-full" />`;
                    ma.classList.add("overflow-hidden", "bg-transparent");
                } else {
                    ma.innerHTML = nome.charAt(0).toUpperCase();
                }
            }

            const dn = document.getElementById('detail-master-name');
            if (dn) dn.innerText = nome;
            const dp = document.getElementById('detail-master-phone');
            if (dp) dp.innerText = lead.phone;
            const da = document.getElementById('detail-master-avatar');
            if (da) {
                if (lead.profile_data && lead.profile_data.picture) {
                    da.innerHTML = `<img src="${lead.profile_data.picture}" class="w-full h-full object-cover rounded-full" />`;
                    da.classList.add("overflow-hidden", "bg-transparent");
                } else {
                    da.innerHTML = nome.charAt(0).toUpperCase();
                }
            }

            let badgeCls = 'bg-blue-500/20 text-blue-400 border-blue-500/30';
            let temp = (lead.temperature || 'frio').toLowerCase();
            if (temp.includes('quente') || temp.includes('alta')) badgeCls = 'bg-red-500/20 text-red-400 border-red-500/30';
            if (temp.includes('morno') || temp.includes('media')) badgeCls = 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30';

            const dmt = document.getElementById('detail-master-tags');
            if (dmt) dmt.innerHTML = `<span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${badgeCls}">${lead.temperature || 'FRIO'}</span>`;

            const dms = document.getElementById('detail-master-stage');
            if (dms) dms.innerText = lead.pipeline_stage || "PROSPECÇÃO";

            // [META ADS UI]
            const adContainer = document.getElementById('detail-ad-container');
            if (adContainer) {
                if (lead.ad_source || lead.ad_campaign_name) {
                    adContainer.classList.remove('hidden');
                    const adIcon = document.getElementById('detail-master-ad-icon');
                    const adName = document.getElementById('detail-master-ad-name');
                    
                    if (adName) adName.innerText = lead.ad_campaign_name || "Campanha (Origem Desconhecida)";
                    
                    if (adIcon) {
                        if (lead.ad_source === 'instagram') {
                            adIcon.className = "text-pink-500";
                            adIcon.innerHTML = '<i class="fa-brands fa-instagram"></i>';
                        } else if (lead.ad_source === 'facebook' || lead.ad_source === 'meta') {
                            adIcon.className = "text-blue-500";
                            adIcon.innerHTML = '<i class="fa-brands fa-meta"></i>';
                        } else if (lead.ad_source === 'google') {
                            adIcon.className = "text-red-500";
                            adIcon.innerHTML = '<i class="fa-brands fa-google"></i>';
                        } else {
                            adIcon.className = "text-gray-500";
                            adIcon.innerHTML = '<i class="fa-solid fa-bullhorn"></i>';
                        }
                    }
                } else {
                    adContainer.classList.add('hidden');
                }
            }

            // Atividade: Última mensagem e Atendente
            const lmEl = document.getElementById('detail-master-lastmsg');
            if (lmEl) lmEl.innerText = timeAgoBr(lead.last_message_at || lead.updated_at);
            const agEl = document.getElementById('detail-master-agent');
            if (agEl) agEl.innerText = lead.is_paused_for_human ? 'Humano' : 'Bot';

            // [AUDIT FIX] - Atualizar o badge de status no topo do chat baseado no estado real do banco
            const btnHandoff = document.getElementById('btn-master-handoff');
            const btnResume = document.getElementById('btn-master-resume-ai');
            const statusBadge = document.getElementById('btn-master-status');
            
            if (lead.is_paused_for_human) {
                if (statusBadge) {
                    statusBadge.innerHTML = '<i class="fa-solid fa-user-astronaut mr-1.5"></i> Humano';
                    statusBadge.className = 'flex items-center bg-orange-500/10 text-orange-500 border border-orange-500/30 px-3 py-1.5 rounded-full text-[11px] font-bold';
                }
                toggleMasterHandoff(true);
            } else {
                if (statusBadge) {
                    statusBadge.innerHTML = '<i class="fa-solid fa-robot mr-1.5"></i> IA Ativa';
                    statusBadge.className = 'flex items-center bg-emerald-500/10 text-emerald-500 border border-emerald-500/30 px-3 py-1.5 rounded-full text-[11px] font-bold';
                }
                toggleMasterHandoff(false);
            }

            // Mark as read
            fetchWithAuth(`/api/v1/ws/inbox/leads/${lead.id}/read`, { method: 'POST' }).catch(() => { });
            const idx = allInboxLeads.findIndex(l => l.id === lead.id);
            if (idx >= 0) allInboxLeads[idx].unread_count = 0;

            await loadMasterChat(lead.id);
            loadLeadMedia(lead.id);
        }

        /* --- CHAT ENGINE REWIRE PARA O INBOX MASTER --- */
        function toggleMasterHandoff(isActive) {
            const inp = document.getElementById('msg-input-master');
            const btn = document.getElementById('btn-send-master');
            const handoffBtn = document.getElementById('btn-master-handoff');
            const resumeBtn = document.getElementById('btn-master-resume-ai');
            const statusBadge = document.getElementById('btn-master-status');
            
            if (!inp || !btn) return;

            if (isActive) {
                inp.disabled = false; btn.disabled = false;
                inp.placeholder = "Modo Humano ativado. Digite sua mensagem para o WhatsApp...";
                if (handoffBtn) handoffBtn.classList.add('hidden');
                if (resumeBtn) resumeBtn.classList.remove('hidden');
                if (statusBadge) {
                    statusBadge.innerHTML = '<i class="fa-solid fa-user-astronaut mr-1.5"></i> Humano';
                    statusBadge.className = 'flex items-center bg-orange-500/10 text-orange-500 border border-orange-500/30 px-3 py-1.5 rounded-full text-[11px] font-bold';
                }
                inp.focus();
            } else {
                inp.disabled = true; btn.disabled = true;
                inp.placeholder = "Assuma o controle no topo (Botão Laranja) para digitar...";
                if (handoffBtn) handoffBtn.classList.remove('hidden');
                if (resumeBtn) resumeBtn.classList.add('hidden');
                if (statusBadge) {
                    statusBadge.innerHTML = '<i class="fa-solid fa-robot mr-1.5"></i> IA Ativa';
                    statusBadge.className = 'flex items-center bg-emerald-500/10 text-emerald-500 border border-emerald-500/30 px-3 py-1.5 rounded-full text-[11px] font-bold';
                }
                inp.value = '';
                
                // [AUDIT FIX] - Avisar backend para retomar IA
                if (ws && ws.readyState === WebSocket.OPEN && activeLeadId) {
                    ws.send(JSON.stringify({ action: "resume_ai", lead_id: activeLeadId }));
                }
            }
        }

        async function loadMasterChat(leadId) {
            const chatDiv = document.getElementById('chat-history-master');
            if (!chatDiv) return;
            chatDiv.innerHTML = '<div class="absolute inset-0 flex items-center justify-center text-brand-500 mt-20"><i class="fa-solid fa-circle-notch fa-spin text-2xl mb-2"></i></div>';
            toggleMasterHandoff(false);

            try {
                const res = await fetchWithAuth(`/api/v1/ws/inbox/messages/${leadId}`);
                if (!res.ok) throw new Error("API not ok");
                const payload = await res.json();
                chatDiv.innerHTML = '';

                if (payload && payload.data && payload.data.length > 0) {
                    payload.data.forEach(m => drawMsgMaster(m.sender_type, m.content, m.media_url, m.media_type, m.created_at));
                    scrollToBottomMaster();
                } else {
                    chatDiv.innerHTML = '<div class="absolute inset-0 flex flex-col items-center justify-center text-gray-600 space-y-2"><i class="fa-regular fa-comments text-4xl mb-2"></i><span>Ainda não há mensagens com este contato.</span></div>';
                }
            } catch (e) { console.error('loadMasterChat error:', e); }
        }

        function formatMsgTime(isoStr) {
            if (!isoStr) return '';
            try {
                const d = new Date(isoStr);
                return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
            } catch { return ''; }
        }

        function renderMediaContent(mediaUrl, mediaType, text) {
            if (!mediaUrl || !mediaType) return '';

            // Corrigir caminho da URL se necessário
            let fullUrl = mediaUrl;
            if (mediaUrl.startsWith('/media/')) {
                fullUrl = window.location.origin + mediaUrl;
            }

            if (mediaType === 'audio') {
                return `
                    <div class="my-1.5">
                        <div class="flex items-center gap-2 bg-black/20 rounded-xl px-3 py-2">
                            <i class="fa-solid fa-microphone text-emerald-400 text-sm"></i>
                            <audio id="audio-${Math.random().toString(36).substr(2, 9)}" controls class="h-8 flex-1" style="max-width:240px;" preload="metadata">
                                <source src="${fullUrl}" type="audio/ogg">
                            </audio>
                            <div class="flex items-center gap-1 ml-1 border-l border-white/10 pl-2">
                                <button onclick="changeAudioSpeed(this)" class="text-[10px] font-bold text-cyan-400 hover:text-white transition-colors">1x</button>
                            </div>
                        </div>
                        ${text && !text.startsWith('[Áudio') ? `<div class="mt-1.5 text-[12px] opacity-80">${text.replace(/\\n/g, '<br>')}</div>` : ''}
                    </div>`;
            }

            if (mediaType === 'image' || mediaType === 'sticker') {
                const escapedText = (text || 'Imagem').replace(/'/g, "\\'");
                return `
                    <div class="my-1.5">
                        <img src="${fullUrl}" alt="Imagem" 
                            class="max-w-[220px] max-h-[200px] rounded-lg cursor-pointer hover:opacity-90 transition-opacity border border-white/10"
                            onclick="openImageModal(this.src, '${escapedText}')"
                            onerror="this.outerHTML='<div class=\\'text-xs text-gray-500\\'>📷 Imagem indisponível</div>'" />
                        ${displayText && displayText !== '📷 Imagem' ? `<div class="mt-1.5 text-[12px] opacity-80">${displayText.replace(/\\n/g, '<br>')}</div>` : ''}
                    </div>`;
            }

            if (mediaType === 'document') {
                const fname = text || 'Documento';
                return `
                    <div class="my-1.5 flex items-center gap-2 bg-black/20 rounded-xl px-3 py-2.5 cursor-pointer hover:bg-black/30 transition-colors" onclick="window.open('${fullUrl}', '_blank')">
                        <i class="fa-solid fa-file-pdf text-red-400 text-lg"></i>
                        <div class="flex-1 min-w-0">
                            <div class="text-xs font-semibold truncate">${fname}</div>
                            <div class="text-[10px] text-gray-500">Clique para abrir</div>
                        </div>
                        <i class="fa-solid fa-download text-gray-500 text-xs"></i>
                    </div>`;
            }

            if (mediaType === 'video') {
                return `
                    <div class="my-1.5">
                        <video controls class="max-w-[240px] rounded-lg border border-white/10" preload="metadata">
                            <source src="${fullUrl}">
                        </video>
                        ${text && text !== '🎥 Vídeo' ? `<div class="mt-1.5 text-[12px] opacity-80">${text.replace(/\\n/g, '<br>')}</div>` : ''}
                    </div>`;
            }

            return '';
        }

        function drawMsgMaster(sender, text, mediaUrl, mediaType, createdAt) {
            const d = document.getElementById('chat-history-master');
            if (!d) return;
            const w = document.createElement('div');
            const time = formatMsgTime(createdAt);
            const mediaHtml = renderMediaContent(mediaUrl, mediaType, text);
            const hasMedia = !!mediaHtml;

            // Texto limpo (sem prefixos de mídia se há renderização visual)
            let displayText = text || '';
            if (hasMedia && mediaType === 'audio' && displayText.startsWith('[Áudio')) displayText = '';
            if (hasMedia && mediaType === 'image' && displayText === '📷 Imagem') displayText = '';
            if (hasMedia && mediaType === 'document' && displayText.startsWith('📄')) displayText = '';
            if (hasMedia && mediaType === 'video' && displayText === '🎥 Vídeo') displayText = '';

            if (sender === 'ai' || sender === 'human' || sender === 'agent') {
                w.className = "flex justify-end w-full";
                const isH = sender === 'human';
                w.innerHTML = `
                    <div class="max-w-[70%] text-[13px] ${isH ? 'bg-orange-900/40 border-orange-500/50' : 'bg-[#0f172a] border-brand-500/30'} px-4 py-3 text-gray-200 rounded-2xl border ${isH ? 'rounded-br-sm' : 'rounded-br-sm'} shadow-lg relative glow-effect mb-4">
                        ${mediaHtml}
                        ${displayText ? displayText.replace(/\\n/g, '<br>') : ''}
                        <div class="text-[9px] ${isH ? 'text-orange-400' : 'text-brand-400/80'} text-right mt-1.5 flex justify-end items-center gap-2">
                            <span class="font-normal opacity-60">${time}</span>
                            <span class="uppercase font-bold tracking-wider">${isH ? '<i class="fa-solid fa-user mr-1"></i> Humano' : '<i class="fa-solid fa-robot mr-1"></i> Borges (Bot)'}</span>
                        </div>
                    </div>
                `;
            } else {
                w.className = "flex justify-start w-full";
                w.innerHTML = `
                    <div class="max-w-[70%] text-[13px] bg-ui-800/80 px-4 py-3 text-white rounded-2xl border border-ui-700/80 rounded-bl-sm shadow-md mb-4">
                        ${mediaHtml}
                        ${displayText ? displayText.replace(/\\n/g, '<br>') : ''}
                        <div class="text-[9px] text-gray-500 text-left mt-1.5 flex items-center gap-2">
                            <span class="uppercase font-bold tracking-wider"><i class="fa-brands fa-whatsapp mr-1 text-emerald-500"></i> Cliente</span>
                            <span class="font-normal opacity-60">${time}</span>
                        </div>
                    </div>
                `;
            }
            d.appendChild(w);
        }

        function scrollToBottomMaster() {
            const d = document.getElementById('chat-history-master');
            if (d) d.scrollTop = d.scrollHeight;
        }

        // ─── Tabs do Painel de Detalhes ───
        function switchDetailTab(tab) {
            document.querySelectorAll('.detail-tab-btn').forEach(btn => {
                if (btn.id === `detail-tab-${tab}`) {
                    btn.className = 'detail-tab-btn text-xs px-3 py-1.5 rounded font-semibold bg-cyan-500/15 text-cyan-400 border border-cyan-500/30';
                } else {
                    btn.className = 'detail-tab-btn text-xs px-3 py-1.5 rounded font-semibold bg-transparent text-[#5a5a6e] border border-transparent';
                }
            });
            document.getElementById('detail-content-info').classList.toggle('hidden', tab !== 'info');
            document.getElementById('detail-content-media').classList.toggle('hidden', tab !== 'media');
        }

        // ─── Gallery de Mídias ───
        async function loadLeadMedia(leadId) {
            try {
                const res = await fetchWithAuth(`/api/v1/ws/inbox/leads/${leadId}/media`);
                if (!res.ok) return;
                const payload = await res.json();
                const data = payload.data;

                // Imagens
                const imgGrid = document.getElementById('media-images-grid');
                if (imgGrid) {
                    if (data.images && data.images.length > 0) {
                        imgGrid.innerHTML = data.images.map(img => {
                            const escapedText = (img.content || 'Imagem do Lead').replace(/'/g, "\\'");
                            let fullUrl = img.media_url;
                            if (fullUrl && fullUrl.startsWith('/media/')) fullUrl = window.location.origin + fullUrl;
                            return `
                                <div class="aspect-square rounded overflow-hidden cursor-pointer hover:opacity-80 transition-opacity border border-white/5" 
                                     onclick="openImageModal('${fullUrl}', '${escapedText}')">
                                    <img src="${fullUrl}" class="w-full h-full object-cover" onerror="this.parentElement.innerHTML='<div class=\\'flex items-center justify-center h-full bg-[#1e1e2e] text-[#3a3a4e] text-xs\\'>📷</div>'" />
                                </div>
                            `;
                        }).join('');
                    } else {
                        imgGrid.innerHTML = '<span class="text-[10px] text-[#3a3a4e] col-span-3">Nenhuma imagem</span>';
                    }
                }

                // Áudios
                const audioList = document.getElementById('media-audios-list');
                if (audioList) {
                    if (data.audios && data.audios.length > 0) {
                        audioList.innerHTML = data.audios.map(aud => {
                            let fullUrl = aud.media_url;
                            if (fullUrl && fullUrl.startsWith('/media/')) fullUrl = window.location.origin + fullUrl;
                            return `
                                <div class="flex items-center gap-2 bg-[#0a0a0f] rounded-lg p-2 border border-[#1e1e2e]">
                                    <i class="fa-solid fa-play text-[10px] text-emerald-400"></i>
                                    <audio controls class="h-7 flex-1" style="max-width:180px;" preload="metadata">
                                        <source src="${fullUrl}" type="audio/ogg">
                                    </audio>
                                    <span class="text-[9px] text-[#5a5a6e]">${formatMsgTime(aud.created_at)}</span>
                                </div>
                            `;
                        }).join('');
                    } else {
                        audioList.innerHTML = '<span class="text-[10px] text-[#3a3a4e]">Nenhum áudio</span>';
                    }
                }

                // Documentos
                const docList = document.getElementById('media-docs-list');
                if (docList) {
                    if (data.documents && data.documents.length > 0) {
                        docList.innerHTML = data.documents.map(doc => {
                            let fullUrl = doc.media_url;
                            if (fullUrl && fullUrl.startsWith('/media/')) fullUrl = window.location.origin + fullUrl;
                            return `
                                <div class="flex items-center gap-2 bg-[#0a0a0f] rounded-lg p-2 border border-[#1e1e2e] cursor-pointer hover:bg-[#111118] transition-colors" onclick="window.open('${fullUrl}', '_blank')">
                                    <i class="fa-solid fa-file-pdf text-red-400"></i>
                                    <span class="text-[11px] text-gray-300 truncate flex-1">${doc.content || 'Documento'}</span>
                                    <i class="fa-solid fa-download text-[10px] text-[#5a5a6e]"></i>
                                </div>
                            `;
                        }).join('');
                    } else {
                        docList.innerHTML = '<span class="text-[10px] text-[#3a3a4e]">Nenhum documento</span>';
                    }
                }
            } catch (e) { console.error('loadLeadMedia error:', e); }
        }

        function initInboxEvents() {
            const sendMsgFormM = document.getElementById('send-msg-form-master');
            if (sendMsgFormM) {
                sendMsgFormM.onsubmit = (e) => {
                    e.preventDefault();
                    const i = document.getElementById('msg-input-master');
                    const txt = i.value.trim();
                    if (!txt || !activeLeadId) return;

                    drawMsgMaster('human', txt);
                    scrollToBottomMaster();

                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({ action: "send_message", lead_id: activeLeadId, content: txt }));
                    }
                    if (i) i.value = '';
                };
            }
        }

        async function sendMediaFile(file) {
            if (!file || !activeLeadId) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                // Feedback visual imediato (Opcional: poderia desenhar um skeleton)
                const res = await fetch(`/api/v1/ws/inbox/leads/${activeLeadId}/send-media`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('borges_token')}` },
                    body: formData
                });
                
                if (res.ok) {
                    console.log("Mídia enviada com sucesso!");
                    document.getElementById('chat-file-input').value = ""; // Limpar input
                }
            } catch (e) { console.error("Erro ao enviar mídia", e); }
        }

        /* --- WEBSOCKET ENGINE --- */
        function connectWebSocket() {
            const token = localStorage.getItem('borges_token');
            if (!token) return;
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/inbox/stream?token=${token}`;
            ws = new WebSocket(wsUrl);

            ws.onopen = () => console.log('✅ Borges WebSocket Integrado ao Inbox!');
            ws.onmessage = (e) => {
                try {
                    const data = JSON.parse(e.data);

                    if (data.type === 'dashboard_update') {
                        fetchDashboardMock();
                        fetchKanbanData();
                    } else if (data.type === 'inbox_update' && data.lead_id) {
                        // Atualiza TODAS as views que podem exibir leads
                        fetchKanbanData();
                        fetchInboxLeads(); // Sidebar de Conversas

                        if (activeLeadId == data.lead_id) {
                            if (data.message) {
                                drawMsgMaster(data.message.sender_type, data.message.content, data.message.media_url, data.message.media_type, data.message.created_at);
                                scrollToBottomMaster();
                            }
                        }
                    }
                } catch (err) { }
            };
            ws.onclose = () => { setTimeout(connectWebSocket, 3000); };
        }
        /* --- BASE 44 AI BRAIN ANIMATION --- */
        function initAIBrain() {
            const canvas = document.getElementById('aibrain-canvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const SIZE = 220;
            let time = 0;
            const cx = SIZE / 2;
            const cy = SIZE / 2;

            const nodes = [
                { x: cx, y: cy - 60 },
                { x: cx + 52, y: cy - 20 },
                { x: cx + 32, y: cy + 48 },
                { x: cx - 32, y: cy + 48 },
                { x: cx - 52, y: cy - 20 },
                { x: cx, y: cy },
                { x: cx + 28, y: cy - 38 },
                { x: cx - 28, y: cy - 38 },
                { x: cx + 45, y: cy + 18 },
                { x: cx - 45, y: cy + 18 },
            ];

            const edges = [
                [0, 1], [1, 2], [2, 3], [3, 4], [4, 0],
                [0, 5], [1, 5], [2, 5], [3, 5], [4, 5],
                [0, 6], [0, 7], [1, 8], [4, 9],
                [5, 6], [5, 7], [5, 8], [5, 9],
            ];

            // Pulses traveling along edges
            const pulses = edges.map(([from, to], i) => ({
                from, to,
                t: (i * 0.15) % 1,
                speed: 0.004 + Math.random() * 0.003,
            }));

            function draw() {
                time += 0.012;
                const t = time;
                ctx.clearRect(0, 0, SIZE, SIZE);

                // Outer glow ring
                const outerGlow = ctx.createRadialGradient(cx, cy, 70, cx, cy, 110);
                outerGlow.addColorStop(0, "rgba(6,182,212,0.06)");
                outerGlow.addColorStop(1, "rgba(6,182,212,0)");
                ctx.fillStyle = outerGlow;
                ctx.beginPath();
                ctx.arc(cx, cy, 110, 0, Math.PI * 2);
                ctx.fill();

                // Rotating dashed orbit
                ctx.save();
                ctx.translate(cx, cy);
                ctx.rotate(t * 0.3);
                ctx.strokeStyle = "rgba(6,182,212,0.2)";
                ctx.lineWidth = 1;
                ctx.setLineDash([6, 10]);
                ctx.beginPath();
                ctx.arc(0, 0, 85, 0, Math.PI * 2);
                ctx.stroke();
                ctx.setLineDash([]);
                ctx.restore();

                // Counter-rotating inner ring
                ctx.save();
                ctx.translate(cx, cy);
                ctx.rotate(-t * 0.5);
                ctx.strokeStyle = "rgba(6,182,212,0.12)";
                ctx.lineWidth = 1;
                ctx.setLineDash([3, 14]);
                ctx.beginPath();
                ctx.arc(0, 0, 65, 0, Math.PI * 2);
                ctx.stroke();
                ctx.setLineDash([]);
                ctx.restore();

                // Edges
                edges.forEach(([from, to]) => {
                    const a = nodes[from], b = nodes[to];
                    const grad = ctx.createLinearGradient(a.x, a.y, b.x, b.y);
                    grad.addColorStop(0, "rgba(6,182,212,0.15)");
                    grad.addColorStop(0.5, "rgba(6,182,212,0.3)");
                    grad.addColorStop(1, "rgba(6,182,212,0.15)");
                    ctx.strokeStyle = grad;
                    ctx.lineWidth = 0.8;
                    ctx.beginPath();
                    ctx.moveTo(a.x, a.y);
                    ctx.lineTo(b.x, b.y);
                    ctx.stroke();
                });

                // Pulses along edges
                pulses.forEach((pulse) => {
                    pulse.t += pulse.speed;
                    if (pulse.t > 1) pulse.t = 0;
                    const a = nodes[pulse.from], b = nodes[pulse.to];
                    const px = a.x + (b.x - a.x) * pulse.t;
                    const py = a.y + (b.y - a.y) * pulse.t;
                    const pg = ctx.createRadialGradient(px, py, 0, px, py, 5);
                    pg.addColorStop(0, "rgba(6,182,212,0.95)");
                    pg.addColorStop(1, "rgba(6,182,212,0)");
                    ctx.fillStyle = pg;
                    ctx.beginPath();
                    ctx.arc(px, py, 5, 0, Math.PI * 2);
                    ctx.fill();
                });

                // Nodes
                nodes.forEach((node, i) => {
                    const pulse = Math.sin(t * 2 + i * 0.8) * 0.5 + 0.5;
                    const radius = i === 5 ? 7 : 4;
                    const glow = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, radius + 6);
                    glow.addColorStop(0, `rgba(6,182,212,${0.6 + pulse * 0.4})`);
                    glow.addColorStop(1, "rgba(6,182,212,0)");
                    ctx.fillStyle = glow;
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, radius + 6, 0, Math.PI * 2);
                    ctx.fill();

                    ctx.fillStyle = `rgba(6,182,212,${0.7 + pulse * 0.3})`;
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
                    ctx.fill();

                    // White dot center
                    ctx.fillStyle = "rgba(255,255,255,0.9)";
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, i === 5 ? 2.5 : 1.5, 0, Math.PI * 2);
                    ctx.fill();
                });

                // Center core glow
                const coreGlow = Math.sin(t * 1.5) * 0.2 + 0.8;
                const coreG = ctx.createRadialGradient(cx, cy, 0, cx, cy, 20);
                coreG.addColorStop(0, `rgba(6,182,212,${coreGlow})`);
                coreG.addColorStop(0.5, `rgba(6,182,212,0.2)`);
                coreG.addColorStop(1, "rgba(6,182,212,0)");
                ctx.fillStyle = coreG;
                ctx.beginPath();
                ctx.arc(cx, cy, 20, 0, Math.PI * 2);
                ctx.fill();

                // Floating small particles
                for (let i = 0; i < 6; i++) {
                    const angle = (i / 6) * Math.PI * 2 + t * 0.4;
                    const r = 75 + Math.sin(t + i) * 8;
                    const px = cx + Math.cos(angle) * r;
                    const py = cy + Math.sin(angle) * r;
                    const alpha = Math.sin(t * 1.5 + i) * 0.3 + 0.5;
                    ctx.fillStyle = `rgba(6,182,212,${alpha})`;
                    ctx.beginPath();
                    ctx.arc(px, py, 2, 0, Math.PI * 2);
                    ctx.fill();
                }

                window.requestAnimationFrame(draw);
            }

            draw();
        }

        /* ----------------------------------------------------
           Borges AI - Logic
        ---------------------------------------------------- */
        let aiMessages = [];

        function updateAIStats(leadsArray) {
            const total = leadsArray.length;
            const quentes = leadsArray.filter(l => l.temperature === 'quente' || l.temperature === 'Alta').length;
            const fechados = leadsArray.filter(l => l.pipeline_stage === 'FECHADO' || l.pipeline_stage === 'Fechado' || l.stage === 'fechado').length;
            const receita = leadsArray.filter(l => l.pipeline_stage === 'FECHADO' || l.pipeline_stage === 'Fechado' || l.stage === 'fechado')
                .reduce((sum, l) => sum + (parseFloat(l.estimated_value) || parseFloat(l.closed_value) || 0), 0);

            const elTotal = document.getElementById('ai-stat-total');
            const elQuentes = document.getElementById('ai-stat-quentes');
            const elFechados = document.getElementById('ai-stat-fechados');
            const elReceita = document.getElementById('ai-stat-receita');

            if (elTotal) elTotal.innerText = total;
            if (elQuentes) elQuentes.innerText = quentes;
            if (elFechados) elFechados.innerText = fechados;
            if (elReceita) elReceita.innerText = `R$ ${receita.toLocaleString('pt-BR')}`;
        }

        function appendAIMessage(role, content) {
            const container = document.getElementById('ai-messages-container');
            const welcomeState = document.getElementById('ai-welcome-state');
            const loader = document.getElementById('ai-chat-loader');

            if (welcomeState) welcomeState.classList.add('hidden');

            const msgDiv = document.createElement('div');
            msgDiv.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'} w-full animate-fade-in`;

            let innerHTML = '';

            if (role === 'assistant') {
                // Parse simple markdown-like bolding and line breaks for now
                const formattedContent = content.replace(/\*\*(.*?)\*\*/g, '<strong class="text-cyan-300 font-semibold">$1</strong>')
                    .replace(/\n/g, '<br>');

                innerHTML = `
                    <div class="w-8 h-8 rounded-lg flex items-center justify-center mr-3 flex-shrink-0 mt-1" style="background: linear-gradient(135deg,#06b6d4,#0e7490)">
                        <i class="fa-solid fa-wand-magic-sparkles text-white text-[10px]"></i>
                    </div>
                    <div class="max-w-[85%] rounded-2xl px-5 py-4 bg-[#111118] border border-[#1e1e2e] text-[#c0c0d0] text-sm leading-relaxed shadow-lg">
                        ${formattedContent}
                    </div>
                `;
            } else {
                innerHTML = `
                    <div class="max-w-[85%] rounded-2xl px-5 py-4 border border-cyan-500/20 text-white text-sm leading-relaxed shadow-[0_4px_15px_rgba(6,182,212,0.1)]" style="background: rgba(6,182,212,0.1)">
                        ${content}
                    </div>
                `;
            }

            msgDiv.innerHTML = innerHTML;

            if (loader) {
                container.insertBefore(msgDiv, loader);
            } else {
                container.appendChild(msgDiv);
            }

            // Scroll to bottom
            container.scrollTop = container.scrollHeight;
        }

        async function handleAISubmit(e) {
            e.preventDefault();
            const inputEl = document.getElementById('ai-msg-input');
            const btnEl = document.getElementById('ai-btn-send');
            const loader = document.getElementById('ai-chat-loader');
            const container = document.getElementById('ai-messages-container');

            const text = inputEl.value.trim();
            if (!text || inputEl.disabled) return;

            // Add user message
            appendAIMessage('user', text);
            inputEl.value = '';

            // Set loading state
            inputEl.disabled = true;
            btnEl.disabled = true;
            if (loader) {
                loader.classList.remove('hidden');
                loader.classList.add('flex');
            }
            container.scrollTop = container.scrollHeight;

            try {
                const res = await fetchWithAuth(`/api/v1/ai/strategic-analysis?prompt=${encodeURIComponent(text)}`, {
                    method: 'POST'
                });
                
                if (res.ok) {
                    const data = await res.json();
                    appendAIMessage('assistant', data.response);
                } else {
                    throw new Error("API Error");
                }
            } catch (error) {
                console.error("AI Error:", error);
                appendAIMessage('assistant', "Erro de conexão com o Core Neurológico. Tente novamente em instantes.");
            } finally {
                // Remove loading state
                inputEl.disabled = false;
                btnEl.disabled = false;
                if (loader) {
                    loader.classList.add('hidden');
                    loader.classList.remove('flex');
                }
                inputEl.focus();
                container.scrollTop = container.scrollHeight;
            }
        }

        /* ----------------------------------------------------
           Appointments Calendar - Logic
        ---------------------------------------------------- */
        let calendarMode = 'week'; // week | day
        let calendarCurrentDate = new Date();
        const HOURS = Array.from({ length: 14 }, (_, i) => i + 7); // 07:00 ~ 20:00
        const DAYS_OF_WEEK = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];
        const MONTHS = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];

        // Mock data
        const mockAppointments = [
            { id: 1, title: 'Reunião de Alinhamento', type: 'qualificacao', date_time: new Date(new Date().setHours(10, 0, 0, 0)).toISOString(), duration_minutes: 45, status: 'agendado', contact_name: 'João Silva' },
            { id: 2, title: 'Apresentação Base44', type: 'demo', date_time: new Date(new Date().setHours(14, 30, 0, 0)).toISOString(), duration_minutes: 60, status: 'confirmado', contact_name: 'Maria Souza' }
        ];

        function initCalendar() {
            // Initial render
            renderCalendarGrid();
        }

        function setCalendarViewMode(mode) {
            calendarMode = mode;
            document.getElementById('btn-view-week').className = `px-3 py-1.5 text-xs font-medium transition-colors ${mode === 'week' ? 'bg-cyan-500/20 text-cyan-300' : 'text-[#5a5a6e] hover:text-white'}`;
            document.getElementById('btn-view-day').className = `px-3 py-1.5 text-xs font-medium transition-colors ${mode === 'day' ? 'bg-cyan-500/20 text-cyan-300' : 'text-[#5a5a6e] hover:text-white'}`;
            renderCalendarGrid();
        }

        function getStartOfWeek(d) {
            const date = new Date(d);
            const day = date.getDay();
            const diff = date.getDate() - day; // Adjust if day is 0 (Sunday) to Monday? Actually Sunday is 0 here.
            return new Date(date.setDate(diff));
        }

        function renderCalendarGrid() {
            const daysColContainer = document.getElementById('calendar-days-cols');
            const hoursColContainer = document.getElementById('calendar-hours-col');
            const weekRangeLabel = document.getElementById('calendar-week-range');
            const calendarGridContainer = document.getElementById('calendar-grid-view');

            if (!daysColContainer || !hoursColContainer) return;

            daysColContainer.innerHTML = '';
            hoursColContainer.innerHTML = '';

            // Render hours left col
            HOURS.forEach(h => {
                hoursColContainer.innerHTML += `
                    <div class="h-16 flex items-start justify-end pr-2 pt-1 border-b border-[#1e1e2e]/40">
                        <span class="text-[9px] text-[#3a3a4e]">${String(h).padStart(2, '0')}:00</span>
                    </div>
                `;
            });

            // Determine days to show
            let daysToShow = [];
            if (calendarMode === 'week') {
                let startOfWeek = getStartOfWeek(calendarCurrentDate);
                for (let i = 0; i < 7; i++) {
                    let nextDay = new Date(startOfWeek);
                    nextDay.setDate(startOfWeek.getDate() + i);
                    daysToShow.push(nextDay);
                }
                const endOfWeek = daysToShow[6];
                if (weekRangeLabel) {
                    weekRangeLabel.innerText = `${String(startOfWeek.getDate()).padStart(2, '0')} ${MONTHS[startOfWeek.getMonth()].substring(0, 3)} – ${String(endOfWeek.getDate()).padStart(2, '0')} ${MONTHS[endOfWeek.getMonth()].substring(0, 3)} ${endOfWeek.getFullYear()}`;
                }
                calendarGridContainer.style.minWidth = '700px';
            } else {
                daysToShow = [new Date(calendarCurrentDate)];
                if (weekRangeLabel) {
                    weekRangeLabel.innerText = `${DAYS_OF_WEEK[daysToShow[0].getDay()]}, ${String(daysToShow[0].getDate()).padStart(2, '0')} de ${MONTHS[daysToShow[0].getMonth()]}`;
                }
                calendarGridContainer.style.minWidth = '100%';
            }

            // Render day columns
            const today = new Date();
            daysToShow.forEach(day => {
                const isToday = day.getDate() === today.getDate() && day.getMonth() === today.getMonth() && day.getFullYear() === today.getFullYear();

                let dayColHTML = `
                    <div class="flex-1 min-w-0 border-r border-[#1e1e2e] ${isToday && calendarMode === 'week' ? 'bg-cyan-500/[0.02]' : ''}">
                        <div class="h-8 flex flex-col items-center justify-center border-b border-[#1e1e2e] cursor-pointer hover:bg-white/[0.02]" onclick="calendarCurrentDate = new Date(${day.getTime()}); setCalendarViewMode('day')">
                            <span class="text-[9px] text-[#3a3a4e] uppercase">${DAYS_OF_WEEK[day.getDay()]}</span>
                            <span class="text-xs font-bold ${isToday ? 'text-cyan-400' : 'text-[#8b8b9e]'}">${day.getDate()}</span>
                        </div>
                `;

                // Render slots
                HOURS.forEach(h => {
                    const slots = mockAppointments.filter(a => {
                        const aDate = new Date(a.date_time);
                        return aDate.getDate() === day.getDate() && aDate.getMonth() === day.getMonth() && aDate.getFullYear() === day.getFullYear() && aDate.getHours() === h;
                    });

                    let slotsHTML = '';
                    slots.forEach(a => {
                        const tColor = a.type === 'demo' ? '14,116,144' : '6,182,212';
                        slotsHTML += `
                            <button class="w-full text-left rounded px-1.5 py-1 mb-1 hover:opacity-90 transition-opacity overflow-hidden" 
                                style="background: linear-gradient(135deg, rgba(${tColor},0.2), rgba(${tColor},0.12)); border: 1px solid rgba(${tColor},0.25)">
                                <p class="text-[10px] font-semibold text-white truncate">${a.contact_name || a.title}</p>
                                <p class="text-[9px] text-cyan-300/70 truncate">${new Date(a.date_time).getHours().toString().padStart(2, '0')}:${new Date(a.date_time).getMinutes().toString().padStart(2, '0')} · ${a.duration_minutes}min</p>
                            </button>
                        `;
                    });

                    dayColHTML += `
                        <div class="h-16 border-b border-[#1e1e2e]/40 relative px-0.5 py-0.5 overflow-hidden">
                            ${slotsHTML}
                        </div>
                    `;
                });

                dayColHTML += `</div>`;
                daysColContainer.innerHTML += dayColHTML;
            });
        }

        function openNewAppointmentModal() {
            const modal = document.getElementById('calendar-modal-backdrop');
            const form = document.getElementById('calendar-form-modal');
            if (modal && form) {
                modal.classList.remove('hidden');
                form.classList.remove('hidden');
            }
        }

        function closeCalendarModals() {
            const modal = document.getElementById('calendar-modal-backdrop');
            const form = document.getElementById('calendar-form-modal');
            if (modal && form) {
                modal.classList.add('hidden');
                form.classList.add('hidden');
            }
        }

        async function generateAsaasBilling() {
            if (!currentTenantConfigId) return;

            if (!confirm("Tem certeza que deseja criar as cobranças MRR e Setup no Asaas para este cliente? Eles receberão os avisos nativos.")) return;

            const btn = document.getElementById('btn-generate-asaas');
            const originalHtml = btn.innerHTML;
            btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Emitindo...';
            btn.disabled = true;

            try {
                const res = await fetchWithAuth(`/api/v1/super/tenants/${currentTenantConfigId}/asaas/generate`, {
                    method: 'POST'
                });

                const data = await res.json();
                if (res.ok) {
                    alert(data.message || "Faturamento gerado com sucesso no Asaas!");
                } else {
                    alert("Erro Asaas: " + (data.detail || "Falha na comunicação"));
                }
            } catch (e) {
                console.error(e);
                alert("Erro ao conectar com a API para geração.");
            } finally {
                btn.innerHTML = originalHtml;
                btn.disabled = false;
            }
        }

        /* ----------------------------------------------------
           Reports / Dashboard Analytics - Logic
        ---------------------------------------------------- */
        let reportsLeads = [];
        const STAGE_ORDER = ["novo", "contato", "qualificacao", "agendamento", "reuniao", "proposta", "fechado"];
        const STAGE_LABEL = { novo: "Novo", contato: "Contato", qualificacao: "Qualificação", agendamento: "Agendamento", reuniao: "Reunião", proposta: "Proposta", fechado: "Fechado" };
        const STAGE_COLORS = ["#4f46e5", "#3b82f6", "#06b6d4", "#22c55e", "#f59e0b", "#f97316", "#10b981"];
        const ORIGIN_COLORS = { whatsapp: "#25d366", instagram: "#ec4899", meta_ads: "#3b82f6", organico: "#8b5cf6", indicacao: "#f59e0b", site: "#ef4444" };

        async function initReports() {

            try {
                // Fetch Leads
                const rLeads = await fetchWithAuth(`/api/v1/ws/inbox/leads`);
                if (rLeads.ok) {
                    const payload = await rLeads.json();
                    reportsLeads = payload.data || [];
                }

                // For now, mock tasks and contracts since endpoints may not exist in this backend snapshot
                const tasks = [{ status: "pendente", due_date: new Date(Date.now() - 86400000).toISOString() }];
                const contracts = [{ status: "assinado", value: 5000, duration_months: 12 }, { status: "enviado", value: 2000 }];

                renderReportsDashboard(reportsLeads, tasks, contracts);

                // Bind filters if not already bound
                const fromEl = document.getElementById('reports-date-from');
                const toEl = document.getElementById('reports-date-to');
                if (fromEl && !fromEl.onchange) {
                    fromEl.onchange = () => initReports();
                    toEl.onchange = () => initReports();
                }

            } catch (e) { console.error("Error loading reports", e); }
        }

        function clearReportDates() {
            document.getElementById('reports-date-from').value = "";
            document.getElementById('reports-date-to').value = "";
            initReports();
        }

        function fmtMoney(v) { return `R$ ${(v || 0).toLocaleString("pt-BR")}`; }

        function renderReportsDashboard(allLeads, tasks, contracts) {
            const dateFrom = document.getElementById('reports-date-from').value;
            const dateTo = document.getElementById('reports-date-to').value;
            const btnClear = document.getElementById('reports-btn-clear');
            if (dateFrom || dateTo) btnClear.classList.remove('hidden');
            else btnClear.classList.add('hidden');

            const leads = allLeads.filter(l => {
                const c = new Date(l.created_date || l.created_at || new Date());
                if (dateFrom && new Date(dateFrom) > c) return false;
                if (dateTo) { const t = new Date(dateTo); t.setHours(23, 59, 59); if (t < c) return false; }
                return true;
            });

            // KPIs
            const activeLeads = leads.filter(l => !["perdido", "desqualificado"].includes(l.pipeline_stage));
            const closed = leads.filter(l => l.pipeline_stage === "fechado");
            const lost = leads.filter(l => l.pipeline_stage === "perdido");
            const convRate = leads.length === 0 ? "0%" : ((closed.length / leads.length) * 100).toFixed(1) + "%";
            const closedRevenue = closed.reduce((s, l) => s + (l.closed_value || l.estimated_value || 0), 0);
            const pipelineValue = activeLeads.reduce((s, l) => s + (l.estimated_value || 0), 0);
            const hotLeads = leads.filter(l => l.temperature === "quente" && !["fechado", "perdido"].includes(l.pipeline_stage));
            const hotRevenue = hotLeads.reduce((s, l) => s + (l.estimated_value || 0), 0);

            // Neglected > 48h
            const neglected = leads.filter(l => {
                if (["fechado", "perdido", "desqualificado"].includes(l.pipeline_stage)) return false;
                if (!l.last_message_at) return true;
                return Date.now() - new Date(l.last_message_at).getTime() > 48 * 60 * 60 * 1000;
            });

            document.getElementById('kpi-closed-revenue').innerText = fmtMoney(closedRevenue);
            document.getElementById('kpi-closed-contracts').innerText = `${closed.length} contratos`;
            document.getElementById('kpi-pipeline-value').innerText = fmtMoney(pipelineValue);
            document.getElementById('kpi-pipeline-leads').innerText = `${activeLeads.length} leads`;
            document.getElementById('kpi-conv-rate').innerText = convRate;
            document.getElementById('kpi-conv-lost').innerText = `${lost.length} perdidos`;
            document.getElementById('kpi-risk-revenue').innerText = fmtMoney(hotRevenue);
            document.getElementById('kpi-risk-leads').innerText = `${hotLeads.length} leads quentes parados`;

            // Ops
            const signed = contracts.filter(c => c.status === "assinado");
            const pending = contracts.filter(c => c.status === "enviado");
            const mrr = signed.reduce((s, c) => s + ((c.value || 0) / (c.duration_months || 12)), 0);
            const overdue = tasks.filter(t => t.due_date && new Date(t.due_date) < new Date() && !["concluida", "cancelada"].includes(t.status));

            document.getElementById('kpi-op-signed').innerText = signed.length;
            document.getElementById('kpi-op-mrr').innerText = `MRR: ${fmtMoney(mrr)}/mês`;
            document.getElementById('kpi-op-pending').innerText = pending.length;
            document.getElementById('kpi-op-pending-val').innerText = fmtMoney(pending.reduce((s, c) => s + (c.value || 0), 0));
            document.getElementById('kpi-op-neglected').innerText = neglected.length;
            document.getElementById('kpi-op-tasks').innerText = overdue.length;

            // Alarms
            const alertsCont = document.getElementById('reports-alerts-container');
            alertsCont.innerHTML = "";
            if (neglected.length > 0) {
                const val = neglected.reduce((s, l) => s + (l.estimated_value || 0), 0);
                alertsCont.innerHTML += `<div class="flex items-center gap-3 px-4 py-3 rounded-xl border border-amber-500/30 bg-amber-500/5 text-amber-400">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    <div><p class="text-xs font-semibold">${neglected.length} leads sem follow-up há +48h</p><p class="text-[10px] opacity-70">Risco de perda de ${fmtMoney(val)}</p></div>
                </div>`;
            }
            if (overdue.length > 0) {
                alertsCont.innerHTML += `<div class="flex items-center gap-3 px-4 py-3 rounded-xl border border-red-500/30 bg-red-500/5 text-red-400">
                    <i class="fa-regular fa-clock"></i>
                    <div><p class="text-xs font-semibold">${overdue.length} tarefas em atraso</p><p class="text-[10px] opacity-70">Verifique a página de Tarefas</p></div>
                </div>`;
            }

            // Funnel
            const funnelCont = document.getElementById('reports-funnel-container');
            funnelCont.innerHTML = "";
            const maxFnl = Math.max(...STAGE_ORDER.map(st => leads.filter(l => l.pipeline_stage === st).length), 1);
            STAGE_ORDER.forEach((s, idx) => {
                const count = leads.filter(l => l.pipeline_stage === s).length;
                funnelCont.innerHTML += `
                    <div class="flex items-center gap-3">
                        <span class="text-[10px] text-[#5a5a6e] w-20 text-right flex-shrink-0">${STAGE_LABEL[s]}</span>
                        <div class="flex-1 h-6 bg-[#0a0a0f] rounded-md overflow-hidden">
                            <div class="h-full rounded-md transition-all duration-500 flex items-center px-2" style="width: ${(count / maxFnl) * 100}%; background: ${STAGE_COLORS[idx]}; min-width: ${count > 0 ? 24 : 0}px">
                                ${count > 0 ? `<span class="text-[10px] text-white font-bold">${count}</span>` : ""}
                            </div>
                        </div>
                    </div>`;
            });

            // Origins
            const origCont = document.getElementById('reports-origin-container');
            const oStats = ["whatsapp", "instagram", "meta_ads", "organico", "indicacao", "site"].map(o => {
                const ol = leads.filter(l => l.origin === o);
                return { name: o === "meta_ads" ? "Meta Ads" : o.charAt(0).toUpperCase() + o.slice(1), count: ol.length, rec: ol.filter(l => l.pipeline_stage === "fechado").reduce((s, l) => s + (l.closed_value || l.estimated_value || 0), 0), col: ORIGIN_COLORS[o] };
            }).filter(d => d.count > 0).sort((a, b) => b.count - a.count);

            origCont.innerHTML = "";
            if (oStats.length === 0) origCont.innerHTML = `<p class="text-xs text-[#3a3a4e] text-center py-8">Sem dados de origem</p>`;
            else {
                const maxO = Math.max(...oStats.map(x => x.count), 1);
                oStats.forEach(o => {
                    origCont.innerHTML += `
                        <div class="flex items-center gap-4">
                            <span class="text-xs text-[#8b8b9e] w-20 flex-shrink-0">${o.name}</span>
                            <div class="flex-1 space-y-1">
                                <div class="flex items-center gap-2">
                                    <div class="flex-1 h-4 bg-[#0a0a0f] rounded overflow-hidden">
                                        <div class="h-full rounded" style="width: ${(o.count / maxO) * 100}%; background: ${o.col}; opacity: 0.9"></div>
                                    </div>
                                    <span class="text-xs text-white font-semibold w-6">${o.count}</span>
                                </div>
                                ${o.rec > 0 ? `<p class="text-[10px] text-[#5a5a6e]">Receita fechada: <span class="text-green-400">${fmtMoney(o.rec)}</span></p>` : ""}
                            </div>
                        </div>`;
                });
            }

            // Temp Pie Chart
            const tData = [
                { name: "Quente 🔥", val: leads.filter(l => l.temperature === "quente").length, col: "#ef4444" },
                { name: "Morno 🌡", val: leads.filter(l => l.temperature === "morno").length, col: "#f59e0b" },
                { name: "Frio ❄️", val: leads.filter(l => l.temperature === "frio").length, col: "#3b82f6" }
            ].filter(d => d.val > 0);

            const tLeg = document.getElementById('reports-temp-legend');
            tLeg.innerHTML = "";
            tData.forEach(t => tLeg.innerHTML += `<div class="flex items-center gap-1.5 text-xs"><div class="w-2 h-2 rounded-full" style="background: ${t.col}"></div><span class="text-[#8b8b9e]">${t.name}: <span class="text-white font-semibold">${t.val}</span></span></div>`);

            const canvas = document.getElementById('reports-temp-chart');
            if (canvas) {
                const ctx = canvas.getContext('2d');
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                let total = tData.reduce((s, t) => s + t.val, 0);
                if (total > 0) {
                    let start = -0.5 * Math.PI;
                    const cx = canvas.width / 2, cy = canvas.height / 2, r = Math.min(cx, cy);
                    tData.forEach(t => {
                        let slice = (t.val / total) * 2 * Math.PI;
                        ctx.beginPath();
                        ctx.moveTo(cx, cy);
                        ctx.arc(cx, cy, r, start, start + slice);
                        ctx.fillStyle = t.col;
                        ctx.fill();
                        start += slice;
                    });
                }
            }

            // Hot Leads Panel
            const hlCont = document.getElementById('reports-hot-leads-container');
            const hlList = document.getElementById('reports-hot-leads-list');
            if (hotLeads.length > 0) {
                hlCont.classList.remove('hidden');
                document.getElementById('reports-hot-leads-count').innerText = `${hotLeads.length} leads`;
                hlList.innerHTML = "";
                hotLeads.slice(0, 5).forEach(l => {
                    let hours = l.last_message_at ? Math.floor((Date.now() - new Date(l.last_message_at).getTime()) / 3600000) : '--';
                    hlList.innerHTML += `
                        <div class="flex items-center justify-between py-2 px-3 rounded-lg bg-[#0a0a0f] border border-[#1e1e2e]">
                            <div>
                                <p class="text-xs font-semibold text-white">${l.name || l.phone}</p>
                                <p class="text-[10px] text-[#5a5a6e] uppercase">${l.pipeline_stage}</p>
                            </div>
                            <div class="text-right">
                                <p class="text-xs text-green-400 font-semibold">${fmtMoney(l.estimated_value)}</p>
                                <p class="text-[10px] text-[#5a5a6e]">${hours}h atrás</p>
                            </div>
                        </div>`;
                });
                if (hotLeads.length > 5) hlList.innerHTML += `<p class="text-[10px] text-[#5a5a6e] text-center pt-1">+ ${hotLeads.length - 5} leads quentes</p>`;
            } else hlCont.classList.add('hidden');
        }

        /* ----------------------------------------------------
           Settings / Configs - Logic
        ---------------------------------------------------- */
        let settingsCompanyId = null;
        let originalSettings = { ai_config: {} };

        async function initSettings() {

            switchSettingsTab('company');
            try {
                // Mock Fetching settings vs Base44
                const res = await fetchWithAuth(`/api/v1/ws/config/`);
                if (res.ok) {
                    const data = await res.json();
                    settingsCompanyId = data.id;
                    originalSettings = data;
                } else {
                    // Seed mock 
                    originalSettings = {
                        name: "Minha Empresa", whatsapp_number: "+55 11 99999-9999", sla_hours: 24,
                        ai_config: { greeting_message: "Olá! Sou o assistente comercial.", tone: "consultivo" },
                        welcome_message: "Bem-vindo!"
                    };
                }

                document.getElementById('set-company-name').value = originalSettings.name || "";
                document.getElementById('set-company-wpp').value = originalSettings.whatsapp_number || "";
                document.getElementById('set-company-sla').value = originalSettings.sla_hours || 24;
                document.getElementById('set-ai-greeting').value = originalSettings.ai_config?.greeting_message || "";
                document.getElementById('set-ai-tone').value = originalSettings.ai_config?.tone || "consultivo";
                document.getElementById('set-msg-welcome').value = originalSettings.welcome_message || "";

                await loadSettingsUsers();
            } catch (e) { console.error('Error initSettings', e); }
        }

        async function loadSettingsUsers() {
            const list = document.getElementById('settings-users-list');
            try {
                // Mock users endpoint since it might not be implemented in current FastAPI snapshot
                // Normally: await fetchWithAuth(`/api/v1/users/${currentTenantId}`);
                const users = [{ id: 1, full_name: "Admin", email: "admin@empresa.com", role: "company_admin" }];
                list.innerHTML = "";
                if (users.length === 0) { list.innerHTML = `<p class="text-xs text-[#5a5a6e]">Nenhum colaborador adicionado</p>`; return; }

                users.forEach(u => {
                    const roleBadge = u.role === "company_admin" ? `<span class="text-xs px-2 py-1 rounded bg-cyan-500/10 text-cyan-300 font-medium">Admin</span>` : `<span class="text-xs px-2 py-1 rounded bg-blue-500/10 text-blue-400 font-medium">Usuário</span>`;
                    list.innerHTML += `
                        <div class="flex items-center justify-between p-3 rounded-lg bg-[#0a0a0f] border border-[#1e1e2e]">
                            <div class="flex-1">
                                <p class="text-sm font-semibold text-white">${u.full_name || "Sem nome"}</p>
                                <p class="text-xs text-[#5a5a6e]">${u.email}</p>
                            </div>
                            <div class="flex items-center gap-3">
                                ${roleBadge}
                            </div>
                        </div>`;
                });
            } catch (e) { list.innerHTML = `<p class="text-xs text-red-400">Erro ao carregar colaboradores</p>`; }
        }

        function switchSettingsTab(tab) {
            document.querySelectorAll('.settings-tab-pane').forEach(el => el.classList.add('hidden'));
            const p = document.getElementById('settings-tab-' + tab);
            if (p) p.classList.remove('hidden');

            const btns = ['company', 'users', 'ai', 'messages'];
            btns.forEach(b => {
                const btn = document.getElementById('tab-btn-' + b);
                if (!btn) return;
                if (b === tab) {
                    btn.className = "flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-all border bg-cyan-500/15 text-cyan-300 border-cyan-500/30";
                } else {
                    btn.className = "flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-all border bg-[#111118] text-[#5a5a6e] border-[#1e1e2e] hover:text-white hover:bg-[#1c1c28]";
                }
            });
        }

        async function saveSettings() {
            const btn = document.getElementById('settings-btn-save');
            const originalHtml = btn.innerHTML;
            btn.innerHTML = `<i class="fa-solid fa-circle-notch animate-spin w-4 h-4"></i> Salvando`;
            btn.disabled = true;

            const payload = {
                name: document.getElementById('set-company-name').value,
                cnpj: document.getElementById('set-company-cnpj').value,
                whatsapp_number: document.getElementById('set-company-wpp').value,
                sla_hours: Number(document.getElementById('set-company-sla').value),
                ai_config: {
                    ...originalSettings.ai_config,
                    agent_name: document.getElementById('set-ai-name').value,
                    agent_goal: document.getElementById('set-ai-goal').value,
                    greeting_message: document.getElementById('set-ai-greeting').value,
                    tone: document.getElementById('set-ai-tone').value
                },
                welcome_message: document.getElementById('set-msg-welcome').value,
            };

            try {
                // If the endpoint doesn't exist yet, we just simulate it
                // await fetchWithAuth(`/api/v1/companies/${settingsCompanyId}`, { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload)});
                await new Promise(r => setTimeout(r, 600));
                console.log("Settings saved mock payload -> ", payload);
                originalSettings = { ...originalSettings, ...payload };
            } catch (e) { console.error("Save error", e); }

            btn.innerHTML = `<i class="fa-solid fa-check w-4 h-4 text-white"></i> Salvo!`;
            setTimeout(() => { btn.innerHTML = originalHtml; btn.disabled = false; }, 1500);
        }

        async function inviteUser() {
            const email = document.getElementById('set-invite-email').value;
            const role = document.getElementById('set-invite-role').value;
            const btn = document.getElementById('settings-btn-invite');
            if (!email) return;

            btn.innerText = "Enviando...";
            btn.disabled = true;
            try {
                // Simulating invite user
                await new Promise(r => setTimeout(r, 800));
                console.log(`Convite enviado para ${email} como ${role}`);
                document.getElementById('set-invite-email').value = "";
                await loadSettingsUsers();
            } catch (e) { }
            btn.innerText = "Enviar Convite";
            btn.disabled = false;
        }

        function openLeadModal(lead) {
            const modal = document.getElementById('lead-info-modal');
            if (!modal) return;

            // Populate data
            const nome = (lead.name && lead.name !== "Desconhecido") ? lead.name : lead.phone;
            const avatar = document.getElementById('modal-lead-avatar');
            const nameEl = document.getElementById('modal-lead-name');
            const phoneEl = document.getElementById('modal-lead-phone');
            const emailEl = document.getElementById('modal-lead-email');
            const stageEl = document.getElementById('modal-lead-stage');
            const tempEl = document.getElementById('modal-lead-temperature');
            const sumEl = document.getElementById('modal-lead-summary');
            const valEl = document.getElementById('modal-lead-value');

            if (nameEl) nameEl.innerText = nome;
            if (avatar) {
                if (lead.profile_data && lead.profile_data.picture) {
                    avatar.innerHTML = `<img src="${lead.profile_data.picture}" class="w-full h-full object-cover rounded-full" />`;
                    avatar.classList.add("overflow-hidden", "bg-transparent");
                } else {
                    avatar.innerHTML = nome.charAt(0).toUpperCase();
                }
            }
            if (phoneEl) phoneEl.innerText = lead.phone || '--';
            if (emailEl) emailEl.innerText = lead.email || '--';
            if (stageEl) stageEl.innerText = lead.pipeline_stage || 'PROSPECÇÃO';
            if (tempEl) {
                tempEl.innerText = lead.temperature === "quente" ? "Alta" : lead.temperature === "morno" ? "Média" : lead.temperature || "Baixa";
                tempEl.className = `px-2 py-0.5 rounded text-[10px] uppercase font-medium border ${getBadgeCol(lead.temperature)}`;
            }

            const txt = (lead.last_message && lead.last_message !== "Conversa iniciada") ? lead.last_message : 'Aguardando processamento de linguagem...';
            if (sumEl) sumEl.innerText = txt;
            if (valEl) valEl.innerText = (lead.estimated_value && lead.estimated_value > 0) ? `R$ ${lead.estimated_value.toLocaleString('pt-BR')}` : 'R$ 0';

            // Set action
            const btnChat = document.getElementById('modal-btn-chat');
            if (btnChat) {
                btnChat.onclick = () => {
                    closeLeadModal();
                    goToChat(lead);
                };
            }

            modal.classList.remove('hidden');
            modal.classList.add('flex');
            // short delay for transition
            setTimeout(() => {
                const mc = modal.querySelector('.modal-content');
                if (mc) mc.classList.remove('scale-95', 'opacity-0');
            }, 10);
        }

        function closeLeadModal() {
            const modal = document.getElementById('lead-info-modal');
            if (!modal) return;
            const mc = modal.querySelector('.modal-content');
            if (mc) mc.classList.add('scale-95', 'opacity-0');
            setTimeout(() => {
                modal.classList.remove('flex');
                modal.classList.add('hidden');
            }, 200);
        }

        function goToChat(lead) {
            switchView('inbox');
            openInboxMaster(lead);
        }

        /* --- MODAL LOGIC --- */
        function openImageModal(src, caption = "") {
            const modal = document.getElementById("image-modal");
            const modalImg = document.getElementById("modal-img");
            const captionText = document.getElementById("modal-caption");
            if (!modal || !modalImg) return;
            
            modal.style.display = "block";
            modalImg.src = src;
            if (captionText) captionText.innerHTML = caption;
        }

        function closeImageModal() {
            const modal = document.getElementById("image-modal");
            if (modal) modal.style.display = "none";
        }

        window.onclick = function(event) {
            const modal = document.getElementById("image-modal");
            if (event.target == modal) closeImageModal();
        }

        /* --- AUDIO SPEED CONTROL --- */
        function changeAudioSpeed(btn) {
            const player = btn.closest('.flex').querySelector('audio');
            if (!player) return;
            
            const speeds = [1, 1.5, 2];
            let current = parseFloat(btn.innerText.replace('x', ''));
            let nextIndex = (speeds.indexOf(current) + 1) % speeds.length;
            let nextSpeed = speeds[nextIndex];
            
            player.playbackRate = nextSpeed;
            btn.innerText = nextSpeed + 'x';
            
            if (nextSpeed > 1) {
                btn.classList.add('text-emerald-400');
                btn.classList.remove('text-cyan-400');
            } else {
                btn.classList.remove('text-emerald-400');
                btn.classList.add('text-cyan-400');
            }
        }
    