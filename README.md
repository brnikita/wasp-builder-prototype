# Wasp Builder Prototype

Build Wasp.sh applications using AI (OpenRouter/Grok).

## Prerequisites

- Docker & Docker Compose
- OpenRouter API key (https://openrouter.ai/keys)

## Setup

1. Create `.env` file:
```bash
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

2. Start services:
```bash
docker-compose up -d
```

3. Access the dashboard:
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

## Usage

1. Click "New App" to create an application
2. Enter a name and detailed description
3. AI will generate the Wasp code
4. Start the app to run it in a Docker container
5. Access the running app on its assigned port (10001+)

## Architecture

- **Frontend**: Next.js 14, TypeScript, TailwindCSS (port 3000)
- **Backend**: FastAPI, Pydantic, SQLAlchemy (port 8000)
- **Database**: PostgreSQL (port 5432)
- **LLM**: OpenRouter API (Grok 3 Fast)
- **Generated apps**: Ports 10001-10999

