"""
LangGraph workflow definition implementing the Gated Pipeline topology.
"""
from langgraph.graph import StateGraph, END
from state import AgentState
from nodes import (
    coordinator_node,
    throttler_node,
    validator_node,
    conflict_resolver_node
)
from agents import catalog_agent, support_agent, pricing_agent


def check_safety_gate(state: AgentState) -> str:
    """
    Safety Gate: Determines if pricing logic should run.
    Returns 'unsafe' if spike detected, otherwise 'safe'.
    """
    spike_detected = state.get("complaint_spike_detected", False)
    
    if spike_detected:
        print("\n🚨 SAFETY GATE: SPIKE DETECTED - ROUTING TO THROTTLER")
        return "unsafe"
    
    print("\n✅ SAFETY GATE: PASSED - PROCEEDING TO PRICING")
    return "safe"


def check_schema_gate(state: AgentState) -> str:
    """
    Schema Gate: Validates catalog data quality.
    Returns 'invalid' if schema validation failed, otherwise 'valid'.
    """
    schema_passed = state.get("schema_validation_passed", True)
    retry_count = state.get("retry_count", 0)
    
    if not schema_passed and retry_count < 2:
        print(f"\n⚠️ SCHEMA GATE: VALIDATION FAILED (Retry {retry_count + 1}/2)")
        return "retry"
    elif not schema_passed:
        print("\n❌ SCHEMA GATE: MAX RETRIES EXCEEDED")
        return "invalid"
    
    print("\n✅ SCHEMA GATE: VALIDATION PASSED")
    return "valid"


# Build the workflow graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("coordinator", coordinator_node)
workflow.add_node("catalog_agent", catalog_agent)
workflow.add_node("support_agent", support_agent)
workflow.add_node("pricing_agent", pricing_agent)
workflow.add_node("validator", validator_node)
workflow.add_node("throttler", throttler_node)
workflow.add_node("resolver", conflict_resolver_node)

# Set entry point
workflow.set_entry_point("coordinator")

# Coordinator dispatches to parallel analysis
workflow.add_edge("coordinator", "support_agent")
workflow.add_edge("support_agent", "catalog_agent")

# Safety Gate: Check for complaint spike
workflow.add_conditional_edges(
    "catalog_agent",
    check_safety_gate,
    {
        "unsafe": "throttler",  # Spike detected -> freeze operations
        "safe": "pricing_agent"  # Safe -> continue to pricing
    }
)

# Pricing flows to validator, then validator flows to resolver
workflow.add_edge("pricing_agent", "validator")
workflow.add_edge("validator", "resolver")

# Both throttler and resolver end the workflow
workflow.add_edge("throttler", END)
workflow.add_edge("resolver", END)

# Compile the graph
app = workflow.compile()

# Export for visualization
if __name__ == "__main__":
    print("LangGraph workflow compiled successfully!")
    print("\nWorkflow structure:")
    print("1. Coordinator → Support Agent → Catalog Agent")
    print("2. Safety Gate checks for complaint spike")
    print("3a. If spike: → Throttler → END")
    print("3b. If safe: → Pricing Agent → Validator → Resolver → END")
