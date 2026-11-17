# Cuort

**AI-Powered Customer Support Orchestrator**

Cuort is an AI-powered customer support management platform that automates the process of receiving, understanding, categorizing, and responding to customer complaints. Five specialized AI agents work together through a central orchestrator to find knowledge-based solutions, generate replies, and escalate complex or sensitive cases to human support agents.

## Project Goals

- Reduce manual customer-support workload.
- Reduce customer response and resolution time.
- Automatically identify complaint categories, sentiment, and priority.
- Provide answers grounded in company knowledge documents.
- Keep humans in control of sensitive and complicated cases.
- Provide a centralized dashboard for customers, support agents, and administrators.

## Primary Users

| User | Responsibilities |
|---|---|
| Customer | Submits complaints, tracks tickets, and communicates with support. |
| Support Agent | Reviews escalations, responds to customers, and resolves tickets. |
| Admin | Manages users, tickets, knowledge documents, categories, and system settings. |

## Core Functionalities

- Customer registration, login, and role-based access.
- Complaint submission with subject and description.
- Automatic ticket ID generation.
- AI-powered complaint classification, sentiment detection, and prioritization.
- Knowledge-base management and PDF uploads.
- Semantic search over company FAQs, policies, and support documents.
- AI-generated customer replies grounded in retrieved knowledge.
- Human review, editing, approval, and rejection of suggested replies.
- Escalation of complicated, critical, sensitive, or unsupported cases.
- Ticket assignment and status management.
- Customer and support-agent conversation history.
- Ticket search and filtering.
- Dashboard statistics and analytics.
- Agent activity timeline showing each agent's decisions and outputs.

## The Five AI Agents

### Agent 1 — Complaint Intake

- Reads incoming customer complaints.
- Understands the customer's problem and extracts important details.
- Produces a concise complaint summary.
- **Output:** Cleaned complaint, summary, and extracted information.

### Agent 2 — Classification and Priority

- Identifies the complaint category.
- Detects customer sentiment.
- Assigns Low, Medium, High, or Critical priority.
- **Output:** Category, priority, sentiment, and confidence.

### Agent 3 — Knowledge Retriever

- Searches company FAQs, policies, and uploaded documents.
- Uses embeddings and vector similarity search.
- Retrieves relevant passages and their source documents.
- **Output:** Matching knowledge passages, similarity scores, and document references.

### Agent 4 — Response Generator

- Creates professional, customer-friendly replies.
- Uses complaint details and retrieved knowledge.
- Avoids unsupported claims and identifies missing information.
- **Output:** Suggested response and supporting knowledge references.

### Agent 5 — Escalation Manager

- Evaluates priority, sensitivity, risk, evidence quality, and confidence.
- Identifies cases requiring human attention.
- Routes difficult complaints to the appropriate support team.
- **Output:** Escalation decision, reason, and recommended next action.

Agent 5 should use deterministic business rules for safety-critical routing. An LLM may provide supporting analysis, but it must not independently authorize sensitive actions such as refunds, account changes, or security-sensitive operations.

## End-to-End Working Flow

```mermaid
flowchart TD
    A[Customer submits complaint] --> B[Create ticket]
    B --> C[Agent 1: Intake]
    C --> D[Agent 2: Classification]
    D --> E{Critical or sensitive?}
    E -->|Yes| H[Agent 5: Human escalation]
    E -->|No| F[Agent 3: Knowledge retrieval]
    F --> G{Relevant evidence found?}
    G -->|No| H
    G -->|Yes| I[Agent 4: Generate reply]
    I --> J[Agent 5: Safety and confidence checks]
    J --> K{Safe to auto-send?}
    K -->|Yes| L[Send AI response]
    K -->|No| H
    L --> M[Update ticket and await customer]
    H --> N[Support agent reviews ticket]
    N --> O[Human sends response]
    M --> P[Ticket resolution or reopening]
    O --> P
```

### Flow Explanation

1. The customer submits a complaint through the Cuort website.
2. The backend validates the request and creates a ticket.
3. Agent 1 reads the complaint, extracts details, and creates a summary.
4. Agent 2 identifies its category, sentiment, and priority.
5. The orchestrator checks whether the case is critical or sensitive.
6. If it is critical or sensitive, the ticket is escalated to a human.
7. Otherwise, Agent 3 searches the knowledge base using Retrieval-Augmented Generation (RAG).
8. If relevant evidence is not found, the ticket is escalated.
9. If evidence is found, Agent 4 generates a grounded response.
10. Agent 5 checks safety, confidence, and auto-send eligibility.
11. Safe, low-risk cases may receive an automatic reply according to configured policies.
12. Other cases are assigned to a human support agent for review.
13. The system stores the response, agent activity, and ticket status.
14. The customer can reply, confirm resolution, or reopen an unresolved ticket.

