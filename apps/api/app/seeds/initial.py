"""
Seed data: 3 TEA profiles + students per profile + activities.
Idempotent — skips existing records; deactivates non-TEA profiles.
"""
import uuid
from sqlmodel import Session, select
from ..database import engine
from ..models import User, StudentProfile, Student, TeacherStudent, Activity
from ..services.auth_service import hash_password

TEA_PROFILE_PREFIX = "TEA —"


def run():
    with Session(engine) as session:
        _seed_users(session)
        _seed_profiles(session)
        _seed_students(session)
        _seed_activities(session)

    from .seed_tea_activities import run as run_tea
    run_tea()


def _seed_users(session: Session):
    users = [
        {"email": "admin@eduadapt.local", "name": "Admin EduAdapt", "role": "admin", "password": "admin123"},
        {"email": "professor@eduadapt.local", "name": "Professora Ana", "role": "teacher", "password": "professor123"},
        # Students — one per TEA profile
        {"email": "lucas@eduadapt.local", "name": "Lucas (Não Verbal)", "role": "student", "password": "aluno123"},
        {"email": "aluno@eduadapt.local", "name": "Lucas Exemplo", "role": "student", "password": "aluno123"},  # legacy alias
        {"email": "maria@eduadapt.local", "name": "Maria (Hipersensibilidade Visual)", "role": "student", "password": "aluno123"},
        {"email": "joao@eduadapt.local", "name": "João (Apoio Visual)", "role": "student", "password": "aluno123"},
    ]
    for u in users:
        existing = session.exec(select(User).where(User.email == u["email"])).first()
        if not existing:
            session.add(User(
                id=str(uuid.uuid4()),
                email=u["email"],
                hashed_password=hash_password(u["password"]),
                name=u["name"],
                role=u["role"],
            ))
    session.commit()


def _seed_profiles(session: Session):
    teacher = session.exec(select(User).where(User.email == "professor@eduadapt.local")).first()
    if not teacher:
        return

    # Deactivate non-TEA profiles so they stop appearing in the UI
    old_profiles = session.exec(
        select(StudentProfile).where(StudentProfile.teacher_id == teacher.id)
    ).all()
    for p in old_profiles:
        if not p.name.startswith(TEA_PROFILE_PREFIX):
            p.is_active = False
            session.add(p)
    session.commit()

    # 3 TEA profiles — ordered from simplest (non-verbal) to most complex
    tea_profiles = [
        {
            "name": "TEA — Não Verbal",
            "description": (
                "Aluno com TEA sem comunicação verbal funcional. "
                "Utiliza CAA (comunicação aumentativa e alternativa): pictogramas, "
                "prancha de comunicação, apontar. Necessita de atividades extremamente "
                "simples com apoio visual exclusivo."
            ),
            "reading_level": "initial",
            "autonomy_level": "low",
            "main_difficulties": [
                "comunicação verbal",
                "escrita",
                "leitura convencional",
                "instruções verbais longas",
                "múltiplos estímulos simultâneos",
            ],
            "recommended_strategies": [
                "pictogramas AAC",
                "seleção por apontar ou toque",
                "uma imagem por vez",
                "fundo branco",
                "resposta por escolha visual (2 opções)",
                "reforço imediato",
            ],
            "preferred_modalities": ["visual", "drag_drop"],
            "resources_to_avoid": [
                "respostas escritas",
                "leitura de textos",
                "instruções longas",
                "mais de 3 opções simultaneamente",
            ],
            "accessibility_complexity": "minimal",
            "notes": "Perfil mais simples. Imagens devem ser pictogramas AAC: símbolo único, fundo branco, traço preto grosso.",
        },
        {
            "name": "TEA — Hipersensibilidade Visual",
            "description": (
                "Aluno com TEA e hipersensibilidade a estímulos visuais. "
                "Cores vibrantes, layouts densos e animações causam desconforto e sobrecarga sensorial. "
                "Prefere ambientes visuais simples, com poucas cores e muito espaço em branco."
            ),
            "reading_level": "basic",
            "autonomy_level": "medium",
            "main_difficulties": [
                "excesso de estímulos visuais",
                "cores saturadas e vibrantes",
                "layouts com muitos elementos",
                "transições visuais bruscas",
            ],
            "recommended_strategies": [
                "fundo branco ou cinza muito claro",
                "máximo 2 cores por tela",
                "fontes sans-serif grandes",
                "muito espaço em branco",
                "imagens com paleta dessaturada",
                "uma instrução por vez",
            ],
            "preferred_modalities": ["text", "audio", "drag_drop"],
            "resources_to_avoid": [
                "cores primárias saturadas",
                "imagens coloridas complexas",
                "animações",
                "ícones decorativos",
                "backgrounds coloridos",
            ],
            "accessibility_complexity": "low_stimulation",
            "notes": "Imagens geradas devem ter paleta dessaturada/pastel, composição limpa, poucos detalhes.",
        },
        {
            "name": "TEA — Apoio Visual e Leitura Inicial",
            "description": (
                "Aluno com TEA em fase de alfabetização funcional. "
                "Consegue ler palavras simples com apoio visual. "
                "Responde bem a imagens coloridas e instruções curtas combinadas com figuras."
            ),
            "reading_level": "initial",
            "autonomy_level": "low",
            "main_difficulties": [
                "enunciados longos",
                "vocabulário abstrato",
                "mais de 3 alternativas",
                "ausência de suporte visual",
            ],
            "recommended_strategies": [
                "texto curto + imagem de apoio",
                "uma instrução por vez",
                "imagens coloridas e claras",
                "máximo 3 opções de resposta",
                "feedback visual imediato",
            ],
            "preferred_modalities": ["visual", "audio", "drag_drop"],
            "resources_to_avoid": [
                "textos longos sem imagens",
                "vocabulário técnico",
                "mais de 4 itens por tela",
            ],
            "accessibility_complexity": "supported",
            "notes": "Imagens devem ser cartoon colorido claro, estilo educacional amigável.",
        },
    ]

    for p in tea_profiles:
        existing = session.exec(
            select(StudentProfile).where(
                StudentProfile.name == p["name"],
                StudentProfile.teacher_id == teacher.id,
            )
        ).first()
        if not existing:
            session.add(StudentProfile(
                id=str(uuid.uuid4()),
                teacher_id=teacher.id,
                **p,
            ))
    session.commit()


