from app.db.models import Incident
from app.db.session import SessionLocal
from app.services.embedding_service import generate_embedding

def search_similar_incidents(query: str, top_k: int = 5):
    """
    Find the top-k incidents by L2 distance between the query embedding and
    stored pgvector embeddings (same metric as the previous FAISS IndexFlatL2).
    """
    db = SessionLocal()
    try:
        query_embedding = generate_embedding(query)

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