## Use Cases

| Use case | Cuort behavior |
|---|---|
| Delivery complaint | Retrieves delivery policies and provides guidance; escalates shipment disputes when needed. |
| Refund request | Retrieves refund policy; routes refund approval or payment actions to a human. |
| Login issue | Retrieves account troubleshooting instructions; escalates security concerns. |
| Billing dispute | Identifies and prioritizes the dispute, then routes it to billing support. |
| Product issue | Retrieves troubleshooting guides and suggests relevant steps. |
| Angry customer | Detects negative sentiment and can prioritize human attention. |
| Missing information | Requests clarification or escalates when no reliable solution is available. |

## Technology Stack

The project uses a Python backend and an AI-focused architecture. Prefer free and open-source tools for development. External API free tiers and cloud hosting may have usage limits or change their terms.

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React.js | Customer, support, and admin interfaces |
| Frontend language | TypeScript | Type-safe frontend development |
| Styling | Tailwind CSS | Responsive user interface |
| Backend language | Python 3.12+ | Backend and AI application logic |
| API framework | FastAPI | REST APIs and request handling |
| Agent orchestration | LangGraph | Stateful, conditional multi-agent workflow |
| LLM provider | Groq API | Language understanding and response generation |
| LLM integration | Groq Python SDK / LangChain Groq | Calls to Groq-hosted models |
| Main database | PostgreSQL | Users, tickets, messages, and application data |
| Vector search | pgvector | Similarity search over knowledge chunks |
| Embeddings | Sentence Transformers, `all-MiniLM-L6-v2` | Local text embeddings |
| Embedding runtime | ONNX Runtime (optional optimization) | Efficient local embedding inference |
| ORM | SQLAlchemy | Database models and queries |
| Validation/settings | Pydantic and pydantic-settings | Data validation and configuration |
| PDF processing | PyMuPDF | Extract text from uploaded PDFs |
| Authentication | JWT + Argon2 password hashing | Secure sessions and password storage |
| Testing | Pytest and HTTPX | Backend and API tests |
| Frontend testing | Vitest | Frontend unit tests |
| API documentation | FastAPI OpenAPI / Swagger UI | Interactive API documentation |
| Containers | Docker and Docker Compose | Consistent local development and deployment |
| Version control | Git and GitHub | Source control and collaboration |
| IDE | VS Code | Development environment |

### Important Technology Notes

- **Groq is the LLM provider.** Configure the model through environment variables so it can be changed without modifying agent code. Check the current Groq model catalogue and rate limits before choosing a model.
- **LangGraph coordinates the agents.** It manages shared workflow state, conditional routing, and execution flow. The five agents should be Python modules/nodes in one modular backend, not five separate services.
- **Sentence Transformers creates embeddings locally.** The embedding model is separate from the Groq chat model; do not assume Groq provides the embeddings used by this RAG setup.
- **PostgreSQL + pgvector stores and searches embeddings.** The same PostgreSQL instance can store application records and knowledge chunks.
- **Human approval is required for sensitive actions.** AI-generated text should not independently issue refunds, modify accounts, or perform security-sensitive operations.
- **Free does not mean unlimited.** Groq API access, cloud hosting, and hosted databases may have quotas, rate limits, or paid plans.

## Suggested Database Tables

| Table | Purpose |
|---|---|
| `users` | Customer, support-agent, and admin accounts |
| `tickets` | Complaint details, category, priority, and status |
| `ticket_messages` | Customer, AI, and human conversation messages |
| `agent_runs` | Agent inputs, outputs, status, and execution metadata |
| `knowledge_documents` | Uploaded document metadata and processing status |
| `knowledge_chunks` | Extracted text chunks, document references, and embeddings |
| `ticket_assignments` | Human support-agent assignments |

Use UUID primary keys, timestamps, foreign keys, appropriate indexes, and role-based access controls.

## Suggested Backend API Routes

Use the `/api/v1` prefix.

| Method | Route | Purpose |
|---|---|---|
| POST | `/auth/register` | Register a user |
| POST | `/auth/login` | Authenticate a user |
| POST | `/tickets` | Create a complaint ticket |
| GET | `/tickets` | List tickets allowed for the current user |
| GET | `/tickets/{ticket_id}` | Get ticket details |
| POST | `/tickets/{ticket_id}/messages` | Add a conversation message |
| GET | `/tickets/{ticket_id}/timeline` | View ticket and agent activity |
| POST | `/knowledge/upload` | Upload a knowledge document |
| GET | `/knowledge` | List knowledge documents |
| POST | `/tickets/{ticket_id}/assign` | Assign a human support agent |
| POST | `/tickets/{ticket_id}/approve` | Approve a suggested response |
| POST | `/tickets/{ticket_id}/escalate` | Escalate a ticket |
| GET | `/admin/analytics` | View administrative analytics |

