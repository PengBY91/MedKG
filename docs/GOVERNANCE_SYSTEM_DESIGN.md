# Medical Data Governance & Analysis System - Design & Development Plan

## 1. Requirement Analysis & Gap Assessment

Based on the provided "Pain Points -> Capabilities -> Functions" matrix, and comparing it with the current `MedKG` codebase, we have identified the following integration strategy.

### 1.1 Core Module Mapping
| Module Name | User Requirement | Current State in MedKG | Planned Enhancement |
| :--- | :--- | :--- | :--- |
| **Terminology Service** | Multi-standard management, Semantic mapping, Audit | `terminology_service.py` (Basic Interface) | **Upgrade**: Add Vector Search (FAISS/Chroma) for fuzzy matching; Add `StandardRegistry` for managing ICD/SNOMED versions. |
| **Clinical NLP** | NER, Negation, Post-structuring | `MedLink` references (Placeholder) | **New**: Create `ClinicalNLPService` using local LLM or spaCy/BERT models for Entity Extraction. Integrate with `enhanced_ingest_service.py`. |
| **Data Governance** | Rules Engine, Closed-loop repair, Quality Dashboard | `data_governance_service.py` (Basic Assets & Mock Scores) | **Upgrade**: Integrate `rule_service.py` for executable logic; Add `QualityTask` workflow for "Alert -> Fix" cycle. |
| **Data Catalog** | Auto-scan, Lineage, Privacy | `DataAsset` model (Manual) | **Upgrade**: specific `ScanService` to read DB schemas; Add privacy masking middleware. |

---

## 2. Proposed System Expansions (Beyond Request)

To further enhance the value of this system within the `MedKG` agent platform, I propose adding the following intelligent capabilities:

### A. KG-Augmented Anomaly Detection (Rule+)
*   **Concept**: Traditional rules are rigid (e.g., "Age > 0"). We can use the Knowledge Graph to detect semantic anomalies.
*   **Feature**: "Logical Consistency Check".
    *   *Example*: A patient is diagnosed with "Male Infertility" but the procedure recorded is "Cesarean Section". A simple rule might miss this, but the KG knows `Male -> Cannot undergo -> C-Section`.
*   **Implementation**: A `KGRuleValidator` that queries `graph_service` for semantic conflicts.

### B. LLM-Driven "Autopilot" Cleaning (Agentic Repair)
*   **Concept**: Instead of just flagging errors, use the Agent to propose fixes.
*   **Feature**: "One-Click Fix".
    *   *Example*: "Diagnosis: AMI" -> System suggests: "Did you mean 'Acute Myocardial Infarction' (ICD-10 I21.9)?"
*   **Implementation**: Integrate `conversation_service.py` to allow the Governance Assistant to chat with the data steward.

### C. Governance "Impact Analysis"
*   **Concept**: Show the downstream impact of poor quality.
*   **Feature**: "Quality Impact Graph".
    *   *Example*: "This 'Unknown Drug' code is affecting 3 Research Cohorts and 1 Financial Report."
*   **Implementation**: Visualize `DataAsset.lineage` combined with usage logs.

---

## 3. Development Plan (MVP Strategy)

We will adopt the **"Hybrid Driver"** strategy: **Terminology-Enabled Quality Control**.
*Rationale*: You cannot effectively assess quality without standardized terminology.

### Phase 1: Foundation (Weeks 1-2)
*   **Objective**: Get the "Brain" working.
*   **Tasks**:
    1.  **Terminology Engine**: Implement `VectorTerminologyService` to index a subset of ICD-10.
    2.  **Asset Registry**: Update `DataGovernanceService` to support real schema definitions (not just mocks).
    3.  **Basic Rules**: Implement `RuleService` with 5 hard logic rules (e.g., Format check, Range check).

### Phase 2: The Core Loop (Weeks 3-4)
*   **Objective**: "Scan -> Detect -> Report".
*   **Tasks**:
    1.  **Ingestion Pipeline**: Create a pipeline that accepts a CSV/JSON, runs Terminology Normalization, then checks Rules.
    2.  **Quality Dashboard**: Expose `get_quality_report` API with real calculated metrics.
    3.  **Frontend**: Basic Vue page to view Assets and their Quality Scores.

### Phase 3: Intelligence & NLP (Weeks 5-6)
*   **Objective**: Handle unstructured text.
*   **Tasks**:
    1.  **NLP Pipeline**: Integrate extraction logic extracting entities from "Chief Complaint".
    2.  **Smart Mapping**: Use LLM to suggest mappings for unknown terms.

---

## 4. Technical Architecture Diagram

```mermaid
graph TD
    User[Data Steward/Doctor] --> WebUI[Governance Web UI]
    WebUI --> API[FastAPI Backend]
    
    subgraph "Core Services"
        API --> GS[Governance Service]
        API --> TS[Terminology Service]
        API --> NS[Clinical NLP Service]
    end
    
    subgraph "Engines"
        GS --> RE[Rule Engine]
        TS --> VS[Vector Store (Chroma)]
        NS --> LLM[Local LLM / BERT]
    end
    
    subgraph "Data Layer"
        RE --> DB[(Governance DB)]
        VS --> KB[(Ontology KB)]
    end
    
    GS -.->|Validates| Data[Ingested Data]
    TS -.->|Normalizes| Data
```

## 5. Deployment & Complexity Assessment

*   **Complexity**: Medium-High.
    *   *Challenge*: Reliable term mapping is hard. Requires tuning vector embeddings.
    *   *Challenge*: "Closed-loop" requires complex state management (Ticket status, user assignment).
*   **Resource Requirements**:
    *   Python 3.10+
    *   Vector Database (Chroma/Milvus)
    *   ~2 weeks for Backend MVP, ~1 week for Frontend MVP.
