"""Python script to test API endpoints"""

import asyncio
import httpx
import json


API_URL = "http://localhost:8000"


async def test_api():
    """Test all API endpoints"""
    
    print("=== Testing AI Jewelry Consultation System API ===\n")
    
    async with httpx.AsyncClient() as client:
        
        # Test 1: Root endpoint
        print("1. Testing root endpoint...")
        response = await client.get(f"{API_URL}/")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        print()
        
        # Test 2: Health check
        print("2. Testing health check...")
        response = await client.get(f"{API_URL}/api/health")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        print()
        
        # Test 3: Consultation
        print("3. Testing consultation endpoint...")
        response = await client.post(
            f"{API_URL}/api/consultation/user_001",
            json={
                "message": "Ищу золотое кольцо для помолвки, бюджет до 50 тысяч",
                "conversation_history": []
            }
        )
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        print()
        
        # Test 4: Get customer profile
        print("4. Testing get customer profile...")
        response = await client.get(f"{API_URL}/api/customer/user_001/profile")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        print()
        
        # Test 5: Update customer preferences
        print("5. Testing update customer preferences...")
        response = await client.put(
            f"{API_URL}/api/customer/user_001/preferences",
            json={
                "style_preference": "classic",
                "budget_min": 30000,
                "budget_max": 80000,
                "preferred_materials": ["gold", "white_gold"],
                "skin_tone": "warm",
                "occasion_types": ["wedding", "formal"]
            }
        )
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        print()
        
        # Test 6: Product search
        print("6. Testing product search...")
        response = await client.post(
            f"{API_URL}/api/products/search",
            json={
                "query": "элегантное золотое кольцо с бриллиантом",
                "limit": 5
            }
        )
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        print()
        
        # Test 7: Customer analysis
        print("7. Testing customer analysis...")
        response = await client.post(f"{API_URL}/api/analysis/customer")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        print()
        
        # Test 8: Trend analysis
        print("8. Testing trend analysis...")
        response = await client.post(
            f"{API_URL}/api/analysis/trends",
            json={
                "content": "В этом сезоне на пике популярности минималистичные украшения из белого золота. Особенно востребованы тонкие браслеты и небольшие серьги. Классические массивные украшения уступают место утонченным изделиям.",
                "source": "Fashion Journal 2024",
                "date": "2024-12-01"
            }
        )
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        print()
    
    print("=== API Testing Complete ===")


if __name__ == "__main__":
    asyncio.run(test_api())

