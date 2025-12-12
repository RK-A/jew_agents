from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from database.session import init_db, close_db
from database.init_db import create_tables, get_table_counts
from database.fill_data import fill_database
from rag.init_qdrant import init_qdrant_collection
from rag.fill_qdrant import sync_products_to_qdrant
from backend.routes import router
from backend.dependencies import cleanup_dependencies
from utils.logging import setup_logging, get_logger


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    
    # Startup
    setup_logging()
    logger.info("Starting AI Jewelry Consultation System")
    logger.info(f"LLM Provider: {settings.llm_provider}")
    logger.info(f"LLM Model: {settings.llm_model}")
    
    try:
        # Initialize database
        await init_db()
        await create_tables()
        logger.info("Database initialized successfully")
        
        # Initialize Qdrant
        try:
            await init_qdrant_collection()
            logger.info("Qdrant initialized successfully")
        except Exception as e:
            logger.warning(f"Qdrant initialization issue (may already exist): {e}")
        
        # Auto-fill data if enabled
        if settings.auto_fill_data:
            logger.info("AUTO_FILL_DATA is enabled, checking if data needs to be filled...")
            counts = await get_table_counts()
            
            if counts.get("jewelry_products", 0) == 0:
                logger.info("No products found, filling database with test data...")
                await fill_database(
                    products_count=settings.default_products_count,
                    users_count=settings.default_users_count,
                    consultations_count=settings.default_consultations_count
                )
                logger.info("Test data filled successfully")
                
                # Sync products to Qdrant
                logger.info("Syncing products to Qdrant...")
                count = await sync_products_to_qdrant()
                logger.info(f"Synced {count} products to Qdrant")
            else:
                logger.info(f"Data already exists: {counts}")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    await cleanup_dependencies()
    await close_db()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="AI Jewelry Consultation System",
    description="Multi-agent AI system for jewelry consultation with RAG and LLM",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Jewelry Consultation System",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

