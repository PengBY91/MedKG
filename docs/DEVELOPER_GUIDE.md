# MedKG Developer Guide

## System Architecture

MedKG is a medical governance and knowledge graph platform composed of the following services:

### 1. Persistence Layer

The system uses a polyglot persistence architecture:

*   **Neo4j**: Primary Knowledge Graph storage. Stores `BodyPart`, `ExaminationMethod`, `Modality`, and their hierarchical relationships (`HAS_SUBPART`, `SUPPORTS_METHOD`).
    *   **Port**: 7474 (HTTP), 7687 (Bolt)
    *   **Credentials**: `neo4j` / `medkg2024` (defined in `docker-compose-neo4j.yml` & `config.py`)
*   **PostgreSQL**: Relational data store for structured application data (users, tasks, logs).
    *   **Port**: 5432
*   **Milvus**: Vector database for RAG (Retrieval-Augmented Generation) capabilities.
*   **MinIO**: Object storage for document management (PDFs, reports).

### 2. Backend (FastAPI)

*   **Entry Point**: `backend/app/main.py`
*   **Configuration**: `backend/app/core/config.py`
*   **KG Service**: `backend/app/core/kg.py` (Handles Neo4j connection lifecycle)
*   **API Routes**: `backend/app/api/api_v1/endpoints/`
    *   `graph.py`: KG Explorer endpoints (Search, Expand, Stats)

### 3. Frontend (Vue 3 + Element Plus)

*   **Entry**: `frontend/src/main.js`
*   **Key Views**:
    *   `ExaminationOntology.vue`: Interactive KG Explorer (Force Layout Graph)
    *   `ExaminationStandardization.vue`: Task management and results
*   **Visualization**: Uses `ECharts` for graph rendering.

## Development Workflow

### Prerequisites
*   Docker & Docker Compose
*   Node.js (for frontend)
*   Python 3.10+ (for backend)

### Setup

1.  **Start Services**:
    ```bash
    docker-compose up -d
    ```
    *Ensure `neo4j`, `postgres`, `milvus`, and `minio` are running.*

2.  **Initialize Knowledge Graph**:
    ```bash
    cd backend
    python run_import.py
    ```
    *This script imports `data/examination_ontology.csv` into Neo4j.*

3.  **Run Backend (Dev)**:
    ```bash
    cd backend
    uvicorn app.main:app --reload --port 8001
    ```

4.  **Run Frontend (Dev)**:
    ```bash
    cd frontend
    npm run dev
    ```

## Key Workflows

### 1. Knowledge Graph Explorer
The Explorer (`/examination/ontology`) allows users to visualize the graph.
*   **Search**: Calls `/api/v1/graph/search`.
*   **Expand**: Clicking a node triggers `expandNode` -> `/api/v1/graph/expand`. This endpoint returns 1-hop neighbors.
*   **Visualization**: ECharts Force Layout. Friction is set to `0.2` for stability.

### 2. Data Standardization
Users upload raw strings, and the system maps them to standard entities using LLM + KG.
*   **Service**: `ExaminationStandardizationService`

## Troubleshooting

*   **Neo4j Auth Error**: Check `docker-compose.yml` vs `docker-compose-neo4j.yml`. We use `medkg2024` as the password.
*   **"Expansion Failed"**: Ensure the backend endpoint correctly handles relationship objects (fixed in recent patch).

## Directory Structure

```
MedKG/
├── backend/
│   ├── app/
│   │   ├── api/          # API Route Controllers
│   │   ├── core/         # Config & Global Services (KG, LLM)
│   │   ├── db/           # SQL Models
│   │   └── services/     # Business Logic
│   ├── run_import.py     # KG Import Script
│   └── verify_data.py    # KG Verification Utility
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── ExaminationOntology.vue       # Graph Explorer
│   │   │   └── ExaminationStandardization.vue # Task UI
├── data/                 # Raw CSV/Text data
└── docker-compose.yml    # Infrastructure definition
```
