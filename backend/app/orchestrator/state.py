from typing import TypedDict, Optional, List, Dict, Any

class TicketWorkflowState(TypedDict, total=False):
    # Initial ticket inputs
    ticket_id: str
    subject: str
    description: str

    # Agent 1: Complaint Intake outputs
    cleaned_complaint: Optional[str]
    summary: Optional[str]
    extracted_entities: Optional[Dict[str, Any]]

    # Agent 2: Classification & Priority outputs
    category: Optional[str]
    sentiment: Optional[str]
    priority: Optional[str]
    confidence: Optional[float]
    is_critical: Optional[bool]
    is_sensitive: Optional[bool]

    # Escalation & routing flags
    requires_escalation: Optional[bool]
    escalation_reason: Optional[str]

    # Future Agents (Week 3/4)
    suggested_reply: Optional[str]
    knowledge_references: Optional[List[Dict[str, Any]]]

    # Execution telemetry & audit trail
    agent_logs: List[Dict[str, Any]]
    errors: List[str]