Protect routes with authentication and role-based authorization. Validate ownership so customers can only access their own tickets.

## Suggested Repository Structure

```text
cuort/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   │   ├── customer/
│   │   │   ├── support/
│   │   │   └── admin/
│   │   ├── layouts/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── types/
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── api/
│   │   ├── agents/
│   │   │   ├── intake_agent.py
│   │   │   ├── classification_agent.py
│   │   │   ├── knowledge_agent.py
│   │   │   ├── response_agent.py
│   │   │   └── escalation_agent.py
│   │   ├── orchestrator/
│   │   │   ├── graph.py
│   │   │   └── state.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   └── security/
│   ├── tests/
│   └── requirements.txt
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## Environment Configuration

Create a local `.env` file in the backend directory. Never commit it to Git.

```env
APP_NAME=Cuort
APP_ENV=development

GROQ_API_KEY=replace_with_your_groq_api_key
GROQ_MODEL=replace_with_a_current_supported_model

DATABASE_URL=postgresql+psycopg://cuort:change_me@localhost:5432/cuort

JWT_SECRET_KEY=replace_with_a_long_random_secret
JWT_ALGORITHM=HS256

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

Commit only `.env.example` with placeholder values. Keep the real API key on the backend and never expose it to the React frontend.

## One-Month Development Plan

### Week 1 — Application Foundation

- Set up the React frontend and FastAPI backend.
- Configure PostgreSQL and pgvector.
- Implement registration, login, and role-based access.
- Build ticket creation, listing, and detail views.
- Create initial customer, support, and admin dashboards.

**Milestone:** Working customer-support ticket platform.

### Week 2 — AI Intake and Classification

- Integrate the Groq API.
- Implement Agent 1 for complaint understanding and summaries.
- Implement Agent 2 for category, sentiment, and priority.
- Create the LangGraph workflow and shared state.
- Store agent execution results.

**Milestone:** AI-powered ticket analysis.

### Week 3 — Knowledge Retrieval and Responses

- Implement PDF upload and text extraction.
- Split documents into searchable chunks.
- Generate local embeddings and store them in pgvector.
- Implement Agent 3 with RAG.
- Implement Agent 4 for evidence-grounded replies.

**Milestone:** Knowledge-based AI response generation.

### Week 4 — Escalation, Testing, and Deployment

- Implement Agent 5 and human handoff.
- Add support-agent review and response approval.
- Complete the activity timeline and basic analytics.
- Test the complete workflow, permissions, and failure cases.
- Containerize the application and prepare a demo.

**Milestone:** Cuort MVP ready for demonstration.

## Security and Reliability Requirements

- Hash passwords using Argon2; never store plain-text passwords.
- Keep Groq API keys and JWT secrets in environment variables.
- Enforce role-based permissions on every protected endpoint.
- Validate uploaded file types and sizes.
- Treat uploaded documents and customer messages as untrusted input.
- Do not let retrieved document text override system instructions.
- Use retrieved evidence as the source for policy answers and retain document references.
- Escalate when evidence is missing, confidence is inadequate, or a case is sensitive.
- Require human approval for refunds, account changes, and other sensitive operations.
- Handle Groq rate limits, timeouts, and temporary failures without losing tickets.
- Record agent decisions and errors without logging passwords, API keys, or unnecessary personal data.

## MVP Acceptance Criteria

The first version is complete when:

1. A customer can register, log in, submit a complaint, and view its ticket.
2. Agents 1 and 2 produce structured summaries and classifications.
3. An admin can upload a PDF and see its processing status.
4. Agent 3 can retrieve relevant passages from the uploaded knowledge base.
5. Agent 4 can generate a reply grounded in retrieved passages.
6. Agent 5 can route critical, sensitive, unsupported, or low-confidence cases to a human.
7. A support agent can review an escalation and send a response.
8. Ticket messages, status changes, and agent activity are persisted.
9. Customers cannot access other customers' tickets or privileged admin functions.
10. The core application can be started locally using documented setup instructions.

## Project Scope Decisions

For the one-month MVP:

- Build a modular monolith with one FastAPI backend.
- Keep each agent in a separate Python module.
- Use LangGraph for workflow orchestration.
- Use Groq for LLM inference and local embeddings for RAG.
- Use PostgreSQL with pgvector instead of a separate vector database.
- Start with in-app customer complaints; add email or WhatsApp integrations later.
- Avoid microservices, Kubernetes, Redis, and unnecessary infrastructure until the MVP works.

---

**Cuort — Intelligent Support. Faster Resolutions.**
