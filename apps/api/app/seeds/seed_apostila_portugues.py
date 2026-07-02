"""
Seed: Apostila de Português — 14 atividades × 4 versões = 56 adaptações.

Fonte: apostila_portugues_transcricao_completa.md (36 páginas)
Tópicos: conto, pontuação, sinônimos/antônimos, carta, ortografia R/RR,
         texto instrucional, ortografia S/SS, substantivos, adjetivos, verbos, anedota.

Segue o mesmo padrão de seed_tea_activities.py (VERSION_PROFILE_NAMES, _build_output_data, etc.)
Idempotente — verifica (title, teacher_id) antes de inserir.
"""
import re
import uuid
from sqlmodel import Session, select

from ..database import engine
from ..models.user import User
from ..models.story import Story
from ..models.activity import Activity
from ..models.adaptation import ActivityAdaptation
from ..models.student_profile import StudentProfile
from ..services.openai_service import _make_prompts, _make_generated_slots
from ..services.emoji_service import get_emoji_for_concept


VERSION_PROFILE_NAMES = {
    "padrao": None,
    "p1": "TEA — Apoio Visual e Leitura Inicial",
    "p2": "TEA — Hipersensibilidade Visual",
    "p3": "TEA — Não Verbal",
}

VERSION_AUDIO_CONFIG = {
    "padrao": {"voice": "alloy",   "rhythm": 1.00, "pitch": "normal"},
    "p1":     {"voice": "shimmer", "rhythm": 0.95, "pitch": "normal"},
    "p2":     {"voice": "nova",    "rhythm": 0.80, "pitch": "normal"},
    "p3":     {"voice": "onyx",    "rhythm": 0.62, "pitch": "grave"},
}

FMT_TO_INTERACTION_TYPE = {
    "diss":  None,
    "mc":    "multiple_choice",
    "dnd":   "drag_and_drop",
    "seq":   "sequencing",
    "toque": "multiple_choice",
    "par":   "drag_and_drop",
}


RAVI_NINA_STORY_TITLE = "O Coelho e a Chuva"
RAVI_NINA_STORY_CONTENT = """Ravi era um coelho curioso. Um dia, ele acordou e viu o céu escuro.
De repente, começou a chover forte. Ravi correu até uma árvore para se proteger.
Lá, ele encontrou Nina, uma tartaruga calma.
— Não tenha medo, a chuva vai passar — disse Nina.
Ravi respirou fundo. Os dois esperaram juntos.
Quando a chuva parou, Ravi e Nina viraram amigos."""
RAVI_NINA_ACTIVITY_CODES = {"AT-PORT-06", "AT-PORT-07"}
CARTA_CARLOS_STORY_TITLE = "Carta de Carlos para Ana"
CARTA_CARLOS_STORY_CONTENT = """São Paulo, 10 de março.
Querida Ana,
Estou com saudade. Plantei flores no jardim e lembrei de você.
Com carinho,
Carlos."""
CARTA_CARLOS_ACTIVITY_CODES = {"AT-PORT-12"}
ANEDOTA_DETETIVE_STORY_TITLE = "A anedota do detetive"
ANEDOTA_DETETIVE_STORY_CONTENT = """Um detetive procurou seu guarda-chuva por toda a sala.
Ele olhou embaixo da mesa, atrás da porta e dentro do armário.
No fim, descobriu que estava segurando o guarda-chuva o tempo todo."""
ANEDOTA_DETETIVE_ACTIVITY_CODES = {"AT-PORT-19"}


def _build_ravi_nina_story_media() -> tuple[list[dict], list[dict]]:
    image_options = [
        {"id": "story_img_1", "description": "Ravi, coelho", "illustration_type": "emoji", "active_style": "pictogram", "is_active": True, "image_url": None, "emoji": "🐰"},
        {"id": "story_img_2", "description": "Nina, tartaruga", "illustration_type": "emoji", "active_style": "pictogram", "is_active": True, "image_url": None, "emoji": "🐢"},
        {"id": "story_img_3", "description": "chuva forte", "illustration_type": "emoji", "active_style": "pictogram", "is_active": True, "image_url": None, "emoji": "🌧️"},
        {"id": "story_img_4", "description": "árvore", "illustration_type": "emoji", "active_style": "pictogram", "is_active": True, "image_url": None, "emoji": "🌳"},
    ]
    audio_options = [{
        "id": "story_audio_1",
        "script": RAVI_NINA_STORY_CONTENT,
        "tts_script": re.sub(r" {2,}", " ", RAVI_NINA_STORY_CONTENT.replace("\n", " ")).strip(),
        "voice_style": "calma",
        "voice": "shimmer",
        "rhythm": 0.85,
        "pitch": "normal",
        "audio_url": None,
        "source": "seed",
    }]
    return image_options, audio_options


def _seed_ravi_nina_story(session: Session, teacher: User) -> Story:
    image_options, audio_options = _build_ravi_nina_story_media()
    story = session.exec(
        select(Story).where(
            Story.teacher_id == teacher.id,
            Story.title == RAVI_NINA_STORY_TITLE,
        )
    ).first()
    if story:
        story.content = RAVI_NINA_STORY_CONTENT
        story.image_options = image_options
        story.audio_options = audio_options
        story.status = "active"
        session.add(story)
        session.flush()
        return story

    story = Story(
        id=str(uuid.uuid4()),
        teacher_id=teacher.id,
        title=RAVI_NINA_STORY_TITLE,
        content=RAVI_NINA_STORY_CONTENT,
        image_options=image_options,
        audio_options=audio_options,
        status="active",
    )
    session.add(story)
    session.flush()
    return story


def _seed_context_story(
    session: Session,
    teacher: User,
    title: str,
    content: str,
    image_options: list[dict],
    audio_id: str,
) -> Story:
    audio_options = [{
        "id": audio_id,
        "script": content,
        "tts_script": re.sub(r" {2,}", " ", content.replace("\n", " ")).strip(),
        "voice_style": "calma",
        "voice": "shimmer",
        "rhythm": 0.85,
        "pitch": "normal",
        "audio_url": None,
        "source": "seed",
    }]
    story = session.exec(
        select(Story).where(
            Story.teacher_id == teacher.id,
            Story.title == title,
        )
    ).first()
    if story:
        existing_audio = story.audio_options or []
        if existing_audio and existing_audio[0].get("audio_url"):
            audio_options[0]["audio_url"] = existing_audio[0]["audio_url"]
        story.content = content
        story.image_options = image_options
        story.audio_options = audio_options
        story.status = "active"
        session.add(story)
        session.flush()
        return story

    story = Story(
        id=str(uuid.uuid4()),
        teacher_id=teacher.id,
        title=title,
        content=content,
        image_options=image_options,
        audio_options=audio_options,
        status="active",
    )
    session.add(story)
    session.flush()
    return story


