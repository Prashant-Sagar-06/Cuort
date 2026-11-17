import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.app.database import Base

class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"

class MessageSenderType(str, enum.Enum):
    CUSTOMER = "customer"
    AGENT = "agent"
    AI = "ai"
    SYSTEM = "system"

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    ticket_number = Column(String(50), unique=True, index=True, nullable=False)
    
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), default="General", nullable=False)
    priority = Column(
        Enum(TicketPriority, name="ticket_priority_enum", values_callable=lambda x: [e.value for e in x]),
        default=TicketPriority.MEDIUM,
        nullable=False
    )
    status = Column(
        Enum(TicketStatus, name="ticket_status_enum", values_callable=lambda x: [e.value for e in x]),
        default=TicketStatus.OPEN,
        nullable=False
    )
    
    sentiment = Column(String(50), nullable=True)
    summary = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    customer = relationship("User", foreign_keys=[customer_id], backref="created_tickets")
    assigned_agent = relationship("User", foreign_keys=[assigned_agent_id], backref="assigned_tickets")
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketMessage.created_at")

    def __repr__(self):
        return f"<Ticket {self.ticket_number} - {self.status.value}>"

class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    sender_type = Column(
        Enum(MessageSenderType, name="message_sender_type_enum", values_callable=lambda x: [e.value for e in x]),
        default=MessageSenderType.CUSTOMER,
        nullable=False
    )
    message = Column(Text, nullable=False)
    is_internal_note = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    ticket = relationship("Ticket", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])

    def __repr__(self):
        return f"<TicketMessage {self.id} on {self.ticket_id} by {self.sender_type}>"

class TicketAssignment(Base):
    __tablename__ = "ticket_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    assigned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    ticket = relationship("Ticket", backref="assignments")
    agent = relationship("User", foreign_keys=[agent_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])
