import base64 as _b64
import os as _os
import uuid as _uuid_mod
from typing import Optional
from sqlmodel import Session, select
from ..models.api_key import ApiKey
from .emoji_service import get_emoji_for_concept

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

# gpt-image-1 is the only supported model; dall-e-2 deprecated Nov 2024, dall-e-3 removed 2025
VALID_IMAGE_MODELS = {"gpt-image-1"}

_STATIC_DIR = "/app/static/images"
_AUDIO_DIR = "/app/static/audio"
_API_BASE_URL = _os.environ.get("API_BASE_URL", "http://localhost:8000")
TTS_MODEL = _os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")


def make_openai_client(openai_key: str):
    from openai import AsyncOpenAI
    verify_ssl = _os.environ.get("OPENAI_VERIFY_SSL", "true").lower() not in {"0", "false", "no"}
    if verify_ssl:
        return AsyncOpenAI(api_key=openai_key)

    import httpx
    return AsyncOpenAI(api_key=openai_key, http_client=httpx.AsyncClient(verify=False))


def _save_image(resp_data) -> str:
    """Extract image URL from OpenAI response.
    gpt-image-1 returns b64_json (saved to disk); dall-e-3 returns a direct URL.
    """
    if resp_data.url:
        return resp_data.url
    b64 = resp_data.b64_json
    if not b64:
        raise ValueError("OpenAI response has neither url nor b64_json")
    _os.makedirs(_STATIC_DIR, exist_ok=True)
    filename = f"{_uuid_mod.uuid4()}.png"
    with open(f"{_STATIC_DIR}/{filename}", "wb") as f:
        f.write(_b64.b64decode(b64))
    return f"{_API_BASE_URL}/static/images/{filename}"


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


def _get_profile_image_modifier(profile_name: str) -> str:
    """Return a prompt suffix that tailors image generation to a specific TEA profile.

    The modifier is appended to the base prompt before calling the image model.
    Saved as generated[style]["prompt_used"] in output_data so reviewers can inspect it.
    """
    name = profile_name.lower()

    if "não verbal" in name or "nao verbal" in name:
        # Minimal, single-symbol AAC pictogram style
        return (
            "AAC pictogram style, single symbol, thick black outline, pure white background, "
            "flat 2D shape, no text, no shadows, no gradients, no extra details, "
            "high contrast black and white, symbol communication board style"
        )

    if "hipersensibilidade" in name:
        # Muted, desaturated — reduces visual overload
        return (
            "muted desaturated color palette, soft pastel tones, white background, "
            "minimal details, clean simple composition, no bright colors, no red or yellow, "
            "low visual noise, calm gentle illustration"
        )

    if "apoio visual" in name or "leitura inicial" in name:
        # Friendly colorful cartoon but clean and educational
        return (
            "bright colorful friendly cartoon, clear distinct outlines, "
            "simple clean background, educational illustration style, "
            "child-friendly, readable labels if any"
        )

    # Default: no additional modifier
    return ""


def _make_prompts(subject: str) -> dict:
    return {style: f"{subject}, {cfg['suffix']}" for style, cfg in IMAGE_STYLES.items()}


def _make_generated_slots() -> dict:
    return {style: {"image_url": None, "generated_at": None} for style in IMAGE_STYLES}