def _seed_carta_carlos_story(session: Session, teacher: User) -> Story:
    return _seed_context_story(
        session,
        teacher,
        CARTA_CARLOS_STORY_TITLE,
        CARTA_CARLOS_STORY_CONTENT,
        [
            {"id": "carta_story_img_1", "description": "carta", "illustration_type": "emoji", "active_style": "pictogram", "is_active": True, "image_url": None, "emoji": "✉️"},
            {"id": "carta_story_img_2", "description": "Carlos escreve", "illustration_type": "emoji", "active_style": "pictogram", "is_active": True, "image_url": None, "emoji": "✍️"},
            {"id": "carta_story_img_3", "description": "Ana recebe", "illustration_type": "emoji", "active_style": "pictogram", "is_active": True, "image_url": None, "emoji": "📬"},
        ],
        "carta_story_audio_1",
    )


def _seed_anedota_detetive_story(session: Session, teacher: User) -> Story:
    return _seed_context_story(
        session,
        teacher,
        ANEDOTA_DETETIVE_STORY_TITLE,
        ANEDOTA_DETETIVE_STORY_CONTENT,
        [
            {"id": "anedota_story_img_1", "description": "detetive", "illustration_type": "emoji", "active_style": "pictogram", "is_active": True, "image_url": None, "emoji": "🕵️"},
            {"id": "anedota_story_img_2", "description": "guarda-chuva", "illustration_type": "emoji", "active_style": "pictogram", "is_active": True, "image_url": None, "emoji": "☂️"},
            {"id": "anedota_story_img_3", "description": "humor", "illustration_type": "emoji", "active_style": "pictogram", "is_active": True, "image_url": None, "emoji": "😄"},
        ],
        "anedota_story_audio_1",
    )


def _build_narration(enun: str, dados: dict, fmt: str, version_key: str) -> str:
    """Generate natural TTS narration from structured activity data."""
    def _name(z):
        if isinstance(z, str): return z
        if isinstance(z, dict): return z.get("name", "")
        return str(z)

    zone_names = [_name(z) for z in dados.get("zones", [])]
    item_names = [_name(i) for i in dados.get("items", []) if _name(i) != "Minha resposta"]

    if fmt in ("mc", "toque"):
        opts = zone_names
        if version_key == "p3":
            opts_simple = " ou ".join(opts[:2]) if len(opts) >= 2 else (opts[0] if opts else "")
            return f"{enun} {opts_simple}. [aguarda toque]"
        elif version_key == "p2":
            return enun + "".join(f" [pausa] {o}." for o in opts)
        elif version_key == "p1":
            return f"{enun} Escolha: {'. '.join(opts)}."
        else:
            return f"{enun} As opções são: {'. '.join(opts)}."

    elif fmt in ("dnd", "par"):
        all_items = item_names if item_names else zone_names
        if version_key == "p3":
            return f"{enun} [aguarda toque]"
        elif version_key == "p2":
            return enun + "".join(f" [pausa] {i}." for i in all_items)
        elif version_key == "p1":
            return f"{enun} Os itens são: {'. '.join(all_items)}."
        else:
            return f"{enun} Organize os itens: {'. '.join(all_items)}."

    elif fmt == "seq":
        if version_key == "p3":
            return f"{enun} [aguarda toque]"
        elif version_key == "p2":
            return enun + "".join(f" [pausa] {i}." for i in item_names)
        elif version_key == "p1":
            return f"{enun} Coloque em ordem: {'. '.join(item_names)}."
        else:
            return f"{enun} Numere em ordem: {'. '.join(item_names)}."

    else:  # diss
        return enun


def _build_output_data(versao: dict, version_key: str) -> dict:
    fmt = versao.get("fmt", "mc")
    enun = versao.get("enun", "Observe e responda.")
    dados = versao.get("dados", {})
    contexto = versao.get("contexto", "")
    apoios = versao.get("apoios", [])
    audio_cfg = VERSION_AUDIO_CONFIG[version_key]

    interaction_type = FMT_TO_INTERACTION_TYPE.get(fmt)
    interaction_options = []

    if interaction_type:
        items_raw = dados.get("items", [])
        zones_raw = dados.get("zones", [])
        correct = dados.get("correct_answer", {})

        items = []
        for raw in items_raw:
            name = raw if isinstance(raw, str) else raw.get("name", str(raw)) if isinstance(raw, dict) else str(raw)
            items.append({
                "name": name,
                "image_prompt": f"simple educational illustration of {name}",
                "prompts": _make_prompts(name),
                "generated": _make_generated_slots(),
                "active_style": "cartoon_2d",
                "image_url": None,
            })

        zones = []
        for raw in zones_raw:
            if isinstance(raw, str):
                zones.append({"name": raw})
            elif isinstance(raw, dict):
                zones.append(raw)
            else:
                zones.append({"name": str(raw)})

        if fmt == "seq" and not zones and items:
            zones = [{"name": f"{i+1}°"} for i in range(len(items))]
            if not correct:
                correct = {item["name"]: f"{i+1}°" for i, item in enumerate(items)}

        interaction_options.append({
            "type": interaction_type,
            "instructions": dados.get("instructions", enun),
            "items": items,
            "zones": zones,
            "correct_answer": correct,
            "feedback_correct": dados.get("feedback_correct", "Muito bem!"),
            "feedback_incorrect": dados.get("feedback_incorrect", "Tente novamente."),
        })

    image_options = []
    for i, apoio in enumerate(apoios[:2]):
        if isinstance(apoio, str):
            description = apoio
            base_subject = apoio
        elif isinstance(apoio, dict):
            description = apoio.get("description", apoio.get("name", ""))
            base_subject = apoio.get("base_subject", description)
        else:
            description = str(apoio)
            base_subject = description

        image_options.append({
            "id": f"img_{i+1}",
            "description": description,
            "base_subject": base_subject,
            "prompts": _make_prompts(base_subject),
            "generated": _make_generated_slots(),
            "active_style": "cartoon_2d",
            "is_active": True,
            "image_url": None,
            "illustration_type": "generated",
        })

    if not image_options:
        image_options = [{
            "id": "img_1",
            "description": "Ilustração da atividade",
            "base_subject": "educational illustration",
            "prompts": _make_prompts("educational illustration"),
            "generated": _make_generated_slots(),
            "active_style": "cartoon_2d",
            "is_active": True,
            "image_url": None,
            "illustration_type": "generated",
        }]

    for img in image_options:
        emoji = get_emoji_for_concept(img.get("description", ""))
        if emoji:
            img["illustration_type"] = "emoji"
            img["emoji"] = emoji

    narration = _build_narration(enun, dados, fmt, version_key)
    if contexto:
        full_script = f"{contexto} {narration}"
        display_text = f"{contexto}\n\n{enun}"
    else:
        full_script = narration
        display_text = enun

    tts_script = re.sub(r'\[(?:pausa|repete|aguarda toque)\]', ' ', full_script, flags=re.IGNORECASE)
    tts_script = re.sub(r' {2,}', ' ', tts_script).strip()

    return {
        "text_adaptations": [{"version": 1, "content": display_text}],
        "image_options": image_options,
        "audio_options": [{
            "id": "audio_1",
            "script": full_script,
            "tts_script": tts_script,
            "voice_style": audio_cfg["pitch"],
            "voice": audio_cfg["voice"],
            "rhythm": audio_cfg["rhythm"],
            "pitch": audio_cfg["pitch"],
            "audio_url": None,
            "source": "seed",
        }],
        "interaction_options": interaction_options,
        "print_version": {
            "format": "A4",
            "layout": "single_column",
            "font_size": "large",
            "instructions": enun,
            "answer_space": fmt == "diss",
        },
        "validation": {
            "clarity_score": 5,
            "accessibility_score": 5,
            "pedagogical_score": 5,
            "difficulty_score": 3,
            "approved": True,
            "notes": "Atividade pré-validada — Apostila de Português, Escola Dr. Martinho Lutero.",
        },
    }


