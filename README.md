# ServiceNow Agentic Incident Flow (Task 0)

An automated IT incident triage pipeline connecting **ServiceNow Personal Developer Instance (PDI)** and **Google Gemini LLM** via a secure, high-performance **FastAPI** backend service.

---

## 📹 Live Demo Video

📺 **Watch the 2–4 Minute End-to-End Walkthrough:**
👉 **[Click Here to Play the Demo Video](assets/demo_video.mp4)**

*(The demo video is embedded directly in the repository at `assets/demo_video.mp4` — click the link above to play it directly in GitHub's built-in media player!)*

*Demonstrating: Incident creation on live ServiceNow PDI, asynchronous webhook trigger via ngrok, Gemini reasoning, and automatic write-back for `respond`, `ask`, and `escalate`.*

---

## Architecture Flow

```mermaid
sequenceDiagram
    participant User as 👤 ServiceNow User
    participant SN as 🏢 ServiceNow PDI
    participant BR as ⚡ Business Rule (Async)
    participant Ngrok as 🌐 ngrok Public Tunnel
    participant FastAPIMiddleware as 🛡️ Webhook Auth Middleware
    participant WebhookAPI as 🚀 POST /api/v1/webhook
    participant Processor as ⚙️ Incident Processor
    participant Gemini as 🤖 Gemini LLM
    participant SNRestAPI as 📝 ServiceNow Table API

    User->>SN: Creates new incident
    SN->>BR: Triggers (after insert)
    BR->>Ngrok: POST /api/v1/webhook + X-Webhook-Secret
    Ngrok->>FastAPIMiddleware: Forward payload
    alt Invalid or missing secret
        FastAPIMiddleware-->>Ngrok: 401 Unauthorized
    end
    FastAPIMiddleware->>WebhookAPI: Authenticated request
    WebhookAPI->>Processor: Deduplication check
    alt Duplicate incident
        WebhookAPI-->>Ngrok: 202 Accepted ("status": "duplicate")
    end
    WebhookAPI-->>Ngrok: 202 Accepted (< 2s, queued)
    Note over WebhookAPI,Processor: Immediate response avoids ServiceNow timeout
    Processor->>Gemini: Classify incident against 5 KB articles
    Gemini-->>Processor: JSON {"decision": "...", "message": "..."}
    alt Decision: "respond"
        Processor->>SNRestAPI: PATCH incident (work_notes + close_notes + close_code + state=6 Resolved)
    else Decision: "ask"
        Processor->>SNRestAPI: PATCH incident (comments visible to user)
    else Decision: "escalate"
        Processor->>SNRestAPI: PATCH incident (internal work_notes for human agent)
    end
    SNRestAPI-->>SN: Incident updated automatically
```

---

## 1. Quickstart: How to Run the App

### Step 1: Environment Configuration
Ensure your `.env` file in the project root is configured:

```env
# Gemini API Key (from https://aistudio.google.com/apikey)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash

# ServiceNow PDI Instance
SERVICENOW_INSTANCE_URL=https://devXXXXXX.service-now.com
SERVICENOW_USERNAME=agent
SERVICENOW_PASSWORD=your_password_here
WEBHOOK_SECRET=[ENCRYPTION_KEY]
```

### Step 2: Start the FastAPI Server
Open a terminal in the project directory and run:

```bash
uv run uvicorn src.main:app --reload --port 8000
```

You should see logs indicating:
- `Configuration validated ✓`
- `All services initialized ✓`
- `Webhook ready at POST /api/v1/webhook`
- `Health check at GET /api/v1/health`
- `Uvicorn running on http://127.0.0.1:8000`

---

## 2. Interactive Browser Testing (Swagger UI)

FastAPI provides an interactive web interface out of the box:

1. Open your browser and navigate to:
   👉 **http://localhost:8000/docs**

2. **Test Health Endpoint:**
   - Click on **GET /api/v1/health**
   - Click **Try it out** ➔ **Execute**
   - Result: `200 OK`

3. **Test Webhook Endpoint:**
   - Click on **POST /api/v1/webhook**
   - Click **Try it out**
   - In **X-Webhook-Secret**, enter: `task0-secret-key-2026`
   - In **Request body**, enter a sample payload:
     ```json
     {
       "incident_sys_id": "test_sys_id_001",
       "number": "INC0010001",
       "short_description": "Printer not printing after office move",
       "description": "It was working yesterday. I tried turning it off and on.",
       "priority": 3
     }
     ```
   - Click **Execute** ➔ Result: `202 Accepted`!

---

## 3. Exposing via ngrok for ServiceNow

1. In a second terminal window, run:
   ```bash
   ngrok http 8000
   ```
2. Note your public forwarding HTTPS URL.
3. Your public webhook endpoint URL is:
   `https://<your-subdomain>.ngrok-free.app/api/v1/webhook`

---

## 4. Setting up ServiceNow Business Rule

1. Log into your ServiceNow instance.
2. Navigate to **System Definition > Business Rules** and click **New**.
3. Configure the Business Rule:
   - **Name**: `Task0 Agentic Incident Webhook`
   - **Table**: `Incident [incident]`
   - **Active**: Checked
   - **Advanced**: Checked
4. Under the **When to run** tab:
   - **When**: `after`
   - **Insert**: Checked
5. Under the **Advanced** tab, paste the code from `assets/business_rule.js`:
   ```javascript
   (function executeRule(current, previous /*null when async*/) {
       try {
           var payload = {
               "incident_sys_id": current.getValue('sys_id'),
               "number": current.getValue('number'),
               "short_description": current.getValue('short_description'),
               "description": current.getValue('description'),
               "priority": parseInt(current.getValue('priority'), 10)
           };

           var r = new sn_ws.RESTMessageV2();
           r.setEndpoint('https://<your-subdomain>.ngrok-free.app/api/v1/webhook');
           r.setHttpMethod('POST');
           r.setRequestHeader('Content-Type', 'application/json');
           r.setRequestHeader('X-Webhook-Secret', 'task0-secret-key-2026');
           r.setRequestBody(JSON.stringify(payload));
           r.executeAsync();

           gs.info('Task0: sent incident ' + current.getValue('number'));
       } catch (ex) {
           gs.error('Task0: failed to send incident: ' + ex.message);
       }
   })(current, previous);
   ```
6. Click **Submit**.

---

## 5. End-to-End Test Scenarios

| Scenario | Short Description | Description | Expected Decision | Resulting Action on Ticket |
|---|---|---|---|---|
| **Incident 1** | `Printer not printing after office move` | `It was working yesterday. I tried turning it off and on.` | **`respond`** | Ticket resolved (`state=6`), `close_code="Solution provided"`, solution posted in `work_notes` & `close_notes`. |
| **Incident 2** | `Cannot send email` | `It just doesn't work.` | **`ask`** | Clarifying question added to customer-facing `comments`. |
| **Incident 3** | `Request: annual leave approval` | `I would like to take next week off.` | **`escalate`** | Internal `work_notes` added routing to a human agent. |

---

## 6. Automated Testing (99% Coverage)

```bash
# Run all unit, integration, and E2E tests
uv run pytest -v

# Run with test coverage report
uv run pytest --cov=src -v
```

---

## 7. Verification Screenshots

Live test executions captured on ServiceNow PDI:

### Scenario 1: `respond` — Network Printer Issue
| Before Submit (Form Creation) | After Agent Processing (Resolved) |
|---|---|
| ![Incident 1 Before](assets/screenshots/incident_1_respond_before.png) | ![Incident 1 After](assets/screenshots/incident_1_respond_after.png) |

---

### Scenario 2: `ask` — Vague Email Issue
| Before Submit (Form Creation) | After Agent Processing (Customer Comment) |
|---|---|
| ![Incident 2 Before](assets/screenshots/incident_2_ask_before.png) | ![Incident 2 After](assets/screenshots/incident_2_ask_after.png) |

---

### Scenario 3: `escalate` — Annual Leave Request (Out of Scope)
| After Agent Processing (Internal Work Note) |
|---|
| ![Incident 3 After](assets/screenshots/incident_3_escalate_after.png) |

---

## 8. Repository Structure & Deliverables

```text
.
├── .env.example                  # Environment variable template (NFR2)
├── .gitignore                    # Git ignore rules
├── pyproject.toml                # uv & Python project configuration
├── README.md                     # Comprehensive architecture & setup guide
├── prompt.txt                    # Deliverable 4: Exact Gemini prompt payload
├── reflection.md                 # Deliverable 5: Engineering reflection note
├── assets/
│   ├── demo_video.mp4            # Deliverable 2: End-to-end demo video walkthrough
│   ├── business_rule.js          # ServiceNow Business Rule script
│   ├── kb_articles.json          # 5 reference knowledge-base articles
│   ├── payload_contract.json     # ServiceNow incident payload contract
│   ├── test_incidents.json       # 3 required test scenarios
│   └── screenshots/              # Deliverable 3: Incident verification images
│       ├── incident_1_respond_before.png
│       ├── incident_1_respond_after.png
│       ├── incident_2_ask_before.png
│       ├── incident_2_ask_after.png
│       └── incident_3_escalate_after.png
├── src/
│   ├── main.py                   # FastAPI lifespan & app entrypoint
│   ├── api/
│   │   ├── dependencies.py       # FastAPI dependency injection
│   │   ├── middleware/auth.py    # X-Webhook-Secret authentication middleware
│   │   └── routes/
│   │       ├── health.py         # GET /api/v1/health endpoint
│   │       └── webhook.py        # POST /api/v1/webhook endpoint
│   ├── core/
│   │   ├── config.py             # Pydantic BaseSettings (.env loading)
│   │   └── security.py           # Constant-time token comparison
│   ├── prompts/
│   │   ├── builder.py            # Dynamic prompt builder
│   │   └── templates.py          # Grounded system instructions
│   ├── schemas/
│   │   ├── decision.py           # GeminiDecision schema (respond/ask/escalate)
│   │   ├── incident.py           # IncidentPayload matching contract exactly
│   │   └── responses.py          # WebhookResponse and ErrorResponse
│   └── services/
│       ├── gemini_service.py     # Google Gemini API integration
│       ├── incident_processor.py # Orchestration & in-memory dedup guard (FR5)
│       └── servicenow_service.py # ServiceNow Table API write-back (FR4)
└── tests/                        # 43 automated tests (99% coverage)
    ├── conftest.py
    ├── unit/                     # Unit tests (schemas, dedup, security, prompts)
    ├── integration/              # Integration tests (Gemini, ServiceNow, processor)
    └── e2e/                      # End-to-end webhook execution tests
```
