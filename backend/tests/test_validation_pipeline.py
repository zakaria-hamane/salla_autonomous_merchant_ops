"""
Test script to verify the Validation Pipeline (Hallucination & Contradiction Detection).
This test directly invokes the validator and resolver nodes to test validation logic.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path to import backend modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
from nodes import validator_node, conflict_resolver_node

# Load environment variables
load_dotenv()


def test_hallucination_detection():
    """Test that the validator catches phantom competitor data."""
    print("="*70)
    print("TEST 1: HALLUCINATION DETECTION")
    print("="*70)
    
    # Create a pricing proposal with a FAKE competitor price
    # This simulates the Pricing Agent hallucinating data
    fake_proposal = {
        "product_id": "prod_001",
        "product_name": "Test Product",
        "current_price": 100.0,
        "proposed_price": 95.0,
        "cost": 50.0,
        "status": "DECREASE",
        "signals_used": [
            "competitor_price: $85.00",  # FAKE! This doesn't exist in pricing_context
            "sentiment: neutral"
        ],
        "reasoning": "Matching phantom competitor"
    }
    
    state = {
        "merchant_id": "test_hallucination",
        "pricing_context": [],  # Empty! No competitor data exists
        "pricing_proposals": [fake_proposal],
        "validation_flags": [],
        "sentiment_score": 0.0,
        "catalog_issues": [],
        "support_summary": {},
        "merchant_locks": {},
        "audit_log": []
    }
    
    print("\n🧪 Running validator with fake competitor data...")
    
    # Run validator
    validator_result = validator_node(state)
    state.update(validator_result)
    
    # Run resolver
    resolver_result = conflict_resolver_node(state)
    state.update(resolver_result)
    
    validation_flags = state.get("validation_flags", [])
    final_report = state.get("final_report", {})
    pricing_actions = final_report.get("pricing_actions", [])
    
    print(f"\n✓ Validation Flags Found: {len(validation_flags)}")
    for flag in validation_flags:
        print(f"  - {flag['type']}: {flag['message']}")
    
    print(f"\n✓ Pricing Actions:")
    for action in pricing_actions:
        print(f"  - {action['product_id']}: Status={action['status']}, Note={action.get('note', 'N/A')}")
    
    # Verify the hallucination was caught
    assert len(validation_flags) > 0, "❌ FAILED: No validation flags detected!"
    assert any(f["type"] == "HALLUCINATION" for f in validation_flags), "❌ FAILED: Hallucination not detected!"
    assert pricing_actions[0]["status"] == "BLOCKED", "❌ FAILED: Proposal was not blocked!"
    
    print("\n✅ TEST PASSED: Hallucination was detected and blocked!")
    return True


def test_data_mismatch_detection():
    """Test that the validator catches mismatched competitor prices."""
    print("\n" + "="*70)
    print("TEST 2: DATA MISMATCH DETECTION")
    print("="*70)
    
    # Create pricing context with actual competitor price
    real_pricing_context = [{
        "product_id": "prod_002",
        "competitor_price": 120.0  # Real price is $120
    }]
    
    # Create a proposal claiming a DIFFERENT competitor price
    mismatch_proposal = {
        "product_id": "prod_002",
        "product_name": "Test Product 2",
        "current_price": 100.0,
        "proposed_price": 95.0,
        "cost": 50.0,
        "status": "DECREASE",
        "signals_used": [
            "competitor_price: $85.00",  # WRONG! Real price is $120
            "sentiment: neutral"
        ],
        "reasoning": "Matching wrong competitor price"
    }
    
    state = {
        "merchant_id": "test_mismatch",
        "pricing_context": real_pricing_context,
        "pricing_proposals": [mismatch_proposal],
        "validation_flags": [],
        "sentiment_score": 0.0,
        "catalog_issues": [],
        "support_summary": {},
        "merchant_locks": {},
        "audit_log": []
    }
    
    print("\n🧪 Running validator with mismatched competitor data...")
    
    # Run validator
    validator_result = validator_node(state)
    state.update(validator_result)
    
    # Run resolver
    resolver_result = conflict_resolver_node(state)
    state.update(resolver_result)
    
    validation_flags = state.get("validation_flags", [])
    final_report = state.get("final_report", {})
    pricing_actions = final_report.get("pricing_actions", [])
    
    print(f"\n✓ Validation Flags Found: {len(validation_flags)}")
    for flag in validation_flags:
        print(f"  - {flag['type']}: {flag['message']}")
    
    print(f"\n✓ Pricing Actions:")
    for action in pricing_actions:
        print(f"  - {action['product_id']}: Status={action['status']}, Note={action.get('note', 'N/A')}")
    
    # Verify the mismatch was caught
    assert len(validation_flags) > 0, "❌ FAILED: No validation flags detected!"
    assert any(f["type"] == "DATA_MISMATCH" for f in validation_flags), "❌ FAILED: Data mismatch not detected!"
    assert pricing_actions[0]["status"] == "BLOCKED", "❌ FAILED: Proposal was not blocked!"
    
    print("\n✅ TEST PASSED: Data mismatch was detected and blocked!")
    return True


def test_contradiction_detection():
    """Test that the validator catches price increases during negative sentiment."""
    print("\n" + "="*70)
    print("TEST 3: CONTRADICTION DETECTION")
    print("="*70)
    
    # Create a proposal for price INCREASE during negative sentiment
    contradiction_proposal = {
        "product_id": "prod_003",
        "product_name": "Test Product 3",
        "current_price": 100.0,
        "proposed_price": 110.0,
        "cost": 50.0,
        "status": "INCREASE",  # Trying to increase price
        "signals_used": [
            "demand: high",
            "cost: stable"
        ],
        "reasoning": "High demand justifies increase"
    }
    
    state = {
        "merchant_id": "test_contradiction",
        "pricing_context": [],
        "pricing_proposals": [contradiction_proposal],
        "validation_flags": [],
        "sentiment_score": -0.5,  # NEGATIVE sentiment!
        "catalog_issues": [],
        "support_summary": {},
        "merchant_locks": {},
        "audit_log": []
    }
    
    print("\n🧪 Running validator with price increase during negative sentiment...")
    
    # Run validator
    validator_result = validator_node(state)
    state.update(validator_result)
    
    # Run resolver
    resolver_result = conflict_resolver_node(state)
    state.update(resolver_result)
    
    validation_flags = state.get("validation_flags", [])
    final_report = state.get("final_report", {})
    pricing_actions = final_report.get("pricing_actions", [])
    
    print(f"\n✓ Validation Flags Found: {len(validation_flags)}")
    for flag in validation_flags:
        print(f"  - {flag['type']}: {flag['message']}")
    
    print(f"\n✓ Pricing Actions:")
    for action in pricing_actions:
        print(f"  - {action['product_id']}: Status={action['status']}, Note={action.get('note', 'N/A')}")
    
    # Verify the contradiction was caught
    assert len(validation_flags) > 0, "❌ FAILED: No validation flags detected!"
    assert any(f["type"] == "CONTRADICTION" for f in validation_flags), "❌ FAILED: Contradiction not detected!"
    assert pricing_actions[0]["status"] == "BLOCKED", "❌ FAILED: Proposal was not blocked!"
    
    print("\n✅ TEST PASSED: Contradiction was detected and blocked!")
    return True


def main():
    print("\n" + "="*70)
    print("VALIDATION PIPELINE TEST SUITE")
    print("="*70)
    
    try:
        test_hallucination_detection()
        test_data_mismatch_detection()
        test_contradiction_detection()
        
        print("\n" + "="*70)
        print("🎉 ALL TESTS PASSED!")
        print("="*70)
        print("\nThe validation pipeline successfully:")
        print("  ✓ Detects hallucinated competitor data")
        print("  ✓ Catches mismatched data claims")
        print("  ✓ Identifies contradictory pricing decisions")
        print("\n" + "="*70)
        
    except AssertionError as e:
        print(f"\n{e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()