# ─── 14 Atividades da Apostila ───────────────────────────────────────────────

APOSTILA_ACTIVITIES = [

    # ══ CONTO: O COELHO E A CHUVA ═══════════════════════════════════════════

    {
        "code": "AT-PORT-06",
        "title": "Personagens do conto: O Coelho e a Chuva",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Identificar os personagens de um conto.",
        "activity_type": "multiple_choice",
        "statement": "No conto, Ravi é um coelho e Nina é uma tartaruga.",
        "question": "Quem são os personagens do conto 'O Coelho e a Chuva'?",
        "expected_answer": "Ravi e Nina",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Quem são os personagens do conto 'O Coelho e a Chuva'?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Ravi e Nina", "Lobo e menina", "Gato e cachorro", "Coelho e raposa"],
                    "correct_answer": {"correct_zone": "Ravi e Nina"},
                    "instructions": "Escolha os personagens certos.",
                },
                "apoios": ["coelho", "tartaruga"],
                "roteiro": "Tom natural. Lê a pergunta e as quatro opções.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "No conto, Ravi é um COELHO e Nina é uma TARTARUGA. Quem são os personagens?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Ravi e Nina", "Lobo e menina", "Gato e cachorro"],
                    "correct_answer": {"correct_zone": "Ravi e Nina"},
                    "instructions": "Escolha os personagens do conto.",
                },
                "apoios": ["coelho", "tartaruga"],
                "roteiro": "Voz clara. Enfatiza os nomes Ravi e Nina.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste os personagens do conto para a caixa certa.",
                "dados": {
                    "items": ["🐰 Ravi", "🐢 Nina", "🐺 Lobo", "🐱 Gato"],
                    "zones": [{"name": "Está no conto"}, {"name": "Não está no conto"}],
                    "correct_answer": {
                        "🐰 Ravi": "Está no conto",
                        "🐢 Nina": "Está no conto",
                        "🐺 Lobo": "Não está no conto",
                        "🐱 Gato": "Não está no conto",
                    },
                    "instructions": "Arraste para a caixa certa.",
                },
                "apoios": ["coelho", "tartaruga"],
                "roteiro": "Voz pausada. Coelho Ravi… tartaruga Nina… [pausa] estão no conto. Mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Toque no COELHO do conto.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🐰 Coelho Ravi", "🐺 Lobo"],
                    "correct_answer": {"correct_zone": "🐰 Coelho Ravi"},
                    "instructions": "Toque.",
                },
                "apoios": ["coelho"],
                "roteiro": "Voz muito lenta. COELHO… Ravi… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-PORT-07",
        "title": "Sequência de acontecimentos: O Coelho e a Chuva",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Ordenar os acontecimentos de um conto em sequência.",
        "activity_type": "drag_drop",
        "statement": "Ravi acordou, choveu forte, ele foi até a árvore e encontrou Nina.",
        "question": "O que aconteceu PRIMEIRO na história?",
        "expected_answer": "Ravi acorda e vê o céu escuro",
        "versoes": {
            "padrao": {
                "fmt": "seq",
                "enun": "Coloque os acontecimentos do conto em ordem. Numere de 1 a 4.",
                "dados": {
                    "items": ["Ravi encontra Nina", "Começa a chover forte", "Os dois viraram amigos", "Ravi acorda e vê o céu escuro"],
                    "zones": [],
                    "correct_answer": {
                        "Ravi acorda e vê o céu escuro": "1°",
                        "Começa a chover forte": "2°",
                        "Ravi encontra Nina": "3°",
                        "Os dois viraram amigos": "4°",
                    },
                    "instructions": "Numere de 1 a 4.",
                },
                "apoios": ["chuva", "árvore"],
                "roteiro": "Tom natural. Lê as 4 frases.",
            },
            "p1": {
                "fmt": "seq",
                "enun": "Numere de 1 a 3 a ordem certa dos acontecimentos.",
                "dados": {
                    "items": ["Ravi encontra Nina", "Começa a chover forte", "Ravi acorda"],
                    "zones": [],
                    "correct_answer": {
                        "Ravi acorda": "1°",
                        "Começa a chover forte": "2°",
                        "Ravi encontra Nina": "3°",
                    },
                    "instructions": "Numere de 1 a 3.",
                },
                "apoios": ["chuva", "coelho"],
                "roteiro": "Voz clara. Lê as 3 frases uma vez.",
            },
            "p2": {
                "fmt": "seq",
                "enun": "Toque na ordem certa do que aconteceu.",
                "dados": {
                    "items": ["🌥️ céu escuro", "🌧️ chuva forte", "🐢 encontra Nina"],
                    "zones": [],
                    "correct_answer": {
                        "🌥️ céu escuro": "1°",
                        "🌧️ chuva forte": "2°",
                        "🐢 encontra Nina": "3°",
                    },
                    "instructions": "Toque na ordem certa.",
                },
                "apoios": ["chuva", "tartaruga"],
                "roteiro": "Voz pausada. Primeiro… [pausa] depois… [pausa] no fim…",
            },
            "p3": {
                "fmt": "toque",
                "enun": "O que aconteceu PRIMEIRO? Ravi acordou ou encontrou Nina? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🌅 Ravi acordou", "🐢 Encontrou Nina"],
                    "correct_answer": {"correct_zone": "🌅 Ravi acordou"},
                    "instructions": "Toque.",
                },
                "apoios": ["chuva"],
                "roteiro": "Voz muito lenta. PRIMEIRO… acordou… [aguarda toque]",
            },
        },
    },

    # ══ SINAIS DE PONTUAÇÃO ══════════════════════════════════════════════════

    {
        "code": "AT-PORT-08",
        "title": "Pontuação: ponto final e exclamação",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Identificar a função do ponto final e do ponto de exclamação.",
        "activity_type": "multiple_choice",
        "statement": "O ponto final (.) encerra uma frase. O ponto de exclamação (!) indica emoção ou surpresa.",
        "question": "Qual sinal usamos no FIM de uma frase comum (sem emoção e sem pergunta)?",
        "expected_answer": "Ponto final (.)",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Qual sinal usamos para ENCERRAR uma frase comum?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Ponto final (.)", "Ponto de exclamação (!)", "Ponto de interrogação (?)", "Vírgula (,)"],
                    "correct_answer": {"correct_zone": "Ponto final (.)"},
                    "instructions": "Escolha o sinal correto.",
                },
                "apoios": ["pontuação"],
                "roteiro": "Tom natural. Lê as quatro opções.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "A frase 'Que dia lindo!' usa qual sinal de pontuação no final?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Ponto de exclamação (!)", "Ponto final (.)", "Ponto de interrogação (?)"],
                    "correct_answer": {"correct_zone": "Ponto de exclamação (!)"},
                    "instructions": "Escolha o sinal.",
                },
                "apoios": ["pontuação"],
                "roteiro": "Voz clara. Lê com ênfase em emoção.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste cada sinal para a sua função.",
                "dados": {
                    "items": ["(.)", "(!)"],
                    "zones": [{"name": "Encerra uma frase"}, {"name": "Mostra emoção ou alegria"}],
                    "correct_answer": {"(.)": "Encerra uma frase", "(!)": "Mostra emoção ou alegria"},
                    "instructions": "Arraste o sinal para a função.",
                },
                "apoios": ["pontuação"],
                "roteiro": "Voz pausada. Ponto final encerra… exclamação emoção… mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Qual sinal encerra a frase? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["(.) Ponto final", "(!) Exclamação"],
                    "correct_answer": {"correct_zone": "(.) Ponto final"},
                    "instructions": "Toque.",
                },
                "apoios": ["pontuação"],
                "roteiro": "Voz muito lenta. FIM… ponto final… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-PORT-09",
        "title": "Pontuação: travessão e interrogação",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Reconhecer o travessão como marcador de fala e a interrogação como marcador de pergunta.",
        "activity_type": "multiple_choice",
        "statement": "O travessão (—) indica que um personagem vai falar. O ponto de interrogação (?) indica uma pergunta.",
        "question": "Qual sinal indica que alguém vai FALAR no texto?",
        "expected_answer": "Travessão (—)",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "No texto: — Não tenha medo, a chuva vai passar. Qual sinal indica que Nina vai falar?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Travessão (—)", "Ponto final (.)", "Vírgula (,)", "Reticências (...)"],
                    "correct_answer": {"correct_zone": "Travessão (—)"},
                    "instructions": "Escolha o sinal de fala.",
                },
                "apoios": ["diálogo"],
                "roteiro": "Tom natural. Lê o exemplo e as opções.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "Qual sinal usamos para fazer uma PERGUNTA?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Ponto de interrogação (?)", "Ponto final (.)", "Travessão (—)"],
                    "correct_answer": {"correct_zone": "Ponto de interrogação (?)"},
                    "instructions": "Escolha o sinal de pergunta.",
                },
                "apoios": ["pontuação"],
                "roteiro": "Voz clara. Lê uma vez.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste o sinal para a sua função.",
                "dados": {
                    "items": ["(—) Travessão", "(?) Interrogação"],
                    "zones": [{"name": "Alguém vai falar"}, {"name": "É uma pergunta"}],
                    "correct_answer": {"(—) Travessão": "Alguém vai falar", "(?) Interrogação": "É uma pergunta"},
                    "instructions": "Arraste para a função certa.",
                },
                "apoios": ["pontuação"],
                "roteiro": "Voz pausada. Travessão… falar… pergunta… mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Toque no sinal de PERGUNTA.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["(?) Pergunta", "(—) Fala"],
                    "correct_answer": {"correct_zone": "(?) Pergunta"},
                    "instructions": "Toque.",
                },
                "apoios": ["pontuação"],
                "roteiro": "Voz muito lenta. PERGUNTA… [aguarda toque]",
            },
        },
    },

    # ══ SINÔNIMOS E ANTÔNIMOS ════════════════════════════════════════════════

    {
        "code": "AT-PORT-10",
        "title": "Sinônimos: palavras de mesmo sentido",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Identificar palavras com o mesmo significado (sinônimos).",
        "activity_type": "multiple_choice",
        "statement": "Sinônimos são palavras de mesmo sentido. Ex.: bonita / linda, alegre / contente.",
        "question": "Qual palavra é sinônimo de BONITO?",
        "expected_answer": "lindo",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Qual palavra tem o MESMO sentido que BONITO?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["lindo", "feio", "pequeno", "triste"],
                    "correct_answer": {"correct_zone": "lindo"},
                    "instructions": "Escolha o sinônimo.",
                },
                "apoios": ["bonito"],
                "roteiro": "Tom natural. Enfatiza mesmo sentido.",
            },
            "p1": {
                "fmt": "dnd",
                "enun": "Arraste para ligar as palavras que têm o MESMO sentido (sinônimos).",
                "dados": {
                    "items": ["alegre", "contente", "enorme", "gigante"],
                    "zones": [{"name": "Par 1: mesmo sentido"}, {"name": "Par 2: mesmo sentido"}],
                    "correct_answer": {
                        "alegre": "Par 1: mesmo sentido",
                        "contente": "Par 1: mesmo sentido",
                        "enorme": "Par 2: mesmo sentido",
                        "gigante": "Par 2: mesmo sentido",
                    },
                    "instructions": "Agrupe os sinônimos.",
                },
                "apoios": ["alegre"],
                "roteiro": "Voz clara. Alegre e contente… mesmo sentido. Enorme e gigante… mesmo sentido.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste cada par para SINÔNIMO (igual) ou ANTÔNIMO (contrário).",
                "dados": {
                    "items": ["😀 alegre / 😁 contente", "😀 alegre / 😢 triste"],
                    "zones": [{"name": "Sinônimo: mesmo sentido"}, {"name": "Antônimo: sentido contrário"}],
                    "correct_answer": {
                        "😀 alegre / 😁 contente": "Sinônimo: mesmo sentido",
                        "😀 alegre / 😢 triste": "Antônimo: sentido contrário",
                    },
                    "instructions": "Arraste para igual ou contrário.",
                },
                "apoios": ["alegre"],
                "roteiro": "Voz pausada. Igual… diferente… mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "BONITO e LINDO têm o mesmo sentido? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["✅ Sim, são iguais", "❌ Não, são contrários"],
                    "correct_answer": {"correct_zone": "✅ Sim, são iguais"},
                    "instructions": "Toque.",
                },
                "apoios": ["bonito"],
                "roteiro": "Voz muito lenta. IGUAL… bonito… lindo… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-PORT-11",
        "title": "Antônimos: palavras de sentido contrário",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Identificar a palavra de sentido oposto (antônimo).",
        "activity_type": "multiple_choice",
        "statement": "Antônimos são palavras de sentido contrário. Ex.: quente ↔ frio, grande ↔ pequeno.",
        "question": "Qual é o antônimo (contrário) de GRANDE?",
        "expected_answer": "pequeno",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Qual é o ANTÔNIMO (contrário) de GRANDE?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["pequeno", "enorme", "gigante", "longo"],
                    "correct_answer": {"correct_zone": "pequeno"},
                    "instructions": "Escolha o contrário.",
                },
                "apoios": ["grande", "pequeno"],
                "roteiro": "Tom natural. Enfatiza contrário.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "Qual palavra é o CONTRÁRIO de QUENTE?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["frio", "calor", "morno"],
                    "correct_answer": {"correct_zone": "frio"},
                    "instructions": "Escolha o contrário.",
                },
                "apoios": ["quente", "frio"],
                "roteiro": "Voz clara. Lê uma vez.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste cada palavra para o seu antônimo.",
                "dados": {
                    "items": ["☀️ quente", "😁 alegre", "📦 cheio"],
                    "zones": [{"name": "❄️ frio"}, {"name": "😢 triste"}, {"name": "📭 vazio"}],
                    "correct_answer": {
                        "☀️ quente": "❄️ frio",
                        "😁 alegre": "😢 triste",
                        "📦 cheio": "📭 vazio",
                    },
                    "instructions": "Arraste para o contrário.",
                },
                "apoios": ["quente", "frio"],
                "roteiro": "Voz pausada. Contrário… oposto… mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "O contrário de GRANDE é PEQUENO? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["✅ Sim", "❌ Não"],
                    "correct_answer": {"correct_zone": "✅ Sim"},
                    "instructions": "Toque.",
                },
                "apoios": ["grande", "pequeno"],
                "roteiro": "Voz muito lenta. CONTRÁRIO… grande… PEQUENO… [aguarda toque]",
            },
        },
    },

    # ══ CARTA PESSOAL ════════════════════════════════════════════════════════

    {
        "code": "AT-PORT-12",
        "title": "Carta pessoal: remetente e destinatário",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Reconhecer remetente, destinatário e a estrutura da carta pessoal.",
        "activity_type": "multiple_choice",
        "statement": "Na carta pessoal: o remetente escreve a carta; o destinatário a recebe. Carlos escreveu para Ana.",
        "question": "Quem ESCREVEU a carta para Ana?",
        "expected_answer": "Carlos",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Na carta lida em aula, quem é o REMETENTE (quem escreve) e quem é a DESTINATÁRIA (quem recebe)?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Carlos escreveu para Ana", "Ana escreveu para Carlos", "Beatriz escreveu para Janete", "Janete escreveu para Carlos"],
                    "correct_answer": {"correct_zone": "Carlos escreveu para Ana"},
                    "instructions": "Escolha a opção correta.",
                },
                "apoios": ["carta"],
                "roteiro": "Tom natural. Lê a questão.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "A carta começa com 'Querida Ana'. Isso significa que a carta foi enviada:",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Para Ana", "De Ana", "Pela professora"],
                    "correct_answer": {"correct_zone": "Para Ana"},
                    "instructions": "Escolha a opção certa.",
                },
                "apoios": ["carta"],
                "roteiro": "Voz clara. Lê uma vez.",
            },
            "p2": {
                "fmt": "seq",
                "enun": "Ordene as partes da carta pessoal.",
                "dados": {
                    "items": ["Assinatura (Carlos)", "Cidade e data", "Saudação (Querida Ana)"],
                    "zones": [],
                    "correct_answer": {
                        "Cidade e data": "1°",
                        "Saudação (Querida Ana)": "2°",
                        "Assinatura (Carlos)": "3°",
                    },
                    "instructions": "Ordene início, meio e fim.",
                },
                "apoios": ["carta"],
                "roteiro": "Voz pausada. Início… meio… fim… mova.",
            },
            "p3": {
                "fmt": "toque",
                "contexto": "Carlos escreveu uma carta para a sua avó Ana. Ele colocou a carta no correio. A avó recebeu a carta em casa.",
                "enun": "Carlos ESCREVEU a carta ou a RECEBEU? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["✍️ Escreveu", "📬 Recebeu"],
                    "correct_answer": {"correct_zone": "✍️ Escreveu"},
                    "instructions": "Toque.",
                },
                "apoios": ["carta"],
            },
        },
    },

    # ══ ORTOGRAFIA: R / RR ═══════════════════════════════════════════════════

    {
        "code": "AT-PORT-13",
        "title": "Ortografia: R ou RR",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Aplicar a regra do R simples e do RR em palavras.",
        "activity_type": "multiple_choice",
        "statement": "Usamos RR entre duas vogais quando o som é forte. Ex.: cachorro, garrafa. Usamos R no início de palavras.",
        "question": "A palavra CA__O (veículo) usa R ou RR?",
        "expected_answer": "RR — carro",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Complete: CA____O. Carro (veículo) ou caro (custoso)? Qual grafia está correta para o veículo?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["CARRO (RR)", "CARO (R)", "CARRRO (RRR)"],
                    "correct_answer": {"correct_zone": "CARRO (RR)"},
                    "instructions": "Escolha a grafia correta.",
                },
                "apoios": ["carro"],
                "roteiro": "Tom natural. Lê e explica a diferença.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "GA____AFA — garrafa. Entre as vogais A e A o som é forte. Usa-se R ou RR?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["RR (garrafa)", "R (garafa)"],
                    "correct_answer": {"correct_zone": "RR (garrafa)"},
                    "instructions": "Escolha R ou RR.",
                },
                "apoios": ["garrafa"],
                "roteiro": "Voz clara. Lê com ênfase no som forte.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste cada palavra para R simples ou RR (som forte entre vogais).",
                "dados": {
                    "items": ["🐀 rato", "🚗 carro", "🐶 cachorro", "🌹 rosa"],
                    "zones": [{"name": "R simples"}, {"name": "RR (som forte)"}],
                    "correct_answer": {
                        "🐀 rato": "R simples",
                        "🌹 rosa": "R simples",
                        "🚗 carro": "RR (som forte)",
                        "🐶 cachorro": "RR (som forte)",
                    },
                    "instructions": "Arraste para R ou RR.",
                },
                "apoios": ["rato", "carro"],
                "roteiro": "Voz pausada. Rato… rosa… um R. Carro… cachorro… RR.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "CACHORRO usa R ou RR? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["RR (cachoRRo)", "R (cachoro)"],
                    "correct_answer": {"correct_zone": "RR (cachoRRo)"},
                    "instructions": "Toque.",
                },
                "apoios": ["cachorro"],
                "roteiro": "Voz muito lenta. CACHORRO… RR… [aguarda toque]",
            },
        },
    },

    # ══ TEXTO INSTRUCIONAL ═══════════════════════════════════════════════════

    {
        "code": "AT-PORT-14",
        "title": "Texto instrucional: lavar as mãos",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Ordenar os passos de um texto instrucional e reconhecer sua finalidade.",
        "activity_type": "drag_drop",
        "statement": "Texto instrucional sobre como lavar as mãos: molhar → aplicar sabão → esfregar → enxaguar → secar.",
        "question": "O que vem DEPOIS de molhar as mãos?",
        "expected_answer": "Aplicar o sabão",
        "versoes": {
            "padrao": {
                "fmt": "seq",
                "enun": "Numere os passos de 1 a 5 na ordem correta para lavar as mãos.",
                "dados": {
                    "items": ["Secar com toalha", "Aplicar o sabão", "Enxaguar com água", "Molhar as mãos", "Esfregar bem as mãos"],
                    "zones": [],
                    "correct_answer": {
                        "Molhar as mãos": "1°",
                        "Aplicar o sabão": "2°",
                        "Esfregar bem as mãos": "3°",
                        "Enxaguar com água": "4°",
                        "Secar com toalha": "5°",
                    },
                    "instructions": "Numere de 1 a 5.",
                },
                "apoios": ["mãos", "sabão"],
                "roteiro": "Tom natural. Lê os 5 passos.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "Ao lavar as mãos, o que fazemos DEPOIS de aplicar o sabão?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Esfregar bem as mãos", "Secar com toalha", "Molhar as mãos"],
                    "correct_answer": {"correct_zone": "Esfregar bem as mãos"},
                    "instructions": "Escolha o passo seguinte.",
                },
                "apoios": ["mãos", "sabão"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "seq",
                "enun": "Toque nos passos na ordem certa.",
                "dados": {
                    "items": ["💧 molhar", "🧼 sabão", "👏 esfregar"],
                    "zones": [],
                    "correct_answer": {"💧 molhar": "1°", "🧼 sabão": "2°", "👏 esfregar": "3°"},
                    "instructions": "Toque na ordem certa.",
                },
                "apoios": ["mãos", "sabão"],
                "roteiro": "Voz pausada. Primeiro… depois… no fim…",
            },
            "p3": {
                "fmt": "toque",
                "enun": "O que vem PRIMEIRO? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["💧 Molhar as mãos", "🧼 Aplicar sabão"],
                    "correct_answer": {"correct_zone": "💧 Molhar as mãos"},
                    "instructions": "Toque.",
                },
                "apoios": ["mãos"],
                "roteiro": "Voz muito lenta. PRIMEIRO… molhar… [aguarda toque]",
            },
        },
    },

    # ══ ORTOGRAFIA: S / SS ═══════════════════════════════════════════════════

    {
        "code": "AT-PORT-15",
        "title": "Ortografia: S ou SS",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Aplicar a regra do S simples e do SS em palavras.",
        "activity_type": "multiple_choice",
        "statement": "Usamos SS entre duas vogais quando o som é forte. Ex.: osso, passeio. Não usamos SS no início de palavras.",
        "question": "A palavra O__O (osso) usa S ou SS?",
        "expected_answer": "SS — osso",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Complete: O____O. Qual é a escrita correta?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["OSSO (SS)", "OSO (S)", "OSSSO"],
                    "correct_answer": {"correct_zone": "OSSO (SS)"},
                    "instructions": "Escolha a grafia correta.",
                },
                "apoios": ["osso"],
                "roteiro": "Tom natural. Lê.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "PASSEIO: entre as vogais A e E o som é forte. Usa-se S ou SS?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["SS (passeio)", "S (paseio)"],
                    "correct_answer": {"correct_zone": "SS (passeio)"},
                    "instructions": "Escolha S ou SS.",
                },
                "apoios": ["passear"],
                "roteiro": "Voz clara. Lê com ênfase.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste cada palavra para S simples ou SS (entre vogais, som forte).",
                "dados": {
                    "items": ["🦴 osso", "👞 sapato", "🚶 passeio", "🌵 sino"],
                    "zones": [{"name": "S simples"}, {"name": "SS (entre vogais)"}],
                    "correct_answer": {
                        "🦴 osso": "SS (entre vogais)",
                        "🚶 passeio": "SS (entre vogais)",
                        "👞 sapato": "S simples",
                        "🌵 sino": "S simples",
                    },
                    "instructions": "Arraste para S ou SS.",
                },
                "apoios": ["osso", "sapato"],
                "roteiro": "Voz pausada. Osso… passeio… SS. Sapato… sino… S simples.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "OSSO usa SS ou S? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["SS (oSSo)", "S (oso)"],
                    "correct_answer": {"correct_zone": "SS (oSSo)"},
                    "instructions": "Toque.",
                },
                "apoios": ["osso"],
                "roteiro": "Voz muito lenta. OSSO… SS… [aguarda toque]",
            },
        },
    },

    # ══ SUBSTANTIVO ══════════════════════════════════════════════════════════

    {
        "code": "AT-PORT-16",
        "title": "Substantivo comum ou próprio",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Classificar substantivos em comuns (genérico) e próprios (específico).",
        "activity_type": "multiple_choice",
        "statement": "Substantivo próprio: nome específico de pessoa, cidade, país. Ex.: Brasil, João. Substantivo comum: nome genérico. Ex.: cidade, menino.",
        "question": "Qual das palavras abaixo é um SUBSTANTIVO PRÓPRIO?",
        "expected_answer": "Brasil",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Qual das palavras é um SUBSTANTIVO PRÓPRIO (nome específico, escrito com letra maiúscula)?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Brasil", "cidade", "carro", "menino"],
                    "correct_answer": {"correct_zone": "Brasil"},
                    "instructions": "Escolha o substantivo próprio.",
                },
                "apoios": ["Brasil", "cidade"],
                "roteiro": "Tom natural. Lê.",
            },
            "p1": {
                "fmt": "dnd",
                "enun": "Arraste cada palavra para PRÓPRIO (específico) ou COMUM (genérico).",
                "dados": {
                    "items": ["João", "menino", "Brasil", "cidade"],
                    "zones": [{"name": "Próprio (específico)"}, {"name": "Comum (genérico)"}],
                    "correct_answer": {
                        "João": "Próprio (específico)",
                        "Brasil": "Próprio (específico)",
                        "menino": "Comum (genérico)",
                        "cidade": "Comum (genérico)",
                    },
                    "instructions": "Arraste para próprio ou comum.",
                },
                "apoios": ["nome", "cidade"],
                "roteiro": "Voz clara. João é específico… menino é geral.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Nome de pessoa ou país específico → PRÓPRIO. Palavra geral → COMUM.",
                "dados": {
                    "items": ["🌎 Brasil", "👦 menino", "🏙️ cidade", "👤 Maria"],
                    "zones": [{"name": "✅ Substantivo Próprio"}, {"name": "📋 Substantivo Comum"}],
                    "correct_answer": {
                        "🌎 Brasil": "✅ Substantivo Próprio",
                        "👤 Maria": "✅ Substantivo Próprio",
                        "👦 menino": "📋 Substantivo Comum",
                        "🏙️ cidade": "📋 Substantivo Comum",
                    },
                    "instructions": "Arraste para próprio ou comum.",
                },
                "apoios": ["nome", "cidade"],
                "roteiro": "Voz pausada. Nome específico… geral… mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "BRASIL é um substantivo PRÓPRIO ou COMUM? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["✅ Próprio", "📋 Comum"],
                    "correct_answer": {"correct_zone": "✅ Próprio"},
                    "instructions": "Toque.",
                },
                "apoios": ["Brasil"],
                "roteiro": "Voz muito lenta. BRASIL… PRÓPRIO… [aguarda toque]",
            },
        },
    },

    # ══ ADJETIVOS ════════════════════════════════════════════════════════════

    {
        "code": "AT-PORT-17",
        "title": "Adjetivos: caracterizar o substantivo",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Identificar adjetivos e aplicá-los para caracterizar substantivos.",
        "activity_type": "multiple_choice",
        "statement": "Adjetivos descrevem características. Ex.: bolo pequeno, menina feliz, sorvete gelado.",
        "question": "Na frase 'O sorvete está GELADO', qual palavra é o adjetivo?",
        "expected_answer": "gelado",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Na frase 'O sorvete está GELADO', qual palavra é o ADJETIVO (diz como o sorvete é)?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["gelado", "sorvete", "está", "o"],
                    "correct_answer": {"correct_zone": "gelado"},
                    "instructions": "Escolha o adjetivo.",
                },
                "apoios": ["sorvete"],
                "roteiro": "Tom natural. Lê a frase.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "Qual adjetivo combina com SORVETE (descreve como ele é)?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["gelado", "rápido", "enorme", "barulhento"],
                    "correct_answer": {"correct_zone": "gelado"},
                    "instructions": "Escolha o adjetivo certo.",
                },
                "apoios": ["sorvete"],
                "roteiro": "Voz clara. Qual palavra descreve o sorvete?",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste o adjetivo certo para cada substantivo.",
                "dados": {
                    "items": ["🍦 gelado", "🌸 cheirosa", "🐢 lenta"],
                    "zones": [{"name": "sorvete"}, {"name": "flor"}, {"name": "tartaruga"}],
                    "correct_answer": {
                        "🍦 gelado": "sorvete",
                        "🌸 cheirosa": "flor",
                        "🐢 lenta": "tartaruga",
                    },
                    "instructions": "Arraste o adjetivo para o substantivo.",
                },
                "apoios": ["sorvete", "flor"],
                "roteiro": "Voz pausada. Como é o sorvete… a flor… a tartaruga… mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "O sorvete é GELADO ou QUENTE? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["❄️ Gelado", "🔥 Quente"],
                    "correct_answer": {"correct_zone": "❄️ Gelado"},
                    "instructions": "Toque.",
                },
                "apoios": ["sorvete"],
                "roteiro": "Voz muito lenta. SORVETE… GELADO… [aguarda toque]",
            },
        },
    },

    # ══ VERBOS ═══════════════════════════════════════════════════════════════

    {
        "code": "AT-PORT-18",
        "title": "Verbos: identificar ações",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Identificar palavras que indicam ação (verbos) em frases.",
        "activity_type": "multiple_choice",
        "statement": "Verbos indicam ação. Ex.: O menino PULA. A menina CANTA. A criança BRINCA.",
        "question": "Na frase 'A menina CANTA no coral', qual palavra indica uma AÇÃO?",
        "expected_answer": "canta",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Na frase 'A menina CANTA no coral', qual palavra indica uma AÇÃO (verbo)?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["canta", "menina", "coral", "a"],
                    "correct_answer": {"correct_zone": "canta"},
                    "instructions": "Escolha o verbo.",
                },
                "apoios": ["menina", "música"],
                "roteiro": "Tom natural. Lê a frase.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "Qual das palavras abaixo é um VERBO (indica ação)?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["brincar", "bola", "menino", "escola"],
                    "correct_answer": {"correct_zone": "brincar"},
                    "instructions": "Escolha o verbo.",
                },
                "apoios": ["brincar"],
                "roteiro": "Voz clara. Qual palavra indica uma ação?",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste cada palavra para VERBO (ação) ou SUBSTANTIVO (coisa / pessoa).",
                "dados": {
                    "items": ["🎵 cantar", "⚽ jogar", "🏫 escola", "👦 menino"],
                    "zones": [{"name": "Verbo (ação)"}, {"name": "Substantivo (coisa/pessoa)"}],
                    "correct_answer": {
                        "🎵 cantar": "Verbo (ação)",
                        "⚽ jogar": "Verbo (ação)",
                        "🏫 escola": "Substantivo (coisa/pessoa)",
                        "👦 menino": "Substantivo (coisa/pessoa)",
                    },
                    "instructions": "Arraste para verbo ou substantivo.",
                },
                "apoios": ["brincar", "cantar"],
                "roteiro": "Voz pausada. Ação… coisa… mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "CORRER é uma AÇÃO? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["✅ Sim, é ação", "❌ Não é ação"],
                    "correct_answer": {"correct_zone": "✅ Sim, é ação"},
                    "instructions": "Toque.",
                },
                "apoios": ["correr"],
                "roteiro": "Voz muito lenta. CORRER… ação… SIM… [aguarda toque]",
            },
        },
    },

    # ══ ANEDOTA ══════════════════════════════════════════════════════════════

    {
        "code": "AT-PORT-19",
        "title": "Anedota: texto curto com humor",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Identificar as características da anedota como gênero textual com humor.",
        "activity_type": "multiple_choice",
        "statement": "A anedota é um texto curto com humor. Tem personagens, uma situação cotidiana e um final inesperado e engraçado.",
        "question": "A anedota é um tipo de texto:",
        "expected_answer": "curto e engraçado (com humor)",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "A anedota é um gênero textual:",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["curto e engraçado (com humor)", "longo e científico", "triste e reflexivo", "uma receita de culinária"],
                    "correct_answer": {"correct_zone": "curto e engraçado (com humor)"},
                    "instructions": "Escolha a característica certa.",
                },
                "apoios": ["humor"],
                "roteiro": "Tom natural. Lê as opções.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "A anedota do detetive terminou de forma inesperada e engraçada. Isso é característica:",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Da anedota (texto com humor)", "De uma notícia", "De uma carta"],
                    "correct_answer": {"correct_zone": "Da anedota (texto com humor)"},
                    "instructions": "Escolha a opção certa.",
                },
                "apoios": ["humor"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste as características para ANEDOTA ou NOTÍCIA.",
                "dados": {
                    "items": ["😂 tem humor", "📰 informa fatos reais", "😲 final inesperado", "📅 tem data e local"],
                    "zones": [{"name": "Anedota"}, {"name": "Notícia"}],
                    "correct_answer": {
                        "😂 tem humor": "Anedota",
                        "😲 final inesperado": "Anedota",
                        "📰 informa fatos reais": "Notícia",
                        "📅 tem data e local": "Notícia",
                    },
                    "instructions": "Arraste para anedota ou notícia.",
                },
                "apoios": ["humor"],
                "roteiro": "Voz pausada. Anedota… notícia… mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "A anedota é um texto ENGRAÇADO ou TRISTE? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["😂 Engraçado", "😢 Triste"],
                    "correct_answer": {"correct_zone": "😂 Engraçado"},
                    "instructions": "Toque.",
                },
                "apoios": ["humor"],
                "roteiro": "Voz muito lenta. ANEDOTA… engraçado… [aguarda toque]",
            },
        },
    },
]


