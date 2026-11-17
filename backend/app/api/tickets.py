import uuid
import secrets
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.database import get_db, SessionLocal
from backend.app.models.user import User, UserRole
from backend.app.models.ticket import (
    Ticket,
    TicketMessage,
    TicketAssignment,
    TicketPriority,
    TicketStatus,
    MessageSenderType
)
from backend.app.models.agent_run import AgentRun
from backend.app.schemas.ticket import (
    TicketCreate,
    TicketResponse,
    TicketDetailResponse,
    TicketMessageCreate,
    TicketMessageResponse,
    TicketStatusUpdate,
    TicketAssignRequest,
    TicketTimelineResponse
)
from backend.app.security.deps import get_current_user, require_role
from backend.app.orchestrator.graph import execute_ticket_workflow

router = APIRouter()

def run_workflow_background(ticket_id: uuid.UUID):
    """Background task runner to execute LangGraph workflow safely with its own session."""
    with SessionLocal() as db_session:
        try:
            execute_ticket_workflow(ticket_id, db_session)
        except Exception as e:
            print(f"[Workflow Error] Failed processing ticket {ticket_id}: {e}")

def generate_ticket_number() -> str:
    """Generate a clean, professional ticket identifier like TCK-A1B2C3."""
    return f"TCK-{secrets.token_hex(3).upper()}"

def build_ticket_response(ticket: Ticket) -> dict:
    """Helper to convert Ticket ORM to dict with relationship names."""
    return {
        "id": ticket.id,
        "ticket_number": ticket.ticket_number,
        "customer_id": ticket.customer_id,
        "customer_name": ticket.customer.full_name if ticket.customer else None,
        "customer_email": ticket.customer.email if ticket.customer else None,
        "assigned_agent_id": ticket.assigned_agent_id,
        "assigned_agent_name": ticket.assigned_agent.full_name if ticket.assigned_agent else None,
        "subject": ticket.subject,
        "description": ticket.description,
        "category": ticket.category,
        "priority": ticket.priority,
        "status": ticket.status,
        "sentiment": ticket.sentiment,
        "summary": ticket.summary,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
    }

def build_message_response(msg: TicketMessage) -> dict:
    """Helper to format TicketMessage response with sender name."""
    sender_name = None
    if msg.sender:
        sender_name = msg.sender.full_name
    elif msg.sender_type == MessageSenderType.AI:
        sender_name = "Cuort AI Assistant"
    elif msg.sender_type == MessageSenderType.SYSTEM:
        sender_name = "Cuort System"

    return {
        "id": msg.id,
        "ticket_id": msg.ticket_id,
        "sender_id": msg.sender_id,
        "sender_name": sender_name,
        "sender_type": msg.sender_type,
        "message": msg.message,
        "is_internal_note": msg.is_internal_note,
        "created_at": msg.created_at,
    }

@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket_in: TicketCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a new customer complaint ticket.
    Creates the ticket, records the initial message, and triggers
    the multi-agent AI pipeline in the background.
    """
    ticket_num = generate_ticket_number()
    
    while db.query(Ticket).filter(Ticket.ticket_number == ticket_num).first():
        ticket_num = generate_ticket_number()

    ticket = Ticket(
        ticket_number=ticket_num,
        customer_id=current_user.id,
        subject=ticket_in.subject,
        description=ticket_in.description,
        category=ticket_in.category or "General",
        priority=TicketPriority.MEDIUM,
        status=TicketStatus.OPEN
    )
    db.add(ticket)
    db.flush()

    initial_message = TicketMessage(
        ticket_id=ticket.id,
        sender_id=current_user.id,
        sender_type=MessageSenderType.CUSTOMER,
        message=ticket_in.description,
        is_internal_note=False
    )
    db.add(initial_message)
    db.commit()
    db.refresh(ticket)

    # Launch LangGraph AI Agents asynchronously
    background_tasks.add_task(run_workflow_background, ticket.id)

    return build_ticket_response(ticket)

@router.get("", response_model=List[TicketResponse])
def list_tickets(
    status_filter: Optional[TicketStatus] = Query(None, alias="status"),
    priority_filter: Optional[TicketPriority] = Query(None, alias="priority"),
    category_filter: Optional[str] = Query(None, alias="category"),
    search: Optional[str] = Query(None, description="Search subject, description, or ticket number"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List tickets with role-based access control:
    - Customers ONLY see their own tickets.
    - Support Agents and Admins see all tickets with filtering and search.
    """
    query = db.query(Ticket)

    if current_user.role == UserRole.CUSTOMER:
        query = query.filter(Ticket.customer_id == current_user.id)
    
    if status_filter:
        query = query.filter(Ticket.status == status_filter)
    if priority_filter:
        query = query.filter(Ticket.priority == priority_filter)
    if category_filter:
        query = query.filter(Ticket.category.ilike(f"%{category_filter}%"))
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Ticket.ticket_number.ilike(search_term),
                Ticket.subject.ilike(search_term),
                Ticket.description.ilike(search_term)
            )
        )

    tickets = query.order_by(Ticket.created_at.desc()).all()
    return [build_ticket_response(t) for t in tickets]

