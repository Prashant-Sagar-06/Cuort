import uuid
from typing import Dict, Any
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, START, END

from backend.app.orchestrator.state import TicketWorkflowState
from backend.app.agents.intake_agent import run_intake_agent
from backend.app.agents.classification_agent import run_classification_agent
from backend.app.models.ticket import (
    Ticket,
    TicketMessage,
    TicketPriority,
    TicketStatus,
    MessageSenderType
)
from backend.app.models.agent_run import AgentRun

def intake_node(state: TicketWorkflowState) -> Dict[str, Any]:
    """LangGraph node: Executes Agent 1 (Intake)."""
    subject = state.get("subject", "")
    description = state.get("description", "")
    
    agent_res = run_intake_agent(subject, description)
    data = agent_res.get("data", {})
    
    log = {
        "agent_name": "agent_1_intake",
        "input": {"subject": subject, "description": description},
        "output": data,
        "status": agent_res.get("status", "success"),
        "execution_time_ms": agent_res.get("execution_time_ms", 0)
    }
    logs = list(state.get("agent_logs", []))
    logs.append(log)

    return {
        "cleaned_complaint": data.get("cleaned_complaint"),
        "summary": data.get("summary"),
        "extracted_entities": data.get("extracted_entities"),
        "agent_logs": logs
    }

def classification_node(state: TicketWorkflowState) -> Dict[str, Any]:
    """LangGraph node: Executes Agent 2 (Classification & Priority)."""
    cleaned = state.get("cleaned_complaint", "")
    summary = state.get("summary", "")
    entities = state.get("extracted_entities", {})

    agent_res = run_classification_agent(cleaned, summary, entities)
    data = agent_res.get("data", {})

    log = {
        "agent_name": "agent_2_classification",
        "input": {"cleaned_complaint": cleaned, "summary": summary, "entities": entities},
        "output": data,
        "status": agent_res.get("status", "success"),
        "execution_time_ms": agent_res.get("execution_time_ms", 0)
    }
    logs = list(state.get("agent_logs", []))
    logs.append(log)

    return {
        "category": data.get("category"),
        "priority": data.get("priority"),
        "sentiment": data.get("sentiment"),
        "confidence": data.get("confidence"),
        "is_critical": data.get("is_critical"),
        "is_sensitive": data.get("is_sensitive"),
        "agent_logs": logs
    }

def escalation_check_node(state: TicketWorkflowState) -> Dict[str, Any]:
    """
    Evaluates safety rules:
    Critical or highly sensitive tickets are escalated to human support immediately.
    """
    is_critical = state.get("is_critical", False)
    is_sensitive = state.get("is_sensitive", False)
    priority = state.get("priority", "medium")

    requires_escalation = False
    escalation_reason = None
    status = "in_progress"

    if is_critical or priority == "critical":
        requires_escalation = True
        escalation_reason = "Critical priority or severe disruption detected"
        status = "escalated"
    elif is_sensitive:
        requires_escalation = True
        escalation_reason = "Sensitive case (financial/refund or security risk) requires human oversight"
        status = "escalated"

    log = {
        "agent_name": "escalation_rules",
        "input": {"is_critical": is_critical, "is_sensitive": is_sensitive, "priority": priority},
        "output": {"requires_escalation": requires_escalation, "escalation_reason": escalation_reason, "status": status},
        "status": "success",
        "execution_time_ms": 1
    }
    logs = list(state.get("agent_logs", []))
    logs.append(log)

    return {
        "requires_escalation": requires_escalation,
        "escalation_reason": escalation_reason,
        "status": status,
        "agent_logs": logs
    }

def build_ticket_graph():
    """Build and compile the LangGraph workflow for ticket analysis."""
    graph = StateGraph(TicketWorkflowState)

    graph.add_node("intake", intake_node)
    graph.add_node("classification", classification_node)
    graph.add_node("escalation_check", escalation_check_node)

    graph.add_edge(START, "intake")
    graph.add_edge("intake", "classification")
    graph.add_edge("classification", "escalation_check")
    graph.add_edge("escalation_check", END)

    return graph.compile()

# Global compiled instance
ticket_orchestrator = build_ticket_graph()

def execute_ticket_workflow(ticket_id: uuid.UUID, db: Session) -> TicketWorkflowState:
    """
    Executes the full LangGraph pipeline for a ticket and persists
    all agent outputs, telemetry, and status changes in PostgreSQL.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise ValueError(f"Ticket {ticket_id} not found")

    initial_state: TicketWorkflowState = {
        "ticket_id": str(ticket.id),
        "subject": ticket.subject,
        "description": ticket.description,
        "agent_logs": [],
        "errors": []
    }

    final_state = ticket_orchestrator.invoke(initial_state)

    # Persist Agent Runs to PostgreSQL audit log
    for log in final_state.get("agent_logs", []):
        run = AgentRun(
            ticket_id=ticket.id,
            agent_name=log["agent_name"],
            input_data=log["input"],
            output_data=log["output"],
            status=log["status"],
            execution_time_ms=log["execution_time_ms"]
        )
        db.add(run)

    # Update Ticket entity with AI insights
    if final_state.get("summary"):
        ticket.summary = final_state["summary"]
    if final_state.get("category"):
        ticket.category = final_state["category"]
    if final_state.get("sentiment"):
        ticket.sentiment = final_state["sentiment"]
    if final_state.get("priority"):
        # Map string to TicketPriority enum
        p_val = final_state["priority"].lower()
        if p_val in [p.value for p in TicketPriority]:
            ticket.priority = TicketPriority(p_val)

    # Update ticket status if escalated
    if final_state.get("requires_escalation"):
        ticket.status = TicketStatus.ESCALATED
        # Add automated internal note for the support team
        note = TicketMessage(
            ticket_id=ticket.id,
            sender_id=None,
            sender_type=MessageSenderType.SYSTEM,
            message=f"Ticket escalated by AI Orchestrator. Reason: {final_state.get('escalation_reason')}",
            is_internal_note=True
        )
        db.add(note)
    elif ticket.status == TicketStatus.OPEN:
        ticket.status = TicketStatus.IN_PROGRESS

    db.commit()
    db.refresh(ticket)
    return final_state