def _build_image_option(img_id: str, description: str, base_subject: str) -> dict:
    """Build a single image_option dict, checking emoji availability first."""
    emoji = get_emoji_for_concept(description)
    option: dict = {
        "id": img_id,
        "description": description,
        "base_subject": base_subject,
        "prompts": _make_prompts(base_subject),
        "generated": _make_generated_slots(),
        "active_style": "cartoon_2d",
        "is_active": True,
        "image_url": None,
    }
    if emoji:
        option["illustration_type"] = "emoji"
        option["emoji"] = emoji
    else:
        option["illustration_type"] = "generated"
    return option


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

    image_options = [
        _build_image_option("img_1", f"Ilustração de {title}", f"educational illustration of {title}"),
        _build_image_option("img_2", "Pictograma AAC", f"AAC pictogram for {title}"),
    ]

    return {
        "text_adaptations": [
            {"version": 1, "content": f"{statement} {question}{difficulty_hint}{modality_hint}"}
        ],
        "image_options": image_options,
        "audio_options": [
            {
                "id": "audio_1",
                "script": f"{statement} {question}",
                "tts_script": f"{statement} {question}",
                "voice_style": "pausado e claro",
                "voice": "alloy",
                "rhythm": 1.0,
                "pitch": "normal",
                "audio_url": None,
            }
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


# ─── TTS (OpenAI Speech API) ──────────────────────────────────────────────────

def _parse_audio_error(error: str, api_key: str = "") -> str:
    e = error.lower()
    if "does not exist" in e or ("invalid_value" in e and "model" in e):
        if api_key.startswith("sk-proj-"):
            return (
                "Modelo de audio nao habilitado para esta Project Key. "
                "No painel da OpenAI, habilite o modelo gpt-4o-mini-tts no projeto ou use uma chave com acesso a Audio/Speech."
            )
        return "Modelo de audio nao disponivel para sua conta. Verifique acesso a Speech/TTS na OpenAI."
    if "insufficient_quota" in e or ("quota" in e and "exceed" in e):
        return "Cota OpenAI esgotada. Verifique saldo/uso no painel da OpenAI."
    if "invalid_api_key" in e or "incorrect api key" in e:
        return "Chave OpenAI invalida ou revogada."
    if "billing" in e:
        return "Problema de cobranca na conta OpenAI."
    if "rate_limit" in e:
        return "Limite de requisicoes atingido. Aguarde alguns segundos e tente novamente."
    return error

async def generate_audio_tts(
    openai_key: str,
    tts_script: str,
    voice: str = "alloy",
    speed: float = 1.0,
) -> str:
    """Call OpenAI Speech API, save MP3 to disk, return /static/audio/{uuid}.mp3 URL."""
    client = make_openai_client(openai_key)
    clean_speed = max(0.25, min(4.0, float(speed)))
    kwargs = {
        "model": TTS_MODEL,
        "voice": voice,
        "input": tts_script or ".",
        "speed": clean_speed,
        "response_format": "mp3",
    }
    if TTS_MODEL not in {"tts-1", "tts-1-hd"}:
        kwargs["instructions"] = (
            "Fale em portugues do Brasil, com diccao clara, tom acolhedor e ritmo adequado "
            "para estudante com TEA. Respeite pausas naturais e evite entonacao exagerada."
        )
    try:
        response = await client.audio.speech.create(**kwargs)
    except Exception as exc:
        raise RuntimeError(_parse_audio_error(str(exc), openai_key)) from exc
    _os.makedirs(_AUDIO_DIR, exist_ok=True)
    filename = f"{_uuid_mod.uuid4()}.mp3"
    path = f"{_AUDIO_DIR}/{filename}"
    with open(path, "wb") as f:
        f.write(response.content)
    return f"{_API_BASE_URL}/static/audio/{filename}"


# ─── Kernel-consistent generation (gpt-4o-mini) ──────────────────────────────

def _profile_to_tea_variant(profile: dict) -> dict:
    """Map a TEA profile to the instructional design attributes used in the kernel prompt."""
    name = (profile.get("name") or "").lower()

    if "não verbal" in name or "nao verbal" in name:
        return {
            "perfil": "Comunicador Simbólico",
            "nivel_linguagem": "símbolo+palavra",
            "densidade_texto": "pictograma",
            "apoio_visual": "símbolo único",
            "n_opcoes": "2 opções visíveis",
            "resposta_motora": "toque único",
            "carga_sensorial": "mínima",
            "tom_audio": "muito lento e grave",
            "reforco": "imediato",
            "voice": "onyx",
            "rhythm": 0.62,
            "marcadores": "[aguarda toque]",
        }

    if "hipersensibilidade" in name:
        return {
            "perfil": "Conector Visual",
            "nivel_linguagem": "concreta",
            "densidade_texto": "pictograma",
            "apoio_visual": "obrigatório",
            "n_opcoes": "2–3 com imagem",
            "resposta_motora": "arrastar e soltar",
            "carga_sensorial": "baixa",
            "tom_audio": "pausado",
            "reforco": "por etapa",
            "voice": "nova",
            "rhythm": 0.80,
            "marcadores": "[pausa]",
        }

    if "apoio visual" in name or "leitura inicial" in name:
        return {
            "perfil": "Explorador Verbal",
            "nivel_linguagem": "literal",
            "densidade_texto": "frases curtas",
            "apoio_visual": "obrigatório",
            "n_opcoes": "3–4 opções",
            "resposta_motora": "escrever ou selecionar",
            "carga_sensorial": "moderada",
            "tom_audio": "natural",
            "reforco": "final",
            "voice": "shimmer",
            "rhythm": 0.95,
            "marcadores": "",
        }

    # Padrão
    return {
        "perfil": "Padrão",
        "nivel_linguagem": "literal",
        "densidade_texto": "parágrafos",
        "apoio_visual": "opcional",
        "n_opcoes": "4 opções",
        "resposta_motora": "escrever",
        "carga_sensorial": "moderada",
        "tom_audio": "natural",
        "reforco": "final",
        "voice": "alloy",
        "rhythm": 1.0,
        "marcadores": "",
    }


async def generate_adaptation_with_ai(openai_key: str, activity: dict, profile: dict) -> dict:
    try:
        import json
        client = make_openai_client(openai_key)

        def _fmt(val) -> str:
            if val is None or val == "":
                return "não informado"
            if isinstance(val, list):
                return ", ".join(str(v) for v in val) if val else "não informado"
            return str(val)

        variant = _profile_to_tea_variant(profile)
        styles_doc = "\n".join(
            f'   - "{k}": prompts no estilo {v["label"]}'
            for k, v in IMAGE_STYLES.items()
        )

        prompt = f"""Você é designer instrucional para TEA. Gere UMA versão de atividade adaptada.

━━━━ ATIVIDADE ━━━━
Título: {_fmt(activity.get("title"))}
Disciplina: {_fmt(activity.get("discipline"))}
Ano escolar: {_fmt(activity.get("school_year"))}
Objetivo: {_fmt(activity.get("pedagogical_objective"))}
Enunciado: {_fmt(activity.get("statement"))}
Pergunta: {_fmt(activity.get("question"))}
Resposta esperada: {_fmt(activity.get("expected_answer"))}
Observações: {_fmt(activity.get("teacher_notes"))}

━━━━ PERFIL ATIVO: {variant["perfil"]} ━━━━
Nível linguagem: {variant["nivel_linguagem"]}
Densidade texto: {variant["densidade_texto"]}
Apoio visual: {variant["apoio_visual"]}
Nº opções: {variant["n_opcoes"]}
Resposta motora: {variant["resposta_motora"]}
Carga sensorial: {variant["carga_sensorial"]}
Tom áudio: {variant["tom_audio"]}
Reforço: {variant["reforco"]}
Marcadores de narração: {variant["marcadores"] or "nenhum"}

━━━━ REGRAS DE OURO ━━━━
1. NUNCA use ironia, metáfora ambígua, voz passiva longa nem comando duplo.
2. Enunciado começa com verbo de comando (Leia / Toque / Arraste / Ordene…).
3. KERNEL CONSISTENCY: use o mesmo cenário, objetos e vocabulário da atividade original.
4. Distratores em múltipla escolha = confusões conceituais reais (não absurdos).
5. Arrastar-e-soltar: toda peça pertence a um alvo visível (id + "aceita").
6. Toque único: 2 opções grandes; erro nunca é punido; reforço imediato.
7. audio_options[0].script deve incluir os marcadores {variant["marcadores"] or "nenhum"} conforme o perfil.
8. Todos os textos em português. Prompts de imagem em inglês.

INSTRUÇÕES DE ESTRUTURA:
- interaction_options[0].type: "multiple_choice" | "drag_and_drop" | "sequencing"
- items: lista de objetos com id, name, image_prompt (inglês), prompts (line_art+cartoon_2d), generated, active_style="cartoon_2d", image_url=null
- zones: lista de objetos com id, name
- correct_answer: {{item_name: zone_name}} ou {{"correct_zone": zone_name}} para MC
- image_options: 2 itens com id, description, base_subject (inglês), prompts, generated, active_style, is_active, image_url
{styles_doc}

Responda SOMENTE com JSON válido:
{{
  "text_adaptations": [{{"version": 1, "content": "texto adaptado"}}],
  "image_options": [
    {{
      "id": "img_1", "description": "Ilustração principal", "base_subject": "subject in english",
      "prompts": {{"line_art": "...", "cartoon_2d": "..."}},
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
  "audio_options": [{{
    "id": "audio_1",
    "script": "roteiro com marcadores {variant["marcadores"] or 'nenhum'}",
    "tts_script": "roteiro sem marcadores para TTS",
    "voice_style": "{variant["tom_audio"]}",
    "voice": "{variant["voice"]}",
    "rhythm": {variant["rhythm"]},
    "pitch": "normal",
    "audio_url": null
  }}],
  "interaction_options": [{{
    "type": "drag_and_drop",
    "instructions": "instrução direta para o aluno",
    "items": [
      {{
        "name": "item1", "image_prompt": "item1 cartoon",
        "prompts": {{"line_art": "...", "cartoon_2d": "..."}},
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
        result = json.loads(response.choices[0].message.content)

        # Post-process: add emoji illustration_type to image_options returned by AI
        for img in result.get("image_options", []):
            if "illustration_type" not in img:
                emoji = get_emoji_for_concept(img.get("description", ""))
                img["illustration_type"] = "emoji" if emoji else "generated"
                if emoji:
                    img["emoji"] = emoji

        return result
    except Exception:
        from ..agents.orchestrator import run_adaptation_pipeline
        result = await run_adaptation_pipeline(activity, profile, openai_key=None)
        result["_fallback"] = True
        return result
