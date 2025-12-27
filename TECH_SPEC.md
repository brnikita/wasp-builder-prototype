# Wasp Builder Prototype - Technical Specification

## Overview

A dashboard application to create, manage, and run Wasp.sh applications locally using Claude 4.5 Opus for code generation. Each generated app runs in isolated Docker containers with unique ports.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Next.js Frontend                        │
│                    (Dashboard UI, Port: 3000)                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│                        (Port: 8000)                             │
│  • App CRUD operations                                          │
│  • Claude API integration                                       │
│  • Docker container management                                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ┌───────────┐   ┌───────────┐   ┌───────────┐
        │ PostgreSQL│   │  Claude   │   │  Docker   │
        │  (5432)   │   │   API     │   │  Engine   │
        └───────────┘   └───────────┘   └───────────┘
                                                │
                                ┌───────────────┼───────────────┐
                                ▼               ▼               ▼
                        ┌───────────┐   ┌───────────┐   ┌───────────┐
                        │ Wasp App 1│   │ Wasp App 2│   │ Wasp App N│
                        │Port: 10001│   │Port: 10002│   │Port: 100XX│
                        └───────────┘   └───────────┘   └───────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 14, TypeScript, TailwindCSS |
| Backend | FastAPI, Pydantic, Python 3.11+ |
| Database | PostgreSQL 15 |
| AI | Claude 4.5 Opus (Anthropic API) |
| Containers | Docker, Docker Compose |
| Wasp | Wasp CLI v0.20.0 |

## Data Model

### Application Entity

```python
class Application(BaseModel):
    id: UUID
    name: str
    description: str
    status: Literal["created", "generating", "ready", "running", "stopped", "error"]
    port: int  # Range: 10001-10999
    wasp_schema: str | None  # Generated main.wasp content
    prisma_schema: str | None  # Generated schema.prisma content
    source_files: dict | None  # Generated src/ files as JSON
    created_at: datetime
    updated_at: datetime
    error_message: str | None
```

## API Endpoints

### Applications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/apps` | List all applications |
| GET | `/api/apps/{id}` | Get application details |
| POST | `/api/apps` | Create new application |
| DELETE | `/api/apps/{id}` | Delete application |
| POST | `/api/apps/{id}/generate` | Generate Wasp code via Claude |
| POST | `/api/apps/{id}/start` | Start application container |
| POST | `/api/apps/{id}/stop` | Stop application container |
| GET | `/api/apps/{id}/logs` | Get container logs |

### Request/Response Examples

**Create Application:**
```json
POST /api/apps
{
  "name": "my-todo-app",
  "description": "A simple todo app with user authentication"
}
```

**Generate Response:**
```json
{
  "id": "uuid",
  "status": "ready",
  "wasp_schema": "app MyTodoApp { ... }",
  "port": 10001
}
```

## Claude Integration

### Prompt Strategy

1. **System prompt** includes:
   - Full Wasp DSL documentation (from https://wasp.sh/docs)
   - Wasp language reference (`main.wasp` syntax)
   - Prisma schema syntax for `schema.prisma`
   - React/TypeScript conventions for `src/` files
   - Output format constraints

2. **Documentation embedding**: Fetch and store all Wasp docs from official sources.
   
   **Source URLs** (from https://wasp.sh/docs - LLM documentation index):
   ```
   # Core
   general/language
   general/typescript
   data-model/entities
   data-model/prisma-file
   data-model/operations/overview
   data-model/operations/queries
   data-model/operations/actions
   data-model/crud
   
   # Pages & Routing
   tutorial/pages
   tutorial/project-structure
   
   # Authentication
   auth/overview
   auth/ui
   auth/username-and-pass
   auth/email
   auth/social-auth/overview
   auth/entities/entities
   
   # Advanced
   advanced/apis
   advanced/email/email
   advanced/jobs
   advanced/web-sockets
   advanced/middleware-config
   
   # Project Setup
   project/dependencies
   project/env-vars
   project/css-frameworks
   ```

   **Storage structure**:
   ```
   backend/docs/
   ├── core/
   │   ├── language.md
   │   ├── entities.md
   │   ├── operations.md
   │   └── prisma.md
   ├── auth/
   │   ├── overview.md
   │   └── methods.md
   ├── advanced/
   │   └── apis.md
   └── examples/
       └── complete-apps.md
   ```

3. **Doc fetching script**: `backend/scripts/fetch_wasp_docs.py`
   - Runs at build time or on-demand
   - Fetches from `https://wasp.sh/docs/{path}`
   - Converts to markdown for Claude context

3. User provides app description
4. Claude generates:
   - `main.wasp` - App configuration
   - `schema.prisma` - Database models
   - `src/` files - React components and server operations

### Output Format

Claude returns structured JSON:
```json
{
  "main_wasp": "app content...",
  "schema_prisma": "model content...",
  "src_files": {
    "pages/MainPage.tsx": "...",
    "operations.ts": "..."
  }
}
```

## Docker Strategy

### Wasp App Container

Each generated app runs in a container with:
- Wasp CLI pre-installed
- Node.js 18
- PostgreSQL client
- Exposed on unique port (10001-10999)

### Container Lifecycle

1. **Create**: Generate Dockerfile from template
2. **Build**: `docker build` with generated Wasp files
3. **Run**: `docker run -p {port}:3000`
4. **Stop**: `docker stop {container_id}`
5. **Delete**: `docker rm {container_id}` + cleanup files

### Port Allocation

- Reserved range: 10001-10999
- Avoid conflicts with: SSH (22), HTTP (80/443), FTP (21), PostgreSQL (5432), etc.
- Track allocated ports in database

## Project Structure

```
wasp-builder-prototype/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── database.py
│   │   ├── routers/
│   │   │   └── apps.py
│   │   └── services/
│   │       ├── claude_service.py
│   │       └── docker_service.py
│   └── templates/
│       └── wasp_dockerfile.template
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx
│   │   │   └── apps/
│   │   │       ├── page.tsx
│   │   │       └── [id]/page.tsx
│   │   └── components/
│   │       ├── AppList.tsx
│   │       ├── AppCard.tsx
│   │       └── CreateAppForm.tsx
│   └── lib/
│       └── api.ts
└── generated_apps/  # Volume mount for generated Wasp projects
```

## Environment Variables

```env
# Backend
DATABASE_URL=postgresql://user:pass@db:5432/wasp_builder
ANTHROPIC_API_KEY=sk-ant-...
DOCKER_HOST=unix:///var/run/docker.sock

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Docker Compose Services

```yaml
services:
  db:
    image: postgres:15
    ports: ["5432:5432"]
    
  backend:
    build: ./backend
    ports: ["8000:8000"]
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./generated_apps:/app/generated_apps
    
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
```

## UI Pages

1. **Dashboard** (`/`) - List of all apps with status badges
2. **Create App** (`/apps/new`) - Form with name + description
3. **App Detail** (`/apps/[id]`) - View generated code, logs, start/stop/delete controls

## Limitations (Prototype Scope)

- No authentication
- No app editing after generation
- Single-node Docker only
- No persistent volumes for generated apps
- Basic error handling
- No WebSocket for real-time logs (polling instead)

## Development Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Access frontend
http://localhost:3000

# Access API docs
http://localhost:8000/docs
```

