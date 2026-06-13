from typing import Optional
from sqlmodel import Session, select
from ..models.api_key import ApiKey

# ─── Style registry ───────────────────────────────────────────────────────────

IMAGE_STYLES: dict[str, dict] = {
    "line_art": {
        "label": "Desenho P&B — traços simples",
        "suffix": "simple black and white line drawing, educational, minimal clean lines, no color, sketch style, high contrast",
        "model": "gpt-image-1",
        "size": "1024x1024",
    },
    "cartoon_2d": {
        "label": "Cartoon colorido — detalhes 2D",
        "suffix": "colorful 2D cartoon illustration, child-friendly, vibrant colors, simple shapes, cute small details, educational",
        "model": "gpt-image-1",
        "size": "1024x1024",
    },
}

# gpt-image-1 is the recommended model since April 2025; dall-e-2 was deprecated Nov 2024
VALID_IMAGE_MODELS = {"gpt-image-1", "dall-e-3"}


def _parse_image_error(error: str, api_key: str = "") -> str:
    """Return an actionable Portuguese hint for common OpenAI image generation errors."""
    e = error.lower()
    if "does not exist" in e or ("invalid_value" in e and "model" in e):
        if api_key.startswith("sk-proj-"):
            return (
                "Sua chave é do tipo sk-proj-... (Project Key). "
                "Project Keys têm restrições de modelo por projeto. "
                "Resolução: acesse platform.openai.com → seu projeto → "
                "Settings → Limits → habilite 'Images' ou 'gpt-image-1' nas permissões do projeto."
            )
        return (
            "Modelo de imagem não disponível para sua conta. "
            "Acesse platform.openai.com → Settings → Limits e verifique se sua conta tem acesso a modelos de imagem."
        )
    if "insufficient_quota" in e or ("quota" in e and "exceed" in e):
        return "Cota esgotada. Verifique seu saldo em platform.openai.com/usage e adicione créditos se necessário."
    if "invalid_api_key" in e or "incorrect api key" in e:
        return "Chave OpenAI inválida ou revogada. Gere uma nova chave em platform.openai.com/api-keys."
    if "billing" in e:
        return "Problema de cobrança. Adicione um método de pagamento em platform.openai.com/settings/billing."
    if "rate_limit" in e:
        return "Limite de requisições atingido. Aguarde alguns segundos e tente novamente."
    return error


def _make_prompts(subject: str) -> dict:
    return {style: f"{subject}, {cfg['suffix']}" for style, cfg in IMAGE_STYLES.items()}


def _make_generated_slots() -> dict:
    return {style: {"image_url": None, "generated_at": None} for style in IMAGE_STYLES}


# ─── Interaction type detection ───────────────────────────────────────────────

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


# ─── Mock adaptation ──────────────────────────────────────────────────────────

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
        {
            "name": name,
            "image_prompt": f"simple educational illustration of {name}, cartoon style",
            "prompts": _make_prompts(name),
            "generated": _make_generated_slots(),
            "active_style": "cartoon_2d",
            "image_url": None,
        }
        for name in raw_items
    ]

    if interaction_type == "sequencing":
        zones = [{"name": f"{i+1}°"} for i in range(len(items))]
        correct_answer = {item["name"]: f"{i+1}°" for i, item in enumerate(items)}
        instructions = f"Coloque as etapas na ordem correta. {question}"
    elif interaction_type == "multiple_choice":
        items = [{
            "name": "Minha resposta",
            "image_prompt": "",
            "prompts": _make_prompts("student answer card"),
            "generated": _make_generated_slots(),
            "active_style": "cartoon_2d",
            "image_url": None,
        }]
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

    img1_subject = f"educational illustration of {title}"
    img2_subject = f"AAC pictogram for {title}"

    image_options = [
        {
            "id": "img_1",
            "description": f"Ilustração de {title}",
            "base_subject": img1_subject,
            "prompts": _make_prompts(img1_subject),
            "generated": _make_generated_slots(),
            "active_style": "cartoon_2d",
            "is_active": True,
            "image_url": None,
        },
        {
            "id": "img_2",
            "description": "Pictograma AAC",
            "base_subject": img2_subject,
            "prompts": _make_prompts(img2_subject),
            "generated": _make_generated_slots(),
            "active_style": "cartoon_2d",
            "is_active": True,
            "image_url": None,
        },
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


# ─── API key helper ───────────────────────────────────────────────────────────

def get_user_openai_key(session: Session, user_id: str) -> Optional[str]:
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


# ─── OpenAI generation ────────────────────────────────────────────────────────

async def generate_adaptation_with_ai(openai_key: str, activity: dict, profile: dict) -> dict:
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=openai_key)

        def _fmt(val) -> str:
            if val is None or val == "":
                return "não informado"
            if isinstance(val, list):
                return ", ".join(str(v) for v in val) if val else "não informado"
            return str(val)

        styles_doc = "\n".join(
            f'   - "{k}": prompts no estilo {v["label"]}'
            for k, v in IMAGE_STYLES.items()
        )

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
Nível de leitura: {_fmt(profile.get("reading_level"))}
Nível de autonomia: {_fmt(profile.get("autonomy_level"))}
Dificuldades principais: {_fmt(profile.get("main_difficulties"))}
Estratégias recomendadas: {_fmt(profile.get("recommended_strategies"))}
Modalidades preferidas: {_fmt(profile.get("preferred_modalities"))}
Recursos a evitar: {_fmt(profile.get("resources_to_avoid"))}

