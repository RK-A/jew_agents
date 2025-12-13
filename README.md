# AI Jewelry Consultation System

Production-ready multi-agent AI system for jewelry consultation with RAG and LLM integration.

## 🎯 Overview

An intelligent jewelry consultation system powered by AI agents that provides personalized recommendations, analyzes customer preferences, and tracks fashion trends.

### Key Features

- **Multi-Agent Architecture**: Specialized agents for consultation, analytics, and trend analysis
- **Flexible LLM Integration**: Support for OpenAI and GigaChat with runtime provider selection
- **LangChain RAG System**: Semantic search using Qdrant vector database with LangChain embeddings
- **Multiple Embedding Providers**: OpenAI, HuggingFace (local/free), GigaChat, and Local API (LM Studio, LocalAI)
- **Fully Local Option**: Run embeddings completely offline with local models
- **PostgreSQL Database**: Structured data storage for products, customers, and consultations
- **FastAPI REST API**: Modern async API with automatic documentation
- **Docker Deployment**: One-command deployment with Docker Compose
- **Production-Ready**: Full error handling, logging, and monitoring

## 📊 Project Stats

- **46 Python files** with **7000+ lines of code**
- **8 API endpoints** with full OpenAPI documentation
- **3 AI agents** with specialized capabilities
- **2 LLM providers** (OpenAI, GigaChat)
- **4 embedding providers** (OpenAI, HuggingFace, GigaChat, Local API) with 10+ models
- **Fully local embeddings** support (LM Studio, LocalAI)
- **LangChain-powered** RAG system for better integration
- **Comprehensive test suite** with 20+ tests
- **100% async/await** implementation

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- API keys for LLM provider (OpenAI or GigaChat)

### Installation

```bash
# 1. Clone and configure
git clone <repository-url>
cd agents
cp env.example .env
# Edit .env with your API keys

# 2. Start services
docker-compose up -d

# 3. Initialize and fill with test data
docker-compose exec backend python scripts/manage_data.py init
docker-compose exec backend python scripts/manage_data.py fill --products 80 --users 25
docker-compose exec backend python scripts/manage_data.py sync

# 4. Verify installation
docker-compose exec backend python scripts/verify_installation.py

# 5. Access API
open http://localhost:8000/docs
```

### Alternative: Auto-Fill on Startup

Set `AUTO_FILL_DATA=true` in `.env` and restart:
```bash
docker-compose restart backend
```

## 📚 Documentation

- **LOCAL_EMBEDDINGS_GUIDE.md** - 🆕 **Guide for local embeddings (LM Studio, LocalAI)**
- **QUICKSTART_LOCAL_API.txt** - 🆕 **Quick start for local embeddings (3 min)**
- **INSTALL.md** - Complete installation guide with embedding setup
- **MIGRATION_LANGCHAIN.md** - LangChain embeddings migration guide
- **QUICKSTART.txt** - Detailed setup guide
- **DEPLOYMENT.txt** - Production deployment guide
- **PROJECT_STATUS.txt** - Complete project status and features
- **env.example** - Environment configuration template with embedding examples
- **API Docs** - Available at `http://localhost:8000/docs` when running

## 🏗️ Architecture

```
FastAPI Backend → Agent Orchestrator → [LLM + RAG + PostgreSQL]
                                      ↓
                  3 Agents (Consultant, Analysis, Trend)
```

### Components

- **Consultant Agent**: Personalized jewelry recommendations
- **Analysis Agent**: Customer preference analytics and demand forecasting
- **Trend Agent**: Fashion trend analysis from journal content
- **RAG System**: LangChain-powered semantic search with Qdrant
- **Embedding Providers**: OpenAI, HuggingFace (free), GigaChat, Local API (LM Studio/LocalAI)
- **Fully Local Option**: Run embeddings offline with local models
- **LLM Providers**: OpenAI and GigaChat support
- **Database**: PostgreSQL for structured data

## 🔌 API Endpoints

- `POST /api/consultation/{user_id}` - Get jewelry recommendations
- `GET /api/customer/{user_id}/profile` - Get customer profile
- `PUT /api/customer/{user_id}/preferences` - Update preferences
- `POST /api/products/search` - Semantic product search
- `POST /api/analysis/customer` - Run customer analytics
- `POST /api/analysis/trends` - Analyze fashion trends
- `GET /api/health` - System health check
- `GET /docs` - Interactive API documentation

## 🛠️ CLI Tools

```bash
# Installation
python scripts/install_embeddings.py     # Install embedding dependencies

# Data management
python scripts/manage_data.py init       # Initialize database and Qdrant
python scripts/manage_data.py fill       # Generate test data
python scripts/manage_data.py sync       # Sync PostgreSQL to Qdrant
python scripts/manage_data.py status     # Check system status
python scripts/manage_data.py clear      # Clear all data
python scripts/manage_data.py reset      # Full system reset

# Verification
python scripts/verify_installation.py    # Verify installation

# API testing
./scripts/quick_api_test.sh             # Quick API test
./scripts/test_api.sh                   # Comprehensive API test
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test files
pytest tests/test_api_endpoints.py -v
pytest tests/test_database_init.py -v
pytest tests/test_data_generation.py -v
```

## 📁 Project Structure

```
agents/                        # AI agent implementations
backend/                       # FastAPI routes and schemas
database/                      # PostgreSQL models and repositories
llm/                           # LLM provider abstraction
rag/                           # RAG system with Qdrant
  ├── embedding_factory.py     # LangChain embedding factory
  ├── gigachat_embeddings.py   # Custom GigaChat wrapper
  ├── qdrant_service.py        # Qdrant operations
  └── retrieval.py             # RAG retrieval pipeline
scripts/                       # CLI management tools
  ├── install_embeddings.py    # Embedding installation script
  └── manage_data.py           # Data management CLI
tests/                         # Test suite
utils/                         # Logging and utilities
config.py                      # Configuration settings
main.py                        # FastAPI application
INSTALL.md                     # Installation guide
MIGRATION_LANGCHAIN.md         # Migration documentation
```

## ⚙️ Configuration

All configuration via environment variables in `.env`:

```bash
# LLM Provider
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_API_KEY=your_key

# Database
POSTGRES_URL=postgresql+asyncpg://...

# Qdrant
QDRANT_URL=http://localhost:6333

# Embeddings
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_KEY=your_key
```

See `env.example` for all options.

## 🐳 Docker Services

- **postgres**: PostgreSQL 16 database
- **qdrant**: Qdrant vector database
- **backend**: FastAPI application

## 📈 Monitoring

- Health endpoint: `GET /api/health`
- System status: `python scripts/manage_data.py status`
- Logs: `docker-compose logs -f backend`
- Qdrant dashboard: `http://localhost:6333/dashboard`

## 🔒 Security

- API keys via environment variables
- No credentials in code
- Input validation with Pydantic
- SQL injection protection with SQLAlchemy
- CORS configuration
- SSL/TLS ready for production

## 🚢 Production Deployment

See `DEPLOYMENT.txt` for detailed production deployment instructions including:
- Cloud platform deployment (AWS, GCP, Azure)
- Nginx reverse proxy setup
- SSL certificate configuration
- Monitoring and logging
- Backup and recovery
- Scaling strategies

## 🤝 Contributing

The project follows clean code principles:
- Type hints everywhere
- Async/await throughout
- Comprehensive error handling
- Structured logging
- Full test coverage
- Detailed documentation

## 📝 License

Proprietary - All rights reserved

## 🎉 Status

**✅ COMPLETE AND PRODUCTION-READY**

All planned features implemented and tested. Ready for deployment!
