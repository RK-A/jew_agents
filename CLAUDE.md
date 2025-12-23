# AI Jewelry Consultation System - Development Guide

## Project Overview

Multi-agent AI system for jewelry consultation with RAG (Qdrant) and LLM integration (OpenAI/GigaChat).

**Architecture**: FastAPI → LangGraph Agent Orchestrator → [State-based Agent Workflows + LLM + RAG + PostgreSQL]

## Stack

- **Backend**: FastAPI, Python 3.11+, asyncio, httpx
- **AI/LLM**: LangChain, **LangGraph** (state machines), OpenAI/GigaChat APIs
- **Vector DB**: Qdrant with **LangChain integration**
- **Database**: PostgreSQL + SQLAlchemy (async)
- **Embeddings**: OpenAI, GigaChat, Local API (LM Studio/LocalAI) - **No HuggingFace/Torch**
- **Deploy**: Docker + Docker Compose

## Architecture

### LangGraph Multi-Agent System

The system uses **LangGraph** for building stateful, graph-based agent workflows with nodes and edges.

### 3 AI Agents (LangGraph-based)

1. **ConsultantAgent**: Jewelry recommendations + preference collection
2. **AnalysisAgent**: Customer analytics + demand forecasting  
3. **TrendAgent**: Fashion trend analysis + catalog updates
   - Graph workflow: extract_keywords → analyze_trends → calculate_scores → identify_emerging → generate_recommendations → generate_report

### Database (PostgreSQL)

- `jewelry_products`: Inventory (id, name, category, material, price, etc.)
- `customer_preferences`: User profiles (user_id, style, budget, materials, etc.)
- `consultation_records`: Chat history (id, user_id, message, response, etc.)

### Simplified RAG Pipeline (LangChain + Qdrant)

**Architecture**: User Query → LangChain Embeddings → Qdrant Vector Search → Filtered Results → LLM Context

**Key Features**:
- Native LangChain integration with Qdrant VectorStore
- Simplified embedding factory (OpenAI, GigaChat, Local API only)
- No heavy dependencies (removed HuggingFace/Torch)
- Automatic preference-based filtering and ranking
- Async operations throughout

## Project Structure

```
.
├── agents
│   ├── analysis_agent.py       # LangGraph-based analysis workflow
│   ├── base_agent.py            # Base agent with common utilities
│   ├── consultant_agent.py      # LangGraph-based consultation workflow
│   ├── example_usage.py
│   ├── graph_states.py          # LangGraph state definitions (NEW)
│   ├── __init__.py
│   ├── orchestrator.py          # LangGraph-based multi-agent orchestrator
│   └── trend_agent.py           # LangGraph-based trend analysis workflow
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
│   ├── embedding_factory.py    # Simplified: OpenAI, GigaChat, Local only
│   ├── langchain_rag.py         # NEW: LangChain Qdrant integration
│   ├── qdrant_service.py        # Legacy: Direct Qdrant client
│   ├── retrieval.py             # Unified retriever (supports both)
│   ├── gigachat_embeddings.py
│   ├── local_api_embeddings.py
│   ├── fill_qdrant.py
│   ├── init_qdrant.py
│   └── __init__.py
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
- Использовать langchain и langGraph для создания агентов
- Создавать небольшие файлы
- Везде использовать асинхронный режим / ожидание (без блокировки ввода-вывода)
- Вводить подсказки для всех функций
- Управлять конфигурацией (без жестко заданных значений)
- Структурированное ведение журнала с контекстом
- Корректная обработка ошибок с резервными версиями
- Небольшие специализированные функции (максимум 20-30 строк)
- Шаблон внедрения зависимостей

### ❌ DO NOT
- Не нужно создавать файлы документации Markdown или txt в корневом каталоге
- Использовать блокирующий ввод-вывод (запросы, time.sleep)
- Значения конфигурации жесткого кода
- Добавляйте комментарии к очевидному коду
- Создавайте неполные функции или задачи TODOS
- Используйте print() для ведения журнала
- Комбинируйте асинхронный и синхронизирующий код

## Development Tips

- Абстрагирование провайдера LLM: переключение OpenAI на GigaChat через config
- Резервный вариант RAG: в случае сбоя Qdrant используйте режим только для LLM
- **Embeddings**: OpenAI (рекомендуется), GigaChat или локальный API (LM Studio/LocalAI)
- Локальные вложения: установите `EMBEDDING_BASE_URL=http://host.docker.internal:1234/v1` для LM Studio в Docker
- Все операции с базой данных: асинхронная SQLAlchemy с использованием `asyncpg`
- Параллельные операции: используйте "asyncio.gather()" для параллельных задач
- Ведение журнала ошибок: структурированное ведение журнала с идентификатором пользователя, типом агента, временной меткой
- **LangGraph workflows**: Все агенты используют state-based графы для прозрачности выполнения

## Python prompt

You are an expert in Python, FastAPI, and scalable API development.

Write concise, technical responses with accurate Python examples. Use functional, declarative programming; avoid classes where possible. Prefer iteration and modularization over code duplication. Use descriptive variable names with auxiliary verbs (e.g., is_active, has_permission). Use lowercase with underscores for directories and files (e.g., routers/user_routes.py). Favor named exports for routes and utility functions. Use the Receive an Object, Return an Object (RORO) pattern. Use def for pure functions and async def for asynchronous operations. Use type hints for all function signatures. Prefer Pydantic models over raw dictionaries for input validation.

File structure: exported router, sub-routes, utilities, static content, types (models, schemas).

Avoid unnecessary curly braces in conditional statements. For single-line statements in conditionals, omit curly braces. Use concise, one-line syntax for simple conditional statements (e.g., if condition: do_something())
