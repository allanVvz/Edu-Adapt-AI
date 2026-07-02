"""
Seed: Apostila de Matematica - blocos da transcricao oficial.

Fonte: C:\\Repositores\\Edu Adapt docs\\apostila_matematica_transcricao_completa.md
Idempotente: verifica (title, teacher_id) antes de inserir e cria adaptacoes por
perfil apenas quando ainda nao existem.
"""
import uuid
from sqlmodel import Session, select

from ..database import engine
from ..models.user import User
from ..models.story import Story
from ..models.activity import Activity
from ..models.adaptation import ActivityAdaptation
from ..models.student_profile import StudentProfile
from .seed_apostila_portugues import _build_output_data, _seed_context_story


PROFILE_NAMES = {
    "p1": "TEA — Apoio Visual e Leitura Inicial",
    "p2": "TEA — Hipersensibilidade Visual",
    "p3": "TEA — Não Verbal",
}


def _mc_versions(question: str, correct: str, distractors: list[str], supports: list[str]) -> dict:
    options = [correct, *distractors]
    p2_options = options[:3]
    p3_options = [correct, distractors[0] if distractors else "Outra resposta"]
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
            "enun": f"Leia com calma. {question}",
            "dados": {
                "items": ["Minha resposta"],
                "zones": p2_options,
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
                "zones": p2_options,
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
                "zones": p3_options,
                "correct_answer": {"correct_zone": correct},
                "instructions": "Toque.",
            },
            "apoios": supports[:1],
        },
    }


def _dnd_versions(question: str, items: list[str], zones: list[str], correct: dict, supports: list[str]) -> dict:
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
                "instructions": "Arraste cada item para a coluna correta.",
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
                "instructions": "Arraste para a coluna certa.",
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
                "instructions": "Mova um item de cada vez.",
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


def _seq_versions(question: str, items: list[str], supports: list[str]) -> dict:
    correct = {item: f"{idx + 1}°" for idx, item in enumerate(items)}
    return {
        "padrao": {
            "fmt": "seq",
            "enun": question,
            "dados": {"items": items, "correct_answer": correct, "instructions": "Coloque em ordem."},
            "apoios": supports,
        },
        "p1": {
            "fmt": "seq",
            "enun": f"{question} Observe a ordem.",
            "dados": {"items": items, "correct_answer": correct, "instructions": "Ordene os passos."},
            "apoios": supports,
        },
        "p2": {
            "fmt": "seq",
            "enun": f"{question} [pausa] Primeiro, depois, ultimo.",
            "dados": {"items": items[:3], "instructions": "Ordene devagar."},
            "apoios": supports[:1],
        },
        "p3": {
            "fmt": "toque",
            "enun": f"Toque no primeiro: {items[0]}.",
            "dados": {
                "items": ["Minha resposta"],
                "zones": [items[0], items[-1]],
                "correct_answer": {"correct_zone": items[0]},
                "instructions": "Toque.",
            },
            "apoios": supports[:1],
        },
    }


