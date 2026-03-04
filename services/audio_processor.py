import os
import base64
import tempfile
import httpx
from openai import AsyncOpenAI
from core.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def download_media_from_evolution(instance_name: str, message_id: str) -> str:
    """
    Caso o webhook não traga o base64 nativamente, nós buscamos a mídia diretamente pelo ID.
    O endpoint da Evolution V2 para isso é POST /chat/getBase64FromMediaMessage/{instance}
    """
    url = f"{settings.EVOLUTION_API_URL}/chat/getBase64FromMediaMessage/{instance_name}"
    headers = {
        "apikey": settings.EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "message": {
            "key": {
                "id": message_id
            }
        }
    }
    
    async with httpx.AsyncClient() as http_client:
        response = await http_client.post(url, json=payload, headers=headers, timeout=30.0)
        if response.status_code == 200:
            data = response.json()
            return data.get("base64", "")
        return ""

async def transcribe_audio_base64(base64_data: str) -> str:
    """
    Converte o base64 OGG/PTT do WhatsApp em um arquivo temporário e envia para o modelo Whisper da OpenAI.
    """
    if not base64_data:
        return ""
        
    # Limpar a string base64 se ela vier com prefixo do tipo data:audio/ogg;base64,
    if "," in base64_data:
        base64_data = base64_data.split(",")[1]
        
    try:
        audio_bytes = base64.b64decode(base64_data)
        
        # O PTT do WhatsApp geralmente usa codec Opus (extensão ogg)
        # O Whisper OGG diretamente nativamente sem precisar de conversão manual na grande maioria das vezes.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name
            
        # Enviar para a OpenAI
        with open(tmp_file_path, "rb") as audio_file:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                response_format="text"
            )
            
        # Remover o arquivo temporário
        os.remove(tmp_file_path)
        
        return str(transcript).strip()
    except Exception as e:
        print(f"[Whisper Error] Falha na transcrição: {e}")
        return ""
