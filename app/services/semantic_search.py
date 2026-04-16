from app.db.models import Incident
from app.db.session import SessionLocal
from app.services.embedding_service import model

def search_similar_incidents(query: str, top_k: int = 5):
    """
    Find the top-k incidents by L2 distance between the query embedding and
    stored pgvector embeddings (same metric as the previous FAISS IndexFlatL2).
    """
    db = SessionLocal()
    try:
        query_embedding = model.encode(query)
        query_list = (
            query_embedding.tolist()
            if hasattr(query_embedding, "tolist")
            else list(query_embedding)
        )

        results = (
            db.query(Incident)
            .filter(Incident.embedding.isnot(None))
            .order_by(Incident.embedding.l2_distance(query_list))
            .limit(top_k)
            .all()
        )
        return results
    finally:
        db.close()
