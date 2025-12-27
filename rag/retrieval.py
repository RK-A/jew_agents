"""Simplified RAG retrieval pipeline using LangChain"""

import logging
from typing import List, Dict, Any, Optional, Union
from rag.qdrant_service import QdrantService
from rag.langchain_rag import LangChainRAG


logger = logging.getLogger(__name__)


class RAGRetriever:
    """Simplified RAG retrieval pipeline using LangChain integration"""
    
    def __init__(self, rag_service: Union[QdrantService, LangChainRAG]):
        """
        Initialize RAG retriever
        
        Args:
            rag_service: Either QdrantService (legacy) or LangChainRAG (recommended)
        """
        self.rag_service = rag_service
        self.use_langchain = isinstance(rag_service, LangChainRAG)
        logger.info(f"Initialized RAG retriever (LangChain: {self.use_langchain})")
    
    async def retrieve_relevant_products(
        self,
        query: str,
        user_preferences: Optional[Dict[str, Any]] = None,
        limit: int = 5,
        include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve relevant products based on query and user preferences
        
        Args:
            query: User query string
            user_preferences: User preference dict (style, budget, materials, etc.)
            limit: Maximum number of products to return
            include_context: Whether to include formatted context for LLM
        
        Returns:
            Dict with products and optional LLM context
        """
        try:
            if self.use_langchain:
                products = await self.rag_service.search_with_preferences(
                    query=query,
                    user_preferences=user_preferences,
                    limit=limit
                )
            else:
                category_filter = None
                material_filter = None
                price_min = None
                price_max = None
                
                if user_preferences:
                    preferred_materials = user_preferences.get("preferred_materials", [])
                    if preferred_materials:
                        material_filter = preferred_materials
                    
                    budget_min = user_preferences.get("budget_min")
                    budget_max = user_preferences.get("budget_max")
                    if budget_min is not None:
                        price_min = budget_min
                    if budget_max is not None:
                        price_max = budget_max
                    
                    if "category" in query.lower():
                        for cat in ["rings", "necklaces", "bracelets", "earrings", "pendants"]:
                            if cat in query.lower():
                                category_filter = cat
                                break
                
                products = await self.rag_service.search(
                    query=query,
                    limit=limit,
                    category_filter=category_filter,
                    material_filter=material_filter,
                    price_min=price_min,
                    price_max=price_max,
                    score_threshold=0.45
                )
            
            result = {
                "products": products,
                "count": len(products),
                "query": query
            }
            
            if include_context:
                result["llm_context"] = self._format_products_for_llm(
                    products=products,
                    user_preferences=user_preferences
                )
            
            logger.info(f"Retrieved {len(products)} products for query: '{query}'")
            return result
        
        except Exception as e:
            logger.error(f"Error retrieving products: {e}", exc_info=True)
            return {
                "products": [],
                "count": 0,
                "query": query,
                "error": str(e)
            }
    
    def _format_products_for_llm(
        self,
        products: List[Dict[str, Any]],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format retrieved products as context for LLM"""
        if not products:
            return "No matching products found in catalog."
        
        context_parts = []
        
        if user_preferences:
            prefs_text = self._format_user_preferences(user_preferences)
            context_parts.append(f"User Preferences:\n{prefs_text}\n")
        
        context_parts.append(f"Found {len(products)} relevant products:\n")
        
        for idx, product in enumerate(products, 1):
            product_text = self._format_single_product(product, idx)
            context_parts.append(product_text)
        
        return "\n".join(context_parts)
    
    def _format_user_preferences(self, preferences: Dict[str, Any]) -> str:
        """Format user preferences for LLM context"""
        parts = []
        
        if preferences.get("style_preference"):
            parts.append(f"- Style: {preferences['style_preference']}")
        
        budget_min = preferences.get("budget_min")
        budget_max = preferences.get("budget_max")
        if budget_min or budget_max:
            budget_str = f"- Budget: {budget_min or 0}₽ - {budget_max or 'unlimited'}₽"
            parts.append(budget_str)
        
        materials = preferences.get("preferred_materials", [])
        if materials:
            parts.append(f"- Preferred materials: {', '.join(materials)}")
        
        if preferences.get("skin_tone"):
            parts.append(f"- Skin tone: {preferences['skin_tone']}")
        
        occasions = preferences.get("occasion_types", [])
        if occasions:
            parts.append(f"- Occasions: {', '.join(occasions)}")
        
        return "\n".join(parts) if parts else "No specific preferences"
    
    def _format_single_product(self, product: Dict[str, Any], index: int) -> str:
        """Format single product for LLM context"""
        parts = [f"\n{index}. {product.get('name', 'Unknown')}"]
        
        if product.get("description"):
            parts.append(f"   Description: {product['description']}")
        
        details = []
        if product.get("category"):
            details.append(f"Category: {product['category']}")
        if product.get("material"):
            details.append(f"Material: {product['material']}")
        if product.get("price"):
            details.append(f"Price: {product['price']}₽")
        if product.get("weight"):
            details.append(f"Weight: {product['weight']}g")
        
        if details:
            parts.append(f"   {', '.join(details)}")
        
        if product.get("design_details"):
            design = product["design_details"]
            if isinstance(design, dict):
                design_parts = [f"{k}: {v}" for k, v in design.items()]
                parts.append(f"   Design: {', '.join(design_parts)}")
        
        if product.get("stock_count") is not None:
            stock = product["stock_count"]
            stock_status = "In stock" if stock > 0 else "Out of stock"
            parts.append(f"   Availability: {stock_status} ({stock} units)")
        
        if product.get("score"):
            parts.append(f"   Relevance: {product['score']:.2f}")
        
        return "\n".join(parts)
    
    async def search_by_category(
        self,
        category: str,
        user_preferences: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search products by category with preferences"""
        query = f"{category} jewelry"
        
        try:
            if self.use_langchain:
                products = await self.rag_service.search_with_preferences(
                    query=query,
                    user_preferences=user_preferences,
                    limit=limit
                )
            else:
                products = await self.rag_service.search(
                    query=query,
                    limit=limit,
                    category_filter=category,
                    material_filter=user_preferences.get("preferred_materials") if user_preferences else None,
                    price_min=user_preferences.get("budget_min") if user_preferences else None,
                    price_max=user_preferences.get("budget_max") if user_preferences else None
                )
            
            logger.info(f"Found {len(products)} products in category: {category}")
            return products
        
        except Exception as e:
            logger.error(f"Error searching by category {category}: {e}", exc_info=True)
            return []
    
    async def search_by_style(
        self,
        style: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search products by style"""
        query = f"{style} style jewelry"
        
        try:
            if self.use_langchain:
                products = await self.rag_service.search(query=query, limit=limit)
            else:
                products = await self.rag_service.search(query=query, limit=limit)
            
            style_products = [
                p for p in products
                if p.get("style", "").lower() == style.lower()
            ]
            
            logger.info(f"Found {len(style_products)} products with style: {style}")
            return style_products if style_products else products
        
        except Exception as e:
            logger.error(f"Error searching by style {style}: {e}", exc_info=True)
            return []
    
    async def search_trending_products(
        self,
        limit: int = 10,
        trend_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for trending products with high trend scores"""
        query = "trending fashionable jewelry"
        
        try:
            if self.use_langchain:
                products = await self.rag_service.search(query=query, limit=limit * 2)
            else:
                products = await self.rag_service.search(query=query, limit=limit * 2)
            
            trending = [
                p for p in products
                if p.get("trend_score", 0) >= trend_threshold
            ]
            
            trending = sorted(
                trending,
                key=lambda x: x.get("trend_score", 0),
                reverse=True
            )[:limit]
            
            logger.info(f"Found {len(trending)} trending products")
            return trending
        
        except Exception as e:
            logger.error(f"Error searching trending products: {e}", exc_info=True)
            return []

