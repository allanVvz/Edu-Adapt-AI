"""
Seed: 25 TEA activities × 4 profile versions = 100 adaptations.

Maps each activity version to the 3 TEA profiles + 1 standard (no profile).
All content is pre-validated by the instructional design system.
Idempotent — skips activities that already exist by title.
"""
import re
import uuid
from sqlmodel import Session, select

from ..database import engine
from ..models.user import User
from ..models.activity import Activity
from ..models.adaptation import ActivityAdaptation
from ..models.student_profile import StudentProfile
from ..services.openai_service import _make_prompts, _make_generated_slots
from ..services.emoji_service import get_emoji_for_concept


# ─── Version → Profile mapping ────────────────────────────────────────────────

# p1 = Explorador Verbal → TEA — Apoio Visual e Leitura Inicial
# p2 = Conector Visual   → TEA — Hipersensibilidade Visual
# p3 = Comunicador Simb. → TEA — Não Verbal
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
    "diss":  None,           # dissertativa — sem interação estruturada
    "mc":    "multiple_choice",
    "dnd":   "drag_and_drop",
    "seq":   "sequencing",
    "toque": "multiple_choice",  # 2 opções grandes
    "par":   "drag_and_drop",    # pareamento como D&D
}


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
    """Convert a version dict from the TEA activity spec to output_data format."""
    fmt = versao.get("fmt", "mc")
    enun = versao.get("enun", "Observe e responda.")
    dados = versao.get("dados", {})
    contexto = versao.get("contexto", "")
    apoios = versao.get("apoios", [])
    audio_cfg = VERSION_AUDIO_CONFIG[version_key]

    # Build interaction_options from dados
    interaction_options = []
    interaction_type = FMT_TO_INTERACTION_TYPE.get(fmt)

    if interaction_type:
        items_raw = dados.get("items", [])
        zones_raw = dados.get("zones", [])
        correct = dados.get("correct_answer", {})

        items = []
        for raw in items_raw:
            if isinstance(raw, str):
                name = raw
            elif isinstance(raw, dict):
                name = raw.get("name", str(raw))
            else:
                name = str(raw)
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

    # Build image_options from apoios
    image_options = []
    for i, apoio in enumerate(apoios[:2]):
        img_id = f"img_{i+1}"
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
            "id": img_id,
            "description": description,
            "base_subject": base_subject,
            "prompts": _make_prompts(base_subject),
            "generated": _make_generated_slots(),
            "active_style": "cartoon_2d",
            "is_active": True,
            "image_url": None,
            "illustration_type": "generated",
        })

    # Fallback: always have at least 1 image_option
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
            "notes": "Atividade pré-validada pelo sistema de design instrucional TEA.",
        },
    }


# ─── 25 Activities ───────────────────────────────────────────────────────────

