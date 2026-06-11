from typing import Optional
from sqlmodel import Session, select
from ..models.api_key import ApiKey


def get_user_openai_key(session: Session, user_id: str) -> Optional[str]:
    """Retrieve the teacher's OpenAI key. Returns None if not configured."""
    key = session.exec(
        select(ApiKey).where(
            ApiKey.user_id == user_id,
            ApiKey.provider == "openai",
            ApiKey.status == "active",
        )
    ).first()
    if not key:
        return None
    # NOTE: value is stored plain in MVP — decrypt here when encryption is added
    return key.encrypted_value


async def generate_adaptation_with_ai(openai_key: str, activity: dict, profile: dict) -> dict:
    """Call OpenAI to generate adaptation. Falls back to mock if key is invalid."""
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=openai_key)

        prompt = f"""
Você é um especialista em educação especial. Adapte a atividade abaixo para o perfil do aluno.

ATIVIDADE:
Título: {activity.get("title")}
Enunciado: {activity.get("statement")}
Pergunta: {activity.get("question")}
Resposta esperada: {activity.get("expected_answer")}
Tipo: {activity.get("activity_type")}

PERFIL DO ALUNO:
Nome do perfil: {profile.get("name")}
Dificuldades: {profile.get("main_difficulties")}
Estratégias recomendadas: {profile.get("recommended_strategies")}
Modalidades preferidas: {profile.get("preferred_modalities")}

Responda APENAS com JSON válido no seguinte formato:
{{
  "text_adaptations": [{{"version": 1, "content": "texto adaptado"}}],
  "image_options": [{{"id": "img_1", "description": "descrição", "prompt": "prompt para gerar imagem"}}],
  "audio_options": [{{"id": "audio_1", "script": "roteiro do áudio", "voice_style": "calmo e pausado"}}],
  "interaction_options": [{{"type": "drag_and_drop", "items": [], "zones": []}}],
  "validation": {{"clarity_score": 5, "accessibility_score": 5, "pedagogical_score": 5, "approved": true, "notes": ""}}
}}
"""
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        import json
        return json.loads(response.choices[0].message.content)
    except Exception:
        return _mock_adaptation(activity, profile)


def _mock_adaptation(activity: dict, profile: dict) -> dict:
    title = activity.get("title", "Atividade")
    return {
        "text_adaptations": [
            {
                "version": 1,
                "content": f"OBSERVE A ATIVIDADE.\n\n{activity.get('statement', '')}\n\n{activity.get('question', '')}",
            }
        ],
        "image_options": [
            {
                "id": "img_1",
                "description": f"Imagem ilustrativa para '{title}' com fundo neutro e elementos grandes",
                "prompt": f"Simple educational illustration for '{title}', minimal design, neutral background, large clear elements, child-friendly",
            },
            {
                "id": "img_2",
                "description": "Pictogramas de apoio visual para os elementos principais da atividade",
                "prompt": "Simple pictograms, AAC style, clear icons, white background, educational",
            },
        ],
        "audio_options": [
            {
                "id": "audio_1",
                "script": f"Preste atenção.\n\n{activity.get('statement', 'Observe a atividade.')}\n\nAgora responda.\n\n{activity.get('question', '')}",
                "voice_style": "calmo e pausado, com pausas entre as instruções",
            }
        ],
        "interaction_options": [
            {
                "type": "drag_and_drop",
                "items": activity.get("expected_answer", "").split(".")[0:4] if activity.get("expected_answer") else ["Item 1", "Item 2"],
                "zones": ["Grupo A", "Grupo B"],
                "instructions": "ARRASTE CADA ITEM PARA O LUGAR CERTO.",
            }
        ],
        "print_version": {
            "format": "A4",
            "layout": "single_column",
            "font_size": "large",
            "instructions": f"OBSERVE E RESPONDA.\n\n{activity.get('question', '')}",
            "answer_space": True,
        },
        "validation": {
            "clarity_score": 4,
            "accessibility_score": 4,
            "pedagogical_score": 5,
            "difficulty_score": 3,
            "approved": True,
            "notes": "Adaptação gerada com mock. Revise antes de publicar.",
            "generated_by": "mock",
        },
    }
