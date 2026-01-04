# OpenSPG-KAG Usage Analysis

## 1. Overview
The `openspg-kag` library is a core dependency in the `MedKG` project, playing a critical role in the **Logic Solver**, **Graph Storage**, and **Schema Management** layers. However, the project appears to favor **programmatic configuration** via environment variables over the static `kag_config.yaml` file.

## 2. Configuration (`kag_config.yaml`)
*   **Status**: Present in root, but likely **unused** directly by the backend application logic.
*   **Content**:
    ```yaml
    project:
      namespace: MedicalGovernance
      host_addr: http://127.0.0.1:8887
      id: "1"
    vectorization:
      model:
        label: text-embedding-ada-002
    ```
*   **Observation**: The backend code (`kag_solver_service.py`) explicitly initializes the `KAGConfig` object using environment variables or hardcoded defaults that *match* the values in this file, but it does not load this file.

## 3. Code Integration Checklist

### A. Logic Solver (`kag_solver_service.py`)
*   **Role**: Wrapping `kag.solver.KAGSolver`.
*   **Usage**:
    *   Imports `KAGSolver` and `KAGConfig`.
    *   **Configuration**:
        *   `KAG_PROJECT_ID` (Default: "1")
        *   `KAG_HOST` (Default: "127.0.0.1:8887")
        *   `KAG_NAMESPACE` (Default: "MedicalGovernance")
    *   **Function**: `solve_query(query)` delegating to `self.solver.solve(query)`.
*   **Key Insight**: Explicitly handles the case where `openspg-kag` is missing by using a Mock implementation.

### B. Explanation Service (`explanation_service.py`)
*   **Role**: Consumer of KAG Solver.
*   **Usage**:
    *   Calls `kag_solver_service.solve_query(question)`.
    *   Integrates KAG logic results ("OpenSPG-KAG Phase") with GraphRAG results ("Retrieval Phase") to form a "Knowledge Fusion" answer.
    *   Reasoning Trace: Logs "OpenSPG-KAG Logic Solving" as a distinct step.

### C. Graph Storage (`graph_service.py`)
*   **Role**: Data Persistence Wrapper.
*   **Usage**:
    *   Imports `kag.storage.GraphStorage`.
    *   **Function**: Used for `upsert_vertex` and `upsert_edge`.
    *   **Feature**: Implements "Mutual Indexing" (linking text chunks to graph nodes) via `MENTIONS` edges.

### D. Schema Management (`schema_service.py`)
*   **Role**: Ontology Definition.
*   **Usage**:
    *   Imports `openspg.api.OpenSPGClient`.
    *   **Function**: syncing `Subject` and `Predicate` definitions to the OpenSPG server.

## 4. Conclusion & Recommendations
*   **Role**: `openspg-kag` is deeply integrated for "Logic Graph" capabilities, distinct from the raw Neo4j usage in other parts of the system.
*   **Configuration**: The `kag_config.yaml` is likely for CLI tools or reference. The active configuration is in the **Python code/Environment Variables**.
*   **Risk**: If you intend to change the configuration (e.g., point to a remote server), modifying `kag_config.yaml` **will likely have no effect** on the backend unless `KAG_HOST` env var is also updated.

> [!TIP]
> To change the KAG server address, set the `KAG_HOST` environment variable rather than editing `kag_config.yaml`.
