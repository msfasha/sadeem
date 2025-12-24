#!/bin/bash
# Smoke demo: End-to-end test of the platform
# Prerequisites: 
#   - Kubernetes cluster running
#   - Dataplane Helm chart deployed
#   - Control plane API running (or accessible)
#   - kubectl configured

set -e

echo "=== Smoke Demo: End-to-End Platform Test ==="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
CONTROL_PLANE_URL="${CONTROL_PLANE_URL:-http://localhost:8000}"
TRINO_ENDPOINT="${TRINO_ENDPOINT:-http://trino-coordinator:8080}"

echo "Control Plane URL: $CONTROL_PLANE_URL"
echo "Trino Endpoint: $TRINO_ENDPOINT"

# Step 1: Check Kubernetes cluster
echo ""
echo "=== Step 1: Checking Kubernetes cluster ==="
if kubectl cluster-info &>/dev/null; then
    echo -e "${GREEN}✓${NC} Kubernetes cluster accessible"
else
    echo -e "${RED}✗${NC} Kubernetes cluster not accessible"
    exit 1
fi

# Step 2: Check data plane components
echo ""
echo "=== Step 2: Checking data plane components ==="
components=("minio" "postgres" "iceberg-catalog" "trino-coordinator")
for component in "${components[@]}"; do
    if kubectl get deployment "$component" &>/dev/null; then
        echo -e "${GREEN}✓${NC} $component deployment exists"
    else
        echo -e "${RED}✗${NC} $component deployment not found"
    fi
done

# Step 3: Check control plane API
echo ""
echo "=== Step 3: Checking control plane API ==="
if curl -s "$CONTROL_PLANE_URL/health" | grep -q "healthy"; then
    echo -e "${GREEN}✓${NC} Control plane API is healthy"
else
    echo -e "${RED}✗${NC} Control plane API not responding"
    echo "  Make sure the API is running: cd control_plane && uvicorn api.main:app --reload"
    exit 1
fi

# Step 4: Register a test user (if not exists)
echo ""
echo "=== Step 4: Registering test user ==="
USERNAME="testuser"
PASSWORD="testpass123"
curl -s -X POST "$CONTROL_PLANE_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\", \"role\": \"admin\"}" \
    > /dev/null || echo "User may already exist (continuing...)"

# Step 5: Login and get token
echo ""
echo "=== Step 5: Logging in ==="
TOKEN=$(curl -s -X POST "$CONTROL_PLANE_URL/api/auth/login?username=$USERNAME&password=$PASSWORD" \
    | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}✗${NC} Failed to get access token"
    exit 1
fi
echo -e "${GREEN}✓${NC} Successfully authenticated"

# Step 6: Create a workspace
echo ""
echo "=== Step 6: Creating workspace ==="
WORKSPACE_RESPONSE=$(curl -s -X POST "$CONTROL_PLANE_URL/api/workspaces" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name": "demo-workspace", "description": "Demo workspace"}')

WORKSPACE_ID=$(echo "$WORKSPACE_RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
echo -e "${GREEN}✓${NC} Created workspace (ID: $WORKSPACE_ID)"

# Step 7: Create a Trino connection
echo ""
echo "=== Step 7: Creating Trino connection ==="
CONNECTION_RESPONSE=$(curl -s -X POST "$CONTROL_PLANE_URL/api/connections" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"workspace_id\": $WORKSPACE_ID,
        \"name\": \"trino-connection\",
        \"connection_type\": \"trino\",
        \"config\": {
            \"endpoint\": \"$TRINO_ENDPOINT\",
            \"catalog\": \"iceberg\",
            \"schema\": \"default\"
        }
    }")

CONNECTION_ID=$(echo "$CONNECTION_RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
echo -e "${GREEN}✓${NC} Created Trino connection (ID: $CONNECTION_ID)"

# Step 8: Create a Trino SQL job
echo ""
echo "=== Step 8: Creating Trino SQL job ==="
JOB_RESPONSE=$(curl -s -X POST "$CONTROL_PLANE_URL/api/jobs" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"workspace_id\": $WORKSPACE_ID,
        \"connection_id\": $CONNECTION_ID,
        \"name\": \"demo-query\",
        \"description\": \"Demo Trino SQL query\",
        \"job_type\": \"trino_sql\",
        \"definition\": {
            \"sql\": \"SHOW CATALOGS\"
        }
    }")

JOB_ID=$(echo "$JOB_RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
echo -e "${GREEN}✓${NC} Created job (ID: $JOB_ID)"

# Step 9: Execute the job (create run)
echo ""
echo "=== Step 9: Executing job ==="
RUN_RESPONSE=$(curl -s -X POST "$CONTROL_PLANE_URL/api/runs" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"job_id\": $JOB_ID}")

RUN_ID=$(echo "$RUN_RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
RUN_STATUS=$(echo "$RUN_RESPONSE" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
echo -e "${GREEN}✓${NC} Created run (ID: $RUN_ID, Status: $RUN_STATUS)"

# Step 10: Check run status
echo ""
echo "=== Step 10: Checking run status ==="
sleep 2  # Give it a moment to process
RUN_STATUS_RESPONSE=$(curl -s -X GET "$CONTROL_PLANE_URL/api/runs/$RUN_ID" \
    -H "Authorization: Bearer $TOKEN")

FINAL_STATUS=$(echo "$RUN_STATUS_RESPONSE" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
echo "Final run status: $FINAL_STATUS"

if [ "$FINAL_STATUS" = "succeeded" ]; then
    echo -e "${GREEN}✓${NC} Run completed successfully!"
else
    echo -e "${RED}✗${NC} Run status: $FINAL_STATUS"
    echo "Run details:"
    echo "$RUN_STATUS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RUN_STATUS_RESPONSE"
fi

echo ""
echo "=== Smoke Demo Complete ==="
echo ""
echo "Summary:"
echo "  - Workspace ID: $WORKSPACE_ID"
echo "  - Connection ID: $CONNECTION_ID"
echo "  - Job ID: $JOB_ID"
echo "  - Run ID: $RUN_ID"
echo "  - Final Status: $FINAL_STATUS"

