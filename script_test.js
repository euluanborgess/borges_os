>     <script>
          let currentTenantId = null;
          let activeLeadId = null;
          let ws = null;
  
          document.addEventListener('DOMContentLoaded', async () => {
              await initializeApp();
              // Start Dashboard polling mock (animates numbers)
              setInterval(fetchDashboardMock, 5000);
          });
  
          /* --- SPA ROUTING --- */
          function switchView(viewId, btnEl = null) {
              // Hide all views
              document.querySelectorAll('.app-view').forEach(el => el.classList.remove('active'));
              // Remove active classes from nav items based on Base 44
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
  
              // Route-specific side-effects
              if (viewId === 'pipeline' || viewId === 'inbox') fetchKanbanData();
          }
  
          /* --- API CALLS --- */
          async function initializeApp() {
              try {
                  const res = await fetch('/api/v1/tenant');
                  const t = await res.json();
                  if (t.id) {
                      currentTenantId = t.id;
                      const name = t.name || 'Ag?ncia Borges';
                      document.getElementById('sidebar-name').innerText = name;
                      document.getElementById('username-display').innerText = name.split(' ')[0];
                      document.getElementById('sidebar-avatar').innerText = name.charAt(0).toUpperCase();
  
                      fetchDashboardMock();
                      connectWebSocket();
                  }
              } catch (e) { console.error(" Init Error", e); }
          }
  
          async function fetchDashboardMock() {
              if (!currentTenantId) return;
              try {
                  const res = await fetch(`/api/v1/dashboard/metrics?tenant_id=${currentTenantId}`);
                  const metrics = await res.json();
                  if (metrics.status === 'success') {
                      const data = metrics.data;
                      let tCount = 0;
                      for (const s in data.pipeline_breakdown) tCount += data.pipeline_breakdown[s];
  
                      animateValue("metric-total-leads", parseInt(document.getElementById('metric-total-leads').innerText) || 0, tCount, 1000);
                      animateValue("metric-meetings", parseInt(document.getElementById('metric-meetings').innerText) || 0, data.total_events || 0, 1000);
                      animateValue("metric-interactions", parseInt(document.getElementById('metric-interactions').innerText) || 0, data.waiting_human || 0, 1000);
                  }
              } catch (e) { }
          }
  
          function animateValue(id, start, end, duration) {
              if (start === end) return;
              const obj = document.getElementById(id);
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
          function getBadgeCol(temp) {
              temp = (temp || 'frio').toLowerCase();
              if (temp.includes('quente') || temp.includes('alta')) return 'bg-red-500/20 text-red-400 border-red-500/30';
              if (temp.includes('morno') || temp.includes('media')) return 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30';
              return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
          }
  
          function buildCard(lead) {
              const letter = (lead.name && lead.name !== "Desconhecido") ? lead.name.charAt(0) : "W";
              const nome = (lead.name && lead.name !== "Desconhecido") ? lead.name : lead.phone;
              const badgeCls = getBadgeCol(lead.temperature);
  
              const leadStr = JSON.stringify(lead).replace(/'/g, "&apos;").replace(/"/g, "&quot;");
  
              const txt = (lead.last_message && lead.last_message !== "Conversa iniciada") ? lead.last_message.substring(0, 70) + '...' : 'Aguardando processamento de linguagem...';
  
              return `
                  <div class="lead-card p-4 rounded-xl cursor-pointer" onclick="openDrawer(${leadStr})">
                      <div class="flex justify-between items-center mb-3">
                          <span class="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border ${badgeCls}">${lead.temperature || 'frio'}</span>
                          <span class="text-xs text-brand-400 font-mono font-bold">${lead.score || 0} pts</span>
                      </div>
                      <div class="flex items-center space-x-3 mb-3">
                          <div class="w-8 h-8 rounded-full bg-ui-800 border border-ui-700 flex items-center justify-center text-xs font-bold text-gray-300 shrink-0">
                              ${letter.toUpperCase()}
                          </div>
                          <div class="overflow-hidden">
                              <h4 class="text-gray-200 font-semibold text-sm truncate">${nome}</h4>
                              <p class="text-gray-500 text-[10px] font-mono truncate"><i class="fa-brands fa-whatsapp text-emerald-500/80 mr-1"></i> ${lead.phone}</p>
                          </div>
                      </div>
                      <p class="text-[10px] text-gray-400 font-light italic leading-relaxed line-clamp-2 bg-ui-900/50 p-2 rounded border border-ui-700/50">
                          <span class="font-bold text-brand-400 not-italic uppercase text-[8px] tracking-wider block mb-0.5">Borges Resumo:</span>
                          "${txt}"
                      </p>
                  </div>
              `;
          }
  
          async function fetchKanbanData() {
              if (!currentTenantId) return;
              try {
                  const res = await fetch(`/api/v1/ws/inbox/leads/${currentTenantId}`);
                  const payload = await res.json();
                  if (payload.data) {
                      const cols = {
                          "novo": { el: document.querySelector('#kanban-stage-novo .content-area'), c: 0, b: document.querySelector('#kanban-stage-novo .count-badge') },
                          "contato": { el: document.querySelector('#kanban-stage-contato .content-area'), c: 0, b: document.querySelector('#kanban-stage-contato .count-badge') },
                          "qualificacao": { el: document.querySelector('#kanban-stage-qualificacao .content-area'), c: 0, b: document.querySelector('#kanban-stage-qualificacao .count-badge') },
                          "agendamento": { el: document.querySelector('#kanban-stage-agendamento .content-area'), c: 0, b: document.querySelector('#kanban-stage-agendamento .count-badge') }
                      };
                      Object.values(cols).forEach(col => col.el.innerHTML = '');
  
                      const inboxList = document.getElementById('inbox-leads-list');
                      if (inboxList) inboxList.innerHTML = '';
  
                      payload.data.forEach(lead => {
                          let st = (lead.pipeline_stage || "novo").toLowerCase();
                          let target = "novo";
                          if (st.includes("contato")) target = "contato";
                          else if (st.includes("qualifica")) target = "qualificacao";
                          else if (st.includes("agenda") || st.includes("venda")) target = "agendamento";
  
                          cols[target].el.innerHTML += buildCard(lead);
                          [target].c++;
  
                          // Populate Inbox 3-Col List (Coluna 1)
                          if (inboxList) { const name = (lead.name && lead.name !== "Desconhecido") ? lead.name : lead.phone;
                          const letter = name.charAt(0).toUpperCase();
                          const leadStr = JSON.stringify(lead).replace(/'/g, "&apos;").replace(/"/g, "&quot;");
  
                          // Visual badge baseado no handoff (simulado, vamos fingir que bot=cyan, human=orange)
                          const isH = false; // logic placeholder
                          const agentPill = isH
                              ? `<div class="flex items-center text-[10px] text-orange-400 font-medium"><i class="fa-solid fa-user mr-1"></i> Human</div>`
                              : `<div class="flex items-center text-[10px] text-gray-500 font-medium"><i class="fa-solid fa-robot mr-1"></i> Bot Ativo</div>`;
  
                          inboxList.innerHTML += `
                                  <div class="px-4 py-3 border-b border-ui-800/20 hover:bg-ui-800/80s relative group" onclick='openInboxMaster(${leadStr})'>
                                      <div class="flex items-center space-x-3 relative">
                                          
                                          <!-- Avatar with dynamic WhatsApp icon overlay -->
                                          <div class="relative shrink-0">
                                              <div class="w-10 h-10 rounded-full bg-ui-800 text-gray-300 font-bold flex items-center justify-center border border-ui-700">
                                                  ${letter}
                                              </div>
                                              <div class="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-ui-900 flex items-center justify-center">
                                                  <i class="fa-brands fa-whatsapp text-[10px] text-emerald-500"></i>
                                              </div>
                                          </div>
  
                                          <div class="flex-1 min-w-0">
                                              <div class="flex justify-between items-baseline mb-0.5">
                                                  <h4 class="text-gray-200 text-sm font-semibold truncate group-hover:text-brand-400 transition-colors">${name}</h4>
                                                  <span class="text-[9px] text-gray-500 font-mono shrink-0">Ontem</span>
                                              </div>
                                              ${agentPill}
                                          </div>
                                      </div>
                                  </div>
                              `;
                      }
                      });
  
                  Object.values(cols).forEach(col => col.b.innerText = col.c);
              }
              } catch (e) { }
          }
  
          /* --- DRAWER (HUD) --- */
          async function openDrawer(lead) {
              activeLeadId = lead.id;
              const nome = (lead.name && lead.name !== "Desconhecido") ? lead.name: lead.phone;
  
              document.getElementById('draw-name').innerText = nome;
              document.getElementById('draw-phone').innerText = lead.phone;
              document.getElementById('draw-avatar').innerText = nome.charAt(0).toUpperCase();
              document.getElementById('draw-stage-txt').innerText = lead.pipeline_stage || "PROSPEC??O";
  
              document.getElementById('draw-tags-container').innerHTML = `
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${getBadgeCol(lead.temperature)}">${lead.temperature || 'FRIO'}</span>
              `;
  
              const score = lead.score || 0;
              document.getElementById('draw-score-txt').innerText = score + " pts";
              const bar = document.getElementById('draw-score-bar');
              setTimeout(() => { bar.style.width = score + "%"; }, 100);
  
              document.getElementById('draw-ai-summary').innerText = `O lead trocou mensagens no est?gio atual. Temperatura calculada como "${lead.temperature || 'frio'}". Probabilidade de fechamento em an?lise algor?tmica.`;
  
              document.getElementById('drawer-overlay').classList.add('open');
              setTimeout(() => { document.getElementById('drawer-panel').classList.add('open'); }, 10);
  
              await loadChat(lead.id); // Re-use old chat rendering logic for drawer
          }
  
          function closeDrawer(e) {
              if (e && e.target.id !== 'drawer-overlay' && e.target.tagName !== 'BUTTON' && !e.target.closest('button')) return;
              document.getElementById('drawer-panel').classList.remove('open');
              setTimeout(() => { document.getElementById('drawer-overlay').classList.remove('open'); activeLeadId = null; }, 300);
  
              // Re-lock Handoff visually
              toggleHandoff(false);
          }
  
          /* --- OLD DRAWER CHAT (Used when clicking from KanBan) --- */
          function toggleHandoff(isActive) {
              inp = document.getElementById('msg-input');
              const btn = document.getElementById('btn-send');
              const handoffBtn = document.getElementById('btn-handoff');
              const resumeBtn = document.getElementById('btn-resume-ai');
  
              if (isActive) {
                  inp.disabled = false; btn.disabled = false;
                  inp.placeholder = "Modo Humano ON. Digite sua mensagem de WPP...";
                  handoffBtn.classList.add('hidden'); resumeBtn.classList.remove('hidden');
                  inp.focus();
              } else {
                  inp.disabled = true; btn.disabled = true;
                  inp.placeholder = "Assuma o controle (Handoff) para enviar manuais...";
                  handoffBtn.classList.remove('hidden'); resumeBtn.classList.add('hidden');
                  inp.value = '';
              }
          }
  
          async function loadChat(leadId) {
              const chatDiv = document.getElementById('chat-history');
              chatDiv.innerHTML = '<div class="text-center text-brand-500 mt-20"><i class="fa-solid fa-circle-notch fa-spin text-2xl mb-2"></i></div>';
              toggleHandoff(false);
  
              try {
                  const res = await fetch(`/api/v1/ws/inbox/messages/${currentTenantId}/${leadId}`);
                  const payload = await res.json();
                  chatDiv.innerHTML = '';
  
                  if (payload.data && payload.data.length > 0) {
                      payload.data.forEach(m => drawMsg(m.sender_type, m.content));
                      scrollToBottom();
                  } else {
                      v.innerHTML = '<div  class="text-center text-gray-500 mt-20 text-xs"><i class="fa-regular fa-comments text-2xl mb-2"></i><br>Nenhuma mensagem trocada.</div>';
                  }
              } catch (e) { }
          }
  
          function drawMsg(sender, text) {
              const d = document.getElementById('chat-history');
              const w = document.createElement('div');
  
              if (sender === 'ai' || sender === 'human' || send er === 'agent') {
                  w.className = "flex justify-end";
                  const isH = sender === 'human';
                  w.innerHTML = `
                      <dx-w-[80%] text-[13px] ${isH ? 'bg-orange-900/40 border-orange-500/50' : 'bg-ui-800 border-ui-700/70'} px-4 py-3 text-gray-200 rounded-2xl border ${isH ? 'rounded-br-sm' : 'rounded-br-sm'} shadow-lg relative glow-effect">
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
              d.scrollTop = d.scrollHeight;
          }
  
          document.getElementById('send-msg-form').onsubmit = (e) => {
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
  
          /* --- THE INBOX M (3-COLUMNS) -- - */
          async function openInboxMaster(lead) {
              console.log("Opening master inbox for lead:", lead);
              // Em vez do Drawer estilo Kanban, abre na aba 'inbox' (Coluna 2 e 3)
              if (!document.getElementById('view-inbox').classList.contains('active')) {
                  switchView('inbox');
              }
              activeLeadId = lead.id;
              const nome = (lead.name && lead.name !== "Desconhecido") ? lead.name : lead.phone;
  
              // Revelar Header, Footer e Detalhes da Coluna Central/Direita
              document.getElementById('chat-master-empty').classList.add('hidden');
              document.getElementById('chat-master-header').classList.remove('hidden');
              document.getElementById('chat-master-footer').classList.remove('hidden');
              document.getElementById('chat-history-master').classList.remove('hidden');
              document.getElementById('chat-master-details').classList.remove('hidden');
  
              // Preencher Topbar Coluna Centro
              document.getElementById('chat-master-name').innerText = nome;
              document.getElementById('chat-master-phone').innerText = lead.phone;
              document.getElementById('chat-master-avatar').innerText = nome.charAt(0).toUpperCase();
  
              // Preencher Detalhes Coluna Direita
              document.getElementById('detail-master-name').innerText = nome;
              document.getElementById('detail-master-phone').innerText = lead.phone;
              document.getElementById('detail-master-avatar').innerText = nome.charAt(0).toUpperCase();
  
              let badgeCls = 'bg-blue-500/20 text-blue-400 border-blue-500/30';
              let temp = (lead.temperature || 'frio').toLowerCase();
              if (temp.includes('quente') || temp.includes('alta')) badgeCls = 'bg-red-500/20 text-red-400 border-red-500/30';
              if (temp.includes('morno') || temp.includes('media')) badgeCls = 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30';
  
              document.getElementById('detail-master-tags').innerHTML = `<span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${badgeCls
          } ">${lead.temperature || 'FRIO'}</span>`;
          document.getElementById('detail-master-stage').innerText = lead.pipeline_stage || "PROSPECÇÃO";
  
          // Fechar Drawer antigo caso esteja aberto (fallback)
          closeDrawer();
  
          // Buscar histórico de mensagens e preencher a Coluna Central
          await loadMasterChat(lead.id);
          }
  
          /* --- CHAT ENGINE REWIRE PARA O INBOX MASTER --- */
          function toggleMasterHandoff(isActive) {
              const inp = document.getElementById('msg-input-master');
              const btn = document.getElementById('btn-send-master');
              const handoffBtn = document.getElementById('btn-master-handoff');
              const resumeBtn = document.getElementById('btn-master-resume-ai');
  
              if (isActive) {
                  inp.disabled = false; btn.disabled = false;
                  inp.placeholder = "Modo Humano ativado. Digite sua mensagem para o WhatsApp...";
                  handoffBtn.classList.add('hidden'); resumeBtn.classList.remove('hidden');
                  inp.focus();
              } else {
                  inp.disabled = true; btn.disabled = true;
                  inp.placeholder = "Assuma o controle no topo (Botão Laranja) para digitar...";
                  handoffBtn.classList.remove('hidden'); resumeBtn.classList.add('hidden');
                  inp.value = '';
              }
          }
  
          async function loadMasterChat(leadId) {
              const chatDiv = document.getElementById('chat-history-master');
              chatDiv.innerHTML = '<div class="absolute inset-0 flex items-center justify-center text-brand-500 mt-20"><i class="fa-solid fa-circle-notch fa-spin text-2xl mb-2"></i></div>';
              toggleMasterHandoff(false); // Default to AI mode
  
              try {
                  const res = await fetch(`/api/v1/ws/inbox/messages/${currentTenantId}/${leadId}`);
                  const payload = await res.json();
                  chatDiv.innerHTML = '';
  
                  if (payload.data && payload.data.length > 0) {
                      payload.data.forEach(m => drawMsgMaster(m.sender_type, m.content));
                      scrollToBottomMaster();
                  } else {
                      chatDiv.innerHTML = '<div class="absolute inset-0 flex flex-col items-center justify-center text-gray-600 space-y-2"><i class="fa-regular fa-comments text-4xl mb-2"></i><span>Ainda n?o h? mensagens com este contato.</span></div>';
                  }
              } catch (e) { }
          }
  
          function drawMsgMaster(sender, text) {
              const d = document.getElementById('chat-history-master');
              const w = document.createElement('div');
              // Formatar blocos de chat ao estilo Brand-400 com leveza
              if (sender === 'ai' || sender === 'human' || sender === 'agent') {
                  w.className = "flex justify-end w-full"; // w-full required because flex-col handles layout
                  const isH = sender === 'human';
                  w.innerHTML = `
                      <div class="max-w-[70%] text-[13px] ${isH ? 'bg-orange-900/40 border-orange-500/50' : 'bg-[#0f172a] border-brand-500/30'} px-4 py-3 text-gray-200 rounded-2xl border ${isH ? 'rounded-br-sm' : 'rounded-br-sm'} shadow-lg relative glow-effect mb-4">
                          ${text.replace(/\n/g, '<br>')}
                          <div class="text-[9px] ${isH ? 'text-orange-400' : 'text-brand-400/80'} text-right mt-1.5 flex justify-end items-center uppercase font-bold tracking-wider">
                              ${isH ? '<i class="fa-solid fa-user mr-1"></i> Humano' : '<i class="fa-solid fa-robot mr-1"></i> Borges (Bot)'}
                          </div>
                      </div>
                  `;
              } else {
                  w.className = "flex justify-start w-full";
                  w.innerHTML = `
                      <div class="max-w-[70%] text-[13px] bg-ui-800/80 px-4 py-3 text-white rounded-2xl border border-ui-700/80 rounded-bl-sm shadow-md mb-4">
                          ${text.replace(/\n/g, '<br>')}
                          <div class="text-[9px] text-gray-500 text-left mt-1.5 flex items-center uppercase font-bold tracking-wider">
                              <i class="fa-brands fa-whatsapp mr-1 text-emerald-500"></i> Cliente
                          </div>
                      </div>
                  `;
              }
              d.appendChild(w);
          }
  
          function scrollToBottomMaster() {
              const d = document.getElementById('chat-history-master');
              d.scrollTop = d.scrollHeight;
          }
  
          document.getElementById('send-msg-form-master').onsubmit = (e) => {
              e.preventDefault();
              const i = document.getElementById('msg-input-master');
              const txt = i.value.trim();
              if (!txt || !activeLeadId) return;
  
              drawMsgMaster('human', txt);
              scrollToBottomMaster();
  
              if (ws && ws.readyState === WebSocket.OPEN) {
                  ws.send(JSON.stringify({ action: "send_message", lead_id: activeLeadId, content: txt }));
              }
              i.value = '';
          };
  
          /* --- WEBSOCKET EVENT LISTENER MASTER --- */
          function connectW
              ws = new WebSocket(`ws://${window.location.host}/api/v1/ws/inbox/${currentTenantId}`);
          ws.onmessage = (e) => {
              const data = JSON.parse(e.data);
              if (data.event === "db_update" || data.event.includes("message")) {
                  fetchKanbanData(); // Live reload cards implicitly
              }
              if (activeLeadId && data.lead_id === activeLeadId) {
                  if (data.event === "message_received") {
                      if (dif (!document.getElementById('view-inbox').classList.contains('active')) {
                          drawMsgMaster('lead', data.content);
                          scrollToBottomMaster();
                      } else {
                          drawMsg('lead', data.content);
                          scrollToBottom();
                      }
                  }
                  nt === "message_sent_ai") {
                      etElementById('view-inbox').classList.contains('active')) drawMsgMaster('ai', data.cont                                 scrollToBottomMaster();
                  } else {
                      drawMsg('ai', data.content);
                      scrollToBottom();
                  }
              }
              ws.onclose = () => setTimeout(connectWebSocket, 3000);
          }
      </script>
      <style>
          body {
              background-color: #020617;
              color: #f8fafc;
              font-family: 'Inter', system-ui, -apple-system, sans-serif;
              overflow: hidden;
          }
  
          .no-scrollbar::-webkit-scrollbar {
              display: none;
          }
  
          .no-scrollbar {
              -ms-overflow-style: none;
              scrollbar-width: none;
          }
  
          /* Custom Scrollbar */
          .custom-scroll::-webkit-scrollbar {
              width: 6px;
          }
  
          .custom-scroll::-webkit-scrollbar-track {
              background: transparent;
          }
  
          .custom-scroll::-webkit-scrollbar-thumb {
              background: #1e293b;
              border-radius: 10px;
          }
  
          .custom-scroll::-webkit-scrollbar-thumb:hover {
              background: #334155;
          }
  
          /* Glass Panels */
          .glass-panel {
              background: rgba(15, 23, 42, 0.4);
              backdrop-filter: blur(16px);
              -webkit-backdrop-filter: blur(16px);
              border: 1px solid rgba(255, 255, 255, 0.05);
              box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
          }
  
          .bg-grid {
              position: absolute;
              inset: 0;
              background-size: 50px 50px;
              background-image: linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                  linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
              z-index: -1;
              pointer-events: none;
          }
  
          /* Views Visibility */
          .app-view {
              display: none;
              /* Hide all by default */
              height: 100%;
              width: 100%;
              animation: fadeIn 0.3s ease-in-out;
          }
  
          .app-view.active {
              display: flex;
              /* Show active */
          }
  
          @keyframes fadeIn {
              from {
                  opacity: 0;
                  transform: translateY(10px);
              }
  
              to {
                  opacity: 1;
                  transform: translateY(0);
              }
          }
  
          /* Navigation ACTIVE state */
          .nav-item.active {
              background-color: rgba(45, 212, 191, 0.1);
              /* brand-400 / 10% */
              color: #2dd4bf;
              font-weight: 500;
          }
  
          .nav-item.active i {
              color: #2dd4bf;
          }
  
          /* SVG Brain Animations */
          @keyframes pulse-node {
  
              0%,
              100% {
                  fill: #2dd4bf;
                  r: 3;
                  filter: drop-shadow(0 0 4px #2dd4bf);
              }
  
              50% {
                  fill: #fff;
                  r: 5;
                  filter: drop-shadow(0 0 10px #2dd4bf);
              }
          }
  
          @keyframes flow-line {
              0% {
                  stroke-dashoffset: 100;
                  opacity: 0.3;
              }
  
              50% {
                  opacity: 1;
              }
  
              100% {
                  stroke-dashoffset: -100;
                  opacity: 0.3;
              }
          }
  
          .node {
              animation: pulse-node 3s infinite ease-in-out;
          }
  
          .node:nth-child(even) {
              animation-delay: 1.5s;
              animation-duration: 4s;
          }
  
          .node:nth-child(3n) {
              animation-delay: 0.5s;
              fill: #60a5fa;
          }
  
          .connection {
              stroke: rgba(45, 212, 191, 0.3);
              stroke-width: 1.5;
              stroke-dasharray: 10;
              animation: flow-line 4s linear infinite;
          }
  
          /* Drawer Styles */
          .drawer-overlay {
              background-color: rgba(2, 6, 23, 0.6);
              backdrop-filter: blur(4px);
              opacity: 0;
              pointer-events: none;
              transition: opacity 0.3s ease;
          }
  
          .drawer-overlay.open {
              opacity: 1;
              pointer-events: auto;
          }
  
          .drawer-panel {
              transform: translateX(100%);
              transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
              background-color: #0f172a;
              border-left: 1px solid #1e293b;
          }
  
          .drawer-panel.open {
              transform: translateX(0);
          }
  
          /* Kanban Column Line */
          .column-header-line {
              height: 2px;
              width: 100%;
              background: #1e293b;
              position: relative;
              margin-top: 8px;
              margin-bottom: 16px;
          }
  
          .lead-card {
              background-color: rgba(30, 41, 59, 0.4);
              border: 1px solid #1e293b;
              transition: all 0.2s ease;
          }
  
          .lead-card:hover {
              border-color: #2dd4bf;
              box-shadow: 0 4px 15px rgba(45, 212, 191, 0.15);
              transform: translateY(-2px);
          }
  
          /* Base 44 Layout CSS Fixes */
          :root {
              --bg-primary: #0a0a0f;
              --bg-card: #16161e;
              --border-color: #1e1e2e;
              --accent-cyan: #06b6d4;
          }
  
          body {
              background: var(--bg-primary);
          }
  
          .nav-active {
              background: linear-gradient(135deg, rgba(6, 182, 212, 0.15), rgba(14, 116, 144, 0.08));
              border-left: 3px solid var(--accent-cyan);
          }
  
          .gradient-text {
              background: linear-gradient(135deg, #06b6d4, #0e7490);
              -webkit-background-clip: text;
              -webkit-text-fill-color: transparent;
          }
      </style>
  </head>
  
  <body class="w-screen h-screen flex text-sm relative">
      <div class="bg-grid"></div>
  
      <!-- SIDEBAR BASE 44 -->
      <aside
          class="fixed lg:relative top-0 left-0 h-screen z-50 transition-all duration-300 ease-in-out bg-[#111118] border-r border-[#1e1e2e] flex flex-col w-[250px] shrink-0">
  
          <!-- Logo -->
          <div class="h-16 flex items-center px-4 border-b border-[#1e1e2e] gap-3 shrink-0 cursor-pointer"
              onclick="switchView('dashboard', document.querySelector('.nav-item'))">
              <div
                  class="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-cyan-800 flex items-center justify-center flex-shrink-0 shadow-[0_0_15px_rgba(6,182,212,0.3)]">
                  <i
                      class="fa-solid fa-wand-magic-sparkles w-4 h-4 text-white flex items-center justify-center text-[14px]"></i>
              </div>
              <span class="font-bold text-lg tracking-tight gradient-text">Borges OS</span>
          </div>
  
          <!-- Nav -->
          <nav class="flex-1 py-4 px-2 space-y-1 overflow-y-auto custom-scroll" id="main-nav-container">
              <button onclick="switchView('dashboard', this)"
                  class="nav-item nav-active text-white w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200">
                  <i
                      class="fa-solid fa-border-all w-5 h-5 flex-shrink-0 text-cyan-400 flex items-center justify-center"></i>
                  <span>Dashboard</span>
              </button>
              <button onclick="switchView('pipeline', this)"
                  class="nav-item text-[#8b8b9e] hover:text-white hover:bg-[#1c1c28] w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200">
                  <i class="fa-solid fa-users w-5 h-5 flex-shrink-0 flex items-center justify-center"></i>
                  <span>Leads CRM</span>
              </button>
              <button onclick="switchView('inbox', this)"
                  class="nav-item text-[#8b8b9e] hover:text-white hover:bg-[#1c1c28] w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200">
                  <i class="fa-regular fa-comment-dots w-5 h-5 flex-shrink-0 flex items-center justify-center"></i>
                  <span>Conversas</span>
              </button>
              <button onclick="switchView('calendar', this)"
                  class="nav-item text-[#8b8b9e] hover:text-white hover:bg-[#1c1c28] w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200">
                  <i class="fa-regular fa-calendar w-5 h-5 flex-shrink-0 flex items-center justify-center"></i>
                  <span>Agendamentos</span>
              </button>
              <button onclick="switchView('tasks', this)"
                  class="nav-item text-[#8b8b9e] hover:text-white hover:bg-[#1c1c28] w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200">
                  <i class="fa-solid fa-clipboard-list w-5 h-5 flex-shrink-0 flex items-center justify-center"></i>
                  <span>Tarefas</span>
              </button>
              <button onclick="switchView('contracts', this)"
                  class="nav-item text-[#8b8b9e] hover:text-white hover:bg-[#1c1c28] w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200">
                  <i class="fa-solid fa-file-contract w-5 h-5 flex-shrink-0 flex items-center justify-center"></i>
                  <span>Contratos</span>
              </button>
              <button onclick="switchView('ai', this)"
                  class="nav-item text-[#8b8b9e] hover:text-white hover:bg-[#1c1c28] w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200">
                  <i class="fa-solid fa-brain w-5 h-5 flex-shrink-0 flex items-center justify-center"></i>
                  <span>Borges IA</span>
              </button>
              <button onclick="switchView('reports', this)"
                  class="nav-item text-[#8b8b9e] hover:text-white hover:bg-[#1c1c28] w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200">
                  <i class="fa-solid fa-chart-pie w-5 h-5 flex-shrink-0 flex items-center justify-center"></i>
                  <span>Relatórios</span>
              </button>
              <button onclick="switchView('settings', this)"
                  class="nav-item text-[#8b8b9e] hover:text-white hover:bg-[#1c1c28] w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200">
                  <i class="fa-solid fa-gear w-5 h-5 flex-shrink-0 flex items-center justify-center"></i>
                  <span>Configurações</span>
              </button>
          </nav>
  
          <!-- User profile and Logout -->
          <div class="mt-auto p-3 border-t border-[#1e1e2e] flex flex-col items-center px-3">
              <div class="flex items-center gap-3 w-full">
                  <div class="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-cyan-800 flex items-center justify-center text-xs font-bold text-white shadow-[0_0_10px_rgba(6,182,212,0.2)] flex-shrink-0"
                      id="sidebar-avatar">
                      U
                  </div>
                  <div class="overflow-hidden flex-1">
                      <p class="text-sm font-semibold text-white truncate" id="sidebar-name">Carregando...</p>
                      <p class="text-[10px] text-[#5a5a6e] truncate" id="sidebar-role">System Admin</p>
                  </div>
                  <button
                      class="p-1.5 rounded-lg text-[#5a5a6e] hover:text-white hover:bg-[#1c1c28] transition-colors shrink-0">
                      <i class="fa-solid fa-right-from-bracket w-4 h-4 flex items-center justify-center"></i>
                  </button>
              </div>
              <!-- Collapse toggle -->
              <button
                  class="w-full flex items-center justify-center py-2.5 rounded-lg mt-3 text-[#5a5a6e] hover:text-white hover:bg-[#1c1c28] transition-colors">
                  <i class="fa-solid fa-chevron-left w-4 h-4"></i>
              </button>
          </div>
      </aside>
  
      <!-- MAIN CONTENT -->
      <main class="flex-1 flex flex-col relative w-full h-full bg-transparent overflow-hidden">
  
          <!-- Top bar (NEW - Base 44) -->
          <header
              class="h-16 border-b border-[#1e1e2e] bg-[#111118]/80 backdrop-blur-xl flex items-center px-4 lg:px-6 gap-4 sticky top-0 z-30 shrink-0">
              <button class="lg:hidden text-gray-400 hover:text-white">
                  <i class="fa-solid fa-bars w-5 h-5"></i>
