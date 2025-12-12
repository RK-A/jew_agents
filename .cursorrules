# Cursor Rules: AI Jewelry Consultation System with Multi-Agent Architecture

## Project Context

You are developing a production-grade Python backend application for AI-powered jewelry consultation with multi-agent architecture:

- **Multi-Agent System**: Specialized agents for consultation, customer analysis, and trend forecasting
- **Flexible LLM Integration**: Support for multiple LLM providers (GigaChat, OpenAI) with dynamic provider selection
- **RAG System**: Qdrant vector database for jewelry product embeddings and semantic search
- **Relational Database**: PostgreSQL for jewelry inventory, customer preferences, and consultation history
- **Three Main Entities**: Separate services for agents, backend API, and database layer

**Core Architecture**:
- Backend API (FastAPI) → Agents orchestration → LLM + RAG + PostgreSQL
- Simple, clean code with NO markdown documentation files
- Minimal complexity, production-ready patterns

## Technology Stack

- **Framework**: FastAPI, Python 3.10+
- **AI/LLM**: LangChain, LangGraph for agent orchestration
- **LLM Providers**: OpenAI API, GigaChat API
- **Vector DB**: Qdrant for RAG
- **Relational DB**: PostgreSQL with SQLAlchemy ORM
- **Embeddings**: OpenAI embeddings, Hugging Face embeddings
- **Async**: asyncio, httpx for async HTTP
- **Deployment**: Docker, Docker Compose

## Core Principles

### 1. LLM Provider Abstraction ⭐

- **Provider Interface**: Abstract base class supporting multiple LLM providers
- **Dynamic Selection**: Choose provider and model at runtime via configuration
- **Supported Providers**:
  - OpenAI (GPT-4, GPT-3.5-turbo)
  - GigaChat (Яндекс GigaChat)
- **Configuration Pattern**:
  ```python
  # config.py
  class LLMConfig:
      provider: str  # "openai" or "gigachat"
      model: str     # specific model name
      api_key: str
      temperature: float = 0.7
  ```
- **Provider Factory**:
  ```python
  # services/llm_factory.py
  def create_llm_provider(config: LLMConfig):
      if config.provider == "openai":
          return OpenAIProvider(config)
      elif config.provider == "gigachat":
          return GigaChatProvider(config)
  ```

### 2. RAG System with Qdrant ⭐

- **Vector Store**: Qdrant for semantic search of jewelry products
- **Embeddings**: Configurable embedding model (OpenAI, multilingual-e5, etc.)
- **Jewelry Collections**:
  - Product descriptions
  - Design details (style, material, weight)
  - Customer reviews and preferences
  - Trend data from fashion journals
- **RAG Pipeline**:
  User Query → Embed → Vector Search in Qdrant → Retrieve Relevant Products → Augment LLM Context
- **Collection Structure**:
  ```python
  # Point in Qdrant
  {
      "id": "product_123",
      "vector": [0.1, 0.2, ...],  # embeddings
      "payload": {
          "product_id": "prod_123",
          "name": "Diamond Ring",
          "description": "18K gold with 1.5ct diamond",
          "category": "rings",
          "style": "classic",
          "material": "gold",
          "price": 5000,
          "customer_reviews": [...],
          "trend_score": 0.85
      }
  }
  ```

### 3. PostgreSQL Database Structure

- **Three Main Tables**:
  
  **1. jewelry_products** (Inventory)
  ```sql
  - id, name, description, category, material, weight, price
  - design_details (JSON), images (array), stock_count
  - created_at, updated_at
  ```
  
  **2. customer_preferences** (User Profiles)
  ```sql
  - user_id, style_preference, budget_min, budget_max
  - preferred_materials (array), skin_tone, occasion_types
  - consultation_history (JSON), created_at, last_updated
  ```
  
  **3. consultation_records** (Chat History)
  ```sql
  - id, user_id, agent_type, message, response
  - recommendations (JSON), created_at
  - preference_updates (JSON for tracking changes)
  ```

### 4. Three Agent Architecture ⭐

#### Agent 1: Consultation Agent (ConsultantAgent)
- **Purpose**: Interactive jewelry recommendations and preference collection
- **Workflow**:
  1. Check customer profile in PostgreSQL
  2. If NO profile → Gather preferences (style, budget, occasion, skin tone)
  3. If profile exists → Use existing preferences
  4. Query RAG for relevant products
  5. Generate personalized recommendations via LLM
  6. Update customer preferences in PostgreSQL
- **Tools**: 
  - Get customer profile
  - Search products via RAG
  - Update customer preferences
  - Store consultation record

#### Agent 2: Customer Analysis Agent (AnalysisAgent)
- **Purpose**: Analyze customer preferences, identify trends, forecast demand
- **Workflow**:
  1. Query PostgreSQL for customer preferences (bulk)
  2. Analyze preference patterns (most popular styles, materials, budgets)
  3. Generate demand forecast for different product categories
  4. Identify underserved customer segments
  5. Produce market analysis report
