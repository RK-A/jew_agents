# AI Jewelry Consultation System - Development Guide

## Project Overview

Multi-agent AI system for jewelry consultation with RAG (Qdrant) and LLM integration (OpenAI/GigaChat).

**Architecture**: FastAPI → Agent Orchestrator → [LLM + RAG + PostgreSQL]

## Stack

- **Backend**: FastAPI, Python 3.11+, asyncio, httpx
- **AI/LLM**: LangChain, OpenAI/GigaChat APIs
- **Vector DB**: Qdrant (RAG)
- **Database**: PostgreSQL + SQLAlchemy (async)
- **Embeddings**: OpenAI, HuggingFace, GigaChat, Local API (LM Studio/LocalAI)
- **Deploy**: Docker + Docker Compose

## Architecture

### 3 AI Agents

1. **ConsultantAgent**: Jewelry recommendations + preference collection
2. **AnalysisAgent**: Customer analytics + demand forecasting  
3. **TrendAgent**: Fashion trend analysis + catalog updates

### Database (PostgreSQL)

- `jewelry_products`: Inventory (id, name, category, material, price, etc.)
- `customer_preferences`: User profiles (user_id, style, budget, materials, etc.)
- `consultation_records`: Chat history (id, user_id, message, response, etc.)

### RAG Pipeline (Qdrant)

User Query → Embed → Vector Search → Retrieve Products → Augment LLM Context

## Project Structure

```
.
├── agents
│   ├── analysis_agent.py
│   ├── base_agent.py
│   ├── consultant_agent.py
│   ├── example_usage.py
│   ├── __init__.py
│   ├── orchestrator.py
│   └── trend_agent.py
├── backend
│   ├── api_examples.py
│   ├── dependencies.py
│   ├── __init__.py
│   ├── routes.py
│   └── schemas.py
├── config.py
├── database
│   ├── fill_data.py
│   ├── init_db.py
│   ├── __init__.py
│   ├── models.py
│   ├── repositories.py
│   └── session.py
├── docker-compose.yml
├── Dockerfile
├── env.example
├── llm
│   ├── base.py
│   ├── factory.py
│   ├── gigachat_provider.py
│   ├── __init__.py
│   └── openai_provider.py
├── main.py
├── pytest.ini
├── rag
│   ├── embeddings.py
│   ├── example_usage.py
│   ├── fill_qdrant.py
│   ├── __init__.py
│   ├── init_qdrant.py
│   ├── qdrant_service.py
│   └── retrieval.py
├── README.md
├── CLAUDE.md
├── requirements.txt
├── scripts
│   ├── __init__.py
│   ├── manage_data.py
│   ├── quick_api_test.sh
│   ├── quick_test.py
│   ├── test_api.py
│   ├── test_api.sh
│   └── verify_installation.py
├── tests
│   ├── conftest.py
│   ├── __init__.py
│   ├── test_api_endpoints.py
│   ├── test_database_init.py
│   ├── test_data_generation.py
│   ├── test_integration_init.py
│   └── test_qdrant_init.py
└── utils
    ├── __init__.py
    └── logging.py
```

## API Endpoints

```python
# Simple REST API for agent interaction

# Consultation endpoint
POST /api/consultation/{user_id}
  body: {"message": "I want a ring for engagement"}
  response: {
    "recommendations": [...],
    "questions_for_user": [...],
    "extracted_preferences": {...}
  }

# Get customer profile
GET /api/customer/{user_id}/profile
  response: {...customer preferences...}

# Update customer preferences
PUT /api/customer/{user_id}/preferences
  body: {...}

# Run customer analysis
POST /api/analysis/customer
  response: {...analysis result...}

# Run trend analysis
POST /api/analysis/trends
  body: {"content": "fashion journal text"}
  response: {...trend report...}

# List products by RAG search
POST /api/products/search
  body: {"query": "elegant gold ring"}
  response: [...products...]

# Health check
GET /api/health
```

## Code Quality Rules

### ✅ DO
- Use async/await everywhere (no blocking I/O)
- Type hints on all functions
- Config-driven (no hardcoded values)
- Structured logging with context
- Graceful error handling with fallbacks
- Small focused functions (max 20-30 lines)
- Dependency injection pattern

### ❌ DO NOT
- Create Markdown or txt documentation files in the root
- Use blocking I/O (requests, time.sleep)
- Hardcode configuration values
- Add comments for obvious code
- Create incomplete functions or TODOs
- Use print() for logging
- Mix async and sync code

## Development Tips

- LLM Provider abstraction: switch OpenAI ↔ GigaChat via config
- RAG fallback: if Qdrant fails, use LLM-only mode
- Embeddings: OpenAI, HuggingFace (free), GigaChat, or Local API (LM Studio/LocalAI)
- Local embeddings: set `EMBEDDING_BASE_URL=http://host.docker.internal:1234/v1` for LM Studio in Docker
- All DB operations: async SQLAlchemy with `asyncpg`
- Concurrent ops: use `asyncio.gather()` for parallel tasks
- Error logging: structured logging with user_id, agent_type, timestamp