def _extra_mc_versions(question: str, correct: str, distractors: list[str], supports: list[str]) -> dict:
    options = [correct, *distractors]
    reduced = options[:3]
    return {
        "padrao": {
            "fmt": "mc",
            "enun": question,
            "dados": {
                "items": ["Minha resposta"],
                "zones": options,
                "correct_answer": {"correct_zone": correct},
                "instructions": "Escolha a resposta correta.",
            },
            "apoios": supports,
        },
        "p1": {
            "fmt": "mc",
            "enun": f"Leia com apoio visual. {question}",
            "dados": {
                "items": ["Minha resposta"],
                "zones": reduced,
                "correct_answer": {"correct_zone": correct},
                "instructions": "Toque na resposta certa.",
            },
            "apoios": supports,
        },
        "p2": {
            "fmt": "mc",
            "enun": f"{question} [pausa] Escolha uma opcao.",
            "dados": {
                "items": ["Minha resposta"],
                "zones": reduced,
                "correct_answer": {"correct_zone": correct},
                "instructions": "Escolha uma opcao.",
            },
            "apoios": supports[:1],
        },
        "p3": {
            "fmt": "toque",
            "enun": f"Toque em {correct}.",
            "dados": {
                "items": ["Minha resposta"],
                "zones": [correct, distractors[0] if distractors else "Outra"],
                "correct_answer": {"correct_zone": correct},
                "instructions": "Toque.",
            },
            "apoios": supports[:1],
        },
    }


