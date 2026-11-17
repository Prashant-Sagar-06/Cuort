import json
import time
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from backend.app.config import settings

CLASSIFICATION_SYSTEM_PROMPT = """You are Agent 2 (Classification & Priority) for Cuort, an AI-powered customer support management system.
Your job is to analyze a customer complaint and its summary, then determine the category, sentiment, priority, confidence, and sensitivity flags.

Categories must be one of:
- "Delivery & Shipping"
- "Billing & Refund"
- "Product Issue"
- "Account & Security"
- "Technical Support"
- "General Inquiry"

Priorities must be one of:
- "low": General inquiries, feedback, minor delays without urgency.
- "medium": Standard product issues, routine inquiries, normal shipping questions.
- "high": Damaged items, recurring problems, angry customers, high value disputes.
- "critical": System downtime, security breaches, unauthorized charges, severe safety or legal threats.

Sentiments must be one of:
- "Positive"
- "Neutral"
- "Negative"
- "Frustrated"
- "Angry"

Safety & Escalation Rules:
- Set "is_critical" to true if priority is "critical" or customer mentions legal action, fraud, or complete service blockage.
- Set "is_sensitive" to true if the request involves refunds, billing disputes, password/security changes, or abusive behavior.

Return ONLY a valid JSON object matching this exact schema:
{
  "category": "One of the approved categories",
  "priority": "low | medium | high | critical",
  "sentiment": "One of the approved sentiments",
  "confidence": 0.0 to 1.0,
  "is_critical": true | false,
  "is_sensitive": true | false,
  "reason": "Brief 1-sentence rationale for the classification and priority"
}

Important:
- Return ONLY the raw JSON object. Do not include markdown quotes like ```json or any conversational text.
"""

def run_classification_agent(cleaned_complaint: str, summary: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent 2: Classifies category, detects sentiment, assigns priority and sensitivity flags.
    """
    start_time = time.time()
    
    llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        temperature=0.0
    )

    user_content = (
        f"Complaint: {cleaned_complaint}\n"
        f"Summary: {summary}\n"
        f"Key Entities: {json.dumps(entities)}"
    )

    messages = [
        SystemMessage(content=CLASSIFICATION_SYSTEM_PROMPT),
        HumanMessage(content=user_content)
    ]

    try:
        response = llm.invoke(messages)
        content = response.content.strip()

        # Clean potential markdown code fence
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        result = json.loads(content)
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Normalize priority
        priority = result.get("priority", "medium").lower()
        if priority not in ["low", "medium", "high", "critical"]:
            priority = "medium"

        return {
            "status": "success",
            "execution_time_ms": execution_time_ms,
            "data": {
                "category": result.get("category", "General Inquiry"),
                "priority": priority,
                "sentiment": result.get("sentiment", "Neutral"),
                "confidence": float(result.get("confidence", 0.85)),
                "is_critical": bool(result.get("is_critical", priority == "critical")),
                "is_sensitive": bool(result.get("is_sensitive", False)),
                "reason": result.get("reason", "Standard classification")
            }
        }
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        return {
            "status": "failed",
            "execution_time_ms": execution_time_ms,
            "error": str(e),
            "data": {
                "category": "General Inquiry",
                "priority": "medium",
                "sentiment": "Neutral",
                "confidence": 0.5,
                "is_critical": False,
                "is_sensitive": False,
                "reason": f"Fallback due to analysis error: {e}"
            }
        }
