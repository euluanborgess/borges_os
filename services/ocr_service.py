import base64
import httpx
import json

async def extract_data_from_image(base64_image: str, openai_api_key: str):
    """
    Usa o GPT-4o Vision para extrair dados estruturados de uma imagem (comprovantes, docs).
    """
    if not openai_api_key:
        return {"error": "API Key missing"}

    prompt = """
    Analise esta imagem e extraia todas as informações estruturadas possíveis. 
    Se for um comprovante de pagamento, extraia: valor, data, favorecido e banco.
    Se for um documento de identidade, extraia: nome, cpf/rg e data de nascimento.
    Retorne APENAS um JSON puro.
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    }
                ]
            }
        ],
        "response_format": {"type": "json_object"}
    }

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=45.0)
            data = res.json()
            content = data['choices'][0]['message']['content']
            return json.loads(content)
    except Exception as e:
        print(f"[OCR Error] {e}")
        return None
