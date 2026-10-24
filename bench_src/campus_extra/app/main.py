from fastapi import FastAPI

from app.routers import academics, admin, appointments, assignments, clubs, courses, files, resources, users
from app.seed import init_db

app = FastAPI(
    title="Campus Service API",
    description="A campus services API covering profiles, courses, assignments, appointments, clubs, and files.",
    version="1.0.0",
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(users.router)
app.include_router(courses.router)
app.include_router(assignments.router)
app.include_router(appointments.router)
app.include_router(clubs.router)
app.include_router(files.router)
app.include_router(admin.router)
app.include_router(academics.router)
app.include_router(resources.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
