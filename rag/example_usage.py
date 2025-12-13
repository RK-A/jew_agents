"""Example usage of RAG system for jewelry products"""

import asyncio
from config import settings
from rag.embedding_factory import create_embeddings_from_config
from rag.qdrant_service import QdrantService
from rag.retrieval import RAGRetriever


async def example_rag_usage():
    """Demonstrate RAG system usage"""
    
    # 1. Create LangChain embeddings
    embeddings = create_embeddings_from_config(settings)
    embedding_dimension = settings.get_embedding_dimension()
    print(f"✓ Created LangChain embeddings: {settings.embedding_provider}/{settings.embedding_model}")
    print(f"  Dimension: {embedding_dimension}")
    
    # 2. Initialize Qdrant service
    qdrant_service = QdrantService(
        url=settings.qdrant_url,
        collection_name=settings.qdrant_collection,
        embeddings=embeddings,
        embedding_dimension=embedding_dimension
    )
    print(f"✓ Initialized Qdrant service: {settings.qdrant_url}")
    
    # 3. Check collection status
    exists = await qdrant_service.collection_exists()
    if not exists:
        print("  Collection doesn't exist, creating...")
        await qdrant_service.create_collection()
    else:
        info = await qdrant_service.get_collection_info()
        print(f"  Collection exists: {info}")
    
    # 4. Initialize RAG retriever
    rag_retriever = RAGRetriever(qdrant_service)
    print("✓ Initialized RAG retriever")
    
    # 5. Example search without user preferences
    print("\n--- Example 1: Simple search ---")
    query = "elegant gold ring for engagement"
    result = await rag_retriever.retrieve_relevant_products(
        query=query,
        limit=3
    )
    print(f"Query: {query}")
    print(f"Found: {result['count']} products")
    for product in result['products']:
        print(f"  - {product['name']} ({product['price']}₽) [score: {product['score']:.2f}]")
    
    # 6. Example search with user preferences
    print("\n--- Example 2: Search with user preferences ---")
    user_preferences = {
        "style_preference": "classic",
        "budget_min": 20000,
        "budget_max": 60000,
        "preferred_materials": ["gold", "white_gold"],
        "skin_tone": "warm",
        "occasion_types": ["wedding", "formal"]
    }
    
    result = await rag_retriever.retrieve_relevant_products(
        query="wedding ring",
        user_preferences=user_preferences,
        limit=5,
        include_context=True
    )
    print(f"Query: wedding ring")
    print(f"Found: {result['count']} products")
    print("\nFormatted context for LLM:")
    print(result['llm_context'][:500] + "...")
    
    # 7. Example category search
    print("\n--- Example 3: Search by category ---")
    products = await rag_retriever.search_by_category(
        category="necklaces",
        limit=3
    )
    print(f"Found {len(products)} necklaces")
    for product in products:
        print(f"  - {product['name']}")
    
    # 8. Example trending products
    print("\n--- Example 4: Trending products ---")
    trending = await rag_retriever.search_trending_products(
        limit=5,
        trend_threshold=0.6
    )
    print(f"Found {len(trending)} trending products")
    for product in trending:
        trend_score = product.get('trend_score', 0)
        print(f"  - {product['name']} (trend: {trend_score:.2f})")
    
    # 9. Example direct Qdrant search
    print("\n--- Example 5: Direct Qdrant search with filters ---")
    products = await qdrant_service.search(
        query="modern bracelet",
        limit=3,
        material_filter=["silver"],
        price_min=10000,
        price_max=30000
    )
    print(f"Found {len(products)} silver bracelets (10k-30k₽)")
    for product in products:
        print(f"  - {product['name']} ({product['material']}, {product['price']}₽)")
    
    print("\n✓ All examples completed successfully!")


async def example_update_trend_scores():
    """Example of updating trend scores"""
    
    embeddings = create_embeddings_from_config(settings)
    embedding_dimension = settings.get_embedding_dimension()
    
    qdrant_service = QdrantService(
        url=settings.qdrant_url,
        collection_name=settings.qdrant_collection,
        embeddings=embeddings,
        embedding_dimension=embedding_dimension
    )
    
    # Update trend scores for specific products
    trend_updates = {
        "1": 0.95,  # Product 1 is highly trending
        "2": 0.85,  # Product 2 is trending
        "3": 0.60,  # Product 3 is moderately trending
    }
    
    count = await qdrant_service.update_trend_scores_batch(trend_updates)
    print(f"Updated trend scores for {count} products")


if __name__ == "__main__":
    print("=== RAG System Example Usage ===\n")
    asyncio.run(example_rag_usage())
    
    # Uncomment to test trend score updates
    # asyncio.run(example_update_trend_scores())

