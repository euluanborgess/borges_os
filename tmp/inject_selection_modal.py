import sys

html_modal = """
    <!-- Ad Account Selection Modal -->
    <div id="ad-account-selection-modal" class="fixed inset-0 z-[1001] flex flex-col items-center justify-center bg-black/80 backdrop-blur-sm opacity-0 pointer-events-none transition-all duration-300">
        <div class="bg-[#12161f] border border-[#2a2a3e] rounded-2xl w-[90%] max-w-2xl overflow-hidden shadow-2xl transform scale-95 transition-all duration-300">
            <!-- Header -->
            <div class="p-6 border-b border-[#2a2a3e] flex items-center justify-between">
                <div>
                    <h3 class="text-xl font-bold text-white mb-1">Conecte suas contas de anúncio</h3>
                    <p class="text-sm text-[#8b8b9e]">Selecione qual conta de anúncios a Borges OS vai usar para ler os resultados.</p>
                </div>
                <button onclick="closeAdSelectionModal()" class="text-[#8b8b9e] hover:text-white transition-colors">
                    <i class="fa-solid fa-xmark text-xl"></i>
                </button>
            </div>
            
            <!-- Warning -->
            <div class="bg-amber-500/10 border border-amber-500/20 m-6 p-4 rounded-xl flex items-start gap-4">
                <i class="fa-solid fa-triangle-exclamation text-amber-500 mt-1"></i>
                <div>
                    <p class="text-amber-500 text-sm font-bold">Importante</p>
                    <p class="text-amber-500/80 text-xs">Com base na validação oficial da Meta, exibiremos apenas as contas de anúncios onde seu perfil tem permissões de leitura ativas.</p>
                </div>
            </div>

            <!-- List -->
            <div class="px-6 pb-6 max-h-[40vh] overflow-y-auto custom-scroll">
                <div id="ad-accounts-list" class="space-y-3">
                    <div class="text-center py-8">
                        <i class="fa-solid fa-circle-notch fa-spin text-cyan-500 text-3xl mb-4"></i>
                        <p class="text-[#8b8b9e] text-sm font-bold">Buscando contas no Facebook...</p>
                    </div>
                </div>
            </div>
            
            <!-- Footer -->
            <div class="p-6 border-t border-[#2a2a3e] flex justify-end">
                <button id="btn-confirm-ad-account" disabled onclick="submitAdAccountSelection()" class="px-6 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white font-bold text-sm opacity-50 cursor-not-allowed transition-all">
                    Continuar
                </button>
            </div>
        </div>
    </div>

    <!-- Ad Integration Modal -->
"""