APOSTILA_MATEMATICA_ACTIVITIES = [
    {
        "code": "AT-MAT-06",
        "title": "Numeros ate 100: sequencia e comparacao",
        "statement": "Complete sequencias, escreva numeros por extenso e compare valores ate 100.",
        "question": "Qual numero completa a sequencia 45, 46, __, 48?",
        "expected_answer": "47",
        "pedagogical_objective": "Ler, ordenar, comparar e completar numeros naturais ate 100.",
        "activity_type": "multiple_choice",
        "versoes": _mc_versions("Qual numero completa a sequencia 45, 46, __, 48?", "47", ["44", "49", "54"], ["numeros", "quadro numerico"]),
    },
    {
        "code": "AT-MAT-07",
        "title": "Problemas e decomposicao em dezenas e unidades",
        "statement": "Resolva problemas e decomponha numeros em dezenas e unidades.",
        "question": "Ronaldo tinha 54 carrinhos e ganhou 35. Quantos carrinhos tem ao todo?",
        "expected_answer": "89 carrinhos",
        "pedagogical_objective": "Resolver problemas de adicao e representar numeros por dezenas e unidades.",
        "activity_type": "multiple_choice",
        "versoes": _mc_versions("54 carrinhos mais 35 carrinhos. Quanto da ao todo?", "89", ["79", "80", "99"], ["carrinhos", "material dourado"]),
    },
    {
        "code": "AT-MAT-08",
        "title": "Material dourado: representar quantidades",
        "statement": "Use dezenas e unidades do material dourado para representar numeros.",
        "question": "Qual numero tem 3 dezenas e 2 unidades?",
        "expected_answer": "32",
        "pedagogical_objective": "Associar material dourado a representacao numerica.",
        "activity_type": "multiple_choice",
        "versoes": _mc_versions("Qual numero tem 3 dezenas e 2 unidades?", "32", ["23", "30", "12"], ["material dourado", "dezena"]),
    },
    {
        "code": "AT-MAT-09",
        "title": "Abaco: dezenas e unidades",
        "statement": "Represente e leia numeros no abaco com dezenas e unidades.",
        "question": "No abaco, 6 dezenas e 3 unidades formam qual numero?",
        "expected_answer": "63",
        "pedagogical_objective": "Ler e representar numeros no abaco decimal.",
        "activity_type": "multiple_choice",
        "versoes": _mc_versions("6 dezenas e 3 unidades formam qual numero?", "63", ["36", "60", "30"], ["abaco", "bolinhas"]),
    },
    {
        "code": "AT-MAT-10",
        "title": "Numeros ordinais: posicao na sequencia",
        "statement": "Identifique a posicao dos objetos usando numeros ordinais ate o decimo.",
        "question": "Na sequencia, a zebra esta na quarta posicao. Qual ordinal representa essa posicao?",
        "expected_answer": "4° - quarto",
        "pedagogical_objective": "Reconhecer e usar numeros ordinais ate 10.",
        "activity_type": "multiple_choice",
        "versoes": _mc_versions("A zebra esta na quarta posicao. Qual e o ordinal?", "4° - quarto", ["2° - segundo", "8° - oitavo", "10° - decimo"], ["zebra", "fila"]),
    },
    {
        "code": "AT-MAT-11",
        "title": "Ordinais: fila, escrita e cores",
        "statement": "Relacione posicoes na fila com os ordinais por extenso.",
        "question": "Na fila, quem esta na decima posicao?",
        "expected_answer": "Elisa",
        "pedagogical_objective": "Associar posicao, numeral ordinal e escrita por extenso.",
        "activity_type": "multiple_choice",
        "versoes": _mc_versions("Na fila, Elisa esta na decima posicao. Quem ocupa a decima posicao?", "Elisa", ["Enzo", "Gael", "Ana"], ["fila de criancas", "numero ordinal"]),
    },
    {
        "code": "AT-MAT-12",
        "title": "Adicao: termos, legenda e material dourado",
        "statement": "Resolva adicoes e use os resultados para pintar ou representar com material dourado.",
        "question": "Quanto e 12 + 8?",
        "expected_answer": "20",
        "pedagogical_objective": "Resolver adicoes simples e reconhecer parcela e soma.",
        "activity_type": "multiple_choice",
        "versoes": _mc_versions("Quanto e 12 + 8?", "20", ["18", "19", "25"], ["lagarta", "adicao"]),
    },
    {
        "code": "AT-MAT-13",
        "title": "Problemas de adicao e subtracao",
        "statement": "Resolva problemas com juntar, acrescentar, gastar e retirar.",
        "question": "Pedro tinha 24 figurinhas e ganhou 15. Quantas figurinhas tem agora?",
        "expected_answer": "39 figurinhas",
        "pedagogical_objective": "Interpretar problemas matematicos de adicao e subtracao.",
        "activity_type": "multiple_choice",
        "versoes": _mc_versions("24 figurinhas mais 15 figurinhas. Quanto da?", "39", ["29", "40", "38"], ["figurinhas", "biblioteca"]),
    },
    {
        "code": "AT-MAT-14",
        "title": "Quebra-cabeca de resultados das operacoes",
        "statement": "Resolva operacoes e associe cada resultado a uma peca do quebra-cabeca.",
        "question": "Qual e o resultado de 33 + 15?",
        "expected_answer": "48",
        "pedagogical_objective": "Calcular resultados de adicoes e subtracoes em formato de jogo.",
        "activity_type": "multiple_choice",
        "versoes": _mc_versions("Qual e o resultado de 33 + 15?", "48", ["38", "52", "23"], ["quebra-cabeca", "operacoes"]),
    },
    {
        "code": "AT-MAT-15",
        "title": "Subtracao: termos, legenda e material dourado",
        "statement": "Resolva subtracoes e represente retirar dezenas ou unidades.",
        "question": "Quanto e 66 - 10?",
        "expected_answer": "56",
        "pedagogical_objective": "Resolver subtracoes e reconhecer minuendo, subtraendo e diferenca.",
        "activity_type": "multiple_choice",
        "versoes": _mc_versions("Quanto e 66 - 10?", "56", ["65", "76", "50"], ["elefante", "subtracao"]),
    },
    {
        "code": "AT-MAT-16",
        "title": "Problemas de subtracao",
        "statement": "Resolva problemas em que uma quantidade diminui.",
        "question": "Lucas tinha 45 carrinhos e deu 12. Com quantos ficou?",
        "expected_answer": "33 carrinhos",
        "pedagogical_objective": "Interpretar situacoes de retirada e calcular o restante.",
        "activity_type": "multiple_choice",
        "versoes": _mc_versions("45 carrinhos menos 12 carrinhos. Quanto resta?", "33", ["57", "23", "35"], ["carrinhos", "onibus"]),
    },
    {
        "code": "AT-MAT-17",
        "title": "Quebra-cabeca da subtracao",
        "statement": "Calcule subtracoes e encontre a peca com o resultado correto.",
        "question": "Qual e o resultado de 16 - 8?",
        "expected_answer": "8",
        "pedagogical_objective": "Praticar subtracoes simples por associacao de resultado.",
        "activity_type": "multiple_choice",
        "versoes": _mc_versions("Qual e o resultado de 16 - 8?", "8", ["6", "10", "12"], ["quebra-cabeca", "subtracao"]),
    },
    {
        "code": "AT-MAT-18",
        "title": "Figuras geometricas planas",
        "statement": "Reconheca triangulo, retangulo, circulo e quadrado.",
        "question": "Qual figura tem tres lados?",
        "expected_answer": "Triangulo",
        "pedagogical_objective": "Identificar e nomear figuras geometricas planas.",
        "activity_type": "multiple_choice",
        "versoes": _mc_versions("Qual figura tem tres lados?", "Triangulo", ["Quadrado", "Circulo", "Retangulo"], ["triangulo", "formas geometricas"]),
    },
    {
        "code": "AT-MAT-19",
        "title": "Classificacao e pintura de formas planas",
        "statement": "Classifique objetos e pinte formas de acordo com a legenda.",
        "question": "Arraste cada objeto para a forma que mais parece.",
        "expected_answer": "bola-circulo; presente-quadrado; queijo-triangulo; ticket-retangulo",
        "pedagogical_objective": "Relacionar objetos do cotidiano a formas geometricas planas.",
        "activity_type": "drag_drop",
        "versoes": _dnd_versions(
            "Arraste cada objeto para a forma que mais parece.",
            ["bola", "presente", "pedaco de queijo", "ticket"],
            ["Circulo", "Quadrado", "Triangulo", "Retangulo"],
            {"bola": "Circulo", "presente": "Quadrado", "pedaco de queijo": "Triangulo", "ticket": "Retangulo"},
            ["bola", "presente"],
        ),
    },
    {
        "code": "AT-MAT-20",
        "title": "Solidos geometricos",
        "statement": "Identifique cubo, cone, esfera, cilindro, piramide e paralelepipedo.",
        "question": "Qual solido lembra uma bola?",
        "expected_answer": "Esfera",
        "pedagogical_objective": "Reconhecer solidos geometricos em objetos cotidianos.",
        "activity_type": "multiple_choice",
        "versoes": _mc_versions("Qual solido lembra uma bola?", "Esfera", ["Cubo", "Cone", "Cilindro"], ["bola", "solidos geometricos"]),
    },
    {
        "code": "AT-MAT-21",
        "title": "Medidas de comprimento",
        "statement": "Compare medidas e transforme metros, centimetros e milimetros.",
        "question": "1 metro tem quantos centimetros?",
        "expected_answer": "100 centimetros",
        "pedagogical_objective": "Compreender relacoes entre metro, centimetro e milimetro.",
        "activity_type": "multiple_choice",
        "versoes": _mc_versions("1 metro tem quantos centimetros?", "100 centimetros", ["10 centimetros", "1 centimetro", "1000 centimetros"], ["regua", "fita metrica"]),
    },
    {
        "code": "AT-MAT-22",
        "title": "Instrumentos de medida",
        "statement": "Reconheca regua, fita metrica, trena e balanca.",
        "question": "Qual instrumento usamos para pesar uma melancia?",
        "expected_answer": "Balanca",
        "pedagogical_objective": "Associar instrumentos de medida ao uso adequado.",
        "activity_type": "multiple_choice",
        "versoes": _mc_versions("Qual instrumento usamos para pesar uma melancia?", "Balanca", ["Regua", "Trena", "Fita metrica"], ["balanca", "melancia"]),
    },
    {
        "code": "AT-MAT-23",
        "title": "Relogio e horas",
        "statement": "Relacione relogios analogicos e digitais e resolva situacoes com horas.",
        "question": "Josiane saiu as 7 horas e voltou 4 horas depois. Que horas ela voltou?",
        "expected_answer": "11:00",
        "pedagogical_objective": "Ler horas inteiras e calcular passagem simples do tempo.",
        "activity_type": "multiple_choice",
        "versoes": _mc_versions("7 horas mais 4 horas. Que horas e?", "11:00", ["9:00", "10:00", "12:00"], ["relogio", "tempo"]),
    },
    {
        "code": "AT-MAT-24",
        "title": "Calendario: meses, semanas e datas",
        "statement": "Leia calendarios para identificar mes, dias, semanas e datas comemorativas.",
        "question": "Quantos meses tem o ano?",
        "expected_answer": "12",
        "pedagogical_objective": "Interpretar calendarios mensais e localizar informacoes de tempo.",
        "activity_type": "multiple_choice",
        "versoes": _mc_versions("Quantos meses tem o ano?", "12", ["10", "9", "7"], ["calendario", "meses"]),
    },
]


