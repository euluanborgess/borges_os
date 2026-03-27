from services.llm_engine import _get_client
from core.config import settings
import json

class BorgesIA:
    async def generate_suggestion(self, history, lead_name):
        """
        Gera uma sugestão de resposta ultra-personalizada baseada no histórico e nome.
        """
        # Se o nome for apenas o username, tentamos limpar
        clean_name = lead_name.split(' ')[0] if lead_name else "lá"
        
        system_prompt = f"""
Você é o Chief Intelligence Officer do Borges OS. 
Sua missão é sugerir a PRÓXIMA mensagem ideal para o lead no Instagram.

LEAD ATUAL: {lead_name} (chame de {clean_name})

# CONTEXTO DA CONVERSA (Histórico):
{json.dumps(history, ensure_ascii=False)}

# REGRAS DE OURO:
1. Comece sempre de forma natural. Se for o início, use "{clean_name}, tudo bem?".
2. Analise a ÚLTIMA mensagem do lead no histórico acima. RESPONDA DIRETAMENTE ao que ele perguntou ou comentou.
3. Use um tom executivo, persuasivo, porém amigável (estilo consultor de elite).
4. Mantenha a resposta CURTA (máximo 2 ou 3 frases).
5. Se o lead demonstrou interesse, tente agendar uma breve conversa ou pedir o WhatsApp.
6. Nunca use frases genéricas como "Como posso ajudar?". Seja específico ao contexto!

Responda APENAS com o texto da sugestão, sem aspas extras no início/fim.
"""
        try:
            client = _get_client()
            response = await client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Gere a sugestão personalizada agora com base na última interação."}
                ],
                temperature=0.7
            )
            suggestion = response.choices[0].message.content.strip()
            # Limpar aspas se a IA insistir
            if suggestion.startswith('"') and suggestion.endswith('"'):
                suggestion = suggestion[1:-1]
            return suggestion
        except Exception as e:
            print(f"Error generating AI suggestion: {e}")
            return f"Olá {clean_name}! Como posso te ajudar com o Borges OS hoje?"

borges_ia = BorgesIA()
