import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from backend.app.models.ticket import TicketPriority, TicketStatus, MessageSenderType

class TicketCreate(BaseModel):
    subject: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    category: Optional[str] = "General"

class TicketStatusUpdate(BaseModel):
    status: TicketStatus

class TicketAssignRequest(BaseModel):
    agent_id: uuid.UUID

class TicketMessageCreate(BaseModel):
    message: str = Field(..., min_length=1)
    is_internal_note: bool = False

class TicketMessageResponse(BaseModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    sender_id: Optional[uuid.UUID] = None
    sender_name: Optional[str] = None
    sender_type: MessageSenderType
    message: str
    is_internal_note: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TicketResponse(BaseModel):
    id: uuid.UUID
    ticket_number: str
    customer_id: uuid.UUID
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    assigned_agent_id: Optional[uuid.UUID] = None
    assigned_agent_name: Optional[str] = None
    subject: str
    description: str
    category: str
    priority: TicketPriority
    status: TicketStatus
    sentiment: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TicketDetailResponse(TicketResponse):
    messages: List[TicketMessageResponse] = []

class AgentRunResponse(BaseModel):
    id: uuid.UUID
    agent_name: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    status: str
    execution_time_ms: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TicketTimelineResponse(BaseModel):
    ticket_id: uuid.UUID
    ticket_number: str
    agent_runs: List[AgentRunResponse] = []
    messages: List[TicketMessageResponse] = []
