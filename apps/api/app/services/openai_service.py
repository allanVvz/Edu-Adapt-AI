from typing import Optional
from sqlmodel import Session, select
from ..models.api_key import ApiKey


def _detect_interaction_type(activity: dict) -> str:
    text = " ".join([
        (activity.get("question") or ""),
        (activity.get("activity_type") or ""),
        (activity.get("pedagogical_objective") or ""),
    ]).lower()
    if any(k in text for k in ["ordem", "ordenar", "sequência", "sequencia", "primeiro", "depois", "rotina", "passo", "etapa"]):
        return "sequencing"
    if any(k in text for k in ["qual é", "qual e", "quais são", "escolha", "marque", "assinale", "verdadeiro", "falso"]):
        return "multiple_choice"
    return "drag_and_drop"


def _mock_adaptation(activity: dict, profile: dict) -> dict:
    title = activity.get("title") or "Atividade"
    statement = activity.get("statement") or "Observe e responda."
    question = activity.get("question") or "Qual é a resposta?"
    expected = activity.get("expected_answer") or ""
    modalities = profile.get("preferred_modalities") or []
    difficulties = profile.get("main_difficulties") or []

    interaction_type = _detect_interaction_type(activity)

    raw_items = [w.strip() for w in expected.replace(".", ",").split(",") if 1 < len(w.strip()) < 40][:5]
    if not raw_items:
        raw_items = ["Opção A", "Opção B", "Opção C"]

    items = [
        {"name": name, "image_prompt": f"simple educational illustration of {name}, cartoon style"}
        for name in raw_items
    ]

    if interaction_type == "sequencing":
        zones = [{"name": f"{i+1}°"} for i in range(len(items))]
        correct_answer = {item["name"]: f"{i+1}°" for i, item in enumerate(items)}
        instructions = f"Coloque as etapas na ordem correta. {question}"
    elif interaction_type == "multiple_choice":
        items = [{"name": "Minha resposta", "image_prompt": ""}]
        zones = [{"name": r.strip()} for r in raw_items]
        correct_answer = {"correct_zone": zones[0]["name"]}
        instructions = question
    else:
        zones = [{"name": "Grupo 1"}, {"name": "Grupo 2"}]
        mid = len(items) // 2
        correct_answer = {item["name"]: zones[0]["name"] for item in items[:mid]}
        correct_answer.update({item["name"]: zones[1]["name"] for item in items[mid:]})
        instructions = f"Arraste cada item para o grupo correto. {question}"

    difficulty_hint = f" Atenção às dificuldades: {', '.join(str(d) for d in difficulties)}." if difficulties else ""
    modality_hint = f" Use: {', '.join(str(m) for m in modalities)}." if modalities else ""

    image_options = [
        {"id": "img_1", "description": f"Ilustração de {title}", "prompt": f"simple educational illustration of {title}, colorful, child-friendly"},
        {"id": "img_2", "description": "Pictograma AAC", "prompt": f"AAC pictogram for {title}, simple icon, high contrast"},
    ]

    return {
        "text_adaptations": [
            {"version": 1, "content": f"{statement} {question}{difficulty_hint}{modality_hint}"}
        ],
        "image_options": image_options,
        "audio_options": [
            {"id": "audio_1", "script": f"{statement} {question}", "voice_style": "pausado e claro"}
        ],
        "interaction_options": [
            {
                "type": interaction_type,
                "instructions": instructions,
                "items": items,
                "zones": zones,
                "correct_answer": correct_answer,
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
1. interaction_options[0].type: escolha o tipo correto:
   - "sequencing": quando a atividade pede ordenar/sequenciar/colocar em ordem (rotina, cronologia, passos)
   - "multiple_choice": quando há uma única resposta correta entre opções
   - "drag_and_drop": para classificação em categorias (ex: animais → água ou terra)

2. interaction_options[0].items: objetos {{"name": "texto do item", "image_prompt": "prompt em inglês para DALL-E"}}
   - Extraia os conceitos da "Resposta esperada". NUNCA use "Item 1" ou "item_1" genéricos.
   - Para "multiple_choice": items = [{{"name": "Minha resposta", "image_prompt": ""}}]

3. interaction_options[0].zones: objetos {{"name": "rótulo da zona"}}
   - Para "sequencing": zones = [{{"name": "1°"}}, {{"name": "2°"}}, ...] com N = número de itens
   - Para "drag_and_drop": extraia as categorias da "Pergunta". NUNCA use "Grupo A/B" genéricos.
   - Para "multiple_choice": cada zone é uma opção de resposta

4. interaction_options[0].instructions: instrução direta para o aluno (baseada na pergunta)

5. interaction_options[0].correct_answer: mapeamento correto item→zona
   - drag_and_drop/sequencing: {{"nome_item": "nome_zona", ...}}
   - multiple_choice: {{"correct_zone": "nome_da_zona_correta"}}

6. text_adaptations[0].content: reescreva enunciado + pergunta adaptados ao nível de leitura do aluno.

7. audio_options[0].voice_style: adapte ao nível de autonomia (low=pausado, medium=claro, high=direto).

8. Todos os textos em português brasileiro. Prompts de imagem em inglês.

Responda APENAS com JSON válido neste formato exato:
{{
  "text_adaptations": [{{"version": 1, "content": "texto adaptado ao nível de leitura"}}],
  "image_options": [
    {{"id": "img_1", "description": "descrição", "prompt": "DALL-E prompt em inglês"}},
    {{"id": "img_2", "description": "pictograma AAC", "prompt": "AAC pictogram prompt"}}
  ],
  "audio_options": [{{"id": "audio_1", "script": "roteiro completo em português", "voice_style": "estilo de voz"}}],
  "interaction_options": [{{
    "type": "drag_and_drop",
    "instructions": "instrução direta para o aluno",
    "items": [{{"name": "item1", "image_prompt": "prompt em inglês"}}, {{"name": "item2", "image_prompt": "prompt"}}],
    "zones": [{{"name": "Categoria A"}}, {{"name": "Categoria B"}}],
    "correct_answer": {{"item1": "Categoria A", "item2": "Categoria B"}},
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
