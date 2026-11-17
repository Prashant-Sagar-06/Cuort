import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.agents.intake_agent import run_intake_agent
from backend.app.agents.classification_agent import run_classification_agent
from backend.tests.test_tickets import create_user_and_login

client = TestClient(app)

def test_intake_agent_unit():
    subject = "Login failure on mobile app"
    desc = "I am unable to log in since yesterday. It gives error code 500 when I enter my email."
    res = run_intake_agent(subject, desc)
    assert res["status"] == "success"
    data = res["data"]
    assert "summary" in data
    assert len(data["summary"]) > 0
    assert "extracted_entities" in data

def test_classification_agent_unit():
    cleaned = "The package was delayed by 10 days and I received the wrong shoes."
    summary = "Wrong shoes delivered after 10 days delay."
    entities = {"product": "shoes", "issue": "wrong item"}
    res = run_classification_agent(cleaned, summary, entities)
    assert res["status"] == "success"
    data = res["data"]
    assert data["category"] in [
        "Delivery & Shipping", "Billing & Refund", "Product Issue",
        "Account & Security", "Technical Support", "General Inquiry"
    ]
    assert data["priority"] in ["low", "medium", "high", "critical"]
    assert "sentiment" in data

def test_ticket_timeline_and_agent_run_persistence():
    # Login as customer
    cust_token, _ = create_user_and_login("agent_test_cust@cuort.ai", "customer")
    headers = {"Authorization": f"Bearer {cust_token}"}

    # Create ticket
    create_res = client.post("/api/v1/tickets", headers=headers, json={
        "subject": "Charged twice for subscription",
        "description": "I noticed two charges of $49 on my credit card statement for Order #SUB-999. Please refund the duplicate.",
        "category": "Billing"
    })
    assert create_res.status_code == 201
    ticket_id = create_res.json()["id"]

    # Trigger synchronous analysis
    analyze_res = client.post(f"/api/v1/tickets/{ticket_id}/analyze", headers=headers)
    assert analyze_res.status_code == 200
    ticket_data = analyze_res.json()
    assert ticket_data["summary"] is not None
    assert ticket_data["sentiment"] is not None

    # Fetch timeline
    timeline_res = client.get(f"/api/v1/tickets/{ticket_id}/timeline", headers=headers)
    assert timeline_res.status_code == 200
    timeline = timeline_res.json()
    assert len(timeline["agent_runs"]) >= 2
    agent_names = [r["agent_name"] for r in timeline["agent_runs"]]
    assert "agent_1_intake" in agent_names
    assert "agent_2_classification" in agent_names
