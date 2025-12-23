"""Simplified RAG service using LangChain Qdrant integration"""

import logging
from typing import List, Dict, Any, Optional

from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import Qdrant
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams


logger = logging.getLogger(__name__)


class LangChainRAG:
    """Simplified RAG service using LangChain's Qdrant integration"""
    
    def __init__(
        self,
        url: str,
        collection_name: str,
        embeddings: Embeddings,
        embedding_dimension: int
    ):
        """
        Initialize LangChain RAG service
        
        Args:
            url: Qdrant server URL
            collection_name: Collection name for products
            embeddings: LangChain embeddings instance
            embedding_dimension: Embedding vector dimension
        """
        self.url = url
        self.collection_name = collection_name
        self.embeddings = embeddings
        self.embedding_dimension = embedding_dimension
        self.client = AsyncQdrantClient(url=url)
        self.vector_store = None
        
        logger.info(f"Initialized LangChain RAG: {url}, collection: {collection_name}")
    
    async def initialize_collection(self) -> bool:
        """Create collection if not exists"""
        try:
            collections = await self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
                return True
            
            logger.info(f"Collection {self.collection_name} already exists")
            return False
        
        except Exception as e:
            logger.error(f"Error initializing collection: {e}", exc_info=True)
            raise
    
    def get_vector_store(self) -> Qdrant:
        """Get or create LangChain Qdrant vector store"""
        if self.vector_store is None:
            self.vector_store = Qdrant(
                client=self.client,
                collection_name=self.collection_name,
                embeddings=self.embeddings
            )
        return self.vector_store
    
    async def add_products(self, products: List[Dict[str, Any]]) -> int:
        """
        Add products to vector store
        
        Args:
            products: List of product dicts with text and metadata
            
        Returns:
            Number of products added
        """
        try:
            if not products:
                return 0
            
            texts = []
            metadatas = []
            ids = []
            
            for product in products:
                text = self._build_product_text(product)
                texts.append(text)
                metadatas.append(product)
                ids.append(str(product.get("product_id", product.get("id"))))
            
            vector_store = self.get_vector_store()
            await vector_store.aadd_texts(
                texts=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(products)} products to vector store")
            return len(products)
        
        except Exception as e:
            logger.error(f"Error adding products: {e}", exc_info=True)
            raise
    
    def _build_product_text(self, product: Dict[str, Any]) -> str:
        """Build searchable text from product data"""
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
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for products
        
        Args:
            query: Search query
            limit: Maximum results
            filters: Optional metadata filters
            
        Returns:
            List of products with scores
        """
        try:
            vector_store = self.get_vector_store()
            
            results = await vector_store.asimilarity_search_with_score(
                query=query,
                k=limit,
                filter=filters
            )
            
            products = []
            for doc, score in results:
                product = doc.metadata.copy()
                product["score"] = float(score)
                product["text"] = doc.page_content
                products.append(product)
            
            logger.debug(f"Search '{query}' returned {len(products)} results")
            return products
        
        except Exception as e:
            logger.error(f"Error searching: {e}", exc_info=True)
            return []
    
    async def search_with_preferences(
        self,
        query: str,
        user_preferences: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search with user preference filtering
        
        Args:
            query: Search query
            user_preferences: User preferences for filtering
            limit: Maximum results
            
        Returns:
            List of filtered products
        """
        try:
            filters = self._build_filters(user_preferences)
            products = await self.search(query, limit=limit * 2, filters=filters)
            
            if user_preferences:
                products = self._apply_preference_ranking(products, user_preferences)
            
            return products[:limit]
        
        except Exception as e:
            logger.error(f"Error searching with preferences: {e}", exc_info=True)
            return []
    
    def _build_filters(self, preferences: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Build Qdrant filters from user preferences"""
        if not preferences:
            return None
        
        filters = {}
        
        if preferences.get("preferred_materials"):
            filters["material"] = {"$in": preferences["preferred_materials"]}
        
        price_min = preferences.get("budget_min")
        price_max = preferences.get("budget_max")
        if price_min is not None or price_max is not None:
            price_filter = {}
            if price_min is not None:
                price_filter["$gte"] = price_min
            if price_max is not None:
                price_filter["$lte"] = price_max
            filters["price"] = price_filter
        
        return filters if filters else None
    
    def _apply_preference_ranking(
        self,
        products: List[Dict[str, Any]],
        preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply preference-based ranking boost"""
        for product in products:
            boost = 0.0
            
            if preferences.get("style_preference"):
                if product.get("style") == preferences["style_preference"]:
                    boost += 0.1
            
            if preferences.get("preferred_materials"):
                if product.get("material") in preferences["preferred_materials"]:
                    boost += 0.1
            
            product["score"] = product.get("score", 0.0) + boost
        
        return sorted(products, key=lambda x: x.get("score", 0), reverse=True)
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            info = await self.client.get_collection(self.collection_name)
            
            return {
                "name": self.collection_name,
                "points_count": getattr(info, 'points_count', 0),
                "vectors_count": getattr(info, 'vectors_count', 0),
                "status": str(info.status) if hasattr(info, 'status') else "unknown",
                "vector_size": self.embedding_dimension,
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}", exc_info=True)
            return {}
    
    async def clear_collection(self) -> bool:
        """Clear all products from collection"""
        try:
            await self.client.delete_collection(self.collection_name)
            await self.initialize_collection()
            logger.info(f"Cleared collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {e}", exc_info=True)
            return False

