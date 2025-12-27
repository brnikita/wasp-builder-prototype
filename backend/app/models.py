import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="created")  # created, generating, ready, running, stopped, error
    port = Column(Integer, nullable=True)
    wasp_schema = Column(Text, nullable=True)
    prisma_schema = Column(Text, nullable=True)
    source_files = Column(JSON, nullable=True)
    container_id = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

