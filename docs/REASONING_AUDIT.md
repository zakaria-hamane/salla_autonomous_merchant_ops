# Reasoning Trace Audit & Reliability Metrics

## 1. Reliability Metrics Definitions

To ensure the system is operating safely, we track the following metrics in every `final_report`:

| Metric | Definition | Target |
| :--- | :--- | :--- |
| **Pricing Pass Rate** | `(Approved Proposals / Total Proposals) * 100` | > 80% |
| **Automated Block Rate** | `(Blocked Proposals / Total Proposals) * 100` | < 10% |
| **Hallucination Rate** | `(Hallucination Flags / Total Proposals) * 100` | **0%** (Strict) |
| **Sentiment Score** | Normalized score from -1.0 (Toxic) to 1.0 (Positive) | > 0.0 |
| **Schema Retry Count** | Number of times agents were asked to fix invalid JSON | < 2 |

## 2. Production Safeguards & Schema Detection

### Schema Violation Detection
*   **Mechanism:** We use LangChain's `JsonOutputParser` wrapped in a `try/except` block within the Agent nodes.
*   **Correction:** If parsing fails, the `schema_validation_passed` flag in State is set to `False`. The `check_schema_gate` in the graph routes the flow back to the agent for a retry (up to 2 times).

### Contradiction Detection
*   **Mechanism:** The `validator_node` compares the `Pricing Agent` output against the `Support Agent` output.
*   **Rule:** If `Proposed Price > Current Price` AND `Sentiment Score < -0.3`, a `CONTRADICTION` flag is raised.
*   **Correction:** The `conflict_resolver_node` sees this flag and changes the status to `BLOCKED`.

## 3. Debugging Evidence: The Hallucination Fix

**Issue:** Early versions of the `Pricing Agent` would lower prices claiming "Competitor data" existed when it did not.

**Trace Evidence:**
We created a reproduction script `backend/tests/generate_trace_evidence.py`.

*   **Input:** A proposal claiming `competitor_price: $85.00`.
*   **Context:** Empty pricing context list `[]`.
*   **System Action:**
    1.  `Validator` extracts $85.00.
    2.  `Validator` looks up product ID in context. Result: `None`.
    3.  `Validator` generates `type: HALLUCINATION` flag.
    4.  `Resolver` reads flag, sets status to `BLOCKED`, and adds note: "Blocked: Agent hallucinated data source."

**Screenshot Verification:**
*(Refer to LangSmith trace ID: [Run trace `generate_trace_evidence.py` to generate a fresh ID])*