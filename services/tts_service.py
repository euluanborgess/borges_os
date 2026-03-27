import httpx
import base64
import os

async def text_to_speech_evolution(text: str, instance_id: str, remote_jid: str, evolution_url: str, evolution_api_key: str, openai_api_key: str):
    """
    Gera áudio via OpenAI e envia pelo WhatsApp via Evolution.
    """
    if not openai_api_key: return False

    # 1. Gerar áudio (OpenAI TTS) - FORMATO OPUS É MANDATÓRIO PARA PTT REAL
    headers = {"Authorization": f"Bearer {openai_api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "tts-1", 
        "voice": "alloy", 
        "input": text,
        "response_format": "opus" # [EXPERT FIX] - WhatsApp nativo usa Opus
    }
    
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post("https://api.openai.com/v1/audio/speech", headers=headers, json=payload, timeout=30.0)
            if res.status_code != 200: return False
            audio_bytes = res.content
            
        # 2. Enviar via Evolution (Base64)
        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        
        # Correção para enviar com @s.whatsapp.net se não tiver
        clean_jid = remote_jid
        if "@" not in clean_jid:
            clean_jid = f"{clean_jid}@s.whatsapp.net"

        evt_url = f"{evolution_url.strip().rstrip('/')}/message/sendMedia/{instance_id}"
        evt_payload = {
            "number": clean_jid,
            "mediatype": "audio",
            "mimetype": "audio/ogg; codecs=opus", # [EXPERT FIX] - Mimetype correto para PTT
            "media": b64_audio,
            "fileName": "audio_resposta.opus",
            "ptt": True 
        }
        
        print(f"[TTS DEBUG] Enviando para: {clean_jid} via {evt_url}")
        async with httpx.AsyncClient() as client:
            res = await client.post(evt_url, json=evt_payload, headers={"apikey": evolution_api_key}, timeout=30.0)
            print(f"[TTS DEBUG] Resposta Evolution: {res.status_code} - {res.text}")
            return res.status_code in [200, 201]
    except Exception as e:
        print(f"[TTS Error] {e}")
        return False
