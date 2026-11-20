# AccessPilot

**A multi-agent IT asset & access request assistant built with Google ADK, Gemini and AlloyDB.**

Employees ask in plain language: *"I need a second monitor"* or *"give me access to SAP Finance"*.
AccessPilot finds the right catalog item, applies company policy and then either
assigns the item, sends it to the manager, or raises a ServiceNow ticket for security or procurement.

> Proof of concept. It runs fully offline (SQLite + mock ServiceNow) and switches to AlloyDB,
> Gemini on Vertex AI and real ServiceNow through environment variables.

## Architecture

```
                         ┌────────────────────────────┐
  user ───────────────▶  │  accesspilot (coordinator) │  Gemini, routes by intent
                         └──────┬──────────────┬──────┘
                                │              │
                ┌───────────────▼───┐   ┌──────▼───────────────┐
                │  inventory_agent  │   │   approval_agent     │
                │ search_catalog    │   │ list_pending_approvals│
                │ get_my_assets     │   │ decide_request       │
                │ submit_request    │   │ get_request_status   │
                │ get_request_status│   └──────┬───────────────┘
                └────────┬──────────┘          │
                         ▼                     ▼
                ┌──────────────────────────────────────┐
                │ policy.py  (deterministic rules)      │──▶ ServiceNow ticket
                └──────────────────┬───────────────────┘    (security / procurement)
                                   ▼
                ┌──────────────────────────────────────┐
                │ AlloyDB: employees, catalog (+vector),│
                │ inventory, assets, requests           │
                └──────────────────────────────────────┘
```

| Layer | What it does |
|---|---|
| **Google ADK** | Coordinator agent with two sub-agents; function tools built from typed Python functions |
| **Gemini** | Understands the request, picks the agent, asks clarifying questions, explains outcomes |
| **AlloyDB** | System of record for assets and requests; **AlloyDB AI vector search** (pgvector + in-database Vertex AI embeddings) matches "laptop for coding" to the right catalog item |
| **Policy (code)** | Decides approvals. The LLM never approves anything itself |
| **ServiceNow** | Incident created for privileged access or out-of-stock hardware (mock included) |

## Policy

| Request | Outcome |
|---|---|
| Standard item, ≤ 500 USD, in stock | **Auto-approved** and assigned |
| Sensitive item (e.g. SAP Finance) or cost > 500 USD | **Manager approval**: only the requester's own manager can decide |
| Privileged access (e.g. production DB admin) | **ServiceNow ticket** for security review |
| Hardware out of stock | **ServiceNow ticket** for procurement |
| Item already assigned | Rejected |

## Quick start (offline, no cloud needed)

```bash
pip install -e ".[dev]"
pytest                 # 10 tests
python scripts/demo.py # walks through every policy path without an LLM
```

## Chat with the agents

```bash
cp .env.example .env   # set GOOGLE_CLOUD_PROJECT (Vertex AI) or GOOGLE_API_KEY
gcloud auth application-default login
adk web                # open http://localhost:8000 and pick "accesspilot"
```

Try:
- *"I'm E100, I need a monitor for a second screen"* → auto-approved
- *"I'm E101, I need SAP finance access for month-end close"* → pending manager
- *"I'm M201, show my pending approvals"* → approve it
- *"I'm E100, give me production database admin"* → ServiceNow security ticket

Demo users: employees `E100`, `E101`, `E102`; managers `M200` (Engineering), `M201` (Finance).

## Use AlloyDB

```bash
pip install -e ".[alloydb]"
export ALLOYDB_DSN="postgresql://postgres:<password>@127.0.0.1:5432/accesspilot"
python scripts/init_alloydb.py   # tables, demo data, Vertex AI embeddings
export ACCESSPILOT_DB=alloydb
adk web
```

Catalog search then runs inside AlloyDB:

```sql
SELECT id, name FROM catalog
ORDER BY embedding <=> embedding('text-embedding-005', 'laptop for coding')::vector
LIMIT 3;
```

Deployment to Agent Runtime (Vertex AI Agent Engine) or Cloud Run: see [deploy/README.md](deploy/README.md).

## Project layout

```
accesspilot/
  agent.py          ADK coordinator + inventory_agent + approval_agent
  tools.py          function tools the agents call
  service.py        business logic (testable without an LLM)
  policy.py         deterministic approval rules
  servicenow.py     ServiceNow Table API client + mock
  db/repository.py  SQLite and AlloyDB repositories
  db/schema_alloydb.sql
scripts/demo.py, scripts/init_alloydb.py
tests/
```

## Roadmap

- Agent identity from SSO instead of typed employee ids
- Memory Bank for user preferences across sessions
- Notify managers in Google Chat or Teams when approval is needed
- Evaluation set for routing and clarification quality

## License

MIT