TEA_ACTIVITIES = [

    # ══════════════════ PORTUGUÊS ═══════════════════════════════════════════

    {
        "code": "AT-PORT-01",
        "title": "Interpretar um texto curto",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Extrair informação explícita de um texto.",
        "activity_type": "essay",
        "statement": 'A horta da escola tem alface e tomate. As crianças regam as plantas toda manhã.',
        "question": "Por que as crianças regam as plantas toda manhã?",
        "expected_answer": "Para mantê-las vivas e saudáveis.",
        "versoes": {
            "padrao": {
                "fmt": "diss",
                "enun": 'Leia: "A horta da escola tem alface e tomate. As crianças regam as plantas toda manhã." Explique, com suas palavras, por que as crianças regam as plantas toda manhã.',
                "dados": {},
                "apoios": ["horta", "alface", "tomate"],
                "roteiro": 'Tom natural. Lê o texto inteiro uma vez, depois o enunciado.',
            },
            "p1": {
                "fmt": "mc",
                "enun": "Segundo o texto, o que as crianças fazem toda manhã?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Regam as plantas", "Colhem os tomates", "Plantam alface", "Almoçam na horta"],
                    "correct_answer": {"correct_zone": "Regam as plantas"},
                    "instructions": "Escolha a resposta certa.",
                },
                "apoios": ["horta", "alface"],
                "roteiro": "Voz clara e literal. Lê enunciado e as 4 opções uma vez.",
            },
            "p2": {
                "fmt": "toque",
                "enun": "A horta tem 🥬 alface e 🍅 tomate. Toque no que a horta tem.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🥬 Alface", "🍌 Banana"],
                    "correct_answer": {"correct_zone": "🥬 Alface"},
                    "instructions": "Toque na resposta certa.",
                },
                "apoios": ["alface", "tomate"],
                "roteiro": "Voz pausada. Horta. [pausa] O que tem? [pausa] Toque.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Na horta tem alface. Toque na ALFACE.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🥬 Alface", "🍅 Tomate"],
                    "correct_answer": {"correct_zone": "🥬 Alface"},
                    "instructions": "Toque.",
                },
                "apoios": ["alface"],
                "roteiro": "Voz muito lenta e grave. ALFACE… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-PORT-02",
        "title": "Substantivo e adjetivo",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Distinguir a coisa (substantivo) do como ela é (adjetivo).",
        "activity_type": "multiple_choice",
        "statement": 'Na frase "O gato preto dorme", identifique as classes gramaticais.',
        "question": 'Na frase "O gato preto dorme", qual palavra é o ADJETIVO?',
        "expected_answer": "preto",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": 'Na frase "O gato preto dorme", qual palavra é o ADJETIVO (diz como o gato é)?',
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["preto", "gato", "dorme", "o"],
                    "correct_answer": {"correct_zone": "preto"},
                    "instructions": "Escolha o adjetivo.",
                },
                "apoios": ["gato"],
                "roteiro": "Tom natural. Lê a frase e as 4 opções.",
            },
            "p1": {
                "fmt": "mc",
                "enun": 'Na frase "O gato preto dorme", qual palavra diz a COR do gato?',
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["preto", "gato", "dorme"],
                    "correct_answer": {"correct_zone": "preto"},
                    "instructions": "Qual palavra diz a cor?",
                },
                "apoios": ["gato"],
                "roteiro": "Voz clara. Lê com ênfase em cor.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": 'Da frase "O gato preto dorme", arraste cada palavra para a sua classe.',
                "dados": {
                    "items": ["gato", "preto", "dorme"],
                    "zones": [{"name": "É uma coisa (substantivo)"}, {"name": "Diz como é (adjetivo)"}, {"name": "É uma ação (verbo)"}],
                    "correct_answer": {"gato": "É uma coisa (substantivo)", "preto": "Diz como é (adjetivo)", "dorme": "É uma ação (verbo)"},
                    "instructions": "Arraste cada palavra para a sua classe.",
                },
                "apoios": ["gato"],
                "roteiro": "Voz pausada. Coisa… [pausa] como é… [pausa] ação… mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Toque no gato PRETO.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🐈‍⬛ Gato preto", "🐈 Gato"],
                    "correct_answer": {"correct_zone": "🐈‍⬛ Gato preto"},
                    "instructions": "Toque.",
                },
                "apoios": ["gato"],
                "roteiro": "Voz muito lenta. Gato… PRETO… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-PORT-03",
        "title": "Ordenar a história da Ana",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Reconhecer a ordem dos acontecimentos.",
        "activity_type": "drag_drop",
        "statement": "Ana tem uma manhã cheia de atividades.",
        "question": "Coloque a manhã da Ana em ordem.",
        "expected_answer": "acordou, tomou café, foi à escola, voltou para casa",
        "versoes": {
            "padrao": {
                "fmt": "seq",
                "enun": "Coloque a manhã da Ana em ordem. Numere de 1 a 4.",
                "dados": {
                    "items": ["Ana foi à escola", "Ana acordou", "Ana voltou para casa", "Ana tomou café"],
                    "zones": [],
                    "correct_answer": {"Ana acordou": "1°", "Ana tomou café": "2°", "Ana foi à escola": "3°", "Ana voltou para casa": "4°"},
                    "instructions": "Numere de 1 a 4.",
                },
                "apoios": ["escola", "café"],
                "roteiro": "Tom natural. Lê as 4 frases.",
            },
            "p1": {
                "fmt": "seq",
                "enun": "Ordene os momentos da manhã da Ana. Numere de 1 a 3.",
                "dados": {
                    "items": ["Ana tomou café", "Ana acordou", "Ana foi à escola"],
                    "zones": [],
                    "correct_answer": {"Ana acordou": "1°", "Ana tomou café": "2°", "Ana foi à escola": "3°"},
                    "instructions": "Numere de 1 a 3.",
                },
                "apoios": ["escola", "café"],
                "roteiro": "Voz clara. Lê as 3 frases uma vez.",
            },
            "p2": {
                "fmt": "seq",
                "enun": "Toque nas cenas da Ana, do primeiro ao último.",
                "dados": {
                    "items": ["🌅 acordou", "🍽️ tomou café", "🏫 foi à escola"],
                    "zones": [],
                    "correct_answer": {"🌅 acordou": "1°", "🍽️ tomou café": "2°", "🏫 foi à escola": "3°"},
                    "instructions": "Toque na ordem certa.",
                },
                "apoios": ["acordar", "escola"],
                "roteiro": "Voz pausada. Primeiro… [pausa] depois… [pausa] no fim…",
            },
            "p3": {
                "fmt": "toque",
                "enun": "O que a Ana faz PRIMEIRO de manhã? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🌅 Acordar", "🏫 Ir à escola"],
                    "correct_answer": {"correct_zone": "🌅 Acordar"},
                    "instructions": "Toque.",
                },
                "apoios": ["acordar"],
                "roteiro": "Voz muito lenta. PRIMEIRO… acordar… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-PORT-04",
        "title": "Sinônimo e antônimo",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Reconhecer palavra de sentido igual e de sentido contrário.",
        "activity_type": "multiple_choice",
        "statement": "Palavra-base: ALEGRE.",
        "question": "Qual é o ANTÔNIMO (contrário) de ALEGRE?",
        "expected_answer": "triste",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Qual é o ANTÔNIMO (contrário) de ALEGRE?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["triste", "feliz", "contente", "animado"],
                    "correct_answer": {"correct_zone": "triste"},
                    "instructions": "Escolha o contrário.",
                },
                "apoios": ["alegre", "triste"],
                "roteiro": "Tom natural. Enfatiza contrário.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "Qual palavra quer dizer o MESMO que ALEGRE?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["feliz", "triste", "cansado"],
                    "correct_answer": {"correct_zone": "feliz"},
                    "instructions": "Escolha a palavra de mesmo sentido.",
                },
                "apoios": ["alegre", "feliz"],
                "roteiro": "Voz clara. Lê uma vez.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Pensando em ALEGRE, arraste cada palavra para igual ou contrário.",
                "dados": {
                    "items": ["😀 feliz", "😢 triste"],
                    "zones": [{"name": "Igual a alegre"}, {"name": "Contrário de alegre"}],
                    "correct_answer": {"😀 feliz": "Igual a alegre", "😢 triste": "Contrário de alegre"},
                    "instructions": "Arraste para igual ou contrário.",
                },
                "apoios": ["alegre", "triste"],
                "roteiro": "Voz pausada. Igual… contrário… mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Toque na carinha ALEGRE.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["😀 Alegre", "😢 Triste"],
                    "correct_answer": {"correct_zone": "😀 Alegre"},
                    "instructions": "Toque.",
                },
                "apoios": ["alegre"],
                "roteiro": "Voz muito lenta. ALEGRE… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-PORT-05",
        "title": "Descrever uma cena",
        "discipline": "Português",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Produzir linguagem a partir de uma cena.",
        "activity_type": "essay",
        "statement": "Um menino chuta uma bola no parque ⚽.",
        "question": "Escreva 3 frases descrevendo quem está na cena, o que faz e onde.",
        "expected_answer": "O menino chuta a bola no parque.",
        "versoes": {
            "padrao": {
                "fmt": "diss",
                "enun": "Observe a cena: um menino chuta uma bola no parque ⚽. Escreva 3 frases descrevendo quem está na cena, o que faz e onde.",
                "dados": {},
                "apoios": ["bola", "parque"],
                "roteiro": "Tom natural. Descreva em 3 frases: quem, o quê, onde.",
            },
            "p1": {
                "fmt": "diss",
                "enun": "Descreva a cena do menino com a bola no parque usando o roteiro: Quem? ___ O quê? ___ Onde? ___",
                "dados": {},
                "apoios": ["bola", "parque"],
                "roteiro": "Voz clara. Lê o roteiro: Quem… o quê… onde.",
            },
            "p2": {
                "fmt": "seq",
                "enun": "Monte a frase da cena: arraste cada parte para a ordem certa.",
                "dados": {
                    "items": ["O menino", "chuta", "a bola"],
                    "zones": [],
                    "correct_answer": {"O menino": "1°", "chuta": "2°", "a bola": "3°"},
                    "instructions": "Arraste na ordem certa.",
                },
                "apoios": ["bola", "parque"],
                "roteiro": "Voz pausada. Quem… faz… o quê.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "O que o menino faz na cena? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["⚽ Chuta a bola", "😴 Dorme"],
                    "correct_answer": {"correct_zone": "⚽ Chuta a bola"},
                    "instructions": "Toque.",
                },
                "apoios": ["bola"],
                "roteiro": "Voz muito lenta. CHUTAR a bola… [aguarda toque]",
            },
        },
    },

    # ══════════════════ MATEMÁTICA ═══════════════════════════════════════════

    {
        "code": "AT-MAT-01",
        "title": "Adição com maçãs",
        "discipline": "Matemática",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Somar quantidades em uma situação.",
        "activity_type": "essay",
        "statement": "Tinha 7 maçãs e ganhei mais 5.",
        "question": "Quantas maçãs tenho agora? Mostre a conta.",
        "expected_answer": "12",
        "versoes": {
            "padrao": {
                "fmt": "diss",
                "enun": "Tinha 7 maçãs e ganhei mais 5. Quantas maçãs tenho agora? Mostre a conta.",
                "dados": {},
                "apoios": ["maçã"],
                "roteiro": "Tom natural. Lê o problema.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "Tinha 7 maçãs e ganhei 5. 7 + 5 = ?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["12", "11", "13", "2"],
                    "correct_answer": {"correct_zone": "12"},
                    "instructions": "Escolha o resultado.",
                },
                "apoios": ["maçã"],
                "roteiro": "Voz clara. Lê a conta e as opções.",
            },
            "p2": {
                "fmt": "mc",
                "enun": "🍎🍎🍎🍎🍎🍎🍎 e mais 🍎🍎🍎🍎🍎. Quantas maçãs ao todo?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["12 🍎", "7 🍎", "5 🍎"],
                    "correct_answer": {"correct_zone": "12 🍎"},
                    "instructions": "Conte tudo e escolha.",
                },
                "apoios": ["maçã"],
                "roteiro": "Voz pausada. Conte tudo… [pausa] quantas?",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Toque no grupo de maçãs que tem MAIS.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🍎🍎🍎🍎🍎 Cinco", "🍎🍎 Duas"],
                    "correct_answer": {"correct_zone": "🍎🍎🍎🍎🍎 Cinco"},
                    "instructions": "Toque.",
                },
                "apoios": ["maçã"],
                "roteiro": "Voz muito lenta. MAIS maçãs… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-MAT-02",
        "title": "Fração: a metade da pizza",
        "discipline": "Matemática",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Reconhecer a metade (1/2) de um todo.",
        "activity_type": "multiple_choice",
        "statement": "Uma pizza foi dividida em 2 partes iguais. 🍕",
        "question": "Cada parte representa quanto da pizza?",
        "expected_answer": "1/2",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Uma pizza foi dividida em 2 partes iguais. Cada parte representa quanto da pizza?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["1/2 (a metade)", "1/4", "2 inteiras", "1/8"],
                    "correct_answer": {"correct_zone": "1/2 (a metade)"},
                    "instructions": "Escolha a fração correta.",
                },
                "apoios": ["pizza"],
                "roteiro": "Tom natural. Lê uma vez.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "A pizza tem 8 fatias. A METADE dela são quantas fatias?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["4 fatias", "8 fatias", "2 fatias"],
                    "correct_answer": {"correct_zone": "4 fatias"},
                    "instructions": "Escolha a metade.",
                },
                "apoios": ["pizza"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste para cada prato a parte certa da pizza.",
                "dados": {
                    "items": ["🍕 metade", "🍕🍕 inteira"],
                    "zones": [{"name": "Prato da METADE"}, {"name": "Prato da pizza INTEIRA"}],
                    "correct_answer": {"🍕 metade": "Prato da METADE", "🍕🍕 inteira": "Prato da pizza INTEIRA"},
                    "instructions": "Arraste para o prato certo.",
                },
                "apoios": ["pizza"],
                "roteiro": "Voz pausada. METADE… inteira… mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Toque na METADE da pizza.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🍕 Metade", "🍕🍕 Inteira"],
                    "correct_answer": {"correct_zone": "🍕 Metade"},
                    "instructions": "Toque.",
                },
                "apoios": ["pizza"],
                "roteiro": "Voz muito lenta. METADE… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-MAT-03",
        "title": "Formas geométricas",
        "discipline": "Matemática",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Relacionar a forma ao seu nome e ao número de lados.",
        "activity_type": "multiple_choice",
        "statement": "Triângulo (3 lados), quadrado (4 lados), círculo (0 lados).",
        "question": "Quantos lados tem um triângulo?",
        "expected_answer": "3",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Quantos lados tem um triângulo?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["3", "4", "1", "0"],
                    "correct_answer": {"correct_zone": "3"},
                    "instructions": "Escolha o número de lados.",
                },
                "apoios": ["triângulo"],
                "roteiro": "Tom natural. Lê.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "Qual destas formas tem exatamente 3 lados?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Triângulo", "Quadrado", "Círculo"],
                    "correct_answer": {"correct_zone": "Triângulo"},
                    "instructions": "Escolha a forma com 3 lados.",
                },
                "apoios": ["triângulo"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste cada forma para o seu nome.",
                "dados": {
                    "items": ["🔺", "⬛", "⚫"],
                    "zones": [{"name": "Triângulo"}, {"name": "Quadrado"}, {"name": "Círculo"}],
                    "correct_answer": {"🔺": "Triângulo", "⬛": "Quadrado", "⚫": "Círculo"},
                    "instructions": "Arraste a forma para o nome.",
                },
                "apoios": ["triângulo", "quadrado", "círculo"],
                "roteiro": "Voz pausada. Triângulo… quadrado… círculo…",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Toque no TRIÂNGULO.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🔺 Triângulo", "⬛ Quadrado"],
                    "correct_answer": {"correct_zone": "🔺 Triângulo"},
                    "instructions": "Toque.",
                },
                "apoios": ["triângulo"],
                "roteiro": "Voz muito lenta. TRIÂNGULO… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-MAT-04",
        "title": "Padrão de repetição de cores",
        "discipline": "Matemática",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Descobrir o que continua um padrão.",
        "activity_type": "multiple_choice",
        "statement": "Padrão: 🔴🔵🔴🔵🔴🔵",
        "question": "Se o padrão continuar, qual será a 7ª figura?",
        "expected_answer": "🔴 vermelho",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Observe o padrão 🔴🔵🔴🔵🔴🔵. Se ele continuar, qual será a 7ª figura?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🔴 vermelho", "🔵 azul", "🟢 verde"],
                    "correct_answer": {"correct_zone": "🔴 vermelho"},
                    "instructions": "Escolha a 7ª figura.",
                },
                "apoios": ["vermelho", "azul"],
                "roteiro": "Tom natural. Lê o padrão e as opções.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "No padrão 🔴🔵🔴🔵, qual cor vem logo depois?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🔴 vermelho", "🔵 azul", "🟢 verde"],
                    "correct_answer": {"correct_zone": "🔴 vermelho"},
                    "instructions": "Qual vem depois?",
                },
                "apoios": ["vermelho", "azul"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Continue o padrão 🔴🔵🔴🔵: arraste a figura que vem a seguir.",
                "dados": {
                    "items": ["🔴 Vermelho", "🔵 Azul"],
                    "zones": [{"name": "Vem depois ✓"}, {"name": "Não cabe agora"}],
                    "correct_answer": {"🔴 Vermelho": "Vem depois ✓", "🔵 Azul": "Não cabe agora"},
                    "instructions": "Arraste a que vem depois.",
                },
                "apoios": ["vermelho", "azul"],
                "roteiro": "Voz pausada. Vermelho, azul… [pausa] depois?",
            },
            "p3": {
                "fmt": "toque",
                "enun": "No padrão 🔴🔵🔴🔵, toque na cor que vem depois do AZUL.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🔴 Vermelho", "🔵 Azul"],
                    "correct_answer": {"correct_zone": "🔴 Vermelho"},
                    "instructions": "Toque.",
                },
                "apoios": ["vermelho", "azul"],
                "roteiro": "Voz muito lenta. Depois do azul… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-MAT-05",
        "title": "Dinheiro: somar valores",
        "discipline": "Matemática",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Somar valores em reais.",
        "activity_type": "multiple_choice",
        "statement": "Uma nota de R$10 e uma nota de R$5.",
        "question": "Quanto tenho ao todo?",
        "expected_answer": "R$15",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Tenho 1 nota de R$10 e 1 nota de R$5. Quanto tenho ao todo?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["R$ 15", "R$ 105", "R$ 5", "R$ 50"],
                    "correct_answer": {"correct_zone": "R$ 15"},
                    "instructions": "Escolha o total.",
                },
                "apoios": ["dinheiro"],
                "roteiro": "Tom natural. Lê.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "R$10 + R$5 = ?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["R$ 15", "R$ 510", "R$ 5"],
                    "correct_answer": {"correct_zone": "R$ 15"},
                    "instructions": "Escolha o resultado.",
                },
                "apoios": ["dinheiro"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste cada nota para o seu valor.",
                "dados": {
                    "items": ["💵 dez reais", "💵 cinco reais"],
                    "zones": [{"name": "R$ 10"}, {"name": "R$ 5"}],
                    "correct_answer": {"💵 dez reais": "R$ 10", "💵 cinco reais": "R$ 5"},
                    "instructions": "Arraste a nota para o valor.",
                },
                "apoios": ["dinheiro"],
                "roteiro": "Voz pausada. Dez… cinco… mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Toque na nota que vale MAIS.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["💵 R$ 10", "🪙 R$ 5"],
                    "correct_answer": {"correct_zone": "💵 R$ 10"},
                    "instructions": "Toque.",
                },
                "apoios": ["dinheiro", "moeda"],
                "roteiro": "Voz muito lenta. MAIS dinheiro… [aguarda toque]",
            },
        },
    },

    # ══════════════════ CIÊNCIAS ═══════════════════════════════════════════

    {
        "code": "AT-CIE-01",
        "title": "Vivo ou não vivo",
        "discipline": "Ciências",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Classificar em ser vivo e não vivo.",
        "activity_type": "association",
        "statement": "Seres vivos nascem, crescem e se reproduzem.",
        "question": "Qual destes é um ser VIVO?",
        "expected_answer": "Árvore, gato",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Seres vivos nascem, crescem e se reproduzem. Qual destes é um ser VIVO?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Árvore", "Pedra", "Carro", "Cadeira"],
                    "correct_answer": {"correct_zone": "Árvore"},
                    "instructions": "Escolha o ser vivo.",
                },
                "apoios": ["árvore", "pedra"],
                "roteiro": "Tom natural. Lê.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "Qual destes cresce e respira (é vivo)?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Gato", "Pedra", "Carro"],
                    "correct_answer": {"correct_zone": "Gato"},
                    "instructions": "Escolha o ser vivo.",
                },
                "apoios": ["gato"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste cada um para VIVO ou NÃO VIVO.",
                "dados": {
                    "items": ["🐶 gato", "🌳 árvore", "🪨 pedra", "🚗 carro"],
                    "zones": [{"name": "Vivo"}, {"name": "Não vivo"}],
                    "correct_answer": {"🐶 gato": "Vivo", "🌳 árvore": "Vivo", "🪨 pedra": "Não vivo", "🚗 carro": "Não vivo"},
                    "instructions": "Arraste para vivo ou não vivo.",
                },
                "apoios": ["gato", "árvore"],
                "roteiro": "Voz pausada. Vivo… não vivo… mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Toque no ser VIVO.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🐶 Gato", "🪨 Pedra"],
                    "correct_answer": {"correct_zone": "🐶 Gato"},
                    "instructions": "Toque.",
                },
                "apoios": ["gato"],
                "roteiro": "Voz muito lenta. VIVO… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-CIE-02",
        "title": "Partes da planta",
        "discipline": "Ciências",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Localizar raiz, caule e folha.",
        "activity_type": "association",
        "statement": "A planta tem raiz (embaixo da terra), caule (meio) e folha (em cima). 🌱",
        "question": "Qual parte da planta fica embaixo da terra e busca água?",
        "expected_answer": "Raiz",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Qual parte da planta fica embaixo da terra e busca água?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Raiz", "Folha", "Flor", "Caule"],
                    "correct_answer": {"correct_zone": "Raiz"},
                    "instructions": "Escolha a parte.",
                },
                "apoios": ["planta"],
                "roteiro": "Tom natural. Lê.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "Na planta, qual parte fica EMBAIXO da terra?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Raiz", "Folha", "Flor"],
                    "correct_answer": {"correct_zone": "Raiz"},
                    "instructions": "Escolha a parte.",
                },
                "apoios": ["planta"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste cada nome para a posição na planta 🌱.",
                "dados": {
                    "items": ["Raiz", "Caule", "Folha"],
                    "zones": [{"name": "⬇️ Embaixo"}, {"name": "➡️ No meio"}, {"name": "⬆️ Em cima"}],
                    "correct_answer": {"Raiz": "⬇️ Embaixo", "Caule": "➡️ No meio", "Folha": "⬆️ Em cima"},
                    "instructions": "Arraste para a posição certa.",
                },
                "apoios": ["planta"],
                "roteiro": "Voz pausada. Raiz embaixo… caule meio… folha cima.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "As folhas ficam em cima ou embaixo? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["⬆️ Em cima", "⬇️ Embaixo"],
                    "correct_answer": {"correct_zone": "⬆️ Em cima"},
                    "instructions": "Toque.",
                },
                "apoios": ["planta", "folha"],
                "roteiro": "Voz muito lenta. FOLHA… em cima… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-CIE-03",
        "title": "Cadeia alimentar",
        "discipline": "Ciências",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Ordenar quem come quem.",
        "activity_type": "drag_drop",
        "statement": "Cadeia: capim 🌿 → gafanhoto 🦗 → sapo 🐸 → cobra 🐍.",
        "question": "Ordene a cadeia alimentar (do que é comido para quem come).",
        "expected_answer": "capim, gafanhoto, sapo, cobra",
        "versoes": {
            "padrao": {
                "fmt": "seq",
                "enun": "Ordene a cadeia alimentar (do que é comido para quem come). Numere de 1 a 4.",
                "dados": {
                    "items": ["Sapo", "Capim", "Cobra", "Gafanhoto"],
                    "zones": [],
                    "correct_answer": {"Capim": "1°", "Gafanhoto": "2°", "Sapo": "3°", "Cobra": "4°"},
                    "instructions": "Numere de 1 a 4.",
                },
                "apoios": ["capim", "sapo"],
                "roteiro": "Tom natural. Lê os elos.",
            },
            "p1": {
                "fmt": "seq",
                "enun": "Ordene a cadeia: capim, gafanhoto e sapo. Numere de 1 a 3.",
                "dados": {
                    "items": ["Gafanhoto", "Capim", "Sapo"],
                    "zones": [],
                    "correct_answer": {"Capim": "1°", "Gafanhoto": "2°", "Sapo": "3°"},
                    "instructions": "Numere de 1 a 3.",
                },
                "apoios": ["capim", "sapo"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "seq",
                "enun": "Toque na ordem certa: quem come quem.",
                "dados": {
                    "items": ["🌿 capim", "🦗 gafanhoto", "🐸 sapo"],
                    "zones": [],
                    "correct_answer": {"🌿 capim": "1°", "🦗 gafanhoto": "2°", "🐸 sapo": "3°"},
                    "instructions": "Toque na ordem certa.",
                },
                "apoios": ["capim", "gafanhoto", "sapo"],
                "roteiro": "Voz pausada. Primeiro o capim… depois…",
            },
            "p3": {
                "fmt": "toque",
                "enun": "O gafanhoto 🦗 come o quê? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🌿 Capim", "🐸 Sapo"],
                    "correct_answer": {"correct_zone": "🌿 Capim"},
                    "instructions": "Toque.",
                },
                "apoios": ["gafanhoto", "capim"],
                "roteiro": "Voz muito lenta. Gafanhoto come… CAPIM… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-CIE-04",
        "title": "Estados da água",
        "discipline": "Ciências",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Relacionar gelo, água e vapor à temperatura.",
        "activity_type": "multiple_choice",
        "statement": "A água — gelo (frio) ↔ vapor (quente). 🧊 💧 ♨️",
        "question": "A água vira GELO quando a temperatura fica muito:",
        "expected_answer": "baixa (fria)",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "A água vira GELO quando a temperatura fica muito:",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["baixa (fria)", "alta (quente)", "doce", "salgada"],
                    "correct_answer": {"correct_zone": "baixa (fria)"},
                    "instructions": "Escolha a temperatura.",
                },
                "apoios": ["gelo"],
                "roteiro": "Tom natural. Lê.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "Quando a água ferve bem quente na panela, ela vira:",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Vapor", "Gelo", "Pedra"],
                    "correct_answer": {"correct_zone": "Vapor"},
                    "instructions": "Escolha o estado.",
                },
                "apoios": ["vapor"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste cada estado da água para quente ou frio.",
                "dados": {
                    "items": ["🧊 gelo", "♨️ vapor"],
                    "zones": [{"name": "❄️ Frio"}, {"name": "🔥 Quente"}],
                    "correct_answer": {"🧊 gelo": "❄️ Frio", "♨️ vapor": "🔥 Quente"},
                    "instructions": "Arraste para quente ou frio.",
                },
                "apoios": ["gelo", "vapor"],
                "roteiro": "Voz pausada. Frio… quente… mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "O gelo 🧊 é quente ou frio? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["❄️ Frio", "🔥 Quente"],
                    "correct_answer": {"correct_zone": "❄️ Frio"},
                    "instructions": "Toque.",
                },
                "apoios": ["gelo"],
                "roteiro": "Voz muito lenta. GELO… frio… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-CIE-05",
        "title": "Sentidos e órgãos",
        "discipline": "Ciências",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Associar cada sentido ao seu órgão.",
        "activity_type": "association",
        "statement": "Ver ↔ olhos 👁️, ouvir ↔ ouvido 👂, cheirar ↔ nariz 👃.",
        "question": "Usamos os olhos principalmente para:",
        "expected_answer": "Enxergar",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Usamos os olhos principalmente para:",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Enxergar", "Ouvir", "Cheirar", "Tocar"],
                    "correct_answer": {"correct_zone": "Enxergar"},
                    "instructions": "Escolha a função.",
                },
                "apoios": ["olhos", "ouvido"],
                "roteiro": "Tom natural. Lê.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "Com o nariz, nós:",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Cheiramos", "Vemos", "Ouvimos"],
                    "correct_answer": {"correct_zone": "Cheiramos"},
                    "instructions": "Escolha a função.",
                },
                "apoios": ["nariz"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "par",
                "enun": "Ligue cada sentido ao órgão certo.",
                "dados": {
                    "items": ["ver", "ouvir", "cheirar"],
                    "zones": [{"name": "👁️"}, {"name": "👂"}, {"name": "👃"}],
                    "correct_answer": {"ver": "👁️", "ouvir": "👂", "cheirar": "👃"},
                    "instructions": "Arraste o sentido para o órgão.",
                },
                "apoios": ["olhos", "ouvido", "nariz"],
                "roteiro": "Voz pausada. Ver… ouvir… cheirar…",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Para VER, usamos os...? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["👀 Olhos", "👂 Orelhas"],
                    "correct_answer": {"correct_zone": "👀 Olhos"},
                    "instructions": "Toque.",
                },
                "apoios": ["olhos"],
                "roteiro": "Voz muito lenta. VER… olhos… [aguarda toque]",
            },
        },
    },

    # ══════════════════ HISTÓRIA ═══════════════════════════════════════════

    {
        "code": "AT-HIS-01",
        "title": "Linha do tempo da vida",
        "discipline": "História",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Ordenar as fases da vida humana.",
        "activity_type": "drag_drop",
        "statement": "Bebê 👶 → criança 🧒 → adolescente → adulto 🧑.",
        "question": "Ordene as fases da vida, do mais novo ao mais velho.",
        "expected_answer": "bebê, criança, adolescente, adulto",
        "versoes": {
            "padrao": {
                "fmt": "seq",
                "enun": "Ordene as fases da vida, do mais novo ao mais velho. Numere de 1 a 4.",
                "dados": {
                    "items": ["Adulto", "Bebê", "Adolescente", "Criança"],
                    "zones": [],
                    "correct_answer": {"Bebê": "1°", "Criança": "2°", "Adolescente": "3°", "Adulto": "4°"},
                    "instructions": "Numere de 1 a 4.",
                },
                "apoios": ["bebê", "adulto"],
                "roteiro": "Tom natural. Lê.",
            },
            "p1": {
                "fmt": "seq",
                "enun": "Coloque em ordem: bebê, criança e adulto. Numere de 1 a 3.",
                "dados": {
                    "items": ["Adulto", "Bebê", "Criança"],
                    "zones": [],
                    "correct_answer": {"Bebê": "1°", "Criança": "2°", "Adulto": "3°"},
                    "instructions": "Numere de 1 a 3.",
                },
                "apoios": ["bebê", "adulto"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "seq",
                "enun": "Toque na ordem, do menor ao maior.",
                "dados": {
                    "items": ["👶 bebê", "🧒 criança", "🧑 adulto"],
                    "zones": [],
                    "correct_answer": {"👶 bebê": "1°", "🧒 criança": "2°", "🧑 adulto": "3°"},
                    "instructions": "Toque na ordem.",
                },
                "apoios": ["bebê", "adulto"],
                "roteiro": "Voz pausada. Antes… depois…",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Quem é o mais NOVO? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["👶 Bebê", "🧑 Adulto"],
                    "correct_answer": {"correct_zone": "👶 Bebê"},
                    "instructions": "Toque.",
                },
                "apoios": ["bebê"],
                "roteiro": "Voz muito lenta. Mais NOVO… bebê… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-HIS-02",
        "title": "Transporte antigo e moderno",
        "discipline": "História",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Diferenciar transporte antigo de moderno.",
        "activity_type": "association",
        "statement": "Antigos: carroça 🐎, canoa 🛶. Modernos: avião ✈️, carro 🚗.",
        "question": "Qual destes meios de transporte é o mais ANTIGO?",
        "expected_answer": "Carroça",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Qual destes meios de transporte é o mais ANTIGO?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Carroça", "Avião", "Carro", "Metrô"],
                    "correct_answer": {"correct_zone": "Carroça"},
                    "instructions": "Escolha o mais antigo.",
                },
                "apoios": ["carroça", "avião"],
                "roteiro": "Tom natural. Lê.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "Qual destes é um transporte MODERNO (de hoje)?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Avião", "Carroça", "Canoa"],
                    "correct_answer": {"correct_zone": "Avião"},
                    "instructions": "Escolha o moderno.",
                },
                "apoios": ["avião"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste cada transporte para ANTIGO ou MODERNO.",
                "dados": {
                    "items": ["🐎 carroça", "🛶 canoa", "✈️ avião", "🚗 carro"],
                    "zones": [{"name": "Antigo"}, {"name": "Moderno"}],
                    "correct_answer": {"🐎 carroça": "Antigo", "🛶 canoa": "Antigo", "✈️ avião": "Moderno", "🚗 carro": "Moderno"},
                    "instructions": "Arraste para antigo ou moderno.",
                },
                "apoios": ["carroça", "avião"],
                "roteiro": "Voz pausada. Antigo… moderno… mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Toque no transporte ANTIGO.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🐎 Carroça", "✈️ Avião"],
                    "correct_answer": {"correct_zone": "🐎 Carroça"},
                    "instructions": "Toque.",
                },
                "apoios": ["carroça"],
                "roteiro": "Voz muito lenta. ANTIGO… carroça… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-HIS-03",
        "title": "Regras da comunidade",
        "discipline": "História",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Reconhecer a atitude correta no espaço comum.",
        "activity_type": "essay",
        "statement": "O lixo deve ir na lixeira 🗑️ (não no chão).",
        "question": "Por que jogar o lixo na lixeira é importante para toda a comunidade?",
        "expected_answer": "Mantém a cidade limpa e organizada.",
        "versoes": {
            "padrao": {
                "fmt": "diss",
                "enun": "Por que jogar o lixo na lixeira é importante para toda a comunidade? Escreva 2 motivos.",
                "dados": {},
                "apoios": ["lixeira"],
                "roteiro": "Tom natural. Lê a pergunta.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "Para manter a cidade limpa, onde devemos jogar o lixo?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Na lixeira", "No chão", "No rio", "Na calçada"],
                    "correct_answer": {"correct_zone": "Na lixeira"},
                    "instructions": "Escolha o lugar certo.",
                },
                "apoios": ["lixeira"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "toque",
                "enun": "Qual atitude está CERTA? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🗑️ Jogar na lixeira", "🌫️ Jogar no chão"],
                    "correct_answer": {"correct_zone": "🗑️ Jogar na lixeira"},
                    "instructions": "Toque.",
                },
                "apoios": ["lixeira"],
                "roteiro": "Voz pausada. Lixeira… certo… [aguarda toque]",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Onde o lixo deve ir? Toque na lixeira.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🗑️ Lixeira", "🍎 Maçã"],
                    "correct_answer": {"correct_zone": "🗑️ Lixeira"},
                    "instructions": "Toque.",
                },
                "apoios": ["lixeira"],
                "roteiro": "Voz muito lenta. LIXEIRA… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-HIS-04",
        "title": "Símbolos nacionais do Brasil",
        "discipline": "História",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Reconhecer símbolos do Brasil.",
        "activity_type": "multiple_choice",
        "statement": "Bandeira 🇧🇷 (verde e amarelo) e hino 🎵.",
        "question": "Qual destes é um símbolo nacional do Brasil?",
        "expected_answer": "A bandeira",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Qual destes é um símbolo nacional do Brasil?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["A bandeira", "O sofá", "O celular", "A bicicleta"],
                    "correct_answer": {"correct_zone": "A bandeira"},
                    "instructions": "Escolha o símbolo.",
                },
                "apoios": ["bandeira"],
                "roteiro": "Tom natural. Lê.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "As cores principais da bandeira do Brasil são:",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Verde e amarelo", "Roxo e rosa", "Preto e cinza"],
                    "correct_answer": {"correct_zone": "Verde e amarelo"},
                    "instructions": "Escolha as cores.",
                },
                "apoios": ["bandeira"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "par",
                "enun": "Ligue cada símbolo ao seu nome.",
                "dados": {
                    "items": ["🇧🇷", "🎵"],
                    "zones": [{"name": "bandeira"}, {"name": "hino"}],
                    "correct_answer": {"🇧🇷": "bandeira", "🎵": "hino"},
                    "instructions": "Ligue símbolo ao nome.",
                },
                "apoios": ["bandeira", "hino"],
                "roteiro": "Voz pausada. Bandeira… hino…",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Toque na BANDEIRA do Brasil.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🇧🇷 Bandeira", "🎂 Bolo"],
                    "correct_answer": {"correct_zone": "🇧🇷 Bandeira"},
                    "instructions": "Toque.",
                },
                "apoios": ["bandeira"],
                "roteiro": "Voz muito lenta. BANDEIRA… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-HIS-05",
        "title": "Profissões e ferramentas",
        "discipline": "História",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Associar profissional ao que ele usa.",
        "activity_type": "association",
        "statement": "Médico 🧑‍⚕️ (estetoscópio / seringa) e bombeiro 🧑‍🚒 (extintor / mangueira).",
        "question": "Qual profissional apaga incêndios?",
        "expected_answer": "Bombeiro",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Qual profissional apaga incêndios?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Bombeiro", "Médico", "Padeiro", "Professor"],
                    "correct_answer": {"correct_zone": "Bombeiro"},
                    "instructions": "Escolha o profissional.",
                },
                "apoios": ["bombeiro", "médico"],
                "roteiro": "Tom natural. Lê.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "O médico usa qual destes no trabalho?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Estetoscópio 🩺", "Mangueira 🧯", "Giz"],
                    "correct_answer": {"correct_zone": "Estetoscópio 🩺"},
                    "instructions": "Escolha a ferramenta.",
                },
                "apoios": ["médico", "estetoscópio"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste cada ferramenta para o profissional certo.",
                "dados": {
                    "items": ["💉 seringa", "🩺 estetoscópio", "🧯 extintor", "🚒 caminhão"],
                    "zones": [{"name": "🧑‍⚕️ Médico"}, {"name": "🧑‍🚒 Bombeiro"}],
                    "correct_answer": {"💉 seringa": "🧑‍⚕️ Médico", "🩺 estetoscópio": "🧑‍⚕️ Médico", "🧯 extintor": "🧑‍🚒 Bombeiro", "🚒 caminhão": "🧑‍🚒 Bombeiro"},
                    "instructions": "Arraste para o profissional.",
                },
                "apoios": ["médico", "bombeiro"],
                "roteiro": "Voz pausada. Médico… bombeiro… mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Quem usa a mangueira para apagar fogo? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🧑‍🚒 Bombeiro", "🧑‍⚕️ Médico"],
                    "correct_answer": {"correct_zone": "🧑‍🚒 Bombeiro"},
                    "instructions": "Toque.",
                },
                "apoios": ["bombeiro"],
                "roteiro": "Voz muito lenta. BOMBEIRO… [aguarda toque]",
            },
        },
    },

    # ══════════════════ GEOGRAFIA ═════════════════════════════════════════

    {
        "code": "AT-GEO-01",
        "title": "Posição: em cima e embaixo",
        "discipline": "Geografia",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Usar referências de posição (acima / abaixo).",
        "activity_type": "multiple_choice",
        "statement": "O pássaro 🐦 voa em cima; o peixe 🐟 nada embaixo (na água).",
        "question": "Em relação à água do mar, o pássaro que voa está:",
        "expected_answer": "Acima",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Em relação à água do mar, o pássaro que voa está:",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Acima", "Abaixo", "Dentro"],
                    "correct_answer": {"correct_zone": "Acima"},
                    "instructions": "Escolha a posição.",
                },
                "apoios": ["pássaro", "peixe"],
                "roteiro": "Tom natural. Lê.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "O peixe nada acima ou abaixo da superfície da água?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Abaixo", "Acima"],
                    "correct_answer": {"correct_zone": "Abaixo"},
                    "instructions": "Escolha a posição.",
                },
                "apoios": ["peixe"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Coloque cada um no lugar: arraste o pássaro e o peixe.",
                "dados": {
                    "items": ["🐦 pássaro", "🐟 peixe"],
                    "zones": [{"name": "⬆️ Em cima (céu)"}, {"name": "⬇️ Embaixo (água)"}],
                    "correct_answer": {"🐦 pássaro": "⬆️ Em cima (céu)", "🐟 peixe": "⬇️ Embaixo (água)"},
                    "instructions": "Arraste para a posição certa.",
                },
                "apoios": ["pássaro", "peixe"],
                "roteiro": "Voz pausada. Cima… baixo… mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "O pássaro 🐦 está em cima ou embaixo? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["⬆️ Em cima", "⬇️ Embaixo"],
                    "correct_answer": {"correct_zone": "⬆️ Em cima"},
                    "instructions": "Toque.",
                },
                "apoios": ["pássaro"],
                "roteiro": "Voz muito lenta. Pássaro… EM CIMA… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-GEO-02",
        "title": "Paisagem natural ou construída",
        "discipline": "Geografia",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Diferenciar o que é da natureza do que é feito por pessoas.",
        "activity_type": "association",
        "statement": "Naturais: árvore 🌳, montanha ⛰️. Construídos: prédio 🏢, ponte 🌉.",
        "question": "Qual destas é uma paisagem NATURAL (não feita por pessoas)?",
        "expected_answer": "Floresta",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Qual destas é uma paisagem NATURAL (não feita por pessoas)?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Floresta", "Prédio", "Ponte", "Rua"],
                    "correct_answer": {"correct_zone": "Floresta"},
                    "instructions": "Escolha a paisagem natural.",
                },
                "apoios": ["árvore", "prédio"],
                "roteiro": "Tom natural. Lê.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "O prédio foi feito por quem?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Pelas pessoas", "Pela natureza", "Pelos animais"],
                    "correct_answer": {"correct_zone": "Pelas pessoas"},
                    "instructions": "Escolha quem fez.",
                },
                "apoios": ["prédio"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste cada paisagem para NATURAL ou CONSTRUÍDA.",
                "dados": {
                    "items": ["🌳 árvore", "⛰️ montanha", "🏢 prédio", "🌉 ponte"],
                    "zones": [{"name": "Natural"}, {"name": "Construída"}],
                    "correct_answer": {"🌳 árvore": "Natural", "⛰️ montanha": "Natural", "🏢 prédio": "Construída", "🌉 ponte": "Construída"},
                    "instructions": "Arraste para natural ou construída.",
                },
                "apoios": ["árvore", "prédio"],
                "roteiro": "Voz pausada. Natural… construída… mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Toque na paisagem NATURAL.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🌳 Árvore", "🏢 Prédio"],
                    "correct_answer": {"correct_zone": "🌳 Árvore"},
                    "instructions": "Toque.",
                },
                "apoios": ["árvore"],
                "roteiro": "Voz muito lenta. NATURAL… árvore… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-GEO-03",
        "title": "Clima e o que levar",
        "discipline": "Geografia",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Relacionar o clima ao item adequado.",
        "activity_type": "association",
        "statement": "Chuva ☔ → guarda-chuva ☂️. Frio ❄️ → casaco 🧥. Sol ☀️ → óculos 🕶️.",
        "question": "Em um dia de chuva, o que é mais útil levar?",
        "expected_answer": "Guarda-chuva",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Em um dia de chuva, o que é mais útil levar?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Guarda-chuva", "Óculos de sol", "Ventilador", "Sorvete"],
                    "correct_answer": {"correct_zone": "Guarda-chuva"},
                    "instructions": "Escolha o item.",
                },
                "apoios": ["guarda-chuva", "chuva"],
                "roteiro": "Tom natural. Lê.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "Quando faz muito frio, o que vestimos?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Casaco", "Regata", "Chinelo"],
                    "correct_answer": {"correct_zone": "Casaco"},
                    "instructions": "Escolha a roupa.",
                },
                "apoios": ["casaco"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste cada item para o clima certo.",
                "dados": {
                    "items": ["☂️ guarda-chuva", "🧥 casaco", "🕶️ óculos"],
                    "zones": [{"name": "☔ Chuva"}, {"name": "❄️ Frio"}, {"name": "☀️ Sol"}],
                    "correct_answer": {"☂️ guarda-chuva": "☔ Chuva", "🧥 casaco": "❄️ Frio", "🕶️ óculos": "☀️ Sol"},
                    "instructions": "Arraste para o clima certo.",
                },
                "apoios": ["guarda-chuva", "casaco"],
                "roteiro": "Voz pausada. Chuva… frio… sol… mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Está chovendo ☔. Toque no que ajuda.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["☂️ Guarda-chuva", "🍦 Sorvete"],
                    "correct_answer": {"correct_zone": "☂️ Guarda-chuva"},
                    "instructions": "Toque.",
                },
                "apoios": ["guarda-chuva"],
                "roteiro": "Voz muito lenta. CHUVA… guarda-chuva… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-GEO-04",
        "title": "Mapa e legenda",
        "discipline": "Geografia",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Ler símbolos de uma legenda de mapa.",
        "activity_type": "association",
        "statement": "Legenda: 🏥 hospital, 🏫 escola, 🏪 mercado.",
        "question": "Na legenda do mapa, o símbolo 🏥 indica qual lugar?",
        "expected_answer": "Hospital",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Na legenda do mapa, o símbolo 🏥 indica qual lugar?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Hospital", "Escola", "Mercado", "Praça"],
                    "correct_answer": {"correct_zone": "Hospital"},
                    "instructions": "Escolha o lugar.",
                },
                "apoios": ["hospital", "escola"],
                "roteiro": "Tom natural. Lê.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "Para achar a escola no mapa, qual símbolo procuramos?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🏫", "🏥", "🏪"],
                    "correct_answer": {"correct_zone": "🏫"},
                    "instructions": "Escolha o símbolo.",
                },
                "apoios": ["escola"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste cada símbolo ao seu lugar.",
                "dados": {
                    "items": ["🏥", "🏫", "🏪"],
                    "zones": [{"name": "Hospital"}, {"name": "Escola"}, {"name": "Mercado"}],
                    "correct_answer": {"🏥": "Hospital", "🏫": "Escola", "🏪": "Mercado"},
                    "instructions": "Arraste para o lugar.",
                },
                "apoios": ["hospital", "escola", "mercado"],
                "roteiro": "Voz pausada. Hospital… escola… mercado…",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Onde se cuida de quem está doente? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["🏥 Hospital", "🏫 Escola"],
                    "correct_answer": {"correct_zone": "🏥 Hospital"},
                    "instructions": "Toque.",
                },
                "apoios": ["hospital"],
                "roteiro": "Voz muito lenta. Doente vai ao… HOSPITAL… [aguarda toque]",
            },
        },
    },

    {
        "code": "AT-GEO-05",
        "title": "Transporte por onde se move",
        "discipline": "Geografia",
        "school_year": "até 7º ano",
        "pedagogical_objective": "Relacionar o transporte ao seu caminho (água, ar, terra).",
        "activity_type": "association",
        "statement": "Barco ⛵ (água), avião ✈️ (ar), carro 🚗 (terra).",
        "question": "Qual destes transportes se desloca pela ÁGUA?",
        "expected_answer": "Barco",
        "versoes": {
            "padrao": {
                "fmt": "mc",
                "enun": "Qual destes transportes se desloca pela ÁGUA?",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Barco", "Avião", "Carro", "Trem"],
                    "correct_answer": {"correct_zone": "Barco"},
                    "instructions": "Escolha o transporte.",
                },
                "apoios": ["barco", "avião"],
                "roteiro": "Tom natural. Lê.",
            },
            "p1": {
                "fmt": "mc",
                "enun": "O avião se desloca principalmente pelo:",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["Ar", "Mar", "Trilho"],
                    "correct_answer": {"correct_zone": "Ar"},
                    "instructions": "Escolha o caminho.",
                },
                "apoios": ["avião"],
                "roteiro": "Voz clara. Lê.",
            },
            "p2": {
                "fmt": "dnd",
                "enun": "Arraste cada transporte ao seu caminho.",
                "dados": {
                    "items": ["⛵ barco", "✈️ avião", "🚗 carro"],
                    "zones": [{"name": "💧 Água"}, {"name": "☁️ Ar"}, {"name": "🛣️ Terra"}],
                    "correct_answer": {"⛵ barco": "💧 Água", "✈️ avião": "☁️ Ar", "🚗 carro": "🛣️ Terra"},
                    "instructions": "Arraste para o caminho.",
                },
                "apoios": ["barco", "avião", "carro"],
                "roteiro": "Voz pausada. Água… ar… terra… mova.",
            },
            "p3": {
                "fmt": "toque",
                "enun": "Qual transporte VOA pelo ar? Toque.",
                "dados": {
                    "items": ["Minha resposta"],
                    "zones": ["✈️ Avião", "⛵ Barco"],
                    "correct_answer": {"correct_zone": "✈️ Avião"},
                    "instructions": "Toque.",
                },
                "apoios": ["avião"],
                "roteiro": "Voz muito lenta. VOA… avião… [aguarda toque]",
            },
        },
    },
]


