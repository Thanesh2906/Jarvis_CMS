# Jarvis Clinic AI Assistant

An open-source, local-first AI assistant for a Clinic Management System. It uses FastAPI, MySQL, Ollama, ChromaDB, JWT authentication, role-based tool permissions, and a simple React chat UI.

## What it answers

- How many patients today?
- How many appointments today?
- How many pending lab results?
- How many unpaid invoices?
- Show today’s revenue.
- Search patient basic info.
- Explain clinic reports.
- Answer clinic document questions using RAG.

## Recommended low-cost local model setup

Ollama is recommended because its official documentation and model library support local models including `gpt-oss`, `DeepSeek-R1`, `Qwen3`, and `Llama 3.1`.

| Hardware | Chat model | Embedding model | Notes |
| --- | --- | --- | --- |
| 8 GB RAM, CPU-only | `qwen3:1.7b` or `llama3.2:3b` | `sentence-transformers/all-MiniLM-L6-v2` | Lowest cost; good for simple clinic questions. |
| 16 GB RAM | `llama3.1:8b` or `qwen3:8b` | `BAAI/bge-small-en-v1.5` | Best default balance for this project. |
| 24+ GB VRAM/RAM | `gpt-oss:20b` or larger Qwen/DeepSeek tags | `BAAI/bge-small-en-v1.5` | Better reasoning/tool selection. |

Default `.env` uses `llama3.1:8b`. Change `OLLAMA_MODEL` based on your hardware.

## Folder structure

```text
Jarvis_CMS/
├── backend/
│   ├── app/
│   │   ├── api/              # REST endpoints
│   │   ├── core/             # config, security, RBAC
│   │   ├── db/               # MySQL connection and models
│   │   ├── schemas/          # Pydantic DTOs
│   │   ├── services/         # AI, Ollama, RAG, logging
│   │   └── tools/            # safe clinic tool functions
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/                  # React chat UI
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

## Installation

### 1. Install Ollama and pull a model

```bash
ollama pull llama3.1:8b
```

Or choose a smaller model:

```bash
ollama pull qwen3:1.7b
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set secure secrets.

### 3. Start services

```bash
docker compose up --build
```

Services:

- Backend: <http://localhost:8000>
- API docs: <http://localhost:8000/docs>
- Frontend: <http://localhost:5173>
- MySQL: `localhost:3306`
- ChromaDB files: `./chroma_data`

### 4. Seed a user manually

The demo schema creates tables, but you should create users with a hashed password. For quick local testing, generate a hash:

```bash
cd backend
python -c "from app.core.security import get_password_hash; print(get_password_hash('admin123'))"
```

Insert the hash into MySQL:

```sql
INSERT INTO users (username, hashed_password, full_name, role, is_active)
VALUES ('admin', '<PASTE_HASH>', 'Admin User', 'admin', true);
```

## Example API endpoints

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}'
```

### Ask chat question

```bash
curl -X POST http://localhost:8000/api/chat \
  -H 'Authorization: Bearer <TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"message":"How many appointments today?"}'
```

### Upload document for RAG

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H 'Authorization: Bearer <TOKEN>' \
  -F 'file=@clinic-policy.txt'
```

### Search documents

```bash
curl -X POST http://localhost:8000/api/documents/search \
  -H 'Authorization: Bearer <TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"query":"Explain the appointment cancellation policy"}'
```

## Example questions users can ask

- Admin: “Show today’s revenue.”
- Admin: “How many unpaid invoices do we have?”
- Doctor: “What is my schedule today?”
- Doctor: “Summarize patient 42.”
- Nurse: “How many pending lab results?”
- Nurse: “Search patient named Maria.”
- Billing: “How many unpaid invoices?”
- Any allowed user: “What does the clinic refund policy document say?”

## Security design

- User prompts are never converted into raw SQL.
- Clinic data access is limited to predefined safe Python tool functions.
- Role-based access controls are enforced before every AI tool call.
- Sensitive patient fields are redacted for roles without permission.
- AI questions/responses and tool calls are stored in audit tables.
- JWT protects all assistant, document, and tool endpoints.

## Tool permissions

| Tool | admin | doctor | nurse | billing |
| --- | --- | --- | --- | --- |
| Patient count | ✅ | ✅ | ✅ | ❌ |
| Appointment count | ✅ | ✅ | ✅ | ❌ |
| Pending labs | ✅ | ✅ | ✅ | ❌ |
| Unpaid invoices | ✅ | ❌ | ❌ | ✅ |
| Today revenue | ✅ | ❌ | ❌ | ✅ |
| Search patient | ✅ | ✅ | ✅ | ❌ |
| Patient summary | ✅ | ✅ | ✅ redacted | ❌ |
| Doctor schedule | ✅ | ✅ | ✅ | ❌ |
| Lab pending by date | ✅ | ✅ | ✅ | ❌ |

## Example MySQL queries

The backend uses SQLAlchemy text queries inside safe tool functions. Examples:

```sql
SELECT COUNT(*) FROM patients WHERE DATE(created_at) = CURRENT_DATE;
SELECT COUNT(*) FROM appointments WHERE appointment_date = CURRENT_DATE;
SELECT COUNT(*) FROM lab_results WHERE status = 'pending';
SELECT COUNT(*) FROM invoices WHERE status IN ('unpaid', 'overdue');
SELECT COALESCE(SUM(amount_paid), 0) FROM invoices WHERE DATE(paid_at) = CURRENT_DATE;
```

## How the AI router works

1. The chat endpoint authenticates the user with JWT.
2. `AssistantService` logs the question.
3. `OllamaService` asks the local model to emit strict JSON describing whether it needs a clinic tool, RAG, or normal answer.
4. `ToolRegistry` validates the selected function and user role.
5. Safe SQL is executed only inside predefined functions.
6. RAG queries ChromaDB using sentence-transformer embeddings.
7. The final prompt asks Ollama to answer in simple clinic-friendly language.
8. The answer, selected route, and any tool calls are logged.

## Development

Backend checks:

```bash
cd backend
python -m compileall app
```

Frontend checks:

```bash
cd frontend
npm install
npm run build
```
