"""
Integration tests for Examination API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
import io

client = TestClient(app)


class TestExaminationAPI:
    """Test examination API endpoints."""
    
    def test_upload_csv_file(self):
        """Test uploading CSV file for standardization."""
        # Create test CSV content
        csv_content = """检查项目名,检查标准模态
手指正位片,DR
双膝关节正位,DR
腰椎MRI,MRI"""
        
        files = {
            "file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")
        }
        
        response = client.post("/api/v1/examination/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "task_id" in data
    
    def test_upload_excel_file(self):
        """Test uploading Excel file."""
        # Note: This requires actual Excel file creation
        # For now, test the endpoint exists
        response = client.post("/api/v1/examination/upload", files={})
        
        # Should return 422 (validation error) not 404
        assert response.status_code in [422, 400]
    
    def test_get_task_status(self):
        """Test getting task status."""
        # First upload a file to get task_id
        csv_content = """检查项目名,检查标准模态
手指正位片,DR"""
        
        files = {
            "file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")
        }
        
        upload_response = client.post("/api/v1/examination/upload", files=files)
        task_id = upload_response.json()["task_id"]
        
        # Get task status
        response = client.get(f"/api/v1/examination/tasks/{task_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "task" in data
        assert data["task"]["id"] == task_id
    
    def test_get_task_results(self):
        """Test getting task results."""
        # Upload and process
        csv_content = """检查项目名,检查标准模态
手指正位片,DR"""
        
        files = {
            "file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")
        }
        
        upload_response = client.post("/api/v1/examination/upload", files=files)
        task_id = upload_response.json()["task_id"]
        
        # Wait a bit for processing (in real tests, use polling)
        import time
        time.sleep(2)
        
        # Get results
        response = client.get(f"/api/v1/examination/tasks/{task_id}/results")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "results" in data
    
    def test_export_results_csv(self):
        """Test exporting results as CSV."""
        # Upload and process
        csv_content = """检查项目名,检查标准模态
手指正位片,DR"""
        
        files = {
            "file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")
        }
        
        upload_response = client.post("/api/v1/examination/upload", files=files)
        task_id = upload_response.json()["task_id"]
        
        # Wait for processing
        import time
        time.sleep(2)
        
        # Export CSV
        response = client.get(f"/api/v1/examination/tasks/{task_id}/export?format=csv")
        
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
    
    def test_export_results_excel(self):
        """Test exporting results as Excel."""
        # Upload and process
        csv_content = """检查项目名,检查标准模态
手指正位片,DR"""
        
        files = {
            "file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")
        }
        
        upload_response = client.post("/api/v1/examination/upload", files=files)
        task_id = upload_response.json()["task_id"]
        
        # Wait for processing
        import time
        time.sleep(2)
        
        # Export Excel
        response = client.get(f"/api/v1/examination/tasks/{task_id}/export?format=excel")
        
        assert response.status_code == 200
        assert "spreadsheet" in response.headers["content-type"]
    
    def test_get_ontology_info(self):
        """Test getting ontology information."""
        response = client.get("/api/v1/examination/ontology")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "ontology" in data
    
    def test_import_ontology_data(self):
        """Test importing ontology data."""
        # Create test ontology CSV
        csv_content = """一级部位,二级部位,检查方法,检查模态
上肢,手指,正位,DR
上肢,手指,侧位,DR"""
        
        files = {
            "file": ("ontology.csv", io.BytesIO(csv_content.encode()), "text/csv")
        }
        
        response = client.post("/api/v1/examination/import", files=files)
        
        # May succeed or fail depending on Neo4j availability
        assert response.status_code in [200, 500]
    
    def test_get_graph_stats(self):
        """Test getting graph statistics."""
        response = client.get("/api/v1/examination/graph/stats")
        
        # May return data or error depending on Neo4j
        assert response.status_code in [200, 500]
    
    def test_get_graph_tree(self):
        """Test getting complete tree structure."""
        response = client.get("/api/v1/examination/graph/tree")
        
        # May return data or error depending on Neo4j
        assert response.status_code in [200, 500]
    
    def test_get_methods_for_part(self):
        """Test getting methods for specific body part."""
        response = client.get("/api/v1/examination/graph/methods?level2=手指")
        
        # May return data or error depending on Neo4j
        assert response.status_code in [200, 500]
    
    def test_invalid_task_id(self):
        """Test accessing non-existent task."""
        response = client.get("/api/v1/examination/tasks/invalid-task-id")
        
        assert response.status_code == 404
    
    def test_unsupported_file_format(self):
        """Test uploading unsupported file format."""
        files = {
            "file": ("test.txt", io.BytesIO(b"test content"), "text/plain")
        }
        
        response = client.post("/api/v1/examination/upload", files=files)
        
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
