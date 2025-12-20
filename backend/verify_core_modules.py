import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.schema_service import schema_service
from app.services.enhanced_ingest_service import enhanced_ingest_service
from app.services.graph_service import graph_service
from app.services.kag_solver_service import kag_solver_service
from app.services.search_service import search_service
from app.services.governance_service import governance_service

# Mock UploadFile
class MockUploadFile:
    def __init__(self, filename, content):
        self.filename = filename
        self.content = content
    
    async def read(self):
        return self.content

async def main():
    print("=== Starting Core Module Verification ===\n")

    # 1. Schema Service
    print("[1] Testing Schema Service (OpenSPG Core)...")
    disease_model = {"name": "TestDisease", "properties": {"code": "Text", "symptoms": "Text"}}
    res = await schema_service.create_subject_model(disease_model)
    print(f"    -> Created Subject: {res}")
    
    # 2. Ingest Service (DeepKE)
    print("\n[2] Testing Intelligent Ingestion (DeepKE)...")
    dummy_pdf_content = b"The patient was diagnosed with TestDisease (Code: A123). Recommended Aspirin."
    mock_file = MockUploadFile("test_record.txt", dummy_pdf_content)
    
    ingest_res = await enhanced_ingest_service.process_document(mock_file, user="tester")
    print(f"    -> Ingestion Result: {ingest_res['status']}")
    print(f"    -> Extracted: {ingest_res.get('entities_count', 0)} entities")
    
    # 3. Governance Service (Human-in-the-Loop)
    print("\n[3] Testing Governance Triage (Core 5)...")
    # Simulate an extraction result to triage
    extraction = {
        "text_first_500": "The patient was diagnosed with TestDisease...",
        "entities": [
            {"entity": "TestDisease", "type": "Disease", "confidence": 0.85}, # Low confidence
            {"entity": "Aspirin", "type": "Drug", "confidence": 0.99}
        ]
    }
    task_id = await governance_service.create_review_task("doc-001", extraction)
    print(f"    -> Created Review Task ID: {task_id}")
    
    pending = await governance_service.get_pending_reviews()
    print(f"    -> Pending Tasks: {len(pending)}")
    
    # Simulate Approval
    print("    -> Simulating Human Approval...")
    await governance_service.submit_review(task_id, "approve", None, "tester")
    print("    -> Task Approved.")

    # 4. Graph Service (Storage & Mutual Indexing)
    print("\n[4] Testing Graph Service (KAG/OpenSPG Storage)...")
    node_id = await graph_service.add_node({"type": "TestDisease", "id": "A123", "properties": {"code": "A123"}})
    print(f"    -> Stored Node ID: {node_id}")
    
    # Mutual Indexing
    print("    -> Indexing Chunk <-> Node Link...")
    await graph_service.index_text_chunk_link("chunk-001", [node_id])
    print("    -> Link Created.")

    # 5. Search & Logic (KAG Solver & KG-Rank)
    print("\n[5] Testing Logic & Search (KAG & KG-Rank)...")
    
    # KAG Logic
    logic_ans = await kag_solver_service.solve_query("What is the treatment for TestDisease?")
    print(f"    -> KAG Solver Response: {logic_ans.get('answer', 'No answer')}")
    
    # KG-Rank Retrieval
    search_res = await search_service.search("TestDisease treatment")
    print(f"    -> KG-Rank Top Result: {search_res[0]['text'] if search_res else 'None'}")
    pass

if __name__ == "__main__":
    asyncio.run(main())
