#!/bin/bash
# Quick API test script for AI Jewelry Consultation System

API_URL="http://localhost:8000"
USER_ID="user_001"

echo "=========================================="
echo "AI Jewelry Consultation System - API Test"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    echo -e "${YELLOW}Testing: $name${NC}"
    echo "Endpoint: $method $endpoint"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$API_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$API_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✓ Success (HTTP $http_code)${NC}"
        echo "Response: $(echo $body | jq -C '.' 2>/dev/null || echo $body)"
    else
        echo -e "${RED}✗ Failed (HTTP $http_code)${NC}"
        echo "Response: $body"
    fi
    echo ""
}

# 1. Health Check
test_endpoint "Health Check" "GET" "/api/health"

# 2. Root Endpoint
test_endpoint "Root Endpoint" "GET" "/"

# 3. Get Customer Profile
test_endpoint "Get Customer Profile" "GET" "/api/customer/$USER_ID/profile"

# 4. Product Search
test_endpoint "Product Search" "POST" "/api/products/search" \
    '{"query": "золотое кольцо", "limit": 3}'

# 5. Consultation
test_endpoint "Consultation" "POST" "/api/consultation/$USER_ID" \
    '{"message": "Ищу обручальное кольцо для невесты"}'

# 6. Update Customer Preferences
test_endpoint "Update Preferences" "PUT" "/api/customer/$USER_ID/preferences" \
    '{"style_preference": "modern", "budget_min": 20000, "budget_max": 80000, "preferred_materials": ["gold", "white_gold"]}'

# 7. Customer Analysis
test_endpoint "Customer Analysis" "POST" "/api/analysis/customer"

# 8. Trend Analysis
test_endpoint "Trend Analysis" "POST" "/api/analysis/trends" \
    '{"content": "В этом сезоне особенно популярны минималистичные украшения из белого золота. Тренд на простые формы и чистые линии продолжается.", "source": "Fashion Magazine"}'

echo "=========================================="
echo "API Test Complete"
echo "=========================================="
echo ""
echo "For detailed API documentation, visit:"
echo "  http://localhost:8000/docs"
echo ""