@router.get("/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket_detail(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve full ticket details and conversation thread.
    - Ownership enforced for customers.
    - Internal notes hidden from customers.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if current_user.role == UserRole.CUSTOMER and ticket.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this ticket"
        )

    messages = ticket.messages
    if current_user.role == UserRole.CUSTOMER:
        messages = [m for m in messages if not m.is_internal_note]

    ticket_data = build_ticket_response(ticket)
    ticket_data["messages"] = [build_message_response(m) for m in messages]
    return ticket_data

@router.post("/{ticket_id}/messages", response_model=TicketMessageResponse)
def add_ticket_message(
    ticket_id: uuid.UUID,
    message_in: TicketMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a message to a ticket conversation thread.
    - Customers can only reply to their own tickets (internal notes disallowed).
    - Support agents/admins can post public replies or internal notes.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if current_user.role == UserRole.CUSTOMER:
        if ticket.customer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        sender_type = MessageSenderType.CUSTOMER
        is_internal = False
        
        if ticket.status in [TicketStatus.RESOLVED, TicketStatus.WAITING_CUSTOMER]:
            ticket.status = TicketStatus.IN_PROGRESS
    else:
        sender_type = MessageSenderType.AGENT
        is_internal = message_in.is_internal_note
        if not is_internal and ticket.status == TicketStatus.OPEN:
            ticket.status = TicketStatus.IN_PROGRESS

    msg = TicketMessage(
        ticket_id=ticket.id,
        sender_id=current_user.id,
        sender_type=sender_type,
        message=message_in.message,
        is_internal_note=is_internal
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return build_message_response(msg)

@router.patch("/{ticket_id}/status", response_model=TicketResponse)
def update_ticket_status(
    ticket_id: uuid.UUID,
    status_in: TicketStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update ticket status with role validation."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if current_user.role == UserRole.CUSTOMER:
        if ticket.customer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        if status_in.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customers can only set status to 'resolved' or 'closed'"
            )

    ticket.status = status_in.status
    db.commit()
    db.refresh(ticket)
    return build_ticket_response(ticket)

@router.post("/{ticket_id}/assign", response_model=TicketResponse)
def assign_ticket_agent(
    ticket_id: uuid.UUID,
    assign_in: TicketAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SUPPORT_AGENT, UserRole.ADMIN]))
):
    """Assign a support agent to a ticket (Agents and Admins only)."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    target_agent = db.query(User).filter(User.id == assign_in.agent_id).first()
    if not target_agent or target_agent.role not in [UserRole.SUPPORT_AGENT, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target user is not an active support agent or admin"
        )

    ticket.assigned_agent_id = target_agent.id
    if ticket.status == TicketStatus.OPEN:
        ticket.status = TicketStatus.IN_PROGRESS

    assignment = TicketAssignment(
        ticket_id=ticket.id,
        agent_id=target_agent.id,
        assigned_by_id=current_user.id
    )
    db.add(assignment)
    db.commit()
    db.refresh(ticket)

    return build_ticket_response(ticket)

@router.get("/{ticket_id}/timeline", response_model=TicketTimelineResponse)
def get_ticket_timeline(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get full activity timeline for a ticket, including all multi-agent runs,
    telemetry, and customer/agent messages.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if current_user.role == UserRole.CUSTOMER and ticket.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    runs = db.query(AgentRun).filter(AgentRun.ticket_id == ticket_id).order_by(AgentRun.created_at.asc()).all()

    msgs = ticket.messages
    if current_user.role == UserRole.CUSTOMER:
        msgs = [m for m in msgs if not m.is_internal_note]

    return {
        "ticket_id": ticket.id,
        "ticket_number": ticket.ticket_number,
        "agent_runs": [
            {
                "id": r.id,
                "agent_name": r.agent_name,
                "input_data": r.input_data,
                "output_data": r.output_data,
                "status": r.status,
                "execution_time_ms": r.execution_time_ms,
                "created_at": r.created_at
            }
            for r in runs
        ],
        "messages": [build_message_response(m) for m in msgs]
    }

@router.post("/{ticket_id}/analyze", response_model=TicketResponse)
def trigger_ticket_analysis(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually triggers the LangGraph Multi-Agent pipeline synchronously on a ticket
    and returns the updated ticket with AI analysis.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if current_user.role == UserRole.CUSTOMER and ticket.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    execute_ticket_workflow(ticket_id, db)
    db.refresh(ticket)
    return build_ticket_response(ticket)