js_code = """
        let pendingAdAccountSelectionId = null;
        let selectedAdAccountId = null;
        let selectedAdAccountName = null;

        function openAdSelectionModal(pendingId) {
            pendingAdAccountSelectionId = pendingId;
            const modal = document.getElementById('ad-account-selection-modal');
            modal.classList.remove('opacity-0', 'pointer-events-none');
            modal.children[0].classList.remove('scale-95');
            
            fetchMetaAdAccounts(pendingId);
        }

        function closeAdSelectionModal() {
            const modal = document.getElementById('ad-account-selection-modal');
            modal.classList.add('opacity-0', 'pointer-events-none');
            modal.children[0].classList.add('scale-95');
        }

        async function fetchMetaAdAccounts(pendingId) {
            try {
                const token = localStorage.getItem('bt_token') || localStorage.getItem('bt_session_token');
                if (!token) throw new Error("Usuário não autenticado no Borges OS");
                
                const list = document.getElementById('ad-accounts-list');
                const res = await fetch(`/api/v1/traffic/meta/adaccounts/${pendingId}`, {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                if(!res.ok) throw new Error("Falha ao buscar contas ou token expirado");
                
                const data = await res.json();
                const accounts = data.ad_accounts || [];
                
                if (accounts.length === 0) {
                    list.innerHTML = `<div class="bg-red-500/10 border border-red-500/20 p-4 rounded-xl text-red-400 text-xs font-bold text-center">Nenhuma conta de anúncios (BM) encontrada neste perfil do Facebook. Verifique suas permissões no Meta Business Manager.</div>`;
                    return;
                }
                
                list.innerHTML = '';
                accounts.forEach(acc => {
                    list.innerHTML += `
                        <label class="flex items-center justify-between p-4 border border-[#2a2a3e] rounded-xl hover:border-blue-500/50 hover:bg-white/5 transition-all cursor-pointer group">
                            <div class="flex items-center gap-4">
                                <input type="radio" name="ad_account_radio" value="${acc.account_id}" onchange="selectAdAccount('${acc.account_id}', '${acc.name.replace(/'/g, "\\\\'")}')" class="w-4 h-4 text-blue-600 bg-[#161b22] border-[#2a2a3e] focus:ring-blue-500">
                                <div class="w-10 h-10 bg-blue-500/10 text-blue-500 rounded-lg flex items-center justify-center shrink-0">
                                    <i class="fa-brands fa-meta text-xl"></i>
                                </div>
                                <div>
                                    <p class="text-white font-bold text-sm">${acc.name}</p>
                                    <p class="text-[#8b8b9e] text-xs">ID: ${acc.account_id.replace('act_', '')}</p>
                                </div>
                            </div>
                        </label>
                    `;
                });
            } catch(e) {
                console.error(e);
                document.getElementById('ad-accounts-list').innerHTML = `<div class="bg-red-500/10 border border-red-500/20 p-4 rounded-xl text-red-500 text-xs text-center border-l-4 border-l-red-500">Ocorreu um erro ao recuperar as contas: ${e.message}</div>`;
            }
        }
        
        function selectAdAccount(id, name) {
            selectedAdAccountId = id;
            selectedAdAccountName = name;
            
            const btn = document.getElementById('btn-confirm-ad-account');
            btn.disabled = false;
            btn.classList.remove('opacity-50', 'cursor-not-allowed');
            btn.classList.add('shadow-[0_0_15px_rgba(37,99,235,0.4)]');
        }
        
        async function submitAdAccountSelection() {
            if(!selectedAdAccountId) return;
            try {
                const token = localStorage.getItem('bt_token') || localStorage.getItem('bt_session_token');
                const btn = document.getElementById('btn-confirm-ad-account');
                const oldText = btn.innerHTML;
                btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Salvando...';
                
                const res = await fetch(`/api/v1/traffic/meta/adaccounts/${pendingAdAccountSelectionId}/select`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
                    body: JSON.stringify({ account_id: selectedAdAccountId, name: selectedAdAccountName })
                });
                
                if(!res.ok) throw new Error("Erro na conexão");
                
                btn.innerHTML = '<i class="fa-solid fa-check"></i> Pronto!';
                btn.classList.replace('from-blue-600', 'from-emerald-500');
                btn.classList.replace('to-cyan-500', 'to-emerald-400');
                
                setTimeout(() => {
                    closeAdSelectionModal();
                    // Clean URL
                    window.history.replaceState({}, document.title, window.location.pathname);
                    // Refresh dashboard
                    const trView = document.getElementById('traffic-view');
                    if(trView && !trView.classList.contains('hidden')) {
                        switchView('traffic');
                    }
                }, 1000);
            } catch(e) {
                console.error(e);
                alert("Erro ao confirmar seleção de Ad Account.");
                document.getElementById('btn-confirm-ad-account').innerHTML = 'Continuar';
            }
        }

        // --- Interceptador de URL para abrir Modal Automaticamente ---
        window.addEventListener('DOMContentLoaded', () => {
            const urlParams = new URLSearchParams(window.location.search);
            const modalOpen = urlParams.get('modal');
            const pId = urlParams.get('pending_id');
            if (modalOpen === 'select_ad_account' && pId) {
                setTimeout(() => {
                    openAdSelectionModal(pId);
                }, 500);
            } else if (modalOpen === 'ads_integrated') {
                alert("Conectado com sucesso!");
                window.history.replaceState({}, document.title, window.location.pathname);
            }
        });
    </script>
"""

import os
index_path = r"c:\Users\User\Documents\BorgesOS_Atualizado\public\index.html"
with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

# REPLACE HTML
html = html.replace("    <!-- Ad Integration Modal -->", html_modal)

# REPLACE JS
html = html.replace("    </script>", js_code)

with open(index_path, "w", encoding="utf-8") as f:
    f.write(html)
print("SUCCESS INJECTION")
