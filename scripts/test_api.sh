#!/bin/bash

# Simple script to test API endpoints
# Usage: ./scripts/test_api.sh

API_URL="http://localhost:8000"

echo "=== Testing AI Jewelry Consultation System API ==="
echo ""

# Test 1: Root endpoint
echo "1. Testing root endpoint..."
curl -X GET "${API_URL}/" | jq .
echo ""

# Test 2: Health check
echo "2. Testing health check..."
curl -X GET "${API_URL}/api/health" | jq .
echo ""

# Test 3: Consultation
echo "3. Testing consultation endpoint..."
curl -X POST "${API_URL}/api/consultation/user_001" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Ищу золотое кольцо для помолвки, бюджет до 50 тысяч",
    "conversation_history": []
  }' | jq .
echo ""

# Test 4: Get customer profile
echo "4. Testing get customer profile..."
curl -X GET "${API_URL}/api/customer/user_001/profile" | jq .
echo ""

# Test 5: Update customer preferences
echo "5. Testing update customer preferences..."
curl -X PUT "${API_URL}/api/customer/user_001/preferences" \
  -H "Content-Type: application/json" \
  -d '{
    "style_preference": "classic",
    "budget_min": 30000,
    "budget_max": 80000,
    "preferred_materials": ["gold", "white_gold"],
    "skin_tone": "warm",
    "occasion_types": ["wedding", "formal"]
  }' | jq .
echo ""

# Test 6: Product search
echo "6. Testing product search..."
curl -X POST "${API_URL}/api/products/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "элегантное золотое кольцо с бриллиантом",
    "limit": 5
  }' | jq .
echo ""

# Test 7: Customer analysis
echo "7. Testing customer analysis..."
curl -X POST "${API_URL}/api/analysis/customer" | jq .
echo ""

# Test 8: Trend analysis
echo "8. Testing trend analysis..."
curl -X POST "${API_URL}/api/analysis/trends" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "В этом сезоне на пике популярности минималистичные украшения из белого золота. Особенно востребованы тонкие браслеты и небольшие серьги. Классические массивные украшения уступают место утонченным изделиям.",
    "source": "Fashion Journal 2024",
    "date": "2024-12-01"
  }' | jq .
echo ""

echo "=== API Testing Complete ==="


