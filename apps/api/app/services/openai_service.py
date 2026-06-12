from typing import Optional
from sqlmodel import Session, select
from ..models.api_key import ApiKey


def _mock_adaptation(activity: dict, profile: dict) -> dict:
    title = activity.get("title") or "Atividade"
    statement = activity.get("statement") or "Observe e responda."
    question = activity.get("question") or "Qual é a resposta?"
    expected = activity.get("expected_answer") or ""
    modalities = profile.get("preferred_modalities") or []
    difficulties = profile.get("main_difficulties") or []

    items = [w.strip() for w in expected.replace(".", ",").split(",") if w.strip()][:4]
    if not items:
        items = ["Item A", "Item B"]
    zones = ["Grupo 1", "Grupo 2"]

    difficulty_hint = f" Atenção às dificuldades: {', '.join(str(d) for d in difficulties)}." if difficulties else ""
    modality_hint = f" Use: {', '.join(str(m) for m in modalities)}." if modalities else ""

    return {
        "text_adaptations": [
            {"version": 1, "content": f"{statement} {question}{difficulty_hint}{modality_hint}"}
        ],
        "image_options": [
            {"id": "img_1", "description": f"Ilustração de {title}", "prompt": f"illustration of {title}, simple, colorful, educational"},
            {"id": "img_2", "description": "Pictograma AAC", "prompt": f"AAC pictogram for {title}, simple icon"},
        ],
        "audio_options": [
            {"id": "audio_1", "script": f"{statement} {question}", "voice_style": "pausado e claro"}
        ],
        "interaction_options": [
            {
                "type": "drag_and_drop",
                "instructions": question,
                "items": items,
                "zones": zones,
                "feedback_correct": "Muito bem!",
                "feedback_incorrect": "Tente novamente.",
            }
        ],
        "print_version": {
            "format": "A4",
            "layout": "single_column",
            "font_size": "large",
            "instructions": question,
            "answer_space": True,
        },
        "validation": {
            "clarity_score": 4,
            "accessibility_score": 4,
            "pedagogical_score": 4,
            "difficulty_score": 3,
            "approved": True,
            "notes": "Gerado por mock — configure uma chave OpenAI para adaptações com IA.",
        },
    }


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
    return key.encrypted_value


async def generate_adaptation_with_ai(openai_key: str, activity: dict, profile: dict) -> dict:
    """Call OpenAI to generate adaptation. Falls back to mock pipeline if key fails."""
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=openai_key)

        def _fmt(val) -> str:
            if val is None or val == "":
                return "não informado"
            if isinstance(val, list):
                return ", ".join(str(v) for v in val) if val else "não informado"
            return str(val)

        prompt = f"""Você é um especialista em educação especial e tecnologia assistiva.
Adapte a atividade abaixo para o perfil pedagógico do aluno descrito.

━━━━━━━━ ATIVIDADE ━━━━━━━━
Título: {_fmt(activity.get("title"))}
Disciplina: {_fmt(activity.get("discipline"))}
Ano escolar: {_fmt(activity.get("school_year"))}
Objetivo pedagógico: {_fmt(activity.get("pedagogical_objective"))}
Tipo: {_fmt(activity.get("activity_type"))}
Enunciado: {_fmt(activity.get("statement"))}
Pergunta: {_fmt(activity.get("question"))}
Resposta esperada: {_fmt(activity.get("expected_answer"))}
Observações do professor: {_fmt(activity.get("teacher_notes"))}

━━━━━━━━ PERFIL DO ALUNO ━━━━━━━━
Nome do perfil: {_fmt(profile.get("name"))}
Nível de leitura: {_fmt(profile.get("reading_level"))}  (initial=somente imagens/palavras, basic=frases simples, intermediate=texto curto, advanced=normal)
Nível de autonomia: {_fmt(profile.get("autonomy_level"))}  (low=muito suporte, medium=algum suporte, high=independente)
Dificuldades principais: {_fmt(profile.get("main_difficulties"))}
Estratégias recomendadas: {_fmt(profile.get("recommended_strategies"))}
Modalidades preferidas: {_fmt(profile.get("preferred_modalities"))}
Recursos a evitar: {_fmt(profile.get("resources_to_avoid"))}
Complexidade de acessibilidade: {_fmt(profile.get("accessibility_complexity"))}
Notas adicionais: {_fmt(profile.get("notes"))}

━━━━━━━━ INSTRUÇÕES CRÍTICAS ━━━━━━━━
1. interaction_options.items: extraia EXATAMENTE os conceitos/palavras-chave da "Resposta esperada". NUNCA use "Item 1", "Item 2" genéricos.
2. interaction_options.zones: extraia as CATEGORIAS da "Pergunta" (ex: "em Água ou Terra" → ["Água","Terra"]). NUNCA use "Grupo A", "Grupo B" genéricos.
3. interaction_options.instructions: use a "Pergunta" como instrução direta para o aluno.
4. text_adaptations.content: reescreva enunciado + pergunta com linguagem adaptada ao nível de leitura do aluno.
5. audio_options.voice_style: adapte ao nível de autonomia (low=pausado, medium=claro, high=direto).
6. Todos os textos devem ser em português brasileiro.

Responda APENAS com JSON válido neste formato exato:
{{
  "text_adaptations": [{{"version": 1, "content": "texto adaptado ao nível de leitura"}}],
  "image_options": [
    {{"id": "img_1", "description": "descrição da imagem", "prompt": "prompt em inglês para geração"}},
    {{"id": "img_2", "description": "pictograma AAC", "prompt": "AAC pictogram prompt"}}
  ],
  "audio_options": [{{"id": "audio_1", "script": "roteiro completo em português", "voice_style": "estilo de voz"}}],
  "interaction_options": [{{
    "type": "drag_and_drop",
    "instructions": "instrução direta baseada na pergunta",
    "items": ["item1", "item2", "item3"],
    "zones": ["categoria1", "categoria2"],
    "feedback_correct": "Muito bem!",
    "feedback_incorrect": "Tente novamente."
  }}],
  "print_version": {{
    "format": "A4",
    "layout": "single_column",
    "font_size": "large",
    "instructions": "instrução para impressão",
    "answer_space": true
  }},
  "validation": {{
    "clarity_score": 5,
    "accessibility_score": 5,
    "pedagogical_score": 5,
    "difficulty_score": 3,
    "approved": true,
    "notes": "justificativa"
  }}
}}"""

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        import json
        return json.loads(response.choices[0].message.content)
    except Exception:
        from ..agents.orchestrator import run_adaptation_pipeline
        return await run_adaptation_pipeline(activity, profile, openai_key=None)
