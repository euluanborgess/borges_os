/**
 * Borges OS — Premium Welcome Modal (First Login Experience)
 * Self-injecting module: call initWelcomeModal(userName) to show.
 * 
 * WhatsApp + Instagram connection happen INLINE (no external modals).
 */

(function() {

    // ===== INJECT STYLES =====
    const style = document.createElement('style');
    style.textContent = `
        @keyframes welcomeFadeSlideUp {
            0% { opacity: 0; transform: translateY(30px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        @keyframes welcomeFadeOut {
            0% { opacity: 1; transform: translateY(0); }
            100% { opacity: 0; transform: translateY(-20px); }
        }
        @keyframes welcomeOrbFloat {
            0%, 100% { transform: translate(0, 0) scale(1); }
            25% { transform: translate(30px, -40px) scale(1.1); }
            50% { transform: translate(-20px, -60px) scale(0.95); }
            75% { transform: translate(-40px, -20px) scale(1.05); }
        }
        @keyframes welcomePulseGlow {
            0%, 100% { box-shadow: 0 0 40px rgba(6,182,212,0.15); }
            50% { box-shadow: 0 0 80px rgba(6,182,212,0.3); }
        }
        #welcome-modal {
            position: fixed; inset: 0; z-index: 9999; background: #0a0a0f;
            font-family: 'Inter', -apple-system, sans-serif;
            overflow-y: auto;
        }
        .wm-slide {
            display: none; flex-direction: column; align-items: center; justify-content: center;
            min-height: 100vh; padding: 40px 20px; position: relative;
        }
        .wm-slide.active { display: flex; }
        .wm-fi { animation: welcomeFadeSlideUp 0.8s ease-out forwards; opacity: 0; }
        .wm-fi.d1 { animation-delay: 0.2s; }
        .wm-fi.d2 { animation-delay: 0.6s; }
        .wm-fi.d3 { animation-delay: 1.0s; }
        .wm-fi.d4 { animation-delay: 1.4s; }
        .wm-fi.d5 { animation-delay: 1.8s; }
        .wm-orb {
            position: absolute; border-radius: 50%; filter: blur(80px); pointer-events: none;
            animation: welcomeOrbFloat 10s ease-in-out infinite;
        }
        .wm-btn-primary {
            padding: 14px 40px; background: linear-gradient(135deg,#06b6d4,#0e7490);
            border: none; border-radius: 12px; color: #fff; font-size: 15px; font-weight: 700;
            cursor: pointer; box-shadow: 0 4px 20px rgba(6,182,212,0.3);
            font-family: inherit; transition: all 0.2s;
        }
        .wm-btn-primary:hover { opacity: 0.9; transform: translateY(-1px); }
        .wm-btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .wm-btn-skip {
            padding: 12px 28px; background: transparent; border: 1px solid #1e1e2e;
            border-radius: 12px; color: #5a5a6e; font-size: 13px; cursor: pointer;
            font-family: inherit; transition: all 0.2s;
        }
        .wm-btn-skip:hover { border-color: #06b6d4; color: #06b6d4; }
        .wm-dots { display: flex; gap: 8px; justify-content: center; margin-bottom: 24px; }
        .wm-dot { width: 32px; height: 4px; border-radius: 2px; background: #1e1e2e; transition: background 0.3s; }
        .wm-dot.filled { background: #06b6d4; }
        .wm-icon-box {
            width: 64px; height: 64px; margin: 0 auto 24px; border-radius: 16px;
            display: flex; align-items: center; justify-content: center;
        }
        .wm-qr-area {
            background: #111118; border: 1px solid #1e1e2e; border-radius: 16px;
            padding: 24px; text-align: center; min-height: 200px;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
        }
        .wm-qr-area img { max-width: 200px; max-height: 200px; border-radius: 8px; }
        .wm-insta-area {
            background: #111118; border: 1px solid #1e1e2e; border-radius: 16px;
            padding: 24px; text-align: center;
        }
    `;
    document.head.appendChild(style);

    // ===== INJECT HTML =====
    const modal = document.createElement('div');
    modal.id = 'welcome-modal';
    modal.style.display = 'none';
    modal.innerHTML = `
        <!-- Floating orbs -->
        <div class="wm-orb" style="width:500px;height:500px;top:-10%;left:20%;background:radial-gradient(circle,rgba(6,182,212,0.12) 0%,transparent 70%);animation-duration:12s;"></div>
        <div class="wm-orb" style="width:350px;height:350px;bottom:10%;right:5%;background:radial-gradient(circle,rgba(14,116,144,0.08) 0%,transparent 70%);animation-delay:-5s;animation-duration:15s;"></div>
        <div class="wm-orb" style="width:250px;height:250px;top:40%;left:-5%;background:radial-gradient(circle,rgba(6,100,200,0.06) 0%,transparent 70%);animation-delay:-3s;"></div>

        <!-- SLIDE 1: Welcome -->
        <div class="wm-slide active" id="wm-slide-1">
            <div style="text-align:center;max-width:560px;z-index:10;">
                <div class="wm-fi" style="margin-bottom:32px;">
                    <div style="width:80px;height:80px;margin:0 auto;background:linear-gradient(135deg,#06b6d4,#0e7490);border-radius:20px;display:flex;align-items:center;justify-content:center;font-size:36px;animation:welcomePulseGlow 3s ease-in-out infinite;">
                        <i class="fa-solid fa-bolt" style="color:#fff;"></i>
                    </div>
                </div>
                <h1 class="wm-fi d1" style="font-size:36px;font-weight:800;color:#fff;margin:0 0 12px;letter-spacing:-1px;">
                    Ol\u00e1, <span id="wm-user-name" style="color:#06b6d4;">Parceiro</span>! \ud83c\udf89
                </h1>
                <p class="wm-fi d2" style="font-size:18px;color:#8b8b9e;margin:0 0 8px;line-height:1.6;">
                    Parab\u00e9ns por dar o primeiro passo.
                </p>
                <p class="wm-fi d3" style="font-size:16px;color:#5a5a6e;line-height:1.6;margin:0 0 40px;">
                    Chegou a hora de conhecer o <strong style="color:#06b6d4;">Borges OS</strong> \u2014 a plataforma criada para
                    <strong style="color:#fff;">aumentar suas vendas</strong> e <strong style="color:#fff;">revolucionar sua gest\u00e3o comercial</strong> com intelig\u00eancia artificial.
                </p>
                <button class="wm-fi d4 wm-btn-primary" onclick="wmGoTo(2)" style="padding:16px 48px;font-size:16px;">
                    <i class="fa-solid fa-arrow-right" style="margin-right:8px;"></i> Vamos Configurar
                </button>
                <p class="wm-fi d5" style="font-size:11px;color:#3a3a4e;margin-top:20px;">Leva menos de 2 minutos \u26a1</p>
            </div>
        </div>

        <!-- SLIDE 2: WhatsApp (INLINE QR CODE) -->
        <div class="wm-slide" id="wm-slide-2">
            <div style="text-align:center;max-width:500px;z-index:10;">
                <div class="wm-fi wm-icon-box" style="background:#22c55e20;border:2px solid #22c55e40;">
                    <i class="fa-brands fa-whatsapp" style="font-size:32px;color:#22c55e;"></i>
                </div>
                <div class="wm-dots"><span class="wm-dot filled"></span><span class="wm-dot"></span><span class="wm-dot"></span></div>
                <h2 class="wm-fi d1" style="font-size:24px;font-weight:700;color:#fff;margin:0 0 8px;">Conecte seu WhatsApp</h2>
                <p class="wm-fi d2" style="font-size:14px;color:#5a5a6e;margin:0 0 24px;">
                    A IA do Borges OS vai atender seus leads pelo WhatsApp. Clique para gerar o QR Code e escaneie com seu celular.
                </p>

                <!-- QR Code Area (inline) -->
                <div class="wm-fi d2 wm-qr-area" id="wm-wpp-area" style="margin-bottom:20px;">
                    <button id="wm-btn-connect-wpp" onclick="wmConnectWhatsApp()"
                        style="padding:14px 32px;background:#22c55e;border:none;border-radius:12px;color:#fff;font-size:14px;font-weight:700;cursor:pointer;display:inline-flex;align-items:center;gap:8px;font-family:inherit;box-shadow:0 4px 15px rgba(34,197,94,0.3);transition:all 0.2s;">
                        <i class="fa-brands fa-whatsapp"></i> Gerar QR Code
                    </button>
                    <p id="wm-wpp-status" style="font-size:12px;color:#5a5a6e;margin-top:12px;"></p>
                </div>

                <div style="display:flex;gap:12px;justify-content:center;">
                    <button class="wm-btn-skip" onclick="wmGoTo(3)">Pular por agora \u2192</button>
                    <button class="wm-btn-primary" onclick="wmGoTo(3)" style="font-size:13px;padding:12px 28px;">Pr\u00f3ximo \u2192</button>
                </div>
            </div>
        </div>

        <!-- SLIDE 3: Instagram (INLINE) -->
        <div class="wm-slide" id="wm-slide-3">
            <div style="text-align:center;max-width:500px;z-index:10;">
                <div class="wm-fi wm-icon-box" style="background:linear-gradient(135deg,rgba(168,85,247,0.15),rgba(236,72,153,0.15));border:2px solid rgba(168,85,247,0.3);">
                    <i class="fa-brands fa-instagram" style="font-size:32px;color:#a855f7;"></i>
                </div>
                <div class="wm-dots"><span class="wm-dot filled"></span><span class="wm-dot filled"></span><span class="wm-dot"></span></div>
                <h2 class="wm-fi d1" style="font-size:24px;font-weight:700;color:#fff;margin:0 0 8px;">Conecte seu Instagram</h2>
                <p class="wm-fi d2" style="font-size:14px;color:#5a5a6e;margin:0 0 24px;">
                    Receba mensagens do Instagram Direct no Borges OS. A IA responde por l\u00e1 tamb\u00e9m!
                </p>

                <!-- Instagram Area (inline) -->
                <div class="wm-fi d2 wm-insta-area" id="wm-insta-area" style="margin-bottom:20px;">
                    <button id="wm-btn-connect-insta" onclick="wmConnectInstagram()"
                        style="padding:14px 32px;background:linear-gradient(135deg,#a855f7,#ec4899);border:none;border-radius:12px;color:#fff;font-size:14px;font-weight:700;cursor:pointer;display:inline-flex;align-items:center;gap:8px;font-family:inherit;box-shadow:0 4px 15px rgba(168,85,247,0.3);transition:all 0.2s;">
                        <i class="fa-brands fa-instagram"></i> Conectar Instagram
                    </button>
                    <p id="wm-insta-status" style="font-size:12px;color:#5a5a6e;margin-top:12px;"></p>
                </div>

                <div style="display:flex;gap:12px;justify-content:center;">
                    <button class="wm-btn-skip" onclick="wmGoTo(4)">Pular por agora \u2192</button>
                    <button class="wm-btn-primary" onclick="wmGoTo(4)" style="font-size:13px;padding:12px 28px;">Pr\u00f3ximo \u2192</button>
                </div>
            </div>
        </div>

        <!-- SLIDE 4: Invite Team -->
        <div class="wm-slide" id="wm-slide-4">
            <div style="text-align:center;max-width:480px;z-index:10;">
                <div class="wm-fi wm-icon-box" style="background:rgba(6,182,212,0.1);border:2px solid rgba(6,182,212,0.3);">
                    <i class="fa-solid fa-users" style="font-size:28px;color:#06b6d4;"></i>
                </div>
                <div class="wm-dots"><span class="wm-dot filled"></span><span class="wm-dot filled"></span><span class="wm-dot filled"></span></div>
                <h2 class="wm-fi d1" style="font-size:24px;font-weight:700;color:#fff;margin:0 0 8px;">Convide sua equipe</h2>
                <p class="wm-fi d2" style="font-size:14px;color:#5a5a6e;margin:0 0 32px;">
                    Adicione vendedores e gestores para trabalharem juntos no Borges OS.
                </p>
                <div class="wm-fi d2" style="background:#111118;border:1px solid #1e1e2e;border-radius:16px;padding:24px;text-align:left;margin-bottom:24px;">
                    <label style="display:block;font-size:11px;color:#5a5a6e;margin-bottom:8px;text-transform:uppercase;letter-spacing:0.5px;">Email do colaborador</label>
                    <div style="display:flex;gap:8px;">
                        <input type="email" id="wm-invite-email" placeholder="vendedor@empresa.com"
                            style="flex:1;height:44px;background:#0a0a0f;border:1px solid #1e1e2e;border-radius:10px;padding:0 14px;font-size:14px;color:#fff;outline:none;font-family:inherit;">
                        <button onclick="wmInviteUser()"
                            style="padding:0 20px;background:linear-gradient(135deg,#06b6d4,#0e7490);border:none;border-radius:10px;color:#fff;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit;white-space:nowrap;">
                            <i class="fa-solid fa-paper-plane"></i> Enviar
                        </button>
                    </div>
                    <p id="wm-invite-feedback" style="font-size:11px;color:#3a3a4e;margin:8px 0 0;">Voc\u00ea pode convidar mais pessoas depois em Configura\u00e7\u00f5es.</p>
                </div>
                <button class="wm-btn-primary" onclick="wmGoTo(5)">
                    <i class="fa-solid fa-arrow-right" style="margin-right:8px;"></i> Finalizar
                </button>
            </div>
        </div>

        <!-- SLIDE 5: Done! -->
        <div class="wm-slide" id="wm-slide-5">
            <div style="text-align:center;max-width:480px;z-index:10;">
                <div class="wm-fi" style="margin-bottom:24px;">
                    <div style="width:80px;height:80px;margin:0 auto;background:linear-gradient(135deg,#22c55e20,#15803d20);border:2px solid #22c55e40;border-radius:20px;display:flex;align-items:center;justify-content:center;animation:welcomePulseGlow 3s ease-in-out infinite;">
                        <i class="fa-solid fa-check" style="font-size:36px;color:#22c55e;"></i>
                    </div>
                </div>
                <h2 class="wm-fi d1" style="font-size:32px;font-weight:800;color:#fff;margin:0 0 12px;">Tudo pronto! \ud83d\ude80</h2>
                <p class="wm-fi d2" style="font-size:16px;color:#8b8b9e;margin:0 0 8px;">Seu Borges OS est\u00e1 configurado e pronto para operar.</p>
                <p class="wm-fi d3" style="font-size:14px;color:#5a5a6e;margin:0 0 40px;">A IA j\u00e1 est\u00e1 online e preparada para atender seus leads. Hora de vender! \ud83d\udcb0</p>
                <button class="wm-fi d4 wm-btn-primary" onclick="wmClose()" style="padding:16px 48px;font-size:16px;">
                    <i class="fa-solid fa-rocket" style="margin-right:8px;"></i> Entrar no Borges OS
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    // ===== HELPER: get tenant ID =====
    function getMyTenantId() {
        try {
            const user = JSON.parse(localStorage.getItem('borges_user'));
            return user?.tenant_id;
        } catch(e) { return null; }
    }

    // ===== GLOBAL: Slide Navigation =====
    window.wmGoTo = function(n) {
        document.querySelectorAll('.wm-slide').forEach(s => {
            if (s.classList.contains('active')) {
                s.style.animation = 'welcomeFadeOut 0.3s ease-in forwards';
                setTimeout(() => {
                    s.classList.remove('active');
                    s.style.animation = '';
                    const target = document.getElementById('wm-slide-' + n);
                    if (target) {
                        target.classList.add('active');
                        target.querySelectorAll('.wm-fi').forEach(el => {
                            el.style.animation = 'none';
                            el.offsetHeight;
                            el.style.animation = '';
                        });
                    }
                }, 300);
            }
        });
    };

    // ===== GLOBAL: Close Modal =====
    window.wmClose = async function() {
        // Clear any WhatsApp polling
        if (window._wmWppInterval) {
            clearInterval(window._wmWppInterval);
            window._wmWppInterval = null;
        }

        const m = document.getElementById('welcome-modal');
        m.style.transition = 'opacity 0.5s ease-out';
        m.style.opacity = '0';
        setTimeout(() => { m.style.display = 'none'; }, 500);

        try {
            await fetchWithAuth('/api/v1/auth/complete-onboarding', { method: 'PUT' });
            const u = JSON.parse(localStorage.getItem('borges_user'));
            if (u) { u.first_login = false; localStorage.setItem('borges_user', JSON.stringify(u)); }
        } catch (e) { console.error('Complete onboarding error:', e); }
    };

    // ===== GLOBAL: Init Modal =====
    window.initWelcomeModal = function(userName) {
        const nameEl = document.getElementById('wm-user-name');
        if (nameEl) nameEl.textContent = (userName || 'Parceiro').split(' ')[0];
        const m = document.getElementById('welcome-modal');
        m.style.display = 'block';
        m.style.opacity = '1';
    };

    // ===== WHATSAPP: Connect Inline ===== 
    window.wmConnectWhatsApp = async function() {
        const tid = getMyTenantId();
        if (!tid) { alert('Erro: tenant n\u00e3o identificado. Fa\u00e7a login novamente.'); return; }

        const area = document.getElementById('wm-wpp-area');
        const btn = document.getElementById('wm-btn-connect-wpp');
        const status = document.getElementById('wm-wpp-status');

        // Show loading
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Gerando...';
        status.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin" style="color:#22c55e;"></i> Conectando com a Evolution API...';
        status.style.color = '#22c55e';

        try {
            const res = await fetchWithAuth('/api/v1/super/whatsapp/connect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tenant_id: tid })
            });

            const data = await res.json();

            if (res.ok && data.qrcode) {
                // Show QR Code inline
                btn.style.display = 'none';
                area.innerHTML = `
                    <div style="background:#fff;padding:12px;border-radius:12px;display:inline-block;margin-bottom:12px;box-shadow:0 0 30px rgba(34,197,94,0.15);">
                        <img src="${data.qrcode}" style="width:200px;height:200px;display:block;" alt="QR Code WhatsApp">
                    </div>
                    <p style="font-size:13px;color:#22c55e;font-weight:600;">
                        <i class="fa-solid fa-qrcode" style="margin-right:4px;"></i>
                        Inst\u00e2ncia: <span style="color:#fff;">${data.instance || 'borges'}</span> \u2014 Escaneie com o WhatsApp
                    </p>
                    <p id="wm-wpp-poll-status" style="font-size:11px;color:#5a5a6e;margin-top:8px;">Aguardando leitura do QR Code...</p>
                `;

                // Start polling para detectar conex\u00e3o
                window._wmWppInterval = setInterval(async () => {
                    try {
                        const checkRes = await fetchWithAuth('/api/v1/ws/config/');
                        if (checkRes.ok) {
                            const cfg = await checkRes.json();
                            const num = cfg.whatsapp_number;
                            if (num && num !== 'Aguardando Conex\u00e3o' && num !== 'Pendente') {
                                clearInterval(window._wmWppInterval);
                                window._wmWppInterval = null;
                                area.innerHTML = `
                                    <div style="padding:20px;">
                                        <i class="fa-solid fa-check-circle" style="font-size:48px;color:#22c55e;margin-bottom:12px;"></i>
                                        <p style="font-size:18px;color:#fff;font-weight:700;">WhatsApp Conectado! \u2705</p>
                                        <p style="font-size:14px;color:#22c55e;margin-top:4px;">${num}</p>
                                    </div>
                                `;
                            }
                        }
                    } catch(e) { /* silent */ }
                }, 3000);

            } else if (res.ok && data.whatsapp_number) {
                // Already connected
                btn.style.display = 'none';
                area.innerHTML = `
                    <div style="padding:20px;">
                        <i class="fa-solid fa-check-circle" style="font-size:48px;color:#22c55e;margin-bottom:12px;"></i>
                        <p style="font-size:18px;color:#fff;font-weight:700;">WhatsApp j\u00e1 conectado! \u2705</p>
                        <p style="font-size:14px;color:#22c55e;margin-top:4px;">${data.whatsapp_number}</p>
                    </div>
                `;
            } else {
                // Error
                status.innerHTML = '<i class="fa-solid fa-triangle-exclamation" style="color:#ef4444;margin-right:4px;"></i> ' + (data.detail || 'Erro ao conectar. Tente novamente.');
                status.style.color = '#ef4444';
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-brands fa-whatsapp"></i> Tentar Novamente';
            }
        } catch (e) {
            status.innerHTML = '<i class="fa-solid fa-cloud-bolt" style="color:#ef4444;margin-right:4px;"></i> Falha de conex\u00e3o com a Evolution API.';
            status.style.color = '#ef4444';
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-brands fa-whatsapp"></i> Tentar Novamente';
        }
    };

    // ===== INSTAGRAM: Connect Inline =====
    window.wmConnectInstagram = async function() {
        const tid = getMyTenantId();
        if (!tid) { alert('Erro: tenant não identificado.'); return; }

        const btn = document.getElementById('wm-btn-connect-insta');
        const status = document.getElementById('wm-insta-status');
        const area = document.getElementById('wm-insta-area');

        try {
            const res = await fetchWithAuth('/api/v1/traffic/meta/login?type=insta');
            const data = await res.json();
            
            if (data.url) {
                const width = 600, height = 700;
                const left = (window.innerWidth / 2) - (width / 2);
                const top = (window.innerHeight / 2) - (height / 2);

                window.open(data.url, 'Conectar Instagram', `width=${width},height=${height},left=${left},top=${top}`);

                // Show waiting state
                btn.disabled = true;
                btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Aguardando Autorização...';
                status.innerHTML = 'A janela de conexão com o Instagram foi aberta. Siga os passos nela para autorizar.';
                status.style.color = '#a855f7';

                // Listen for the custom message from the popup
                const msgListener = (event) => {
                    if (event.data && event.data.type === 'META_AUTH_SUCCESS' && event.data.integration_type === 'insta') {
                        window.removeEventListener('message', msgListener);
                        area.innerHTML = `
                            <div style="padding:20px;">
                                <i class="fa-solid fa-check-circle" style="font-size:48px;color:#a855f7;margin-bottom:12px;"></i>
                                <p style="font-size:18px;color:#fff;font-weight:700;">Instagram Conectado! ✅</p>
                                <p style="font-size:13px;color:#a855f7;margin-top:4px;">Mensagens do Direct serão recebidas no Borges OS.</p>
                            </div>
                        `;
                    }
                };
                window.addEventListener('message', msgListener);
            }
        } catch (e) {
            alert("Erro ao iniciar login do Instagram.");
        }
    };

    // ===== INVITE USER =====
    window.wmInviteUser = async function() {
        const input = document.getElementById('wm-invite-email');
        const fb = document.getElementById('wm-invite-feedback');
        const email = input.value.trim();
        if (!email) { fb.textContent = 'Digite um email v\u00e1lido.'; fb.style.color = '#ef4444'; return; }

        fb.textContent = 'Enviando convite...';
        fb.style.color = '#06b6d4';
        try {
            const res = await fetchWithAuth('/api/v1/ws/users/invite', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, role: 'user' })
            });
            if (res.ok) {
                fb.textContent = '\u2713 Convite enviado para ' + email + '!';
                fb.style.color = '#22c55e';
                input.value = '';
            } else {
                const errData = await res.json().catch(() => ({}));
                fb.textContent = '\u2717 ' + (errData.detail || 'Erro ao enviar convite.');
                fb.style.color = '#ef4444';
            }
        } catch (e) {
            fb.textContent = '\u2717 Erro de conex\u00e3o. Verifique sua internet.';
            fb.style.color = '#ef4444';
        }
    };

})();