- **Tools**:
  - Get all customer preferences
  - Generate analytics summary
  - Forecast product demand
  - Identify trends

#### Agent 3: Trend Analysis Agent (TrendAgent)
- **Purpose**: Parse fashion journals, identify trends, update product relevance
- **Workflow**:
  1. Fetch/parse fashion journal data (web scraping or file upload)
  2. Extract mentioned products, styles, designers
  3. Analyze trends (colors, materials, silhouettes)
  4. Update trend scores in Qdrant
  5. Recommend new products to add to catalog
  6. Alert on emerging trends
- **Tools**:
  - Parse journal/article content
  - Extract trend keywords
  - Update product trend scores
  - Generate trend report

### 5. Agent Orchestration Pattern

```python
# agents/orchestrator.py

class AgentOrchestrator:
    def __init__(self, llm_provider, rag_service, db_service):
        self.consultant_agent = ConsultantAgent(llm_provider, rag_service, db_service)
        self.analysis_agent = AnalysisAgent(llm_provider, db_service)
        self.trend_agent = TrendAgent(llm_provider, rag_service, db_service)
    
    async def handle_user_consultation(self, user_id: str, message: str):
        """Main consultation flow"""
        return await self.consultant_agent.process(user_id, message)
    
    async def run_customer_analysis(self):
        """Periodic analysis of customer preferences"""
        return await self.analysis_agent.process()
    
    async def run_trend_analysis(self, content: str):
        """Parse trends from fashion journals"""
        return await self.trend_agent.process(content)
```

### 6. Code Organization

```
project/
├── config.py                          # All configuration (LLM, DB, Qdrant)
├── main.py                            # FastAPI app entry point
│
├── agents/                            # Agent implementations
│   ├── base_agent.py                 # Abstract base agent
│   ├── consultant_agent.py           # ConsultantAgent
│   ├── analysis_agent.py             # AnalysisAgent
│   ├── trend_agent.py                # TrendAgent
│   └── orchestrator.py               # Agent orchestration
│
├── backend/                           # API routes and services
│   ├── routes.py                     # FastAPI endpoints
│   ├── dependencies.py               # DI setup
│   └── schemas.py                    # Pydantic models for API
│
├── llm/                               # LLM provider abstraction
│   ├── base.py                       # Abstract LLMProvider
│   ├── openai_provider.py            # OpenAI implementation
│   ├── gigachat_provider.py          # GigaChat implementation
│   └── factory.py                    # Provider factory
│
├── rag/                               # RAG with Qdrant
│   ├── qdrant_service.py             # Qdrant operations
│   ├── embeddings.py                 # Embedding models
│   └── retrieval.py                  # RAG retrieval pipeline
│
├── database/                          # PostgreSQL layer
│   ├── models.py                     # SQLAlchemy ORM models
│   ├── session.py                    # DB session management
│   ├── schemas.md                    # DB schemas
│   ├── fill_data.py                  # DB fill data
│   └── repositories.py               # Data access layer
│
└── utils/
    └── logging.py                    # Logging config
```

### 7. API Endpoints

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

### 8. Async Patterns

- **Concurrent Operations**: Use `asyncio.gather()` for parallel agent tasks
- **Database Operations**: All DB calls must be async using `sqlalchemy.ext.asyncio`
- **LLM Calls**: Async HTTP client (httpx) for LLM API calls
- **RAG Retrieval**: Async Qdrant client for vector search

Example:
```python
# Process user consultation asynchronously
async def handle_consultation(user_id, message):
    # Parallel: fetch customer profile and RAG search
    profile, products = await asyncio.gather(
        db_service.get_customer_profile(user_id),
        rag_service.search_products(message)
    )
    
    # Then run LLM for recommendation
    recommendation = await llm_provider.generate(
        context={"profile": profile, "products": products},
        prompt=message
    )
    return recommendation
```

### 9. Configuration Management

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM Provider
    llm_provider: str = "openai"  # or "gigachat"
    llm_model: str = "gpt-4"
    llm_api_key: str
    llm_temperature: float = 0.7
    
    # Database
    postgres_url: str = "postgresql+asyncpg://user:pass@localhost/jewelry"
    
    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "jewelry_products"
    
    # Embeddings
    embedding_model: str = "text-embedding-3-small"  # OpenAI or HF
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 10. Error Handling & Logging

- **Try-except blocks** around LLM calls and RAG queries
- **Graceful degradation**: If RAG fails, use direct LLM; if LLM fails, return cached recommendations
- **Structured logging**: Use `logging` module with context (user_id, agent_type, timestamp)
- **No stack traces in production**: Log full details, return user-friendly error messages

Example:
```python
try:
    products = await rag_service.search(query)
except Exception as e:
    logger.error(f"RAG search failed for user {user_id}", exc_info=True)
    products = []  # Fallback to LLM-only mode
```

