import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def create_user_and_login(email: str, role: str):
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "full_name": f"User {role}",
        "role": role
    })
    res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    assert res.status_code == 200
    return res.json()["access_token"], res.json()["user"]

def test_ticket_lifecycle_and_rbac():
    # 1. Setup Customer and Agent
    cust_token, cust_user = create_user_and_login("customer1@cuort.ai", "customer")
    agent_token, agent_user = create_user_and_login("agent1@cuort.ai", "support_agent")
    cust2_token, cust2_user = create_user_and_login("customer2@cuort.ai", "customer")

    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    agent_headers = {"Authorization": f"Bearer {agent_token}"}
    cust2_headers = {"Authorization": f"Bearer {cust2_token}"}

    # 2. Customer 1 creates a ticket
    create_res = client.post("/api/v1/tickets", headers=cust_headers, json={
        "subject": "Damaged product received",
        "description": "My package arrived with a cracked screen. Please help.",
        "category": "Product Issue"
    })
    assert create_res.status_code == 201
    ticket = create_res.json()
    ticket_id = ticket["id"]
    assert ticket["subject"] == "Damaged product received"
    assert ticket["ticket_number"].startswith("TCK-")
    assert ticket["status"] == "open"

    # 3. Customer 1 lists tickets -> sees it
    list_cust = client.get("/api/v1/tickets", headers=cust_headers)
    assert list_cust.status_code == 200
    assert any(t["id"] == ticket_id for t in list_cust.json())

    # 4. Customer 2 lists tickets -> does NOT see Customer 1's ticket
    list_cust2 = client.get("/api/v1/tickets", headers=cust2_headers)
    assert list_cust2.status_code == 200
    assert not any(t["id"] == ticket_id for t in list_cust2.json())

    # 5. Customer 2 tries to GET Customer 1's ticket detail -> 403 Forbidden
    detail_cust2 = client.get(f"/api/v1/tickets/{ticket_id}", headers=cust2_headers)
    assert detail_cust2.status_code == 403

    # 6. Customer 1 adds a follow-up message
    msg_res = client.post(f"/api/v1/tickets/{ticket_id}/messages", headers=cust_headers, json={
        "message": "Here is an update: the box was also wet."
    })
    assert msg_res.status_code == 200
    assert msg_res.json()["sender_type"] == "customer"

    # 7. Agent views full ticket details
    detail_agent = client.get(f"/api/v1/tickets/{ticket_id}", headers=agent_headers)
    assert detail_agent.status_code == 200
    detail_data = detail_agent.json()
    assert len(detail_data["messages"]) >= 2

    # 8. Agent posts an internal note
    internal_res = client.post(f"/api/v1/tickets/{ticket_id}/messages", headers=agent_headers, json={
        "message": "Checking with logistics partner FedEx.",
        "is_internal_note": True
    })
    assert internal_res.status_code == 200
    assert internal_res.json()["is_internal_note"] is True

    # 9. Customer 1 views ticket -> internal note is hidden from customer
    detail_cust = client.get(f"/api/v1/tickets/{ticket_id}", headers=cust_headers)
    assert detail_cust.status_code == 200
    messages = detail_cust.json()["messages"]
    assert all(m["is_internal_note"] is False for m in messages)

    # 10. Agent assigns ticket to themselves
    assign_res = client.post(f"/api/v1/tickets/{ticket_id}/assign", headers=agent_headers, json={
        "agent_id": agent_user["id"]
    })
    assert assign_res.status_code == 200
    assert assign_res.json()["assigned_agent_id"] == agent_user["id"]

    # 11. Customer resolves ticket
    status_res = client.patch(f"/api/v1/tickets/{ticket_id}/status", headers=cust_headers, json={
        "status": "resolved"
    })
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "resolved"
