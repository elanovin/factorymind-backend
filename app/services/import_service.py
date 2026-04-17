import pandas as pd
import uuid
import logging
from datetime import datetime
from app.db.session import SessionLocal
from app.db.models import Incident
from app.services.embedding_service import generate_embedding
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_incidents_from_file(file_path: str):
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    elif file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Use CSV or Excel.")
        
    df.columns = df.columns.str.strip().str.lower()

    required_columns = ["machine_id", "description", "resolution"]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    

    db = SessionLocal()

    batch_id = str(uuid.uuid4())
    imported = 0
    skipped_duplicates = 0
    skipped_invalid = 0

    try:
        for _, row in df.iterrows():
            description = str(row["description"])
            resolution = str(row["resolution"])
            machine_id = str(row["machine_id"])
            existing = db.query(Incident).filter(
                Incident.description == description,
                Incident.resolution == resolution,
            ).first()

            if existing:
                skipped_duplicates += 1
                continue

            # skip bad rows
            if len(description) < 10 or len(resolution) < 10:
                skipped_invalid += 1
                continue

            # embedding
            text_for_embedding = f"{description} {resolution}"
            embedding = generate_embedding(text_for_embedding)
            incident = Incident(
                machine_id=machine_id,
                description=description,
                resolution=resolution,
                category=row.get("category", "uncategorized"),
                severity=row.get("severity", "Medium"),
                timestamp=datetime.utcnow(),
                embedding=embedding,
                source="import",
                import_batch_id=batch_id,
                location=row.get("location"),
                technician=row.get("technician"),
                downtime_minutes=row.get("downtime_minutes"),
                work_order_id=row.get("work_order_id"),
            )

            db.add(incident)
            imported += 1
            logger.info(f"Imported incident for machine {machine_id}")

        db.commit()
        logger.info(f"Import completed. Total imported: {imported}")

    finally:
        db.close()

    return {
        "imported": imported,
        "skipped_duplicates": skipped_duplicates,
        "skipped_invalid": skipped_invalid,
        "batch_id": batch_id
    }