"""
Emoji illustration service — maps educational concepts to emoji.
Used as a first-pass illustration layer before calling the AI image model.
When a concept has a matching emoji, image generation is skipped unless forced.
"""

CONCEPT_EMOJI: dict[str, str] = {
    # ── Horta / Alimentos ────────────────────────────────────────────────────
    "alface": "🥬",
    "tomate": "🍅",
    "banana": "🍌",
    "maçã": "🍎",
    "maca": "🍎",
    "pizza": "🍕",
    "sorvete": "🍦",
    "água": "💧",
    "agua": "💧",
    "gelo": "🧊",
    "vapor": "♨️",
    "maçãs": "🍎",
    "macas": "🍎",
    "laranja": "🍊",
    "uva": "🍇",
    "cenoura": "🥕",
    # ── Animais ──────────────────────────────────────────────────────────────
    "gato": "🐱",
    "cachorro": "🐶",
    "peixe": "🐟",
    "golfinho": "🐬",
    "pássaro": "🐦",
    "passaro": "🐦",
    "sapo": "🐸",
    "cobra": "🐍",
    "gafanhoto": "🦗",
    "capim": "🌿",
    "leão": "🦁",
    "leao": "🦁",
    "elefante": "🐘",
    "cavalo": "🐎",
    "pato": "🦆",
    "galinha": "🐔",
    # ── Natureza / Geografia ─────────────────────────────────────────────────
    "árvore": "🌳",
    "arvore": "🌳",
    "montanha": "⛰️",
    "flor": "🌸",
    "planta": "🌱",
    "floresta": "🌲",
    "folha": "🍃",
    "raiz": "🌱",
    "caule": "🌿",
    "mar": "🌊",
    "oceano": "🌊",
    "rio": "🏞️",
    "pedra": "🪨",
    # ── Transporte ───────────────────────────────────────────────────────────
    "avião": "✈️",
    "aviao": "✈️",
    "barco": "⛵",
    "carro": "🚗",
    "carroça": "🐎",
    "carroca": "🐎",
    "canoa": "🛶",
    "trem": "🚂",
    "metrô": "🚇",
    "metro": "🚇",
    "ônibus": "🚌",
    "onibus": "🚌",
    # ── Lugares ──────────────────────────────────────────────────────────────
    "hospital": "🏥",
    "escola": "🏫",
    "mercado": "🏪",
    "prédio": "🏢",
    "predio": "🏢",
    "ponte": "🌉",
    "parque": "🏞️",
    "casa": "🏠",
    "praça": "🏡",
    "praca": "🏡",
    "lixeira": "🗑️",
    # ── Tempo / Clima ────────────────────────────────────────────────────────
    "sol": "☀️",
    "chuva": "☔",
    "guarda-chuva": "☂️",
    "guarda chuva": "☂️",
    "casaco": "🧥",
    "nuvem": "☁️",
    "frio": "❄️",
    "quente": "🔥",
    "óculos de sol": "🕶️",
    "oculos de sol": "🕶️",
    "ventilador": "🌀",
    # ── Rotina / Ações ───────────────────────────────────────────────────────
    "regar": "💧",
    "acordar": "🌅",
    "café da manhã": "🍽️",
    "cafe da manha": "🍽️",
    "café": "☕",
    "cafe": "☕",
    "mochila": "🎒",
    "dente": "🦷",
    "escovar": "🪥",
    "banho": "🛁",
    # ── Formas / Matemática ──────────────────────────────────────────────────
    "triângulo": "🔺",
    "triangulo": "🔺",
    "quadrado": "⬛",
    "círculo": "⚫",
    "circulo": "⚫",
    "vermelho": "🔴",
    "azul": "🔵",
    "verde": "🟢",
    "amarelo": "🟡",
    # ── Dinheiro ─────────────────────────────────────────────────────────────
    "dinheiro": "💵",
    "moeda": "🪙",
    "nota": "💵",
    # ── Pessoas / Fases da vida ───────────────────────────────────────────────
    "bebê": "👶",
    "bebe": "👶",
    "criança": "🧒",
    "crianca": "🧒",
    "adolescente": "🧑",
    "adulto": "🧑",
    # ── Profissões ────────────────────────────────────────────────────────────
    "médico": "🧑‍⚕️",
    "medico": "🧑‍⚕️",
    "bombeiro": "🧑‍🚒",
    "professor": "🧑‍🏫",
    "padeiro": "🧑‍🍳",
    # ── Sentidos / Órgãos ────────────────────────────────────────────────────
    "olhos": "👀",
    "olho": "👁️",
    "ouvido": "👂",
    "orelha": "👂",
    "nariz": "👃",
    "mão": "✋",
    "mao": "✋",
    # ── Símbolos Pátrios ─────────────────────────────────────────────────────
    "bandeira": "🇧🇷",
    "hino": "🎵",
    # ── Ferramentas / Utensílios ─────────────────────────────────────────────
    "seringa": "💉",
    "estetoscópio": "🩺",
    "estetoscopio": "🩺",
    "extintor": "🧯",
    "mangueira": "🚒",
    "giz": "✏️",
    "pintura corporal": "🎨",
    "pintura": "🎨",
    "indígena": "🛖",
    "indigena": "🛖",
    # ── Posição ──────────────────────────────────────────────────────────────
    "em cima": "⬆️",
    "embaixo": "⬇️",
    "acima": "⬆️",
    "abaixo": "⬇️",
    # ── Cadeia alimentar ─────────────────────────────────────────────────────
    "capim": "🌿",
    # ── Símbolos de sentimento ───────────────────────────────────────────────
    "alegre": "😀",
    "feliz": "😀",
    "triste": "😢",
    "animado": "😄",
    "contente": "😊",
    # ── Horta da escola (AT-PORT-01) ─────────────────────────────────────────
    "horta": "🌱",
    # ── Ação principal (AT-PORT-05) ───────────────────────────────────────────
    "bola": "⚽",
    "menino": "🧒",
    # ── Animais da apostila ───────────────────────────────────────────────────
    "coelho": "🐰",
    "tartaruga": "🐢",
    "rato": "🐭",
    # ── Língua Portuguesa — pontuação / gramática ─────────────────────────────
    "pontuação": "✏️",
    "pontuacao": "✏️",
    "diálogo": "💬",
    "dialogo": "💬",
    "texto": "📄",
    "ortografia": "🔤",
    "substantivo": "🏷️",
    "adjetivo": "✨",
    "verbo": "🏃",
    "verbos": "🏃",
    "sinônimo": "🔄",
    "sinonimo": "🔄",
    "antônimo": "↔️",
    "antonimo": "↔️",
    # ── Itens cotidianos ──────────────────────────────────────────────────────
    "carta": "✉️",
    "garrafa": "🍶",
    "sabão": "🧼",
    "sabao": "🧼",
    "osso": "🦴",
    # ── Tamanho / comparação ─────────────────────────────────────────────────
    "grande": "🐘",
    "pequeno": "🐁",
    # ── Pessoas ───────────────────────────────────────────────────────────────
    "menina": "👧",
    "nome": "🏷️",
    "cidade": "🏙️",
    "brasil": "🇧🇷",
    # ── Ações / verbos ────────────────────────────────────────────────────────
    "brincar": "🎯",
    "cantar": "🎤",
    "correr": "🏃",
    "passear": "🚶",
    # ── Sentimentos / humor ───────────────────────────────────────────────────
    "humor": "😄",
    "bonito": "✨",
    # ── Arte / Música ─────────────────────────────────────────────────────────
    "música": "🎵",
    "musica": "🎵",
}


def get_emoji_for_concept(text: str) -> str | None:
    """Return first matching emoji for the concept text.

    Tries longest keys first so 'guarda-chuva' beats 'chuva'.
    Case-insensitive, accent-insensitive via dual key strategy.
    Returns None when no match is found.
    """
    if not text:
        return None
    t = text.lower().strip()
    for key in sorted(CONCEPT_EMOJI, key=len, reverse=True):
        if key in t:
            return CONCEPT_EMOJI[key]
    return None
