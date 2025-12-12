=============================================================================
AI JEWELRY CONSULTATION SYSTEM - QUICK START GUIDE
=============================================================================

This is a production-ready AI-powered jewelry consultation system with:
- Multi-agent architecture (Consultant, Analysis, Trend agents)
- Flexible LLM providers (OpenAI, GigaChat)
- RAG system with Qdrant for semantic search
- PostgreSQL for structured data
- FastAPI REST API

=============================================================================
SETUP INSTRUCTIONS
=============================================================================

1. COPY ENVIRONMENT CONFIGURATION
   --------------------------------
   Copy the environment template and fill in your API keys:
   
   cp env.example .env
   
   Edit .env and set:
   - LLM_API_KEY: Your OpenAI or GigaChat API key
   - EMBEDDING_API_KEY: Your embeddings API key (can be same as LLM_API_KEY for OpenAI)
   - POSTGRES_URL: Database connection string (default works for Docker setup)
   - QDRANT_URL: Qdrant server URL (default works for Docker setup)


2. START SERVICES WITH DOCKER COMPOSE
   -----------------------------------
   Start PostgreSQL and Qdrant:
   
   docker-compose up -d
   
   This will start:
   - PostgreSQL on port 5432
   - Qdrant on port 6333
   - Backend API on port 8000


3. INITIALIZE DATABASE AND QDRANT
   -------------------------------
   Initialize the database tables and Qdrant collection:
   
   docker-compose exec backend python scripts/manage_data.py init
   
   Or if running locally:
   python scripts/manage_data.py init


4. FILL WITH TEST DATA
   --------------------
   Generate test jewelry products, customer profiles, and consultations:
   
   docker-compose exec backend python scripts/manage_data.py fill --products 80 --users 25 --consultations 40
   
   Or if running locally:
   python scripts/manage_data.py fill --products 80 --users 25


5. SYNC DATA TO QDRANT
   --------------------
   Sync products from PostgreSQL to Qdrant for semantic search:
   
   docker-compose exec backend python scripts/manage_data.py sync
   
   Or if running locally:
   python scripts/manage_data.py sync


6. VERIFY INSTALLATION
   --------------------
   Check system status:
   
   python scripts/manage_data.py status
   
   You should see:
   - PostgreSQL: Connected ✓
   - Qdrant: Connected ✓
   - Product counts in both systems


7. ACCESS THE API
   --------------
   The API is now running at:
   
   - API Docs (Swagger UI): http://localhost:8000/docs
   - API Root: http://localhost:8000/
   - Health Check: http://localhost:8000/api/health

=============================================================================
ALTERNATIVE: AUTO-FILL ON STARTUP
=============================================================================

For quick testing, you can enable automatic data generation on startup:

1. Edit .env and set:
   AUTO_FILL_DATA=true

2. Restart the backend:
   docker-compose restart backend

The system will automatically initialize and fill with test data.

=============================================================================
API ENDPOINTS
=============================================================================

All endpoints are documented at http://localhost:8000/docs

Main endpoints:

1. POST /api/consultation/{user_id}
   - Get personalized jewelry recommendations
   - Body: {"message": "I need a ring for engagement"}

2. GET /api/customer/{user_id}/profile
   - Get customer profile and preferences

3. PUT /api/customer/{user_id}/preferences
   - Update customer preferences

4. POST /api/products/search
   - Search products with semantic search
   - Body: {"query": "gold ring", "limit": 5}

5. POST /api/analysis/customer
   - Run customer analytics

6. POST /api/analysis/trends
   - Analyze fashion trends from content
   - Body: {"content": "fashion journal text"}

7. GET /api/health
   - System health check

=============================================================================
DATA MANAGEMENT COMMANDS
=============================================================================

The manage_data.py script provides several commands:

init                    Initialize database and Qdrant
fill                    Fill with test data
  --products N         Number of products (default: 80)
  --users N            Number of users (default: 25)
  --consultations N    Number of consultations (default: 40)
  --clear              Clear existing data first
  --seed N             Random seed for reproducibility

clear                   Clear all data from PostgreSQL and Qdrant
status                  Check system status
sync                    Sync PostgreSQL products to Qdrant
  --clear              Clear Qdrant before sync
