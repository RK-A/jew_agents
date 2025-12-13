"""FastAPI dependency injection for services and agents"""

from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from sqlalchemy import text

from config import settings
from database.session import AsyncSessionLocal, engine
from database.repositories import (
    JewelryProductRepository,
    CustomerPreferenceRepository,
    ConsultationRecordRepository
)
from llm.factory import create_llm_provider_from_config
from rag.qdrant_service import QdrantService
from rag.embedding_factory import create_embeddings_from_config
from agents.orchestrator import AgentOrchestrator
from utils.logging import get_logger


logger = get_logger(__name__)


# Database session dependency
async def get_db_session():
    """
    Provide async database session
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


# Repository dependencies
async def get_product_repository(session = Depends(get_db_session)) -> JewelryProductRepository:
    """Get jewelry product repository"""
    return JewelryProductRepository(session)


async def get_preference_repository(session = Depends(get_db_session)) -> CustomerPreferenceRepository:
    """Get customer preference repository"""
    return CustomerPreferenceRepository(session)


async def get_consultation_repository(session = Depends(get_db_session)) -> ConsultationRecordRepository:
    """Get consultation record repository"""
    return ConsultationRecordRepository(session)


# LLM provider dependency
_llm_provider_instance = None

async def get_llm_provider():
    """
    Get LLM provider singleton instance
    
    Returns:
        LLMProvider: Configured LLM provider
    """
    global _llm_provider_instance
    
    if _llm_provider_instance is None:
        try:
            _llm_provider_instance = create_llm_provider_from_config(settings)
            logger.info(f"LLM provider initialized: {settings.llm_provider}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM provider: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"LLM provider initialization failed: {str(e)}"
            )
    
    return _llm_provider_instance


# Embeddings service dependency
_embeddings_instance = None

async def get_embeddings_service():
    """
    Get LangChain embeddings singleton instance
    
    Returns:
        Embeddings: Configured LangChain embeddings
    """
    global _embeddings_instance
    
    if _embeddings_instance is None:
        try:
            _embeddings_instance = create_embeddings_from_config(settings)
            logger.info(f"LangChain embeddings initialized: {settings.embedding_provider}/{settings.embedding_model}")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            # Non-critical, can continue without embeddings
            logger.warning("Continuing without embeddings")
    
    return _embeddings_instance


# Qdrant service dependency
_qdrant_service_instance = None

async def get_qdrant_service(
    embeddings_service = Depends(get_embeddings_service)
):
    """
    Get Qdrant service singleton instance
    
    Args:
        embeddings_service: LangChain embeddings dependency
    
    Returns:
        QdrantService: Configured Qdrant service
    """
    global _qdrant_service_instance
    
    if _qdrant_service_instance is None:
        try:
            embedding_dimension = settings.get_embedding_dimension()
            _qdrant_service_instance = QdrantService(
                url=settings.qdrant_url,
                collection_name=settings.qdrant_collection,
                embeddings=embeddings_service,
                embedding_dimension=embedding_dimension
            )
            logger.info(f"Qdrant service initialized: {settings.qdrant_url} (dim: {embedding_dimension})")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant service: {e}")
            # Non-critical, can continue without RAG
            logger.warning("Continuing without Qdrant service")
    
    return _qdrant_service_instance


# Agent orchestrator dependency
_orchestrator_instance = None

async def get_orchestrator(
    llm_provider = Depends(get_llm_provider),
    qdrant_service = Depends(get_qdrant_service)
):
    """
    Get agent orchestrator singleton instance
    
    Args:
        llm_provider: LLM provider dependency
        qdrant_service: Qdrant service dependency
    
    Returns:
        AgentOrchestrator: Configured agent orchestrator
    """
    global _orchestrator_instance
    
    if _orchestrator_instance is None:
        try:
            # Prepare custom prompts dict
            custom_prompts = {}
            if settings.agent_custom_prompt_consultant:
                custom_prompts["consultant"] = settings.agent_custom_prompt_consultant
            if settings.agent_custom_prompt_analysis:
                custom_prompts["analysis"] = settings.agent_custom_prompt_analysis
            if settings.agent_custom_prompt_trend:
                custom_prompts["trend"] = settings.agent_custom_prompt_trend
            
            _orchestrator_instance = AgentOrchestrator(
                llm_provider=llm_provider,
                rag_service=qdrant_service,
                language=settings.agent_language,
                custom_prompts=custom_prompts if custom_prompts else None
            )
            logger.info(f"Agent orchestrator initialized (language: {settings.agent_language})")
        except Exception as e:
            logger.error(f"Failed to initialize agent orchestrator: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Agent orchestrator initialization failed: {str(e)}"
            )
    
    return _orchestrator_instance


# Health check helpers
async def check_database_health() -> bool:
    """
    Check database connection health
    
    Returns:
        bool: True if database is accessible
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def check_qdrant_health(qdrant_service: QdrantService = None) -> bool:
    """
    Check Qdrant connection health
    
    Args:
        qdrant_service: Qdrant service instance
    
    Returns:
        bool: True if Qdrant is accessible
    """
    if qdrant_service is None:
        return False
    
    try:
        # Try to get collection info
        collection_info = await qdrant_service.get_collection_info()
        return collection_info is not None
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        return False


# Cleanup on shutdown
async def cleanup_dependencies():
    """Cleanup all singleton dependencies"""
    global _llm_provider_instance, _embeddings_instance, _qdrant_service_instance, _orchestrator_instance
    
    logger.info("Cleaning up dependencies")
    
    # Reset all singletons
    _llm_provider_instance = None
    _embeddings_instance = None
    _qdrant_service_instance = None
    _orchestrator_instance = None
    
    logger.info("Dependencies cleanup complete")