━━━━━━━━ INSTRUÇÕES CRÍTICAS ━━━━━━━━
1. interaction_options[0].type:
   - "sequencing": ordenar/sequenciar/colocar em ordem (rotina, cronologia, passos)
   - "multiple_choice": resposta única entre opções
   - "drag_and_drop": classificação em categorias

2. interaction_options[0].items: objetos com:
   - "name": texto do item
   - "image_prompt": prompt curto em inglês (backward compat)
   - "prompts": {{"line_art": "...", "cartoon_2d": "..."}} — prompts em inglês por estilo
   - "generated": {{"line_art": {{"image_url": null}}, "cartoon_2d": {{"image_url": null}}}}
   - "active_style": "cartoon_2d"
   - "image_url": null
   Para "multiple_choice": items = [{{"name": "Minha resposta", ...}}]

3. interaction_options[0].zones: objetos {{"name": "rótulo"}}
   - "sequencing": [{{"name": "1°"}}, {{"name": "2°"}}, ...]
   - "drag_and_drop": categorias da pergunta
   - "multiple_choice": cada opção de resposta

4. interaction_options[0].instructions: instrução direta ao aluno

5. interaction_options[0].correct_answer:
   - drag_and_drop/sequencing: {{"nome_item": "nome_zona"}}
   - multiple_choice: {{"correct_zone": "nome_zona_correta"}}

6. image_options[]: cada item deve ter:
   - "id": "img_1", "img_2"
   - "description": descrição em português
   - "base_subject": assunto em inglês para geração de imagem
   - "prompts": {{"line_art": "...", "cartoon_2d": "..."}} em inglês, estilos:
{styles_doc}
   - "generated": {{"line_art": {{"image_url": null, "generated_at": null}}, "cartoon_2d": {{...}}}}
   - "active_style": "cartoon_2d"
   - "is_active": true
   - "image_url": null

7. Todos os textos em português brasileiro. Prompts de imagem em inglês.

Responda APENAS com JSON válido neste formato:
{{
  "text_adaptations": [{{"version": 1, "content": "texto adaptado"}}],
  "image_options": [
    {{
      "id": "img_1", "description": "Ilustração principal", "base_subject": "subject in english",
      "prompts": {{"line_art": "subject, simple black and white...", "cartoon_2d": "subject, colorful 2D cartoon..."}},
      "generated": {{"line_art": {{"image_url": null, "generated_at": null}}, "cartoon_2d": {{"image_url": null, "generated_at": null}}}},
      "active_style": "cartoon_2d", "is_active": true, "image_url": null
    }},
    {{
      "id": "img_2", "description": "Pictograma AAC", "base_subject": "AAC pictogram subject",
      "prompts": {{"line_art": "...", "cartoon_2d": "..."}},
      "generated": {{"line_art": {{"image_url": null, "generated_at": null}}, "cartoon_2d": {{"image_url": null, "generated_at": null}}}},
      "active_style": "cartoon_2d", "is_active": true, "image_url": null
    }}
  ],
  "audio_options": [{{"id": "audio_1", "script": "roteiro em português", "voice_style": "estilo"}}],
  "interaction_options": [{{
    "type": "drag_and_drop",
    "instructions": "instrução direta para o aluno",
    "items": [
      {{
        "name": "item1", "image_prompt": "item1 cartoon",
        "prompts": {{"line_art": "item1, simple black and white...", "cartoon_2d": "item1, colorful 2D..."}},
        "generated": {{"line_art": {{"image_url": null}}, "cartoon_2d": {{"image_url": null}}}},
        "active_style": "cartoon_2d", "image_url": null
      }}
    ],
    "zones": [{{"name": "Categoria A"}}, {{"name": "Categoria B"}}],
    "correct_answer": {{"item1": "Categoria A"}},
    "feedback_correct": "Muito bem!",
    "feedback_incorrect": "Tente novamente."
  }}],
  "print_version": {{
    "format": "A4", "layout": "single_column", "font_size": "large",
    "instructions": "instrução", "answer_space": true
  }},
  "validation": {{
    "clarity_score": 5, "accessibility_score": 5, "pedagogical_score": 5,
    "difficulty_score": 3, "approved": true, "notes": "justificativa"
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
