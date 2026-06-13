import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from .config import settings
from .routes import auth, settings as settings_router, students, profiles, activities, adaptations, student_area, dashboard, admin

app = FastAPI(
    title="EduAdapt AI",
    description="Plataforma multiagente para atividades pedagógicas adaptadas",
    version="0.1.0",
)

cors_kwargs = {
    "allow_origins": settings.cors_origins_list,
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
if settings.cors_origin_regex:
    cors_kwargs["allow_origin_regex"] = settings.cors_origin_regex

app.add_middleware(CORSMiddleware, **cors_kwargs)

app.include_router(auth.router)
app.include_router(settings_router.router)
app.include_router(students.router)
app.include_router(profiles.router)
app.include_router(activities.router)
app.include_router(adaptations.router)
app.include_router(student_area.router)
app.include_router(dashboard.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/static/images/{filename}")
def serve_generated_image(filename: str):
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=404)
    if not filename.endswith((".png", ".jpg", ".jpeg")):
        raise HTTPException(status_code=404)
    filepath = f"/app/static/images/{filename}"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404)
    with open(filepath, "rb") as f:
        return Response(content=f.read(), media_type="image/png")
