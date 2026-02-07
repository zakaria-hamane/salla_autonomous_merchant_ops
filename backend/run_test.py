"""
Test script to run the LangGraph workflow locally.
"""
import os
from dotenv import load_dotenv
from graph import app
from data_loader import load_sample_data

# Load environment variables
load_dotenv()

def main():
    print("="*70)
    print("SALLA AUTONOMOUS MERCHANT OPERATIONS - TEST RUN")
    print("="*70)
    
    # Load sample data
    print("\n📂 Loading sample data...")
    product_data, customer_messages, pricing_context = load_sample_data()
    
    print(f"✓ Loaded {len(product_data)} products")
    print(f"✓ Loaded {len(customer_messages)} customer messages")
    print(f"✓ Loaded {len(pricing_context)} pricing contexts")
    
    # Prepare initial state
    initial_state = {
        "merchant_id": "test_merchant_001",
        "product_data": product_data[:5],  # Limit for testing
        "customer_messages": customer_messages[:10],
        "pricing_context": pricing_context[:3],
        "competitor_data": [],
        "normalized_catalog": [],
        "catalog_issues": [],
        "pricing_proposals": [],
        "support_summary": {},
        "sentiment_score": 0.0,
        "complaint_spike_detected": False,
        "schema_validation_passed": True,
        "throttle_mode_active": False,
        "retry_count": 0,
        "merchant_locks": {},
        "final_report": {},
        "audit_log": []
    }
    
    print("\n🚀 Running LangGraph workflow...")
    print("-"*70)
    
    try:
        # Run the graph
        result = app.invoke(initial_state)
        
        print("\n" + "="*70)
        print("📊 FINAL REPORT")
        print("="*70)
        
        final_report = result.get("final_report", {})
        
        print(f"\nStatus: {final_report.get('status', 'UNKNOWN')}")
        print(f"Alert Level: {final_report.get('alert_level', 'N/A')}")
        
        if final_report.get('status') == 'FROZEN':
            print(f"\n🚨 ALERT: {final_report.get('alert_message', 'System throttled')}")
        
        summary = final_report.get('summary', {})
        if summary:
            print(f"\n📈 Summary:")
            print(f"  - Total Products: {summary.get('total_products', 0)}")
            print(f"  - Approved Changes: {summary.get('approved_changes', 0)}")
            print(f"  - Blocked Changes: {summary.get('blocked_changes', 0)}")
            print(f"  - Locked Products: {summary.get('locked_products', 0)}")
        
        pricing_actions = final_report.get('pricing_actions', [])
        if pricing_actions:
            print(f"\n💰 Pricing Actions ({len(pricing_actions)}):")
            for action in pricing_actions[:5]:  # Show first 5
                print(f"  - {action.get('product_name', action.get('product_id'))}: "
                      f"${action.get('current_price', 0):.2f} → ${action.get('final_price', 0):.2f} "
                      f"[{action.get('status')}]")
        
        recommendations = final_report.get('recommendations', [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"  - {rec}")
        
        print("\n" + "="*70)
        print("✅ Test completed successfully!")
        print("="*70)
        
        # Check LangSmith
        if os.getenv("LANGCHAIN_TRACING_V2") == "true":
            print("\n🔍 LangSmith tracing is enabled!")
            print(f"   Project: {os.getenv('LANGCHAIN_PROJECT', 'default')}")
            print("   Check your traces at: https://smith.langchain.com/")
        
    except Exception as e:
        print(f"\n❌ Error running workflow: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
