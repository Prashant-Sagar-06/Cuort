import json
import time
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from backend.app.config import settings

INTAKE_SYSTEM_PROMPT = """You are Agent 1 (Complaint Intake) for Cuort, an AI-powered customer support management system.
Your goal is to parse incoming customer complaints, extract critical details, and produce a concise summary.

You must return a valid JSON object matching this structure:
{
  "cleaned_complaint": "Cleaned, coherent statement of the complaint without conversational fluff",
  "summary": "A concise 1-2 sentence executive summary of what happened and what the customer wants",
  "extracted_entities": {
    "order_id": "Extracted order number or null if not provided",
    "product_name": "Extracted product name/model or null",
    "issue_type": "Primary issue (e.g., damaged goods, delay, billing, login, refund)",
    "customer_goal": "What the customer wants resolved (e.g., refund, replacement, explanation, fix)"
  }
}

Important:
- Return ONLY the raw JSON object. Do not wrap in markdown quotes like ```json or include conversational text.
"""

def run_intake_agent(subject: str, description: str) -> Dict[str, Any]:
    """
    Agent 1: Cleans complaint, extracts structured entities, and summarizes the issue.
    """
    start_time = time.time()
    
    llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        temperature=0.0
    )

    user_content = f"Subject: {subject}\nDescription: {description}"
    messages = [
        SystemMessage(content=INTAKE_SYSTEM_PROMPT),
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
        return {
            "status": "success",
            "execution_time_ms": execution_time_ms,
            "data": {
                "cleaned_complaint": result.get("cleaned_complaint", description),
                "summary": result.get("summary", subject),
                "extracted_entities": result.get("extracted_entities", {})
            }
        }
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        return {
            "status": "failed",
            "execution_time_ms": execution_time_ms,
            "error": str(e),
            "data": {
                "cleaned_complaint": description,
                "summary": subject,
                "extracted_entities": {}
            }
        }
