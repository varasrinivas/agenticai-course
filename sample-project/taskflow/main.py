from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database import Base, engine
from routers import users, tasks, tags

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TaskFlow API",
    description="A simple task management API used as the reference project for the Gemini CLI course.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(tags.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "taskflow"}
