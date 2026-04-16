from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String, index=True)
    category = Column(String, index=True)
    severity = Column(String)
    description = Column(Text)
    resolution = Column(Text)
    embedding = Column(Vector(384), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)  # type: ignore
    location = Column(String, nullable=True)
    downtime_minutes = Column(Integer, nullable=True)
    technician = Column(String, nullable=True)
    work_order_id = Column(String, nullable=True, index=True)
    source = Column(String, default="manual")
    import_batch_id = Column(String, nullable=True)