def _extra_dnd_versions(question: str, items: list[str], zones: list[str], correct: dict, supports: list[str]) -> dict:
    simple_items = items[:4]
    simple_correct = {k: v for k, v in correct.items() if k in simple_items}
    return {
        "padrao": {
            "fmt": "dnd",
            "enun": question,
            "dados": {
                "items": items,
                "zones": [{"name": z} for z in zones],
                "correct_answer": correct,
                "instructions": "Arraste cada palavra para o grupo correto.",
            },
            "apoios": supports,
        },
        "p1": {
            "fmt": "dnd",
            "enun": f"{question} Use as figuras de apoio.",
            "dados": {
                "items": simple_items,
                "zones": [{"name": z} for z in zones],
                "correct_answer": simple_correct,
                "instructions": "Arraste para o grupo certo.",
            },
            "apoios": supports,
        },
        "p2": {
            "fmt": "dnd",
            "enun": f"{question} [pausa] Mova um item de cada vez.",
            "dados": {
                "items": simple_items[:3],
                "zones": [{"name": z} for z in zones],
                "correct_answer": {k: v for k, v in simple_correct.items() if k in simple_items[:3]},
                "instructions": "Mova devagar.",
            },
            "apoios": supports[:1],
        },
        "p3": {
            "fmt": "toque",
            "enun": f"Toque em {simple_items[0]}.",
            "dados": {
                "items": ["Minha resposta"],
                "zones": [simple_items[0], simple_items[1]],
                "correct_answer": {"correct_zone": simple_items[0]},
                "instructions": "Toque.",
            },
            "apoios": supports[:1],
        },
    }


