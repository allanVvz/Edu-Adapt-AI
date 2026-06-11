from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routes import auth, settings as settings_router, students, profiles, activities, adaptations, student_area, dashboard

app = FastAPI(
    title="EduAdapt AI",
    description="Plataforma multiagente para atividades pedagógicas adaptadas",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(settings_router.router)
app.include_router(students.router)
app.include_router(profiles.router)
app.include_router(activities.router)
app.include_router(adaptations.router)
app.include_router(student_area.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