MATH_STORY_DEFINITIONS = [
    {
        "title": "Numeros ate 100 e material dourado",
        "codes": {"AT-MAT-06", "AT-MAT-07", "AT-MAT-08", "AT-MAT-09"},
        "audio_id": "math_numbers_audio_1",
        "content": (
            "Nesta parte da apostila, usamos numeros ate 100. "
            "Primeiro observamos a sequencia dos numeros. Depois comparamos qual numero e maior ou menor. "
            "Para entender melhor, usamos dezenas e unidades. "
            "Uma dezena vale 10 unidades. No material dourado, uma barra representa uma dezena e um cubinho representa uma unidade. "
            "No abaco, a coluna D mostra as dezenas e a coluna U mostra as unidades. "
            "Depois de observar esse apoio, resolva as atividades de sequencia, decomposicao, material dourado e abaco."
        ),
        "images": [
            {"id": "math_numbers_img_1", "description": "quadro numerico ate 100", "illustration_type": "generated", "active_style": "pictogram", "is_active": True, "image_url": None},
            {"id": "math_numbers_img_2", "description": "material dourado com dezenas e unidades", "illustration_type": "generated", "active_style": "pictogram", "is_active": True, "image_url": None},
            {"id": "math_numbers_img_3", "description": "abaco com colunas D e U", "illustration_type": "generated", "active_style": "pictogram", "is_active": True, "image_url": None},
        ],
    },
    {
        "title": "Fila e numeros ordinais",
        "codes": {"AT-MAT-10", "AT-MAT-11"},
        "audio_id": "math_ordinals_audio_1",
        "content": (
            "Os numeros ordinais mostram posicao, ordem ou lugar. "
            "Primeiro quer dizer 1. Segundo quer dizer 2. Terceiro quer dizer 3. "
            "Quando observamos uma fila, contamos da esquerda para a direita para descobrir a posicao de cada pessoa ou objeto. "
            "Use esse apoio para responder as atividades sobre desenhos em sequencia, fila das criancas e escrita dos ordinais."
        ),
        "images": [
            {"id": "math_ordinals_img_1", "description": "fila de criancas", "illustration_type": "generated", "active_style": "pictogram", "is_active": True, "image_url": None},
            {"id": "math_ordinals_img_2", "description": "cartoes primeiro segundo terceiro", "illustration_type": "generated", "active_style": "pictogram", "is_active": True, "image_url": None},
        ],
    },
    {
        "title": "Historias de adicao e subtracao",
        "codes": {"AT-MAT-12", "AT-MAT-13", "AT-MAT-14", "AT-MAT-15", "AT-MAT-16", "AT-MAT-17"},
        "audio_id": "math_operations_audio_1",
        "content": (
            "Em uma adicao, juntamos quantidades. As partes que somamos se chamam parcelas e o resultado se chama soma ou total. "
            "Em uma subtracao, uma quantidade diminui. Podemos retirar, gastar, perder ou doar. O resultado mostra quanto restou. "
            "Nos problemas da apostila, leia a situacao com calma, descubra se precisa juntar ou retirar e depois calcule. "
            "Use desenhos, material dourado ou pecas de quebra-cabeca para conferir o resultado."
        ),
        "images": [
            {"id": "math_operations_img_1", "description": "adicao com objetos", "illustration_type": "generated", "active_style": "pictogram", "is_active": True, "image_url": None},
            {"id": "math_operations_img_2", "description": "subtracao com objetos sendo retirados", "illustration_type": "generated", "active_style": "pictogram", "is_active": True, "image_url": None},
            {"id": "math_operations_img_3", "description": "quebra-cabeca de resultados", "illustration_type": "generated", "active_style": "pictogram", "is_active": True, "image_url": None},
        ],
    },
    {
        "title": "Formas planas e solidos geometricos",
        "codes": {"AT-MAT-18", "AT-MAT-19", "AT-MAT-20"},
        "audio_id": "math_geometry_audio_1",
        "content": (
            "As formas planas aparecem em desenhos e objetos. O triangulo tem tres lados. O quadrado tem quatro lados iguais. "
            "O retangulo tem quatro lados, com dois lados maiores e dois menores. O circulo e redondo. "
            "Os solidos geometricos tem volume. A esfera parece uma bola, o cubo parece um dado, o cilindro parece uma lata e o cone parece uma casquinha. "
            "Use esse apoio para classificar formas e solidos."
        ),
        "images": [
            {"id": "math_geometry_img_1", "description": "formas geometricas planas", "illustration_type": "generated", "active_style": "pictogram", "is_active": True, "image_url": None},
            {"id": "math_geometry_img_2", "description": "solidos geometricos", "illustration_type": "generated", "active_style": "pictogram", "is_active": True, "image_url": None},
        ],
    },
    {
        "title": "Medidas, relogio e calendario",
        "codes": {"AT-MAT-21", "AT-MAT-22", "AT-MAT-23", "AT-MAT-24"},
        "audio_id": "math_measures_audio_1",
        "content": (
            "Para medir comprimento, podemos usar regua, fita metrica ou trena. Um metro tem 100 centimetros. "
            "Para medir peso, usamos balanca. Para medir tempo, usamos relogio e calendario. "
            "No relogio, o ponteiro pequeno marca as horas e o ponteiro grande marca os minutos. "
            "No calendario, observamos mes, dias da semana, semanas completas e datas importantes."
        ),
        "images": [
            {"id": "math_measures_img_1", "description": "regua fita metrica trena e balanca", "illustration_type": "generated", "active_style": "pictogram", "is_active": True, "image_url": None},
            {"id": "math_measures_img_2", "description": "relogio analogico e digital", "illustration_type": "generated", "active_style": "pictogram", "is_active": True, "image_url": None},
            {"id": "math_measures_img_3", "description": "calendario mensal", "illustration_type": "generated", "active_style": "pictogram", "is_active": True, "image_url": None},
        ],
    },
]


