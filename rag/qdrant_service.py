"""Qdrant vector database service for jewelry products"""

import logging
from typing import List, Dict, Any, Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
)
from rag.embeddings import EmbeddingProvider


logger = logging.getLogger(__name__)


class QdrantService:
    """Service for managing jewelry products in Qdrant vector database"""
    
    def __init__(
        self,
        url: str,
        collection_name: str,
        embedding_provider: EmbeddingProvider
    ):
        self.client = AsyncQdrantClient(url=url)
        self.collection_name = collection_name
        self.embedding_provider = embedding_provider
        logger.info(f"Initialized Qdrant service: {url}, collection: {collection_name}")
    
    async def create_collection(self) -> bool:
        """Create jewelry_products collection if not exists"""
        try:
            collections = await self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name in collection_names:
                logger.info(f"Collection {self.collection_name} already exists")
                return False
            
            dimension = self.embedding_provider.get_dimension()
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection {self.collection_name} with dimension {dimension}")
            return True
        
        except Exception as e:
            logger.error(f"Error creating collection: {e}", exc_info=True)
            raise
    
    async def collection_exists(self) -> bool:
        """Check if collection exists"""
        try:
            collections = await self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            return self.collection_name in collection_names
        except Exception as e:
            logger.error(f"Error checking collection existence: {e}", exc_info=True)
            return False
    
    async def upsert_product(
        self,
        product_id: str,
        description: str,
        payload: Dict[str, Any]
    ) -> bool:
        """Add or update product in Qdrant"""
        try:
            embedding = await self.embedding_provider.embed(description)
            
            point = PointStruct(
                id=product_id,
                vector=embedding,
                payload=payload
            )
            
            await self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.debug(f"Upserted product {product_id} to Qdrant")
            return True
        
        except Exception as e:
            logger.error(f"Error upserting product {product_id}: {e}", exc_info=True)
            raise
    
    async def upsert_products_batch(
        self,
        products: List[Dict[str, Any]]
    ) -> int:
        """Batch upsert multiple products"""
        if not products:
            return 0
        
        try:
            descriptions = [
                self._build_product_description(p) for p in products
            ]
            
            embeddings = await self.embedding_provider.embed_batch(descriptions)
            
            points = [
                PointStruct(
                    id=str(product["product_id"]),
                    vector=embedding,
                    payload=product
                )
                for product, embedding in zip(products, embeddings)
            ]
            
            await self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Batch upserted {len(points)} products to Qdrant")
            return len(points)
        
        except Exception as e:
            logger.error(f"Error batch upserting products: {e}", exc_info=True)
            raise
    
    def _build_product_description(self, product: Dict[str, Any]) -> str:
        """Build comprehensive description for embedding"""
        parts = [
            product.get("name", ""),
            product.get("description", ""),
            f"category: {product.get('category', '')}",
            f"material: {product.get('material', '')}",
            f"style: {product.get('style', '')}",
        ]
        return " ".join(filter(None, parts))
    
    async def search(
        self,
        query: str,
        limit: int = 5,
        category_filter: Optional[str] = None,
        material_filter: Optional[List[str]] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Semantic search for products with optional filters"""
        try:
            query_embedding = await self.embedding_provider.embed(query)
            
            query_filter = self._build_filter(
                category_filter=category_filter,
                material_filter=material_filter,
                price_min=price_min,
                price_max=price_max
            )
            
            results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=query_filter,
                score_threshold=score_threshold
            )
            
            products = [
                {
                    "product_id": result.id,
                    "score": result.score,
                    **result.payload
                }
                for result in results
            ]
            
            logger.debug(f"Search query '{query}' returned {len(products)} results")
            return products
        
        except Exception as e:
            logger.error(f"Error searching products: {e}", exc_info=True)
            raise
    
    def _build_filter(
        self,
        category_filter: Optional[str] = None,
        material_filter: Optional[List[str]] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None
    ) -> Optional[Filter]:
        """Build Qdrant filter from search parameters"""
        conditions = []
        
        if category_filter:
            conditions.append(
                FieldCondition(
                    key="category",
                    match=MatchValue(value=category_filter)
                )
            )
        
        if material_filter:
            for material in material_filter:
                conditions.append(
                    FieldCondition(
                        key="material",
                        match=MatchValue(value=material)
                    )
                )
        
        if price_min is not None or price_max is not None:
            conditions.append(
                FieldCondition(
                    key="price",
                    range=Range(
                        gte=price_min,
                        lte=price_max
                    )
                )
            )
        
        if not conditions:
            return None
        
        return Filter(must=conditions)
    
    async def update_trend_score(
        self,
        product_id: str,
        trend_score: float
    ) -> bool:
        """Update trend score for a product"""
        try:
            await self.client.set_payload(
                collection_name=self.collection_name,
                payload={"trend_score": trend_score},
                points=[product_id]
            )
            
            logger.debug(f"Updated trend score for product {product_id}: {trend_score}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating trend score for {product_id}: {e}", exc_info=True)
            raise
    
    async def update_trend_scores_batch(
        self,
        updates: Dict[str, float]
    ) -> int:
        """Batch update trend scores for multiple products"""
        if not updates:
            return 0
        
        try:
            count = 0
            for product_id, trend_score in updates.items():
                await self.update_trend_score(product_id, trend_score)
                count += 1
            
            logger.info(f"Batch updated trend scores for {count} products")
            return count
        
        except Exception as e:
            logger.error(f"Error batch updating trend scores: {e}", exc_info=True)
            raise
    
    async def delete_product(self, product_id: str) -> bool:
        """Delete product from Qdrant"""
        try:
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=[product_id]
            )
            
            logger.debug(f"Deleted product {product_id} from Qdrant")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting product {product_id}: {e}", exc_info=True)
            raise
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information and statistics"""
        try:
            info = await self.client.get_collection(self.collection_name)
            return {
                "name": info.config.params.vectors.size if hasattr(info.config.params, 'vectors') else None,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status,
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}", exc_info=True)
            raise
    
    async def clear_collection(self) -> bool:
        """Clear all products from collection"""
        try:
            await self.client.delete_collection(self.collection_name)
            await self.create_collection()
            logger.info(f"Cleared collection {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {e}", exc_info=True)
            raise

