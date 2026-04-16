from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from app.db.session import engine
from app.db.models import Base
from app.api.routes import incidents
import os
from dotenv import load_dotenv

load_dotenv()  # must be before services

from app.services.semantic_search import search_similar_incidents
from app.services.llm_service import generate_answer
from pydantic import BaseModel

class AskRequest(BaseModel):
    query: str
    top_k: int = 5


app = FastAPI(title="FactoryMind AI Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for now (dev only)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(incidents.router)


@app.get("/")
def health_check():
    return {"status": "FactoryMind API running"}


@app.post("/ask")
def ask_question(request: AskRequest):

    incidents = search_similar_incidents(request.query, request.top_k)

    answer = generate_answer(request.query, incidents)

    similar_incidents = [
    {
        "id": incident.id,
        "machine_id": incident.machine_id,
        "category": incident.category,
        "severity": incident.severity,
        "description": incident.description,
        "resolution": incident.resolution,
        "timestamp": incident.timestamp,
    }
    for incident in incidents
    ]

    return {
        "answer": answer,
        "similar_incidents": similar_incidents,
    }
