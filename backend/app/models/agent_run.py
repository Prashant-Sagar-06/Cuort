import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.app.database import Base

class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False, index=True)
    
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    
    status = Column(String(50), default="success", nullable=False)
    execution_time_ms = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship
    ticket = relationship("Ticket", backref="agent_runs")

    def __repr__(self):
        return f"<AgentRun {self.agent_name} on {self.ticket_id} ({self.status})>"
