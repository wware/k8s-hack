#!/bin/bash
set -e

# Determine base URL
if command -v minikube &>/dev/null && minikube status &>/dev/null; then
    MINIKUBE_IP=$(minikube ip 2>/dev/null || echo "")
    if [ -n "$MINIKUBE_IP" ]; then
        # Try NodePort first
        NODE_PORT=$(kubectl get svc toy-api -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "")
        if [ -n "$NODE_PORT" ]; then
            BASE_URL="http://${MINIKUBE_IP}:${NODE_PORT}/api/v1"
        else
            BASE_URL="http://localhost:8000/api/v1"
        fi
    else
        BASE_URL="http://localhost:8000/api/v1"
    fi
else
    BASE_URL="http://localhost:8000/api/v1"
fi

echo "🔍 Testing API at ${BASE_URL}"
echo ""

# Function to check response
check_response() {
    if [ $1 -eq $2 ]; then
        echo "✅ Test passed: $3"
    else
        echo "❌ Test failed: $3 (Expected: $2, Got: $1)"
        exit 1
    fi
}

# Test 1: Health check
echo "🏥 Testing health endpoint..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/healthz)
check_response $HEALTH_STATUS 200 "Health check"

# Test 2: List items (should have initial data)
echo ""
echo "📋 Listing all items..."
LIST_RESPONSE=$(curl -s ${BASE_URL}/items)
echo "$LIST_RESPONSE" | jq '.' 2>/dev/null || echo "$LIST_RESPONSE"
LIST_STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/items)
check_response $LIST_STATUS 200 "List items"

# Test 3: Get specific item (item1 from initial data)
echo ""
echo "🔍 Getting specific item (item1)..."
GET_RESPONSE=$(curl -s ${BASE_URL}/items/item1)
echo "$GET_RESPONSE" | jq '.' 2>/dev/null || echo "$GET_RESPONSE"
GET_STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/items/item1)
check_response $GET_STATUS 200 "Get item1"

# Test 4: Create new item
echo ""
echo "➕ Creating new item (test-item)..."
CREATE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST ${BASE_URL}/items \
    -H "Content-Type: application/json" \
    -d '{
        "id": "test-item",
        "name": "Test Item",
        "value": 999
    }')
check_response $CREATE_STATUS 200 "Create item"

# Test 5: Get the created item
echo ""
echo "🔍 Getting created item (test-item)..."
GET_NEW_RESPONSE=$(curl -s ${BASE_URL}/items/test-item)
echo "$GET_NEW_RESPONSE" | jq '.' 2>/dev/null || echo "$GET_NEW_RESPONSE"
GET_NEW_STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/items/test-item)
check_response $GET_NEW_STATUS 200 "Get created item"

# Test 6: Update item
echo ""
echo "✏️ Updating item (test-item)..."
UPDATE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PUT ${BASE_URL}/items/test-item \
    -H "Content-Type: application/json" \
    -d '{
        "id": "test-item",
        "name": "Updated Test Item",
        "value": 1234
    }')
check_response $UPDATE_STATUS 200 "Update item"

# Test 7: Verify update
echo ""
echo "🔍 Verifying update..."
VERIFY_RESPONSE=$(curl -s ${BASE_URL}/items/test-item)
echo "$VERIFY_RESPONSE" | jq '.' 2>/dev/null || echo "$VERIFY_RESPONSE"
VERIFY_VALUE=$(echo "$VERIFY_RESPONSE" | jq -r '.value' 2>/dev/null || echo "")
if [ "$VERIFY_VALUE" = "1234" ]; then
    echo "✅ Test passed: Update verified"
else
    echo "❌ Test failed: Update verification (Expected value: 1234, Got: $VERIFY_VALUE)"
    exit 1
fi

# Test 8: Delete item
echo ""
echo "🗑️ Deleting item (test-item)..."
DELETE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE ${BASE_URL}/items/test-item)
check_response $DELETE_STATUS 200 "Delete item"

# Test 9: Verify deletion (should 404)
echo ""
echo "🔍 Verifying deletion (should 404)..."
VERIFY_DELETE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/items/test-item)
check_response $VERIFY_DELETE_STATUS 404 "Verify deletion"

# Test 10: Error handling - get non-existent item
echo ""
echo "🚫 Testing error handling (non-existent item)..."
ERROR_STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/items/does-not-exist)
check_response $ERROR_STATUS 404 "Error handling - not found"

# Test 11: Error handling - duplicate creation
echo ""
echo "🚫 Testing error handling (duplicate creation)..."
curl -s -X POST ${BASE_URL}/items \
    -H "Content-Type: application/json" \
    -d '{"id": "item1", "name": "Duplicate", "value": 1}' > /dev/null
DUPLICATE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST ${BASE_URL}/items \
    -H "Content-Type: application/json" \
    -d '{"id": "item1", "name": "Duplicate", "value": 1}')
check_response $DUPLICATE_STATUS 409 "Error handling - duplicate"

echo ""
echo "✨ All tests passed successfully!"
echo ""
echo "📊 Summary:"
echo "  - Health check: ✅"
echo "  - List items: ✅"
echo "  - Get item: ✅"
echo "  - Create item: ✅"
echo "  - Update item: ✅"
echo "  - Delete item: ✅"
echo "  - Error handling: ✅"
