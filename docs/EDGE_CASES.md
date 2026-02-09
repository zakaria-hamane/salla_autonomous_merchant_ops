# Edge Case Handling & Safety Protocols

This document outlines the specific strategies implemented in the Salla Autonomous Merchant Operations system to handle edge cases, ensuring safety, determinism, and reliability.

## 1. Catalog Agent Misclassification
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

## 2. Viral-Post-Driven Complaint Spike
**Scenario:** A viral social media post causes a sudden influx of 500+ complaints in one hour.

*   **Anomaly Detection:**
    *   Implemented in `support_agent.py`.
    *   We calculate `complaint_velocity` (complaints per minute relative to baseline) and `sentiment_score`.
    *   Logic: `if velocity > 7.0 or complaint_ratio > 0.5: spike_detected = True`.

*   **Throttling & Safeguards:**
    *   **The Safety Gate:** In `graph.py`, the `check_safety_gate` conditional edge inspects `complaint_spike_detected`.
    *   **The Throttler Node:** If a spike is True, the workflow routes to `throttler_node`.
    *   **Outcome:** The Throttler returns a `FROZEN` status. **ALL** pricing updates are suspended globally for the merchant until the spike is reviewed. This prevents the Pricing Agent from reacting blindly to a PR crisis (e.g., lowering prices due to bad sentiment when the issue is actually shipping delays).

## 3. Preventing Agent Error Feedback Loops
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

## 4. Preventing Overwriting Merchant Decisions
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