# ─── Seed functions ───────────────────────────────────────────────────────────

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
    profiles = {}
    for key, name in profile_names.items():
        profile = session.exec(
            select(StudentProfile).where(StudentProfile.name == name)
        ).first()
        profiles[key] = profile  # may be None if not seeded yet
    return profiles


def _seed_adaptations(
    session: Session,
    activity: Activity,
    versoes: dict,
    profiles: dict,
) -> int:
    count = 0
    for version_key, versao in versoes.items():
        profile_id = None
        if version_key != "padrao":
            profile = profiles.get(version_key)
            if profile:
                profile_id = profile.id

        # Skip if adaptation already exists for this activity + profile combination
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


def _seed_25_activities(session: Session, teacher: User, profiles: dict) -> None:
    total_activities = 0
    total_adaptations = 0

    _EXCLUDED_KEYS = {"code", "versoes"}

    for act_data in TEA_ACTIVITIES:
        versoes = act_data["versoes"]
        activity_fields = {k: v for k, v in act_data.items() if k not in _EXCLUDED_KEYS}

        existing = session.exec(
            select(Activity).where(
                Activity.title == activity_fields["title"],
                Activity.teacher_id == teacher.id,
            )
        ).first()

        if existing:
            activity = existing
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
    print(f"[seed_tea_activities] {total_activities} activities + {total_adaptations} adaptations created.")


def run() -> None:
    with Session(engine) as session:
        teacher = _get_teacher(session)
        profiles = _get_profiles(session)
        _seed_25_activities(session, teacher, profiles)


if __name__ == "__main__":
    run()