### 11. Database Initialization

- **Alembic migrations** for schema management (optional, keep simple)
- **SQLAlchemy async session factory** with connection pooling
- **Context managers for transactions**:
  ```python
  async with db_session() as session:
      await session.execute(...)
      await session.commit()
  ```

### 12. Qdrant Collection Management

```python
# rag/qdrant_service.py

class QdrantService:
    async def create_collection(self):
        """Create jewelry_products collection if not exists"""
        # Vector size depends on embedding model (e.g., 1536 for OpenAI)
        pass
    
    async def upsert_product(self, product_id, description, payload):
        """Add or update product in Qdrant"""
        embedding = await self.embed(description)
        await self.client.upsert(collection_name=self.collection, points=[...])
    
    async def search(self, query: str, limit: int = 5):
        """Semantic search for products"""
        query_embedding = await self.embed(query)
        results = await self.client.search(collection_name=self.collection, ...)
        return results
```

### 13. Simple Rules for Code Quality

1. **NO Markdown files** - All documentation is inline code comments only
2. **Single responsibility** - Each function does ONE thing
3. **Type hints everywhere** - Full type annotations for all functions
4. **Async first** - Use async/await throughout, never blocking calls
5. **Configuration driven** - All settings from config.py, nothing hardcoded
6. **Error handling** - Try-except with proper logging, never silent failures
7. **DI pattern** - Pass dependencies to constructors, use FastAPI dependencies
8. **Simple variable names** - Clear, descriptive, short where possible
9. **No comments for obvious code** - Comment WHY, not WHAT
10. **Keep functions small** - Max 20-30 lines per function

### 14. LLM Provider Interface

```python
# llm/base.py

from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, context: dict = None) -> str:
        """Generate text response from LLM"""
        pass
    
    @abstractmethod
    async def generate_with_tools(self, prompt: str, tools: list) -> dict:
        """Generate response with tool use capability"""
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> list:
        """Generate embeddings for text"""
        pass

# Implementations: OpenAIProvider, GigaChatProvider
```

### 15. Agent Base Class

```python
# agents/base_agent.py

class BaseAgent(ABC):
    def __init__(self, llm_provider: LLMProvider, db_service, rag_service=None):
        self.llm = llm_provider
        self.db = db_service
        self.rag = rag_service
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def process(self, *args, **kwargs):
        pass
    
    async def log_interaction(self, user_id: str, agent_type: str, input_msg: str, output_msg: str):
        """Store interaction record in PostgreSQL"""
        pass
```

## Testing Patterns

```python
import pytest

@pytest.mark.asyncio
async def test_consultant_agent():
    llm = MockLLMProvider()
    agent = ConsultantAgent(llm, db_service, rag_service)
    result = await agent.process("user_1", "I want a ring")
    assert "recommendations" in result

@pytest.mark.asyncio
async def test_rag_search():
    qdrant = QdrantService()
    results = await qdrant.search("elegant gold ring")
    assert len(results) > 0
```

## Docker Compose Setup

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: jewelry
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
  
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
  
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_URL=postgresql+asyncpg://postgres:password@postgres:5432/jewelry
      - QDRANT_URL=http://qdrant:6333
      - LLM_PROVIDER=openai
    depends_on:
      - postgres
      - qdrant
```

## Key Dependencies

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
asyncpg>=0.29.0
qdrant-client>=2.7.0
langchain>=0.1.0
langgraph>=0.0.1
openai>=1.3.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
httpx>=0.25.0
python-dotenv>=1.0.0
```

## Best Practices Summary

1. **Always use async/await** - No blocking calls
2. **LLM provider is abstraction** - Switch providers without code changes
3. **RAG for semantic search** - Use Qdrant for product discovery
4. **PostgreSQL for facts** - Store structured data (users, products, history)
5. **Agents are orchestrators** - LLMProvider + RAG + DB = Agent
6. **Simple API endpoints** - REST with FastAPI, clear request/response
7. **Config-driven setup** - No hardcoded values
8. **Error recovery** - Graceful fallbacks for failures
9. **Type safety** - Full type hints everywhere
10. **No markdown docs** - Inline code comments only, clean and simple

## Critical Rules

❌ **DO NOT**:
- Write Markdown documentation files (README.md, ARCHITECTURE.md, etc.)
- Create complex folder structures or unnecessary files
- Hardcode any configuration values
- Use blocking I/O calls (requests library, time.sleep)
- Add comments for obvious code (bad: `x = x + 1  # increment x`)
- Create TODOs or incomplete functions
- Use print() for logging (use logging module)
- Mix async and sync code

✅ **DO**:
- Keep code simple and readable
- Use type hints on all functions
- Put configuration in config.py
- Log with context (user_id, agent_type, etc.)
- Handle errors gracefully with fallbacks
- Write small focused functions
- Use dependency injection pattern
- Test async code with pytest-asyncio
