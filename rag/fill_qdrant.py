"""Fill Qdrant with jewelry products from PostgreSQL"""

import asyncio
import logging
from typing import List, Dict, Any
from sqlalchemy import select
from config import settings
from database.session import async_session_factory
from database.models import JewelryProduct
from rag.embedding_factory import create_embeddings_from_config
from rag.qdrant_service import QdrantService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch_all_products() -> List[Dict[str, Any]]:
    """Fetch all jewelry products from PostgreSQL"""
    try:
        async with async_session_factory() as session:
            result = await session.execute(select(JewelryProduct))
            products_orm = result.scalars().all()
            
            products = []
            for product in products_orm:
                product_dict = {
                    "product_id": str(product.id),
                    "name": product.name,
                    "description": product.description,
                    "category": product.category,
                    "material": product.material,
                    "weight": float(product.weight) if product.weight else None,
                    "price": float(product.price),
                    "design_details": product.design_details or {},
                    "images": product.images or [],
                    "stock_count": product.stock_count,
                    "style": product.design_details.get("style") if product.design_details else None,
                    "trend_score": 0.5,
                    "created_at": product.created_at.isoformat() if product.created_at else None,
                }
                products.append(product_dict)
            
            logger.info(f"Fetched {len(products)} products from PostgreSQL")
            return products
    
    except Exception as e:
        logger.error(f"Error fetching products from database: {e}", exc_info=True)
        raise


async def sync_products_to_qdrant(
    batch_size: int = 50,
    clear_existing: bool = False
) -> int:
    """
    Sync products from PostgreSQL to Qdrant
    
    Args:
        batch_size: Number of products to process in each batch
        clear_existing: Whether to clear existing collection before sync
    
    Returns:
        Number of products synced
    """
    try:
        logger.info("Starting product sync to Qdrant...")
        
        embeddings = create_embeddings_from_config(settings)
        embedding_dimension = settings.get_embedding_dimension()
        
        qdrant_service = QdrantService(
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection,
            embeddings=embeddings,
            embedding_dimension=embedding_dimension
        )
        
        exists = await qdrant_service.collection_exists()
        if not exists:
            logger.info("Collection doesn't exist, creating...")
            await qdrant_service.create_collection()
        elif clear_existing:
            logger.info("Clearing existing collection...")
            await qdrant_service.clear_collection()
        
        products = await fetch_all_products()
        
        if not products:
            logger.warning("No products found in database")
            return 0
        
        total_synced = 0
        
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1}: {len(batch)} products")
            
            count = await qdrant_service.upsert_products_batch(batch)
            total_synced += count
            
            logger.info(f"Progress: {total_synced}/{len(products)} products synced")
        
        logger.info(f"Successfully synced {total_synced} products to Qdrant")
        
        info = await qdrant_service.get_collection_info()
        logger.info(f"Collection info: {info}")
        
        return total_synced
    
    except Exception as e:
        logger.error(f"Error syncing products to Qdrant: {e}", exc_info=True)
        raise


async def sync_single_product(product_id: int) -> bool:
    """Sync a single product to Qdrant"""
    try:
        async with async_session_factory() as session:
            result = await session.execute(
                select(JewelryProduct).where(JewelryProduct.id == product_id)
            )
            product = result.scalar_one_or_none()
            
            if not product:
                logger.error(f"Product {product_id} not found in database")
                return False
            
            embeddings = create_embeddings_from_config(settings)
            embedding_dimension = settings.get_embedding_dimension()
            
            qdrant_service = QdrantService(
                url=settings.qdrant_url,
                collection_name=settings.qdrant_collection,
                embeddings=embeddings,
                embedding_dimension=embedding_dimension
            )
            
            product_dict = {
                "product_id": str(product.id),
                "name": product.name,
                "description": product.description,
                "category": product.category,
                "material": product.material,
                "weight": float(product.weight) if product.weight else None,
                "price": float(product.price),
                "design_details": product.design_details or {},
                "images": product.images or [],
                "stock_count": product.stock_count,
                "style": product.design_details.get("style") if product.design_details else None,
                "trend_score": 0.5,
            }
            
            description = qdrant_service._build_product_description(product_dict)
            
            await qdrant_service.upsert_product(
                product_id=str(product.id),
                description=description,
                payload=product_dict
            )
            
            logger.info(f"Successfully synced product {product_id} to Qdrant")
            return True
    
    except Exception as e:
        logger.error(f"Error syncing product {product_id}: {e}", exc_info=True)
        raise


async def update_product_trend_scores(trend_updates: Dict[str, float]) -> int:
    """
    Update trend scores for products in Qdrant
    
    Args:
        trend_updates: Dict mapping product_id to trend_score
    
    Returns:
        Number of products updated
    """
    try:
        embeddings = create_embeddings_from_config(settings)
        embedding_dimension = settings.get_embedding_dimension()
        
        qdrant_service = QdrantService(
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection,
            embeddings=embeddings,
            embedding_dimension=embedding_dimension
        )
        
        count = await qdrant_service.update_trend_scores_batch(trend_updates)
        logger.info(f"Updated trend scores for {count} products")
        return count
    
    except Exception as e:
        logger.error(f"Error updating trend scores: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        asyncio.run(sync_products_to_qdrant(clear_existing=True))
    else:
        asyncio.run(sync_products_to_qdrant())

