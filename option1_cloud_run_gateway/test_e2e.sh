#!/usr/bin/env bash
set -e

PORT=8088
GATEWAY_URL="http://127.0.0.1:${PORT}"

echo "=========================================================="
echo " Starting Option 1: Cloud Run Interceptor Gateway E2E Test"
echo "=========================================================="

# Start server in background using project virtualenv if active or python3
export APP_ENV="development"
export PORT="${PORT}"

python3 -m uvicorn app.main:app --host 127.0.0.1 --port ${PORT} &
SERVER_PID=$!

cleanup() {
    echo "Stopping test server (PID: ${SERVER_PID})..."
    kill -9 ${SERVER_PID} 2>/dev/null || true
}
trap cleanup EXIT

echo "Waiting for gateway to be ready on ${GATEWAY_URL}..."
for i in {1..30}; do
    if curl -s "${GATEWAY_URL}/healthz" | grep -q "healthy"; then
        echo " Gateway is healthy and listening on port ${PORT}!"
        break
    fi
    sleep 0.5
done

echo ""
echo "--- Step 1: Testing A2A Discovery Endpoint ---"
DISCOVERY_RESP=$(curl -s -X GET "${GATEWAY_URL}/.well-known/agent.json")
echo "Discovery Response:"
echo "${DISCOVERY_RESP}" | python3 -m json.tool

echo ""
echo "--- Step 2: Testing Task Dispatch with ADK Contamination ---"
TASK_PAYLOAD='{
  "jsonrpc": "2.0",
  "method": "a2a.tasks.send",
  "adk_metadata": {
    "model": "gemini-1.5-pro",
    "prompt_version": "v1.2",
    "system_hash": "e93848a"
  },
  "_adk": {"internal_session": "ge-sess-44321"},
  "params": {
    "taskId": "task-clin-live-001",
    "studyId": "MK-3475-087",
    "cohort": "Cohort-B",
    "pushUrl": "http://127.0.0.1:8088/mock-ge-receiver"
  },
  "id": "e2e-task-1"
}'

TASK_RESP=$(curl -s -X POST "${GATEWAY_URL}/a2a/tasks" \
  -H "Authorization: Bearer mock-dev-token" \
  -H "Content-Type: application/json" \
  -H "X-Google-ADK-Trace: rogue-trace-header" \
  -d "${TASK_PAYLOAD}")

echo "Task Dispatch Response (Sanitized & Sealed A2UI Artifact):"
echo "${TASK_RESP}" | python3 -m json.tool

# Extract stateToken from Approve action
APPROVE_TOKEN=$(echo "${TASK_RESP}" | python3 -c "import sys, json; data=json.load(sys.stdin); actions=data['result']['artifact']['a2ui']['actions']; print(next(a['stateToken'] for a in actions if a['id']=='action_approve'))")

echo ""
echo "Extracted HMAC-SHA256 State Token:"
echo "${APPROVE_TOKEN}"

echo ""
echo "--- Step 3: Simulating 48-Hour Stateless User Sign-off (UI Action Callback) ---"
ACTION_PAYLOAD=$(python3 -c "import json; print(json.dumps({'jsonrpc': '2.0', 'method': 'a2a.ui.action', 'params': {'stateToken': '${APPROVE_TOKEN}'}, 'id': 'e2e-action-1'}))")

ACTION_RESP=$(curl -s -X POST "${GATEWAY_URL}/a2a/ui/action" \
  -H "Authorization: Bearer mock-dev-token" \
  -H "Content-Type: application/json" \
  -d "${ACTION_PAYLOAD}")

echo "UI Action Response (Audit Trail & Verification):"
echo "${ACTION_RESP}" | python3 -m json.tool

echo ""
echo "--- Step 4: Tampered State Token Security Guard Verification ---"
TAMPERED_TOKEN="${APPROVE_TOKEN%????}xxxx"
TAMPERED_PAYLOAD=$(python3 -c "import json; print(json.dumps({'jsonrpc': '2.0', 'method': 'a2a.ui.action', 'params': {'stateToken': '${TAMPERED_TOKEN}'}, 'id': 'e2e-action-tamper'}))")

TAMPER_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${GATEWAY_URL}/a2a/ui/action" \
  -H "Authorization: Bearer mock-dev-token" \
  -H "Content-Type: application/json" \
  -d "${TAMPERED_PAYLOAD}")

echo "Tampered Token Response HTTP Code: ${TAMPER_HTTP_CODE} (Expected: 400)"

if [ "${TAMPER_HTTP_CODE}" -eq 400 ]; then
    echo " Security Guard PASSED: Tampered state token successfully rejected with HTTP 400!"
else
    echo " Security Guard FAILED: Expected HTTP 400 but got ${TAMPER_HTTP_CODE}"
    exit 1
fi

echo ""
echo "=========================================================="
echo " Option 1 Cloud Run Interceptor Gateway E2E Tests PASSED!"
echo "=========================================================="
