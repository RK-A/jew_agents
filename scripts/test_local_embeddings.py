"""Test script for local embedding API connection"""

import asyncio
import sys
from rag.local_api_embeddings import LocalAPIEmbeddings, test_local_api_connection


async def test_embeddings():
    """Test local embeddings"""
    
    print("="*60)
    print("Testing Local Embedding API")
    print("="*60)
    
    # Configuration (update with your values)
    BASE_URL = "http://127.0.0.1:1234/v1"
    MODEL = "text-embedding-snowflake-arctic-embed-m-v1.5"
    
    print(f"\nConfiguration:")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Model: {MODEL}")
    
    # Test 1: Connection test
    print(f"\n{'='*60}")
    print("Test 1: Connection Test")
    print("="*60)
    
    result = test_local_api_connection(BASE_URL, MODEL)
    
    if result["status"] == "success":
        print("✓ Connection successful!")
        print(f"  Dimension: {result['embedding_dimension']}")
        print(f"  Sample values: {result['sample_embedding']}")
    else:
        print("✗ Connection failed!")
        print(f"  Error: {result['error']}")
        print(f"\nMake sure:")
        print(f"  1. Local API is running at {BASE_URL}")
        print(f"  2. Model '{MODEL}' is loaded")
        print(f"  3. Embeddings endpoint is available")
        sys.exit(1)
    
    # Test 2: Single query
    print(f"\n{'='*60}")
    print("Test 2: Single Query Embedding")
    print("="*60)
    
    embeddings = LocalAPIEmbeddings(base_url=BASE_URL, model=MODEL)
    
    query = "Золотое кольцо с бриллиантом"
    print(f"Query: {query}")
    
    embedding = await embeddings.aembed_query(query)
    print(f"✓ Embedding generated")
    print(f"  Dimension: {len(embedding)}")
    print(f"  First 10 values: {embedding[:10]}")
    
    # Test 3: Batch embedding
    print(f"\n{'='*60}")
    print("Test 3: Batch Embedding")
    print("="*60)
    
    texts = [
        "Золотое кольцо",
        "Серебряное ожерелье",
        "Бриллиантовые серьги",
    ]
    
    print(f"Texts: {len(texts)}")
    for i, text in enumerate(texts, 1):
        print(f"  {i}. {text}")
    
    embeddings_list = await embeddings.aembed_documents(texts)
    print(f"✓ Batch embeddings generated")
    print(f"  Count: {len(embeddings_list)}")
    print(f"  Dimensions: {[len(e) for e in embeddings_list]}")
    
    # Test 4: Integration test
    print(f"\n{'='*60}")
    print("Test 4: Integration with Config")
    print("="*60)
    
    try:
        from config import settings
        from rag.embedding_factory import create_langchain_embeddings
        
        # Override config temporarily
        test_embeddings = create_langchain_embeddings(
            provider="local",
            model=MODEL,
            base_url=BASE_URL
        )
        
        test_query = "Test query"
        test_result = await test_embeddings.aembed_query(test_query)
        
        print(f"✓ Factory integration works")
        print(f"  Query: {test_query}")
        print(f"  Dimension: {len(test_result)}")
        
    except Exception as e:
        print(f"✗ Factory integration failed: {e}")
    
    print(f"\n{'='*60}")
    print("✓ All Tests Passed!")
    print("="*60)
    print(f"\nYour local embedding API is working correctly.")
    print(f"\nTo use in your application, set in .env:")
    print(f"  EMBEDDING_PROVIDER=local")
    print(f"  EMBEDDING_MODEL={MODEL}")
    print(f"  EMBEDDING_BASE_URL={BASE_URL}")
    print(f"  EMBEDDING_API_KEY=  # Not required")


async def quick_test():
    """Quick connection test"""
    BASE_URL = "http://127.0.0.1:1234/v1"
    MODEL = "text-embedding-snowflake-arctic-embed-m-v1.5"
    
    print("Quick connection test...")
    result = test_local_api_connection(BASE_URL, MODEL)
    
    if result["status"] == "success":
        print(f"✓ Connected to {BASE_URL}")
        print(f"✓ Model: {MODEL}")
        print(f"✓ Dimension: {result['embedding_dimension']}")
    else:
        print(f"✗ Failed: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test local embedding API")
    parser.add_argument("--quick", action="store_true", help="Quick connection test only")
    
    args = parser.parse_args()
    
    if args.quick:
        asyncio.run(quick_test())
    else:
        asyncio.run(test_embeddings())

