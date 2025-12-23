"""Fix Qdrant dimension mismatch by recreating collection"""

import asyncio
import logging
from config import settings
from rag.embedding_factory import create_embeddings_from_config
from rag.qdrant_service import QdrantService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_and_fix_dimensions():
    """Check dimension mismatch and recreate collection if needed"""
    
    # Get current configuration
    embedding_model = settings.embedding_model
    expected_dim = settings.get_embedding_dimension()
    
    logger.info("=" * 60)
    logger.info("QDRANT DIMENSION FIX UTILITY")
    logger.info("=" * 60)
    logger.info(f"Current embedding provider: {settings.embedding_provider}")
    logger.info(f"Current embedding model: {embedding_model}")
    logger.info(f"Expected dimension: {expected_dim}")
    logger.info(f"Qdrant URL: {settings.qdrant_url}")
    logger.info(f"Collection: {settings.qdrant_collection}")
    logger.info("=" * 60)
    
    try:
        # Initialize embeddings
        logger.info("\nInitializing embeddings...")
        embeddings = create_embeddings_from_config(settings)
        
        # Test embedding dimension
        logger.info("Testing actual embedding dimension...")
        test_vector = await embeddings.aembed_query("test")
        actual_dim = len(test_vector)
        logger.info(f"Actual dimension from model: {actual_dim}")
        
        if actual_dim != expected_dim:
            logger.warning(
                f"\n⚠️  MISMATCH: Config says {expected_dim} but model produces {actual_dim}"
            )
            logger.warning("This usually means the model name in config.py EMBEDDING_DIMENSIONS is wrong")
        
        # Initialize Qdrant service
        logger.info("\nConnecting to Qdrant...")
        qdrant_service = QdrantService(
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection,
            embeddings=embeddings,
            embedding_dimension=actual_dim  # Use actual dimension
        )
        
        # Check if collection exists
        exists = await qdrant_service.collection_exists()
        
        if exists:
            logger.info(f"\n✓ Collection '{settings.qdrant_collection}' exists")
            
            try:
                # Try to get collection info
                info = await qdrant_service.get_collection_info()
                current_dim = info.get('vector_size', 'unknown')
                logger.info(f"Current collection dimension: {current_dim}")
                
                if current_dim != actual_dim:
                    logger.error(
                        f"\n❌ DIMENSION MISMATCH:\n"
                        f"   Collection expects: {current_dim}\n"
                        f"   Your model produces: {actual_dim}\n"
                    )
                    
                    # Ask for confirmation to recreate
                    logger.warning("\n⚠️  SOLUTION: Delete and recreate the collection")
                    logger.warning("This will DELETE all existing vectors!")
                    
                    response = input("\nRecreate collection? (yes/no): ").strip().lower()
                    
                    if response == "yes":
                        logger.info("\nRecreating collection...")
                        await qdrant_service.clear_collection()
                        logger.info(f"✓ Collection recreated with dimension {actual_dim}")
                        logger.info("\nNext steps:")
                        logger.info("  1. Run: python scripts/manage_data.py sync")
                        logger.info("  2. This will upload all products to Qdrant with correct dimensions")
                    else:
                        logger.info("\nAborted. Collection not changed.")
                        logger.info("\nAlternatively, you can:")
                        logger.info(f"  1. Change EMBEDDING_MODEL in .env to match collection dimension ({current_dim})")
                        logger.info("  2. Restart the application")
                else:
                    logger.info(f"\n✓ Dimensions match! Collection is OK.")
                    
            except Exception as e:
                logger.error(f"Error checking collection: {e}")
                logger.info("\nTry recreating the collection:")
                logger.info("  1. Delete collection manually or run clear command")
                logger.info("  2. Run: python scripts/manage_data.py init")
                logger.info("  3. Run: python scripts/manage_data.py sync")
        
        else:
            logger.info(f"\nCollection '{settings.qdrant_collection}' does NOT exist")
            logger.info("Creating new collection...")
            await qdrant_service.create_collection()
            logger.info(f"✓ Collection created with dimension {actual_dim}")
            logger.info("\nNext steps:")
            logger.info("  1. Run: python scripts/manage_data.py sync")
            logger.info("  2. This will upload all products to Qdrant")
    
    except Exception as e:
        logger.error(f"\n❌ Error: {e}", exc_info=True)
        return 1
    
    logger.info("\n" + "=" * 60)
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(check_and_fix_dimensions())
    exit(exit_code)