reset                   Drop tables and reinitialize everything

Examples:
  python scripts/manage_data.py init
  python scripts/manage_data.py fill --products 100 --users 30
  python scripts/manage_data.py sync --clear
  python scripts/manage_data.py status

=============================================================================
TESTING
=============================================================================

Run the test suite:

pytest tests/ -v

Run specific test files:
pytest tests/test_api_endpoints.py -v
pytest tests/test_database_init.py -v
pytest tests/test_data_generation.py -v

=============================================================================
EXAMPLE API CALLS
=============================================================================

1. Get consultation (curl):
   curl -X POST "http://localhost:8000/api/consultation/user_001" \
     -H "Content-Type: application/json" \
     -d '{"message": "I need a gold ring for engagement"}'

2. Search products:
   curl -X POST "http://localhost:8000/api/products/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "elegant gold ring", "limit": 5}'

3. Get customer profile:
   curl "http://localhost:8000/api/customer/user_001/profile"

4. Run customer analysis:
   curl -X POST "http://localhost:8000/api/analysis/customer"

5. Health check:
   curl "http://localhost:8000/api/health"

=============================================================================
DEVELOPMENT MODE
=============================================================================

To run in development mode with hot reload:

1. Install dependencies:
   pip install -r requirements.txt

2. Start services (PostgreSQL and Qdrant only):
   docker-compose up -d postgres qdrant

3. Run backend locally:
   python main.py

The API will run with hot reload at http://localhost:8000

=============================================================================
TROUBLESHOOTING
=============================================================================

1. Database connection fails:
   - Check PostgreSQL is running: docker-compose ps
   - Check connection string in .env
   - Check logs: docker-compose logs postgres

2. Qdrant connection fails:
   - Check Qdrant is running: docker-compose ps
   - Access Qdrant UI: http://localhost:6333/dashboard
   - Check logs: docker-compose logs qdrant

3. LLM provider errors:
   - Check API key in .env is correct
   - Check you have credits/quota
   - Check logs: docker-compose logs backend

4. No test data:
   - Run: python scripts/manage_data.py status
   - If empty, run: python scripts/manage_data.py fill
   - Then sync: python scripts/manage_data.py sync

5. API not responding:
   - Check backend is running: docker-compose ps
   - Check logs: docker-compose logs backend
   - Try health endpoint: curl http://localhost:8000/api/health

=============================================================================
PROJECT STRUCTURE
=============================================================================

agents/              # AI agent implementations
  - consultant_agent.py     # Jewelry consultation agent
  - analysis_agent.py       # Customer analytics agent
  - trend_agent.py          # Fashion trend analysis agent
  - orchestrator.py         # Agent orchestration

backend/             # API layer
  - routes.py              # FastAPI endpoints
  - schemas.py             # Pydantic models
  - dependencies.py        # Dependency injection

database/            # PostgreSQL layer
  - models.py              # SQLAlchemy models
  - repositories.py        # Data access layer
  - fill_data.py           # Test data generation
  - init_db.py             # Database initialization

llm/                 # LLM provider abstraction
  - openai_provider.py     # OpenAI implementation
  - gigachat_provider.py   # GigaChat implementation
  - factory.py             # Provider factory

rag/                 # RAG system with Qdrant
  - qdrant_service.py      # Qdrant operations
  - embeddings.py          # Embedding providers
  - retrieval.py           # RAG pipeline

scripts/             # CLI tools
  - manage_data.py         # Data management CLI

tests/               # Test suite
  - test_api_endpoints.py
  - test_database_init.py
  - test_data_generation.py

config.py            # Configuration settings
main.py              # FastAPI application entry point

=============================================================================
CONFIGURATION OPTIONS
=============================================================================

See env.example for all available configuration options including:
- LLM provider selection (OpenAI, GigaChat)
- Model selection for each provider
- Embeddings model configuration
- Database connection settings
- Qdrant configuration
- Auto-fill settings for test data

=============================================================================
SUPPORT & MORE INFO
=============================================================================

For detailed information, see the code comments and docstrings.
All major functions and classes are fully documented.

API Documentation: http://localhost:8000/docs (when running)
Qdrant Dashboard: http://localhost:6333/dashboard (when running)

=============================================================================

