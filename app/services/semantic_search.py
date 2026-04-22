from app.db.models import Incident
from app.db.session import SessionLocal
from app.services.embedding_service import generate_embedding

def search_similar_incidents(query: str, top_k: int = 5):
    db = SessionLocal()
    try:
        query_embedding = list(generate_embedding(query))

        results = (
            db.query(Incident)
            .filter(Incident.embedding.isnot(None))
            .order_by(Incident.embedding.l2_distance(query_embedding))
            .limit(top_k)
            .all()
        )
        return results
    finally:
        db.close()
