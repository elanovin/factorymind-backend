from sqlalchemy import text
from app.db.session import SessionLocal
from fastapi import UploadFile, File
import os
from app.services.import_service import import_incidents_from_file
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.models import Incident
from app.db.session import SessionLocal
from app.schemas.incident import IncidentCreate, IncidentResponse, SemanticSearchRequest
from app.services.semantic_search import search_similar_incidents
from app.services.embedding_service import generate_embedding

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/incidents", response_model=IncidentResponse)
def create_incident(
    incident: IncidentCreate,
    db: Session = Depends(get_db)
):
    # Generate and store a pgvector embedding for semantic retrieval.
    text_for_embedding = f"{incident.description} {incident.resolution}"
    embedding_list = generate_embedding(text_for_embedding)

    new_incident = Incident(
        machine_id=incident.machine_id,
        category=incident.category,
        severity=incident.severity,
        description=incident.description,
        resolution=incident.resolution,
        embedding=embedding_list,
    )

    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)

    return new_incident


@router.get("/incidents", response_model=List[IncidentResponse])
def get_incidents(
    severity: str | None = None,
    category: str | None = None,
    machine_id: str | None = None
):
    db = SessionLocal()

    query = db.query(Incident)

    if severity:
        query = query.filter(Incident.severity == severity)

    if category:
        query = query.filter(Incident.category == category)

    if machine_id:
        query = query.filter(Incident.machine_id == machine_id)

    incidents = query.all()
    db.close()
    return incidents


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident_by_id(incident_id: int):
    db = SessionLocal()

    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    db.close()

    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    return incident


@router.post("/semantic-search", response_model=List[IncidentResponse])
def semantic_search(payload: SemanticSearchRequest):
    results = search_similar_incidents(payload.query)
    return results

@router.post("/incidents/import")
def import_incidents(file: UploadFile = File(...)):
    temp_path = f"temp_{file.filename}"

    with open(temp_path, "wb") as f:
        f.write(file.file.read())

    try:
        result = import_incidents_from_file(temp_path)
        return result
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
@router.post("/feedback")
def save_feedback(payload: dict):
    db = SessionLocal()
    try:
        db.execute(
            text("""
                INSERT INTO feedback (query, answer, is_helpful)
                VALUES (:query, :answer, :is_helpful)
            """),
            {
                "query": payload.get("query"),
                "answer": payload.get("answer"),
                "is_helpful": payload.get("is_helpful"),
            }
        )
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()