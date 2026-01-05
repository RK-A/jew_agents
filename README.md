# AI Jewelry Consultation System

Multi-agent AI system for jewelry consultation with RAG and LLM integration.

## 🎯 Features

- **5 AI Agents**: Consultation, Analytics, Trend Analysis, Girlfriend, Taste Detection
- **Streaming Support**: Token-by-token streaming for real-time typing effect
- **Voice Input**: Whisper audio transcription (OpenAI API or local server)
- **LLM Providers**: OpenAI, GigaChat (runtime selection)
- **Embeddings**: OpenAI, HuggingFace, GigaChat, Local API (LM Studio/LocalAI)
- **RAG System**: Semantic search with Qdrant + LangChain
- **Database**: PostgreSQL for products, customers, consultations
- **API**: FastAPI with async/await, auto-docs
- **Deploy**: Docker Compose

## 🚀 Quick Start

### 1. Setup

```bash
# Clone and configure
git clone <repository-url>
cd agents
cp env.example .env
# Edit .env with your API keys (LLM_API_KEY, etc.)

# Start all services
docker-compose up -d
```

### 2. Initialize

```bash
# Initialize database and Qdrant
docker-compose exec backend python scripts/manage_data.py init

# Fill with test data
docker-compose exec backend python scripts/manage_data.py fill --products 80 --users 25

# Sync to Qdrant
docker-compose exec backend python scripts/manage_data.py sync

# Verify
docker-compose exec backend python scripts/verify_installation.py
```

### 3. Access

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health
- **Qdrant Dashboard**: http://localhost:6333/dashboard

### Alternative: Auto-Fill

Set `AUTO_FILL_DATA=true` in `.env` and restart:
```bash
docker-compose restart backend
```

## 📡 API Endpoints

### Consultation & Chat
- `POST /api/orchestrator/{user_id}` - Smart routing to appropriate agent
- `POST /api/orchestrator/{user_id}/stream` - Streaming with typing effect
- `POST /api/consultation/{user_id}` - Direct jewelry recommendations
- `POST /api/consultation/{user_id}/stream` - Streaming consultation
- `POST /api/girlfriend/{user_id}` - Friendly advice and style tips
- `POST /api/taste/{user_id}` - Taste detection questionnaire

### Voice & Audio
- `POST /api/transcribe` - Audio to text with Whisper

### Products & Search
- `GET /api/customer/{user_id}/profile` - Customer profile
- `PUT /api/customer/{user_id}/preferences` - Update preferences
- `POST /api/products/search` - Semantic search

### Analytics
- `POST /api/analysis/customer` - Customer analytics
- `POST /api/analysis/trends` - Trend analysis

### System
- `GET /api/health` - Health check

**Example**:
```bash
curl -X POST "http://localhost:8000/api/consultation/user_001" \
  -H "Content-Type: application/json" \
  -d '{"message": "I need a gold ring for engagement"}'
```

## 🛠️ Management Commands

```bash
# Data management
python scripts/manage_data.py init      # Initialize DB + Qdrant
python scripts/manage_data.py fill      # Generate test data
python scripts/manage_data.py sync      # Sync to Qdrant
python scripts/manage_data.py status    # Check status
python scripts/manage_data.py clear     # Clear all data
python scripts/manage_data.py reset     # Full reset

# Embeddings
python scripts/install_embeddings.py    # Install embedding deps

# Verification
python scripts/verify_installation.py   # Verify setup

# API testing
./scripts/quick_api_test.sh            # Quick test
./scripts/test_api.sh                  # Full test
```

## 🧪 Testing

```bash
pytest tests/ -v                        # All tests
pytest tests/test_api_endpoints.py -v  # API tests
pytest tests/test_database_init.py -v  # DB tests
```

## 📁 Structure

```
├── agents/           # AI agents (consultant, analysis, trend)
├── backend/          # FastAPI routes, schemas
├── database/         # PostgreSQL models, repositories
├── llm/              # LLM providers (openai, gigachat)
├── rag/              # RAG system (qdrant, embeddings)
├── scripts/          # CLI tools
├── tests/            # Test suite
├── config.py         # Configuration
└── main.py           # Entry point
```

## ⚙️ Configuration

Environment variables in `.env`:

```bash
# LLM
LLM_PROVIDER=openai              # openai or gigachat
LLM_MODEL=gpt-4
LLM_API_KEY=your_key
LLM_BASE_URL=                    # Optional: http://host.docker.internal:1234/v1 for local

# Embeddings
EMBEDDING_PROVIDER=openai        # openai, huggingface, gigachat, local
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_KEY=your_key
EMBEDDING_BASE_URL=              # Optional: http://host.docker.internal:1234/v1 for local

# Database
POSTGRES_URL=postgresql+asyncpg://...

# Qdrant
QDRANT_URL=http://localhost:6333
```

See `env.example` for all options.

## 📚 Documentation

- **CLAUDE.md** - Development guide (architecture, stack, rules)
- **STREAMING.md** - Token-by-token streaming guide
- **WHISPER.md** - Audio transcription setup
- **INSTALL.md** - Installation guide with embeddings
- **MIGRATION_LANGCHAIN.md** - LangChain embeddings migration
- **env.example** - Configuration template

## 🐳 Docker Services

- `postgres` - PostgreSQL 16
- `qdrant` - Qdrant vector DB
- `backend` - FastAPI app

## 📈 Monitoring

- Health: `GET /api/health`
- Status: `python scripts/manage_data.py status`
- Logs: `docker-compose logs -f backend`
- Qdrant UI: http://localhost:6333/dashboard

## 🤝 Contributing

Clean code principles:
- Type hints everywhere
- Async/await throughout
- Comprehensive error handling
- Structured logging
- Full test coverage

## 🎉 Status

**✅ PRODUCTION-READY** - All features implemented and tested!
