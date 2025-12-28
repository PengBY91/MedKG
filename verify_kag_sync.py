import sys
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Add backend to path
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

async def test_sync():
    print("=== Testing KAG Sync ===")
    
    # Mock services
    # 1. Mock Schema Service
    from app.services.schema_service import schema_service
    schema_service.ensure_standardization_schema = AsyncMock(return_value={"status": "success"})
    
    # 2. Mock Graph Service
    from app.services.graph_service import graph_service
    graph_service.add_node = AsyncMock(return_value="mock_node_id")
    
    # 3. Test ExaminationStandardizationService.sync_task_to_kag
    from app.services.examination_standardization_service import examination_service
    
    mock_results = [
        {
            "original_name": "Test Exam",
            "modality": "CT",
            "status": "success",
            "standardized": [["Head", "Brain", "CT"]]
        },
        {
            "original_name": "Failed Exam",
            "status": "failed"
        }
    ]
    
    await examination_service.sync_task_to_kag("task_123", mock_results)
    
    # Verify calls
    assert schema_service.ensure_standardization_schema.called
    print("✓ Schema ensured")
    
    assert graph_service.add_node.called
    assert graph_service.add_node.call_count == 1 # Only 1 success item
    
    call_args = graph_service.add_node.call_args[0][0]
    assert call_args["type"] == "StdTerm"
    assert call_args["properties"]["original_name"] == "Test Exam"
    print("✓ Valid node synced")
    
    print("\nSUCCESS: Sync logic verified.")

if __name__ == "__main__":
    asyncio.run(test_sync())
