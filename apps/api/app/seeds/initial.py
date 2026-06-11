"""
Run once at startup to create default users, profiles, and seed activity.
Idempotent — skips if data already exists.
"""
import uuid
from sqlmodel import Session, select
from ..database import engine
from ..models import User, StudentProfile, Student, TeacherStudent, Activity
from ..services.auth_service import hash_password


def run():
    with Session(engine) as session:
        _seed_users(session)
        _seed_profiles(session)
        _seed_students(session)
        _seed_activities(session)


def _seed_users(session: Session):
    users = [
        {"email": "admin@eduadapt.local", "name": "Admin EduAdapt", "role": "admin", "password": "admin123"},
        {"email": "professor@eduadapt.local", "name": "Professora Ana", "role": "teacher", "password": "professor123"},
        {"email": "aluno@eduadapt.local", "name": "Lucas Exemplo", "role": "student", "password": "aluno123"},
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

    profiles = [
        {
            "name": "Apoio visual e leitura inicial",
            "description": "Aluno em fase inicial de leitura, responde bem a imagens e instruções curtas",
            "reading_level": "initial",
            "autonomy_level": "low",
            "main_difficulties": ["enunciados longos", "vocabulário abstrato", "excesso de alternativas"],
            "recommended_strategies": ["frases curtas", "apoio visual", "uma instrução por vez", "fundo neutro"],
            "preferred_modalities": ["visual", "audio", "drag_drop"],
            "resources_to_avoid": ["muitas cores simultâneas", "textos longos", "instruções abstratas"],
        },
        {
            "name": "Baixa tolerância a estímulos visuais",
            "description": "Aluno com hipersensibilidade visual, prefere layouts simples e com pouca informação",
            "reading_level": "basic",
            "autonomy_level": "medium",
            "main_difficulties": ["excesso de estímulos", "cores vibrantes", "layout complexo"],
            "recommended_strategies": ["fundo branco ou cinza claro", "poucas imagens", "espaçamento generoso"],
            "preferred_modalities": ["text", "audio"],
            "resources_to_avoid": ["muitas cores", "animações", "ícones decorativos"],
        },
        {
            "name": "Dificuldade de atenção e sequência",
            "description": "Aluno com dificuldade de manter atenção e seguir sequências longas",
            "reading_level": "basic",
            "autonomy_level": "low",
            "main_difficulties": ["atividades com muitas etapas", "textos longos", "falta de estrutura"],
            "recommended_strategies": ["dividir em passos", "uma tarefa por bloco", "feedback imediato"],
            "preferred_modalities": ["drag_drop", "visual", "audio"],
            "resources_to_avoid": ["atividades abertas", "múltiplas perguntas simultâneas"],
        },
        {
            "name": "Comunicação não verbal",
            "description": "Aluno não verbal, utiliza CAA (comunicação aumentativa e alternativa)",
            "reading_level": "initial",
            "autonomy_level": "low",
            "main_difficulties": ["expressão verbal", "escrita", "leitura convencional"],
            "recommended_strategies": ["pictogramas", "seleção por apontar", "apoio visual constante"],
            "preferred_modalities": ["visual", "drag_drop"],
            "resources_to_avoid": ["respostas escritas", "leitura de textos longos"],
        },
        {
            "name": "Baixa visão",
            "description": "Aluno com limitação visual, precisa de elementos grandes e alto contraste",
            "reading_level": "basic",
            "autonomy_level": "medium",
            "main_difficulties": ["leitura de texto pequeno", "imagens com baixo contraste"],
            "recommended_strategies": ["fonte grande", "alto contraste", "áudio de apoio", "elementos grandes"],
            "preferred_modalities": ["audio", "text"],
            "resources_to_avoid": ["texto pequeno", "baixo contraste", "imagens decorativas"],
        },
    ]

    for p in profiles:
        existing = session.exec(
            select(StudentProfile).where(
                StudentProfile.name == p["name"],
                StudentProfile.teacher_id == teacher.id
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
    student_user = session.exec(select(User).where(User.email == "aluno@eduadapt.local")).first()
    profile = session.exec(select(StudentProfile).where(StudentProfile.name == "Apoio visual e leitura inicial")).first()

    if not teacher or not student_user:
        return

    existing_student = session.exec(select(Student).where(Student.user_id == student_user.id)).first()
    if not existing_student:
        student = Student(
            id=str(uuid.uuid4()),
            user_id=student_user.id,
            profile_id=profile.id if profile else None,
            school_year="2º ano",
            learning_notes="Aluno em fase inicial de leitura, responde bem a atividades com imagens e áudio.",
        )
        session.add(student)
        session.flush()

        session.add(TeacherStudent(
            id=str(uuid.uuid4()),
            teacher_id=teacher.id,
            student_id=student.id,
        ))
    session.commit()


def _seed_activities(session: Session):
    teacher = session.exec(select(User).where(User.email == "professor@eduadapt.local")).first()
    if not teacher:
        return

    existing = session.exec(
        select(Activity).where(Activity.title == "Animais e Ambientes")
    ).first()
    if not existing:
        session.add(Activity(
            id=str(uuid.uuid4()),
            teacher_id=teacher.id,
            title="Animais e Ambientes",
            discipline="Ciências",
            school_year="2º ano",
            pedagogical_objective="Identificar onde vivem alguns animais.",
            activity_type="association",
            statement="Observe os animais e associe cada um ao ambiente onde vive.",
            question="Onde cada animal vive?",
            expected_answer="Peixe e golfinho vivem na água. Cachorro e gato vivem na terra.",
            correction_criteria="Percentual de itens corretamente associados.",
            base_complexity=2,
            original_modality="association",
            status="active",
        ))
    session.commit()


if __name__ == "__main__":
    run()
