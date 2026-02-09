# Salla Autonomous Merchant Operations - Build Report

## 1. System Design Rationale

### Architecture: LangGraph Server + Next.js
We chose a **LangGraph Server** architecture served via a standard streaming API, consumed by a **Next.js** frontend.

*   **Why LangGraph?**
    *   **State Management:** Merchant operations require passing complex context (catalog, competitors, sentiment) between steps. LangGraph's state schema is superior to stateless LLM chains.
    *   **Cyclic Capability:** We needed the ability to "loop back" if schema validation fails (self-correction) before finalizing the report.
    *   **Observability:** Built-in integration with LangSmith allows us to trace exactly *why* a price was changed.

*   **Why LangGraph Server (API)?**
    *   Instead of wrapping Python scripts in FastAPI, we use the native `langgraph dev` server.
    *   **Benefit:** This provides out-of-the-box streaming (Server-Sent Events), allowing the frontend to show real-time progress (e.g., "Analyzing Support Messages..." -> "Calculating Prices...") without custom socket management.

### Trade-offs
*   **Complexity vs. Robustness:** We chose a multi-agent modular design over a single large prompt. This increases code complexity but significantly reduces hallucination rates and allows for unit testing specific logic (e.g., testing the Pricing Agent in isolation).
*   **Latency:** The sequential validation steps add latency. We accepted this tradeoff because **accuracy** in pricing is more critical than speed.

## 2. Agent Behavior Rationale

### The Coordinator (Orchestrator)
*   **Rationale:** Acts as the data ingress point. It decouples data loading from processing, allowing us to swap CSV inputs for database inputs without changing downstream agents.

### The Support Agent (Analyst)
*   **Rationale:** Runs *before* pricing. This is critical. We must know the "Sentiment Score" and check for "Viral Spikes" before we attempt to calculate prices. If sentiment is toxic, pricing logic changes.

### The Pricing Agent (Calculator)
*   **Rationale:** Uses a "Chain of Thought" approach. It doesn't just output a number; it outputs `signals_used` and `reasoning`. This is required for the `validator_node` to audit the decision later.

### The Validator & Resolver (The Safety Net)
*   **Rationale:** LLMs are probabilistic. Business logic must be deterministic.
*   **Implementation:** The `conflict_resolver_node` is pure Python logic (no LLM). It enforces hard constraints (Cost Floors, Merchant Locks) that the LLM might ignore.

## 3. Implementation Decisions

*   **Library: CopilotKit:** Used for the frontend to provide a "Conversational UI" experience. It allows the merchant to ask "Why did you block product X?" and contextually retrieve data from the generated report.
*   **Pydantic:** Used everywhere for structured output. We do not parse raw strings; we parse JSON objects validated against schemas to prevent downstream crashes.
*   **Docker:** The entire backend is containerized to ensure the Python environment (often fragile) is consistent across dev and production.

## 4. Debugging Process Documentation

### Challenge: The "Hallucinating Competitor"
During development, the Pricing Agent would occasionally invent a competitor price to justify a price cut.

*   **Detection:** We noticed in LangSmith traces that `signals_used` contained "competitor_price: $85" when the `pricing_context` input was empty.
*   **Fix:** We implemented the `validator_node`. It iterates through `signals_used`, extracts the claimed price via Regex, and compares it to the actual `pricing_context` in the state.
*   **Result:** See `tests/test_validation_pipeline.py`. The system now flags this as a `HALLUCINATION` and blocks the change.

### Challenge: JSON Trailing Commas
GPT-4o-mini occasionally outputted trailing commas in JSON.
*   **Fix:** We switched to using LangChain's `JsonOutputParser` with Pydantic, which is more robust at parsing slightly malformed JSON than standard `json.loads`.

## 5. Testing & Validation Approach

We implemented a dedicated test suite (`backend/tests/`) rather than relying solely on manual testing.

1.  **Unit Tests:** `test_llm.py` and `test_azure_connection.py` verify infrastructure before logic.
2.  **Pipeline Tests:** `test_validation_pipeline.py` mocks state to feed specific edge cases (Hallucinations, Contradictions) into the Resolver to ensure they are blocked.
3.  **End-to-End:** `run_test.py` simulates a full daily run with sample CSV data.

## 6. Final System Walkthrough

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