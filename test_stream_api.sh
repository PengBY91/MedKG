#!/bin/bash

# 测试流式 API 是否工作

echo "Testing streaming API..."
echo ""

curl -N -X POST http://localhost:8000/api/v1/explanation/query-stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(cat ~/.medkg_token 2>/dev/null || echo 'test-token')" \
  -d '{
    "question": "测试问题",
    "session_id": null,
    "use_history": false
  }' 2>&1 | head -20

echo ""
echo "Test completed."

