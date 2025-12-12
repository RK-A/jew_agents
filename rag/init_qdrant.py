"""Initialize Qdrant collection for jewelry products"""

import asyncio
import logging
from config import settings
from rag.embeddings import create_embedding_provider
from rag.qdrant_service import QdrantService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_qdrant_collection() -> bool:
    """Initialize Qdrant collection if it doesn't exist"""
    try:
        logger.info("Initializing Qdrant collection...")
        
        embedding_provider = create_embedding_provider(
            model=settings.embedding_model,
            api_key=settings.embedding_api_key
        )
        
        qdrant_service = QdrantService(
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection,
            embedding_provider=embedding_provider
        )
        
        exists = await qdrant_service.collection_exists()
        
        if exists:
            logger.info(f"Collection '{settings.qdrant_collection}' already exists")
            info = await qdrant_service.get_collection_info()
            logger.info(f"Collection info: {info}")
            return False
        
        created = await qdrant_service.create_collection()
        
        if created:
            logger.info(f"Successfully created collection '{settings.qdrant_collection}'")
            logger.info(f"Vector dimension: {embedding_provider.get_dimension()}")
            return True
        
        return False
    
    except Exception as e:
        logger.error(f"Error initializing Qdrant: {e}", exc_info=True)
        raise


async def check_qdrant_status() -> dict:
    """Check Qdrant collection status and return info"""
    try:
        embedding_provider = create_embedding_provider(
            model=settings.embedding_model,
            api_key=settings.embedding_api_key
        )
        
        qdrant_service = QdrantService(
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection,
            embedding_provider=embedding_provider
        )
        
        exists = await qdrant_service.collection_exists()
        
        if not exists:
            return {
                "exists": False,
                "message": f"Collection '{settings.qdrant_collection}' does not exist"
            }
        
        info = await qdrant_service.get_collection_info()
        
        return {
            "exists": True,
            "collection_name": settings.qdrant_collection,
            "info": info
        }
    
    except Exception as e:
        logger.error(f"Error checking Qdrant status: {e}", exc_info=True)
        return {
            "exists": False,
            "error": str(e)
        }


async def clear_qdrant_collection() -> bool:
    """Clear all data from Qdrant collection"""
    try:
        logger.warning("Clearing Qdrant collection...")
        
        embedding_provider = create_embedding_provider(
            model=settings.embedding_model,
            api_key=settings.embedding_api_key
        )
        
        qdrant_service = QdrantService(
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection,
            embedding_provider=embedding_provider
        )
        
        await qdrant_service.clear_collection()
        logger.info(f"Successfully cleared collection '{settings.qdrant_collection}'")
        return True
    
    except Exception as e:
        logger.error(f"Error clearing Qdrant collection: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(init_qdrant_collection())

