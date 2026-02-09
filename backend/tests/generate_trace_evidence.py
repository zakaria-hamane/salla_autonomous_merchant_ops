"""
backend/tests/generate_trace_evidence.py

Script to generate evidence of hallucination detection for the Reasoning Audit report.
This creates a reproducible trace showing how the system blocks AI hallucinations.
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from nodes import validator_node, conflict_resolver_node


def generate_hallucination_trace():
    print("="*80)
    print("🎥 GENERATING EVIDENCE: Hallucination Detection Trace")
    print("="*80)
    print("Scenario: Agent claims to see a competitor price of $85.00.")
    print("Fact: No competitor data exists for this product.")
    
    # 1. Setup State with a Hallucination
    state = {
        "merchant_id": "trace_evidence_run",
        "pricing_context": [],  # EMPTY context - no competitor data
        "pricing_proposals": [
            {
                "product_id": "P001",
                "product_name": "Espresso Maker",
                "current_price": 120.00,
                "proposed_price": 90.00,
                "cost": 60.00,
                "status": "DECREASE",
                "signals_used": [
                    "competitor_price: $85.00",  # <--- HALLUCINATION
                    "sentiment: 0.1"
                ],
                "reasoning": "Matching competitor price found in analysis."
            }
        ],
        "validation_flags": [],
        "catalog_issues": [],
        "support_summary": {},
        "merchant_locks": {},
        "sentiment_score": 0.1
    }
    
    # 2. Run Validator Node
    print("\n[1] Running Validator Node...")
    print("    - Extracting 'signals_used'...")
    print("    - Querying 'pricing_context'...")
    validator_result = validator_node(state)
    
    # Merge validator results back into state
    state.update(validator_result)
    
    flags = state.get("validation_flags", [])
    print(f"    -> Result: Found {len(flags)} flags.")
    if flags:
        print(f"    -> Flag Type: {flags[0]['type']}")
        print(f"    -> Message: {flags[0]['message']}")
    
    # 3. Run Conflict Resolver
    print("\n[2] Running Conflict Resolver...")
    print("    - Checking flags...")
    print("    - Applying blocking logic...")
    final_state = conflict_resolver_node(state)
    
    report = final_state['final_report']
    actions = report.get('pricing_actions', [])
    
    print("\n" + "="*80)
    print("📝 EVIDENCE SUMMARY")
    print("="*80)
    
    if actions:
        print(f"Action Taken: {actions[0]['status']}")
        print(f"Reasoning:    {actions[0]['note']}")
    else:
        print("⚠️  No actions were generated (unexpected behavior)")
        print(f"Proposals received: {len(state.get('pricing_proposals', []))}")
        print(f"Validation flags: {len(state.get('validation_flags', []))}")
    
    metrics = report.get('metrics', {})
    print(f"Metrics:      Hallucination Rate {metrics.get('hallucination_rate', 0)}%")
    print(f"              Pass Rate {metrics.get('pricing_pass_rate', 0)}%")
    print(f"              Block Rate {metrics.get('automated_block_rate', 0)}%")
    print("="*80)
    
    if actions and actions[0]['status'] == 'BLOCKED':
        print("\n✅ Trace evidence generated successfully.")
        print("This demonstrates the system's ability to detect and block hallucinations.")
    else:
        print("\n⚠️  Expected a BLOCKED action but got different result.")
        print("Debug: Check conflict_resolver_node logic.")


if __name__ == "__main__":
    generate_hallucination_trace()