APOSTILA_ACTIVITIES.extend([
    {
        "code": "AT-PORT-20",
        "title": "Poema visual: forma e sentido",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Identificar a relacao entre formato visual e sentido em um poema visual.",
        "activity_type": "multiple_choice",
        "statement": "O poema visual usa as palavras para formar uma imagem.",
        "question": "No poema visual da apostila, qual animal o formato das palavras representa?",
        "expected_answer": "Cachorro",
        "versoes": _extra_mc_versions(
            "No poema visual, qual animal o formato das palavras representa?",
            "Cachorro",
            ["Gato", "Passaro", "Peixe"],
            ["cachorro", "poema visual"],
        ),
    },
    {
        "code": "AT-PORT-21",
        "title": "Sons do X: classificar palavras",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Reconhecer diferentes sons da letra X em palavras.",
        "activity_type": "drag_drop",
        "statement": "A letra X pode ter sons diferentes, como CH, Z, S ou CS.",
        "question": "Arraste cada palavra para o som correto da letra X.",
        "expected_answer": "xícara-CH; exemplo-Z; texto-S; táxi-CS",
        "versoes": _extra_dnd_versions(
            "Arraste cada palavra para o som correto do X.",
            ["xícara", "exemplo", "texto", "táxi"],
            ["Som de CH", "Som de Z", "Som de S", "Som de CS"],
            {"xícara": "Som de CH", "exemplo": "Som de Z", "texto": "Som de S", "táxi": "Som de CS"},
            ["letra X", "xícara"],
        ),
    },
    {
        "code": "AT-PORT-22",
        "title": "Ortografia: LI ou LH",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Diferenciar palavras escritas com LI e com LH.",
        "activity_type": "multiple_choice",
        "statement": "Algumas palavras usam LI e outras usam LH.",
        "question": "Qual palavra completa FO__A corretamente?",
        "expected_answer": "FOLHA",
        "versoes": _extra_mc_versions(
            "Qual palavra completa FO__A corretamente?",
            "FOLHA",
            ["FOLIA", "FOILA", "FOLA"],
            ["folha", "letra LH"],
        ),
    },
])


