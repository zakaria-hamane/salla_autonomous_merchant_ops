# Salla Autonomous Merchant Operations - Implementation Plan

## Table of Contents
1. [Deliverables & Sub-deliverables Checklist](#1-deliverables--sub-deliverables-checklist)
2. [System Architecture](#2-system-architecture)

---

## 1. Deliverables & Sub-deliverables Checklist

| Status | Category | Deliverable | Specific Implementation Details (Sub-sub-deliverables) | Assignment Reference |
| :---: | :--- | :--- | :--- | :--- |
| ✅ | **1. Architecture** | **Agent Roles & Responsibilities** | • **Coordinator Agent (`nodes.py`):** Orchestrates workflow, loads data.<br>• **Catalog Agent (`catalog_agent.py`):** Normalizes CSV data.<br>• **Support Agent (`support_agent.py`):** Classifies messages & sentiment.<br>• **Pricing Agent (`pricing_agent.py`):** Applies pricing rules. | "Clearly define what each agent does... ownership boundaries." |
| ✅ | | **Communication Model** | • **State Graph (`state.py`):** Uses `AgentState` TypedDict.<br>• **Structured Output:** Pydantic models for JSON enforcement. | "Shared scratchpad / state graph" |
| ✅ | | **Loop Prevention** | • **Retry Counter:** `state.py` includes `retry_count`.<br>• **DAG Structure:** Directed Acyclic Graph prevents infinite recursion. | "Interaction tokens / hop limits... Max depth boundaries" |
| ✅ | | **Fail-safe Mechanisms** | • **Throttler Node (`nodes.py`):** Returns "FROZEN" on viral spikes.<br>• **Safety Gate (`graph.py`):** Conditional edge routing. | "Coordination throttling... Fallback behaviors" |
| ✅ | | **Grounding & Reliability** | • **Cross-Agent Verification:** `conflict_resolver_node` validates Pricing proposals against Catalog issues (see `CROSS_AGENT_VERIFICATION.md`).<br>• **Output Enforcement:** Strict Pydantic validators on LLM outputs.<br>• **Priority Hierarchy:** PRIORITY 1: Merchant Locks → PRIORITY 2: Catalog Integrity → PRIORITY 3: Sentiment → PRIORITY 4: Cost Floor → PRIORITY 5: Approval | "Grounding & reliability verification... Cross-agent verification" |
| ✅ | | **Architecture Diagram** | • **Mermaid/Visual:** Diagram logic is ready for rendering. | "You must submit an architecture diagram" |
| ✅ | **2. Schema Design** | **Product Normalization** | • **Logic:** Extraction of `id`, `name`, `price`, `cost` from text.<br>• **Validation:** Checks for missing critical fields. | "Product normalization schema... Unit mismatches" |
| ✅ | | **Message Ontology** | • **Classification:** `Inquiry`, `Complaint`, `Suggestion`, `Transactional`. | "Customer-message classification ontology... define rules" |
| ✅ | | **Pricing Constraints** | • **Hard Rule 1:** `price >= cost * 1.05`.<br>• **Hard Rule 2:** Block increase if `sentiment < 0`. | "Deterministic rules... Cannot reduce prices below cost" |
| ✅ | | **Validation Pipelines** | • **Hallucination Checks:** Logic to catch ungrounded claims (e.g., phantom competitor data).<br>• **Contradiction Detection:** Explicit check for cross-agent disagreements.<br>• **Implementation:** `validator_node` in `nodes.py` performs regex-based extraction and cross-validation.<br>• **Testing:** Dedicated test suite in `backend/tests/test_validation_pipeline.py`. | "Validation pipelines... Explain how system catches hallucinations... ungrounded claims" |
| ✅ | **3. Implementation** | **Coordinator Logic** | • **Orchestration:** `coordinator_node` loads data.<br>• **Resolution:** `conflict_resolver_node` aggregates outputs. | "Responsible for calling all other agents... Aggregates outputs" |
| ✅ | | **Working Agents** | • **Codebase:** Implemented `catalog`, `support`, `pricing` agents.<br>• **Data Loading:** `data_loader.py` parsing. | "Skeleton/prototype for at least one other agent" |
| ✅ | | **Conflict Resolution** | • **Logic:** Resolver overrides Pricing if Catalog has critical errors. | "Conflict resolution example... Coordinator overrides" |
| ✅ | | **LangGraph Server** | • **Config:** `langgraph.json` entry point.<br>• **Deployment:** `Dockerfile` for `langgraph dev`. | "Deploy as a LangGraph application... **not as a custom FastAPI-only wrapper**" |
| ✅ | | **Observability** | • **Tracing:** `LANGCHAIN_TRACING_V2=true` configured. | "Enable LangSmith Tracing... Traces should show sequence" |
| ✅ | **4. UI Integration** | **CopilotKit Setup** | • **Frontend:** `page.tsx` with `<CopilotKit>` provider.<br>• **Chat:** `<CopilotPopup>` enabled. | "Build a minimal web UI... using CopilotKit" |
| ✅ | | **Dashboard & Report** | • **Visuals:** Status Badges, Pricing Tables, Alert Boxes.<br>• **Interaction:** Trigger button for `runOperationsCheck`. | "Trigger a run... View the final daily report" |
| ❌ | **5. Reasoning Audit** | **Debugging Analysis** | • **Report Needed:** Written example of a specific hallucination fixed during dev.<br>• **Evidence:** Reference to a real LangSmith trace. | "Show how you identified hallucinations... Include real example" |
| ❌ | | **Production Safeguards** | • **Report Needed:** Explanation of schema violation detection.<br>• **Report Needed:** Explanation of contradictory output detection. | "Explain how system would detect... Schema violations" |
| ❌ | | **Reliability Metrics** | • **Report Needed:** Definitions for metrics (e.g., "Classification Accuracy", "Pricing Pass Rate"). | "Define metrics... Accuracy of message classification" |
| ⚠️ | **6. Edge Cases** | **Logic Implementation** | • **Code:** Logic for "Viral Spike" and "Catalog Error" exists.<br>• **Writing:** The written explanation in `EDGE_CASES.md` is missing. | "Provide written answers to the following..." |
| ❌ | | **Feedback Loops & Overrides** | • **Report Needed:** Strategy for preventing agent oscillation.<br>• **Report Needed:** Strategy for immutable merchant overrides/audit logs. | "Preventing agent error feedback loops... Preventing overwriting merchant decisions" |
| ❌ | **7. Build Report** | **System Design Rationale** | • **Report Needed:** Why LangGraph Server? Why this specific architecture? Trade-offs? | "Why you chose your architecture... Tradeoffs" |
| ❌ | | **Agent Behavior Rationale** | • **Report Needed:** Justification for agent structure and logic constraints. | "Why each agent is structured... Why certain logic..." |
| ❌ | | **Implementation Decisions** | • **Report Needed:** Library selection, code structure, custom orchestration explanation. | "Why you selected specific libraries... Explanation of custom orchestration" |
| ❌ | | **Debugging Documentation** | • **Report Needed:** Development logs, reasoning steps, screenshots of traces. | "Show your reasoning steps... Include screenshots" |
| ❌ | | **Testing & Validation** | • **Report Needed:** How outputs were validated and loops tested. | "How you validated agent outputs... How you tested for loop conditions" |
| ❌ | | **Final Walkthrough** | • **Report Needed:** Narrative flow: UI → CopilotKit → API → Agents → UI. | "How the system starts... How agents interact" |

> **Legend:**
> *   ✅ **Complete:** Code and logic are present in the provided files.
> *   ⚠️ **Partial:** The logic (code) exists, but the required *written documentation* is missing.
> *   ❌ **Missing:** The specific written report or document has not been created yet.

---

## 2. System Architecture

### High-Level Design: The "LangGraph Server" Topology

Unlike a simple linear chain or a custom Python script, this system is deployed as a strict **LangGraph Application**. The backend exposes a standard streaming API (`/runs/stream`) which the frontend consumes via Server-Sent Events (SSE). This ensures real-time feedback and adheres to the "No FastAPI Wrapper" constraint.

**Diagram:**

```mermaid
flowchart TD
    %% --- STYLE DEFINITIONS ---
    classDef userNode fill:#ffffff,stroke:#2c3e50,stroke-width:2px,color:#2c3e50,font-size:14px,font-weight:bold,rx:20,ry:20;
    classDef uiNode fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#01579b,font-weight:bold,rx:5,ry:5;
    classDef apiNode fill:#e3f2fd,stroke:#2196f3,stroke-width:2px,color:#0d47a1,font-weight:bold,rx:10,ry:10;
    classDef brainNode fill:#673ab7,stroke:#512da8,stroke-width:3px,color:#ffffff,font-size:16px,font-weight:bold,rx:10,ry:10,shadow:5px;
    classDef workerNode fill:#fff8e1,stroke:#ff9800,stroke-width:2px,color:#e65100,font-size:14px,rx:5,ry:5;
    classDef ruleNode fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#b71c1c,font-size:12px,rx:5,ry:5,stroke-dasharray: 5 5;
    classDef stateNode fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px,stroke-dasharray: 5 5,color:#4a148c,shape:cyl;
    classDef failSafeNode fill:#cfd8dc,stroke:#455a64,stroke-width:2px,color:#000,font-weight:bold,shape:hexagon;
    classDef observeNode fill:#263238,stroke:#000,stroke-width:2px,color:#fff,font-size:12px,rx:5,ry:5;
    classDef gateNode fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#000,shape:diamond,font-size:12px;
    classDef priorityNode fill:#004d40,stroke:#00695c,stroke-width:1px,color:#fff,font-size:11px,shape:rect,rx:2,ry:2;

    %% --- EXTERNAL LAYER ---
    User(("Merchant")):::userNode

    subgraph Frontend ["🖥️ UI Layer (Next.js + CopilotKit)"]
        style Frontend fill:#fcfcfc,stroke:#b0bec5,stroke-width:1px
        Copilot["⚡ Chat UI & Dashboard<br/><i>CopilotPopup Provider</i>"]:::uiNode
    end

    subgraph System ["☁️ Backend (LangGraph Server)"]
        style System fill:#fcfcfc,stroke:#b0bec5,stroke-width:2px,rx:20,ry:20

        API["⚡ LangGraph API Endpoint<br/><i>/runs/stream (SSE)</i>"]:::apiNode
        Smith["️🐞 LangSmith<br/><i>Tracing: LANGCHAIN_TRACING_V2</i>"]:::observeNode

        %% --- STATE MANAGEMENT ---
        subgraph StateStore ["🗄️ Shared Graph State (state.py)"]
            style StateStore fill:#f3e5f5,stroke:#8e24aa,stroke-dasharray: 5 5
            StateData[("AgentState<br/>(Context, Retry Count)")]:::stateNode
            Overrides[("🔐 Merchant Locks<br/>(Priority 1)")]:::stateNode
        end

        %% --- ORCHESTRATION ---
        subgraph LogicFlow ["🧠 Orchestration Pipeline"]
            style LogicFlow fill:#ede7f6,stroke:#673ab7,stroke-width:1px

            DataLoader[("📥 Data Loader<br/>(CSV Parsing)")]:::workerNode
            Coord["Coordinator Agent<br/><i>Orchestrator</i>"]:::brainNode
            
            %% Step 1: Parallel Workers
            subgraph Workers ["Step 1: Analysis & Extraction"]
                style Workers fill:#fff3e0,stroke:#ffe0b2,stroke-width:0px
                Cat["📦 Catalog Agent<br/><i>Normalization</i>"]:::workerNode
                Supp["🎧 Support Agent<br/><i>Classification</i>"]:::workerNode
            end

            %% Safety Gating Layer & Loop Prevention
            subgraph Gating ["🛡️ Gates & Loop Prevention"]
                style Gating fill:#e0f7fa,stroke:#00acc1,stroke-width:1px
                SpikeCheck{{"🔥 Viral Spike?"}}:::gateNode
                Throttler["❄️ THROTTLER<br/>(Return FROZEN)"]:::failSafeNode
                SchemaCheck{{"🛡️ Schema Valid?"}}:::gateNode
                RetryCheck{{"🔄 Max Retries<br/>Exceeded?"}}:::gateNode
            end

            %% Step 2: Pricing
            subgraph PricingLogic ["Step 2: Pricing Strategy"]
                style PricingLogic fill:#fff3e0,stroke:#ffe0b2,stroke-width:0px
                Price["💰 Pricing Agent<br/><i>Apply Rules</i>"]:::workerNode
                NegSent{{"Hard Rule:<br/>Sentiment < 0"}}:::ruleNode
                CostFloor{{"Hard Rule:<br/>Price > Cost"}}:::ruleNode
            end

            %% Step 3: Validation
            subgraph Validation ["Step 3: Validation Pipeline"]
                style Validation fill:#fff3e0,stroke:#ff6f00,stroke-width:1px
                Validator["️ Validator Node<br/><i>Hallucination Check</i>"]:::workerNode
                ContradictionCheck{{"⚠️ Conflict<br/>Detected?"}}:::gateNode
            end

            %% Step 4: Resolution
            subgraph Resolution ["Step 4: Conflict Resolution"]
                style Resolution fill:#e0f2f1,stroke:#00897b,stroke-width:0px
                Resolver["⚖️ Conflict Resolver<br/><i>Final Output Generation</i>"]:::brainNode
                
                %% Visualizing the Priority Hierarchy from Checklist
                Prio1["1. Locks"]:::priorityNode
                Prio2["2. Catalog"]:::priorityNode
                Prio3["3. Sent."]:::priorityNode
                Prio4["4. Cost"]:::priorityNode
                
                Prio1 --- Prio2 --- Prio3 --- Prio4
            end
        end

        %% --- OUTPUTS ---
        Report["📜 Final Daily Report"]:::uiNode

    end

    %% --- CONNECTIONS ---

    %% User Flow
    User <==> Copilot
    Copilot <==> API
    API ==>|Start| DataLoader
    DataLoader --> Coord

    %% Dispatch
    Coord -->|Parallel Exec| Cat & Supp
    Cat & Supp -->|Update| StateData

    %% Gating & Loop Logic
    Supp --> SpikeCheck
    Cat --> SchemaCheck

    %% Viral Spike Path
    SpikeCheck -- "YES" --> Throttler
    Throttler -->|Skip Pricing| Resolver

    %% Schema/Retry Logic
    SchemaCheck -- "VALID" --> PricingLogic
    SchemaCheck -- "INVALID" --> RetryCheck
    
    %% FIXED SYNTAX HERE:
    RetryCheck -- "RETRY < MAX (Increment)" --> Coord
    RetryCheck -- "MAX REACHED (Fail)" --> Resolver

    %% Pricing Logic
    SpikeCheck -- "NO" --> PricingLogic
    StateData --> Price
    Supp -.-> NegSent
    NegSent & CostFloor -.-> Price

    %% Validation Pipeline
    Price --> Validator
    Validator --> ContradictionCheck
    ContradictionCheck -- "No Issues" --> Resolver
    %% FIXED SYNTAX HERE:
    ContradictionCheck -- "Conflict (Flagged)" --> Resolver

    %% Resolution & Priorities
    Prio4 -.- Resolver
    Overrides -.->|Enforce| Resolver
    Resolver --> Report
    Report ==>|JSON Stream| API

    %% Observability
    Coord & Resolver & Validator -.->|Trace| Smith
```