"""
Serviço unificado de processamento de mídias recebidas via WhatsApp.
Suporta: Áudio (Whisper), Imagens (GPT-4o Vision), Documentos/PDF (GPT-4o).
"""
import os
import base64
import tempfile
import httpx
from openai import AsyncOpenAI
from core.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


# ─────────────────── DOWNLOAD DE MÍDIA DA EVOLUTION API ───────────────────

async def download_media_from_evolution(instance_name: str, message_id: str, evolution_url: str | None = None, evolution_api_key: str | None = None, remote_jid: str | None = None) -> str:
    """Baixa a mídia (base64) pela Evolution API usando o ID da mensagem.

    Observação: alguns tenants podem ter URL/chave específicas; por isso aceitamos overrides.
    """
    base_url = (evolution_url or settings.EVOLUTION_API_URL).strip().rstrip('/')
    api_key = (evolution_api_key or settings.EVOLUTION_API_KEY).strip()

    url = f"{base_url}/chat/getBase64FromMediaMessage/{instance_name}"
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json"
    }
    key = {"id": message_id}
    if remote_jid:
        key["remoteJid"] = remote_jid

    payload = {"message": {"key": key}}
    
    async with httpx.AsyncClient() as http_client:
        response = await http_client.post(url, json=payload, headers=headers, timeout=30.0)
        if response.status_code == 200:
            data = response.json()
            return data.get("base64", "")
        else:
            print(f"[MediaProcessor] Download falhou: {response.status_code} - {response.text[:200]}")
        return ""


# ─────────────────── ÁUDIO → TRANSCRIÇÃO (WHISPER) ───────────────────

async def transcribe_audio_base64(base64_data: str) -> str:
    """
    Converte base64 OGG/PTT do WhatsApp em texto usando Whisper.
    """
    if not base64_data:
        return ""
        
    if "," in base64_data:
        base64_data = base64_data.split(",")[1]
        
    try:
        audio_bytes = base64.b64decode(base64_data)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name
            
        with open(tmp_file_path, "rb") as audio_file:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                response_format="text"
            )
            
        os.remove(tmp_file_path)
        return str(transcript).strip()
    except Exception as e:
        print(f"[Whisper Error] Falha na transcrição: {e}")
        return ""


# ─────────────────── IMAGEM → DESCRIÇÃO (GPT-4o VISION) ───────────────────

async def describe_image_base64(base64_data: str, context: str = "") -> str:
    """
    Usa GPT-4o Vision para descrever/interpretar uma imagem recebida.
    O contexto pode incluir instruções como o system prompt do tenant.
    """
    if not base64_data:
        return ""
    
    if "," in base64_data:
        base64_data = base64_data.split(",")[1]
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": context or "Você é um assistente que analisa imagens enviadas por clientes via WhatsApp. Descreva o conteúdo de forma clara e objetiva em português. Se houver texto na imagem, transcreva-o."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_data}",
                                "detail": "auto"
                            }
                        },
                        {
                            "type": "text",
                            "text": "Analise esta imagem enviada pelo cliente."
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Vision Error] Falha ao descrever imagem: {e}")
        return "[Imagem recebida - não foi possível analisar]"


# ─────────────────── DOCUMENTO/PDF → EXTRAÇÃO DE TEXTO ───────────────────

async def extract_document_text(base64_data: str, filename: str = "", mimetype: str = "") -> str:
    """
    Usa GPT-4o para extrair/resumir o conteúdo de um documento.
    Para PDFs, envia como imagem das páginas; para texto, decodifica diretamente.
    """
    if not base64_data:
        return ""
    
    if "," in base64_data:
        base64_data = base64_data.split(",")[1]
    
    try:
        # Para arquivos de texto simples, decodificar diretamente
        if mimetype and ("text" in mimetype or mimetype.endswith("csv")):
            text_content = base64.b64decode(base64_data).decode("utf-8", errors="ignore")
            return f"[Documento: {filename}]\n{text_content[:3000]}"
        
        # Para PDFs e outros: usar GPT-4o Vision tratando como documento
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Você é um assistente que analisa documentos enviados por clientes via WhatsApp. Extraia e resuma o conteúdo principal do documento em português."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{base64_data}",
                                "detail": "auto"
                            }
                        },
                        {
                            "type": "text",
                            "text": f"Analise este documento ({filename or 'sem nome'}). Extraia o texto e as informações principais."
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[DocExtract Error] Falha ao processar documento: {e}")
        return f"[Documento recebido: {filename or 'arquivo'}]"