# ─── Seed functions (idênticas ao padrão de seed_tea_activities.py) ──────────

def _get_teacher(session: Session) -> User:
    teacher = session.exec(
        select(User).where(User.email == "professor@eduadapt.local")
    ).first()
    if not teacher:
        raise RuntimeError("Teacher not found. Run initial seed first.")
    return teacher


def _get_profiles(session: Session) -> dict:
    profile_names = {
        "p1": "TEA — Apoio Visual e Leitura Inicial",
        "p2": "TEA — Hipersensibilidade Visual",
        "p3": "TEA — Não Verbal",
    }
    return {
        key: session.exec(select(StudentProfile).where(StudentProfile.name == name)).first()
        for key, name in profile_names.items()
    }


def _seed_adaptations(session: Session, activity: Activity, versoes: dict, profiles: dict) -> int:
    count = 0
    for version_key, versao in versoes.items():
        profile_id = None
        if version_key != "padrao":
            profile = profiles.get(version_key)
            if profile:
                profile_id = profile.id

        existing = session.exec(
            select(ActivityAdaptation).where(
                ActivityAdaptation.activity_id == activity.id,
                ActivityAdaptation.student_profile_id == profile_id,
            )
        ).first()
        if existing:
            continue

        output_data = _build_output_data(versao, version_key)
        adaptation = ActivityAdaptation(
            id=str(uuid.uuid4()),
            activity_id=activity.id,
            student_profile_id=profile_id,
            generated_by="seed",
            output_data=output_data,
            status="approved",
            version=1,
        )
        session.add(adaptation)
        count += 1
    return count


