# Salla Autonomous Merchant Operations - Comprehensive Project Report

## Table of Contents

1.  [Implementation Plan & Architecture](#1-implementation-plan--architecture)
    *   [Deliverables Checklist](#11-deliverables-checklist)
    *   [System Architecture Diagram](#12-system-architecture-diagram)
2.  [Build Report](#2-build-report)
    *   [System Design Rationale](#21-system-design-rationale)
    *   [Agent Behavior Rationale](#22-agent-behavior-rationale)
    *   [Implementation Decisions](#23-implementation-decisions)
    *   [Debugging Process Documentation](#24-debugging-process-documentation)
    *   [Testing & Validation Approach](#25-testing--validation-approach)
    *   [Final System Walkthrough](#26-final-system-walkthrough)
3.  [Edge Case Handling & Safety Protocols](#3-edge-case-handling--safety-protocols)
    *   [Catalog Agent Misclassification](#31-catalog-agent-misclassification)
    *   [Viral-Post-Driven Complaint Spike](#32-viral-post-driven-complaint-spike)
    *   [Preventing Agent Error Feedback Loops](#33-preventing-agent-error-feedback-loops)
    *   [Preventing Overwriting Merchant Decisions](#34-preventing-overwriting-merchant-decisions)

---

## 1. Implementation Plan & Architecture

### 1.1 Deliverables Checklist

The following checklist tracks the completion status of the project requirements and specific implementation details.

| Status | Category | Deliverable | Specific Implementation Details |
| :---: | :--- | :--- | :--- |
| ✅ | **Architecture** | **Agent Roles** | • **Coordinator:** Orchestrates workflow (`nodes.py`).<br>• **Catalog:** Normalizes data (`catalog_agent.py`).<br>• **Support:** Classifies sentiment (`support_agent.py`).<br>• **Pricing:** Applies rules (`pricing_agent.py`). |
| ✅ | | **Communication** | • **State Graph:** Uses `AgentState` TypedDict.<br>• **Structured Output:** Pydantic models enforce JSON. |
| ✅ | | **Fail-safes** | • **Throttler:** Returns "FROZEN" on viral spikes.<br>• **Safety Gate:** Conditional edge routing in Graph.<br>• **Retry Counter:** Prevents infinite loops. |
| ✅ | | **Grounding** | • **Cross-Agent Verification:** `conflict_resolver_node` checks Pricing vs Catalog.<br>• **Priority Hierarchy:** 1. Locks → 2. Catalog Integrity → 3. Sentiment → 4. Cost Floor. |
| ✅ | **Schema** | **Pipelines** | • **Validation:** `validator_node` detects hallucinations (regex extraction).<br>• **Ontology:** Defined classes (Inquiry, Complaint, etc.).<br>• **Pricing Rules:** Hard constraints (Cost + 5%, Sentiment blocks). |
| ✅ | **Code** | **Orchestration** | • **LangGraph Server:** `langgraph.json` configuration.<br>• **Docker:** Containerized backend.<br>• **Tracing:** LangSmith integration enabled. |
| ✅ | **UI** | **CopilotKit** | • **Frontend:** Next.js + CopilotKit Popup.<br>• **Visuals:** Real-time Dashboard with SSE streaming. |
| ✅ | **Documentation** | **Reports** | • **Build Report:** Included in Section 2.<br>• **Edge Cases:** Included in Section 3.<br>• **Audit:** Debugging and tracing evidence documented. |

### 1.2 System Architecture Diagram

The system is deployed as a **LangGraph Application** exposed via a streaming API (`/runs/stream`) and consumed by a Next.js frontend via Server-Sent Events (SSE).

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
    ContradictionCheck -- "Conflict (Flagged)" --> Resolver

    %% Resolution & Priorities
    Prio4 -.- Resolver
    Overrides -.->|Enforce| Resolver
    Resolver --> Report
    Report ==>|JSON Stream| API

    %% Observability
    Coord & Resolver & Validator -.->|Trace| Smith
```

---

## 2. Build Report

### 2.1 System Design Rationale

#### Architecture: LangGraph Server + Next.js
We chose a **LangGraph Server** architecture served via a standard streaming API, consumed by a **Next.js** frontend.

*   **Why LangGraph?**
    *   **State Management:** Merchant operations require passing complex context (catalog, competitors, sentiment) between steps. LangGraph's state schema is superior to stateless LLM chains.
    *   **Cyclic Capability:** We needed the ability to "loop back" if schema validation fails (self-correction) before finalizing the report.
    *   **Observability:** Built-in integration with LangSmith allows us to trace exactly *why* a price was changed.

*   **Why LangGraph Server (API)?**
    *   Instead of wrapping Python scripts in FastAPI, we use the native `langgraph dev` server.
    *   **Benefit:** This provides out-of-the-box streaming (Server-Sent Events), allowing the frontend to show real-time progress (e.g., "Analyzing Support Messages..." -> "Calculating Prices...") without custom socket management.

#### Trade-offs
*   **Complexity vs. Robustness:** We chose a multi-agent modular design over a single large prompt. This increases code complexity but significantly reduces hallucination rates and allows for unit testing specific logic (e.g., testing the Pricing Agent in isolation).
*   **Latency:** The sequential validation steps add latency. We accepted this tradeoff because **accuracy** in pricing is more critical than speed.

### 2.2 Agent Behavior Rationale

#### The Coordinator (Orchestrator)
*   **Rationale:** Acts as the data ingress point. It decouples data loading from processing, allowing us to swap CSV inputs for database inputs without changing downstream agents.

#### The Support Agent (Analyst)
*   **Rationale:** Runs *before* pricing. This is critical. We must know the "Sentiment Score" and check for "Viral Spikes" before we attempt to calculate prices. If sentiment is toxic, pricing logic changes.

#### The Pricing Agent (Calculator)
*   **Rationale:** Uses a "Chain of Thought" approach. It doesn't just output a number; it outputs `signals_used` and `reasoning`. This is required for the `validator_node` to audit the decision later.

#### The Validator & Resolver (The Safety Net)
*   **Rationale:** LLMs are probabilistic. Business logic must be deterministic.
*   **Implementation:** The `conflict_resolver_node` is pure Python logic (no LLM). It enforces hard constraints (Cost Floors, Merchant Locks) that the LLM might ignore.

### 2.3 Implementation Decisions

*   **Library - CopilotKit:** Used for the frontend to provide a "Conversational UI" experience. It allows the merchant to ask "Why did you block product X?" and contextually retrieve data from the generated report.
*   **Pydantic:** Used everywhere for structured output. We do not parse raw strings; we parse JSON objects validated against schemas to prevent downstream crashes.
*   **Docker:** The entire backend is containerized to ensure the Python environment (often fragile) is consistent across dev and production.

### 2.4 Debugging Process Documentation

#### Challenge: The "Hallucinating Competitor"
During development, the Pricing Agent would occasionally invent a competitor price to justify a price cut.

*   **Detection:** We noticed in LangSmith traces that `signals_used` contained "competitor_price: $85" when the `pricing_context` input was empty.
*   **Fix:** We implemented the `validator_node`. It iterates through `signals_used`, extracts the claimed price via Regex, and compares it to the actual `pricing_context` in the state.
*   **Result:** See `tests/test_validation_pipeline.py`. The system now flags this as a `HALLUCINATION` and blocks the change.

#### Challenge: JSON Trailing Commas
GPT-4o-mini occasionally outputted trailing commas in JSON.
*   **Fix:** We switched to using LangChain's `JsonOutputParser` with Pydantic, which is more robust at parsing slightly malformed JSON than standard `json.loads`.

### 2.5 Testing & Validation Approach

We implemented a dedicated test suite (`backend/tests/`) rather than relying solely on manual testing.

1.  **Unit Tests:** `test_llm.py` and `test_azure_connection.py` verify infrastructure before logic.
2.  **Pipeline Tests:** `test_validation_pipeline.py` mocks state to feed specific edge cases (Hallucinations, Contradictions) into the Resolver to ensure they are blocked.
3.  **End-to-End:** `run_test.py` simulates a full daily run with sample CSV data.

### 2.6 Final System Walkthrough

1.  **Start:** The merchant logs into the Next.js Dashboard.
2.  **Trigger:** They click "Run Operations Check" or ask Copilot "Run analysis."
3.  **Ingest:** The `Coordinator` loads the CSV data (Products, Messages, Competitors).
4.  **Analyze:**
    *   `Support Agent` scans for viral spikes. (If found -> Freeze).
    *   `Catalog Agent` normalizes messy product data.
5.  **Price:** `Pricing Agent` proposes changes based on cost, sentiment, and competitors.
6.  **Validate:** `Validator Node` cross-checks proposals against raw data to catch hallucinations.
7.  **Resolve:** `Conflict Resolver` applies Merchant Locks and Hard Rules.
8.  **Output:** The dashboard updates in real-time via SSE, displaying a PDF-exportable report with "Approved", "Blocked", and "Locked" status badges.

---

## 3. Edge Case Handling & Safety Protocols

This section outlines the specific strategies implemented in the Salla Autonomous Merchant Operations system to handle edge cases, ensuring safety, determinism, and reliability.

### 3.1 Catalog Agent Misclassification
**Scenario:** The Catalog Agent misclassifies a high-value electronic item (e.g., "Espresso Machine") as a low-value "Accessory," leading the Pricing Agent to suggest a suspiciously low price.

*   **Prevention (Schema Constraints):**
    *   We utilize Pydantic models (`CatalogAnalysis` in `catalog_agent.py`) to enforce strict category enums.
    *   The `validator_node` performs cross-reference checks. If a product's price change is > 50% different from the category average, it is flagged.

*   **Detection (Signals):**
    *   **Cost Floor Violation:** The `pricing_agent.py` has a hard rule: `proposed_price >= cost * 1.05`. If a misclassification leads to a price below cost, the "Cost Floor" logic catches it immediately.
    *   **Market Divergence:** The `validator_node` compares the proposed price against `pricing_context` (competitor data). A massive deviation triggers a `DATA_MISMATCH` flag.

*   **Correction:**
    *   The `conflict_resolver_node` blocks any change tagged with `DATA_MISMATCH` or `HALLUCINATION`.
    *   The status is set to `BLOCKED`, requiring human intervention.

### 3.2 Viral-Post-Driven Complaint Spike
**Scenario:** A viral social media post causes a sudden influx of 500+ complaints in one hour.

*   **Anomaly Detection:**
    *   Implemented in `support_agent.py`.
    *   We calculate `complaint_velocity` (complaints per minute relative to baseline) and `sentiment_score`.
    *   Logic: `if velocity > 7.0 or complaint_ratio > 0.5: spike_detected = True`.

*   **Throttling & Safeguards:**
    *   **The Safety Gate:** In `graph.py`, the `check_safety_gate` conditional edge inspects `complaint_spike_detected`.
    *   **The Throttler Node:** If a spike is True, the workflow routes to `throttler_node`.
    *   **Outcome:** The Throttler returns a `FROZEN` status. **ALL** pricing updates are suspended globally for the merchant until the spike is reviewed. This prevents the Pricing Agent from reacting blindly to a PR crisis (e.g., lowering prices due to bad sentiment when the issue is actually shipping delays).

### 3.3 Preventing Agent Error Feedback Loops
**Scenario:** Two agents disagree indefinitely (e.g., Catalog says "Missing Data", Pricing says "Ready"), causing an infinite processing loop.

*   **DAG Structure:**
    *   Our LangGraph is designed as a **Directed Acyclic Graph (DAG)** for the main flow: `Coordinator -> Support -> Catalog -> Pricing -> Validator -> Resolver -> END`.
    *   Back-loops are only allowed for explicit schema retries.

*   **Retry Limits:**
    *   Managed in `graph.py` via `check_schema_gate`.
    *   State variable `retry_count` tracks iterations.
    *   **Limit:** Max 2 retries. If `retry_count >= 2`, the flow forces a route to the `resolver` with a failure flag, breaking the loop.

*   **Priority Hierarchy:**
    *   To prevent logical oscillation, the `conflict_resolver_node` uses a strict hierarchy:
        1.  **Merchant Locks** (Immutable)
        2.  **Safety Throttles** (Viral Spikes)
        3.  **Catalog Critical Errors** (Data integrity)
        4.  **Sentiment Signals**
        5.  **Pricing Rules**

### 3.4 Preventing Overwriting Merchant Decisions
**Scenario:** A merchant explicitly sets a product price to $100. The agent thinks it should be $110 and tries to overwrite it every day.

*   **Immutable Overrides (Merchant Locks):**
    *   The state object (`state.py`) contains a `merchant_locks` dictionary.
    *   **Implementation:** In `conflict_resolver_node`:
        ```python
        if product_id in merchant_locks:
            final_actions.append({
                "status": "LOCKED",
                "note": "Merchant override: price locked",
                "final_price": current_price
            })
            continue
        ```
    *   This logic executes *before* any AI pricing logic is considered.

*   **Audit Logs:**
    *   Every action taken by the system is appended to the `audit_log` list in the state.
    *   This log is returned to the frontend and displayed in the "Audit Trail" section of the report, ensuring transparency.