def _seed_students(session: Session):
    teacher = session.exec(select(User).where(User.email == "professor@eduadapt.local")).first()
    if not teacher:
        return

    profile_nv = session.exec(select(StudentProfile).where(StudentProfile.name == "TEA — Não Verbal")).first()
    profile_hv = session.exec(select(StudentProfile).where(StudentProfile.name == "TEA — Hipersensibilidade Visual")).first()
    profile_av = session.exec(select(StudentProfile).where(StudentProfile.name == "TEA — Apoio Visual e Leitura Inicial")).first()

    student_configs = [
        {"email": "lucas@eduadapt.local", "profile": profile_nv, "year": "1º ano",
         "notes": "Usa prancha de comunicação PECS. Responde melhor com 2 opções visuais."},
        {"email": "aluno@eduadapt.local", "profile": profile_nv, "year": "2º ano",
         "notes": "Aluno legado — perfil TEA Não Verbal."},
        {"email": "maria@eduadapt.local", "profile": profile_hv, "year": "3º ano",
         "notes": "Hipersensibilidade visual severa. Cores saturadas causam crise. Usa fones anti-ruído."},
        {"email": "joao@eduadapt.local", "profile": profile_av, "year": "2º ano",
         "notes": "Lê palavras simples. Precisa de imagem de apoio para manter engajamento."},
    ]

    for cfg in student_configs:
        user = session.exec(select(User).where(User.email == cfg["email"])).first()
        if not user:
            continue
        existing_student = session.exec(select(Student).where(Student.user_id == user.id)).first()
        if not existing_student:
            student = Student(
                id=str(uuid.uuid4()),
                user_id=user.id,
                profile_id=cfg["profile"].id if cfg["profile"] else None,
                school_year=cfg["year"],
                learning_notes=cfg["notes"],
            )
            session.add(student)
            session.flush()
            # Link to teacher
            link_exists = session.exec(
                select(TeacherStudent).where(
                    TeacherStudent.teacher_id == teacher.id,
                    TeacherStudent.student_id == student.id,
                )
            ).first()
            if not link_exists:
                session.add(TeacherStudent(
                    id=str(uuid.uuid4()),
                    teacher_id=teacher.id,
                    student_id=student.id,
                ))
        else:
            # Update profile link for legacy student
            if cfg["profile"] and not existing_student.profile_id:
                existing_student.profile_id = cfg["profile"].id
                session.add(existing_student)
    session.commit()


def _seed_activities(session: Session):
    teacher = session.exec(select(User).where(User.email == "professor@eduadapt.local")).first()
    if not teacher:
        return

    activities = [
        {
            "title": "Animais e Ambientes",
            "discipline": "Ciências",
            "school_year": "2º ano",
            "pedagogical_objective": "Identificar onde vivem alguns animais.",
            "activity_type": "association",
            "statement": "Observe os animais e associe cada um ao ambiente onde vive.",
            "question": "Onde cada animal vive?",
            "expected_answer": "Peixe, Golfinho, Caranguejo vivem na água. Cachorro, Gato, Cavalo vivem na terra.",
            "correction_criteria": "Percentual de itens corretamente associados.",
            "base_complexity": 2,
            "original_modality": "association",
        },
        {
            "title": "Rotina da Manhã",
            "discipline": "Vida Prática",
            "school_year": "1º ano",
            "pedagogical_objective": "Ordenar as etapas da rotina matinal de forma sequencial.",
            "activity_type": "drag_drop",
            "statement": "Toda manhã seguimos uma sequência de passos para ficar prontos para a escola.",
            "question": "Coloque as etapas da manhã na ordem correta.",
            "expected_answer": "acordar, escovar os dentes, tomar banho, tomar café, colocar a mochila",
            "correction_criteria": "Sequência correta das etapas.",
            "base_complexity": 1,
            "original_modality": "sequencing",
        },
        {
            "title": "Cores e Frutas",
            "discipline": "Matemática",
            "school_year": "1º ano",
            "pedagogical_objective": "Associar frutas às suas cores predominantes.",
            "activity_type": "association",
            "statement": "Cada fruta tem uma cor especial.",
            "question": "Associe cada fruta à sua cor.",
            "expected_answer": "Banana é amarela. Maçã é vermelha. Uva é roxa. Laranja é laranja.",
            "correction_criteria": "Associação correta de fruta e cor.",
            "base_complexity": 1,
            "original_modality": "association",
        },
    ]

    for act in activities:
        existing = session.exec(
            select(Activity).where(Activity.title == act["title"])
        ).first()
        if not existing:
            session.add(Activity(
                id=str(uuid.uuid4()),
                teacher_id=teacher.id,
                status="active",
                **act,
            ))
    session.commit()


if __name__ == "__main__":
    run()