def _seed_apostila_activities(session: Session, teacher: User, profiles: dict) -> None:
    total_activities = 0
    total_adaptations = 0
    _EXCLUDED_KEYS = {"code", "versoes"}
    ravi_nina_story = _seed_ravi_nina_story(session, teacher)
    carta_story = _seed_carta_carlos_story(session, teacher)
    anedota_story = _seed_anedota_detetive_story(session, teacher)
    story_by_code = {
        **{code: ravi_nina_story for code in RAVI_NINA_ACTIVITY_CODES},
        **{code: carta_story for code in CARTA_CARLOS_ACTIVITY_CODES},
        **{code: anedota_story for code in ANEDOTA_DETETIVE_ACTIVITY_CODES},
    }

    for act_data in APOSTILA_ACTIVITIES:
        code = act_data.get("code")
        versoes = act_data["versoes"]
        activity_fields = {k: v for k, v in act_data.items() if k not in _EXCLUDED_KEYS}
        linked_story = story_by_code.get(code)
        if linked_story:
            activity_fields["story_id"] = linked_story.id

        existing = session.exec(
            select(Activity).where(
                Activity.title == activity_fields["title"],
                Activity.teacher_id == teacher.id,
            )
        ).first()

        if existing:
            activity = existing
            if linked_story and activity.story_id != linked_story.id:
                activity.story_id = linked_story.id
                session.add(activity)
        else:
            activity = Activity(
                id=str(uuid.uuid4()),
                teacher_id=teacher.id,
                status="active",
                **activity_fields,
            )
            session.add(activity)
            session.flush()
            total_activities += 1

        count = _seed_adaptations(session, activity, versoes, profiles)
        total_adaptations += count

    session.commit()
    print(f"[seed_apostila_portugues] {total_activities} activities + {total_adaptations} adaptations created.")


def run() -> None:
    with Session(engine) as session:
        teacher = _get_teacher(session)
        profiles = _get_profiles(session)
        _seed_apostila_activities(session, teacher, profiles)


if __name__ == "__main__":
    run()