def _seed_math_stories(session: Session, teacher: User) -> dict[str, Story]:
    story_by_code: dict[str, Story] = {}
    for definition in MATH_STORY_DEFINITIONS:
        story = _seed_context_story(
            session,
            teacher,
            definition["title"],
            definition["content"],
            definition["images"],
            definition["audio_id"],
        )
        for code in definition["codes"]:
            story_by_code[code] = story
    return story_by_code


def _get_teacher(session: Session) -> User:
    teacher = session.exec(select(User).where(User.email == "professor@eduadapt.local")).first()
    if not teacher:
        raise RuntimeError("Teacher not found. Run initial seed first.")
    return teacher


def _get_profiles(session: Session) -> dict:
    return {
        key: session.exec(select(StudentProfile).where(StudentProfile.name == name)).first()
        for key, name in PROFILE_NAMES.items()
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
            if existing.status != "published":
                existing.status = "published"
                session.add(existing)
            continue

        output_data = _build_output_data(versao, version_key)
        output_data["validation"]["notes"] = "Atividade pre-validada - Apostila de Matematica, Escola Dr. Martinho Lutero."
        session.add(ActivityAdaptation(
            id=str(uuid.uuid4()),
            activity_id=activity.id,
            student_profile_id=profile_id,
            generated_by="seed",
            output_data=output_data,
            status="published",
            version=1,
        ))
        count += 1
    return count


def _seed_math_activities(session: Session, teacher: User, profiles: dict) -> None:
    total_activities = 0
    total_adaptations = 0
    excluded = {"code", "versoes"}
    story_by_code = _seed_math_stories(session, teacher)

    for act_data in APOSTILA_MATEMATICA_ACTIVITIES:
        code = act_data["code"]
        versoes = act_data["versoes"]
        fields = {k: v for k, v in act_data.items() if k not in excluded}
        fields.update({
            "discipline": "Matemática",
            "school_year": "até 7º ano",
            "base_complexity": 2,
            "original_modality": "apostila impressa",
            "teacher_notes": f"{code} - Fonte: Apostila de Matemática transcrita.",
        })
        linked_story = story_by_code.get(code)
        if linked_story:
            fields["story_id"] = linked_story.id

        existing = session.exec(
            select(Activity).where(
                Activity.title == fields["title"],
                Activity.teacher_id == teacher.id,
            )
        ).first()
        if existing:
            activity = existing
            changed = False
            for key, value in fields.items():
                if getattr(activity, key, None) != value:
                    setattr(activity, key, value)
                    changed = True
            if activity.status != "active":
                activity.status = "active"
                changed = True
            if changed:
                session.add(activity)
        else:
            activity = Activity(id=str(uuid.uuid4()), teacher_id=teacher.id, status="active", **fields)
            session.add(activity)
            session.flush()
            total_activities += 1

        total_adaptations += _seed_adaptations(session, activity, versoes, profiles)

    session.commit()
    print(f"[seed_apostila_matematica] {total_activities} activities + {total_adaptations} adaptations created.")


def run() -> None:
    with Session(engine) as session:
        teacher = _get_teacher(session)
        profiles = _get_profiles(session)
        _seed_math_activities(session, teacher, profiles)


if __name__ == "__main__":
    run()
