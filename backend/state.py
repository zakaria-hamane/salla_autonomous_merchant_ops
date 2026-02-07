"""
Shared state definition for the LangGraph multi-agent system.
"""
import operator
from typing import TypedDict, Annotated, List, Dict, Any


class AgentState(TypedDict):
    """
    The shared blackboard state passed between all agents.
    This is the single source of truth for the entire workflow.
    """
    # Merchant Context
    merchant_id: str
    
    # Raw Data Inputs
    product_data: List[Dict[str, Any]]
    customer_messages: List[Dict[str, Any]]
    pricing_context: List[Dict[str, Any]]
    competitor_data: List[Dict[str, Any]]
    
    # Catalog Agent Outputs
    normalized_catalog: Annotated[List[Dict], operator.add]
    catalog_issues: Annotated[List[Dict], operator.add]
    
    # Support Agent Outputs
    support_summary: Dict[str, Any]
    sentiment_score: float  # -1.0 to 1.0
    complaint_spike_detected: bool
    
    # Pricing Agent Outputs
    pricing_proposals: Annotated[List[Dict], operator.add]
    
    # Validation Flags (Hallucination & Contradiction Detection)
    validation_flags: Annotated[List[Dict], operator.add]
    
    # System Flags & Safety
    schema_validation_passed: bool
    throttle_mode_active: bool
    retry_count: int
    
    # Merchant Overrides (Immutable)
    merchant_locks: Dict[str, Any]
    
    # Final Output
    final_report: Dict[str, Any]
    audit_log: Annotated[List[Dict], operator.add]
