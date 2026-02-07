"""
LangGraph nodes implementing the orchestration logic.
"""
from typing import Dict, Any
from agents.catalog_agent import catalog_agent
from agents.support_agent import support_agent
from agents.pricing_agent import pricing_agent
# Import the data loader here
from data_loader import load_sample_data


def coordinator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Coordinator: Initializes the workflow and prepares data.
    """
    print("\n" + "="*60)
    print("🧠 COORDINATOR AGENT: Starting Daily Operations Run")
    print("="*60)
    
    merchant_id = state.get("merchant_id", "unknown")
    print(f"Merchant: {merchant_id}")
    
    # --- NEW LOGIC: SELF-LOADING DATA ---
    # Check if uploaded data is provided, otherwise load from local storage
    updates = {}
    uploaded_data = state.get("uploaded_data")
    
    if uploaded_data:
        print("📂 Coordinator: Processing uploaded CSV data...")
        import pandas as pd
        from io import StringIO
        
        # Parse uploaded CSVs
        product_data = []
        customer_messages = []
        pricing_context = []
        
        if uploaded_data.get("products_csv"):
            df = pd.read_csv(StringIO(uploaded_data["products_csv"]))
            product_data = df.to_dict('records')
            print(f"✓ Loaded {len(product_data)} products from uploaded file")
        
        if uploaded_data.get("messages_csv"):
            df = pd.read_csv(StringIO(uploaded_data["messages_csv"]))
            customer_messages = df.to_dict('records')
            print(f"✓ Loaded {len(customer_messages)} messages from uploaded file")
        
        if uploaded_data.get("pricing_csv"):
            df = pd.read_csv(StringIO(uploaded_data["pricing_csv"]))
            pricing_context = df.to_dict('records')
            print(f"✓ Loaded {len(pricing_context)} pricing contexts from uploaded file")
        
        updates = {
            "product_data": product_data[:10] if product_data else [],
            "customer_messages": customer_messages[:20] if customer_messages else [],
            "pricing_context": pricing_context[:5] if pricing_context else [],
            "competitor_data": [],
            "catalog_issues": [],
            "pricing_proposals": [],
            "support_summary": {},
            "final_report": {}
        }
    elif not state.get("product_data"):
        print("📂 Coordinator: No input data found. Loading from local storage...")
        product_data, customer_messages, pricing_context = load_sample_data()
        
        # We update the state with the loaded data
        updates = {
            "product_data": product_data[:10],
            "customer_messages": customer_messages[:20],
            "pricing_context": pricing_context[:5],
            "competitor_data": [],
            "catalog_issues": [],
            "pricing_proposals": [],
            "support_summary": {},
            "final_report": {}
        }
        print("✓ Data loaded successfully")
    # ------------------------------------
    
    # Initialize tracking
    return {
        "retry_count": 0,
        "merchant_locks": {},
        "audit_log": [{
            "action": "workflow_started",
            "merchant_id": merchant_id
        }],
        **updates  # Merge the loaded data into the state
    }


def throttler_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Throttler: Freezes all operations when viral spike detected.
    This is the safety circuit breaker.
    """
    print("\n" + "!"*60)
    print("❄️  THROTTLER ACTIVATED: FREEZING ALL OPERATIONS")
    print("!"*60)
    
    support_summary = state.get("support_summary", {})
    
    alert_message = (
        "🔴 VIRAL COMPLAINT SPIKE DETECTED\n"
        f"Complaint Velocity: {support_summary.get('velocity', 0):.1f}/10\n"
        f"Sentiment Score: {support_summary.get('sentiment', 0):.2f}\n"
        "All automated pricing updates have been suspended.\n"
        "Manual review required before resuming operations."
    )
    
    return {
        "throttle_mode_active": True,
        "final_report": {
            "status": "FROZEN",
            "alert_level": "RED",
            "alert_message": alert_message,
            "support_summary": support_summary,
            "actions_taken": [],
            "recommendations": [
                "Review customer complaints immediately",
                "Investigate root cause of spike",
                "Prepare public response if needed",
                "Do not make pricing changes until resolved"
            ]
        },
        "audit_log": [{
            "action": "throttler_activated",
            "reason": "complaint_spike_detected"
        }]
    }


def conflict_resolver_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolver: Cross-checks outputs and finalizes decisions.
    Applies merchant locks and business logic.
    """
    print("\n--- ⚖️  Conflict Resolver: Validating & Finalizing ---")
    
    proposals = state.get("pricing_proposals", [])
    catalog_issues = state.get("catalog_issues", [])
    support_summary = state.get("support_summary", {})
    sentiment = state.get("sentiment_score", 0.0)
    merchant_locks = state.get("merchant_locks", {})
    
    final_actions = []
    warnings = []
    
    # --- NEW: CROSS-AGENT VERIFICATION (Hallucination Check) ---
    # 1. Identify products that the Catalog Agent flagged as "Critical"
    #    This prevents the Pricing Agent from hallucinating a price for invalid data.
    critical_error_ids = set()
    for issue in catalog_issues:
        # Check for critical type or high severity
        if issue.get("type") == "critical" or issue.get("severity") == "high":
            # Handle cases where ID might be under 'product_id' or 'id'
            pid = issue.get("product_id") or issue.get("id")
            if pid:
                critical_error_ids.add(pid)
    
    if critical_error_ids:
        print(f"⚠️  CROSS-CHECK: Found {len(critical_error_ids)} products with critical catalog errors.")
    # -----------------------------------------------------------
    
    # Process each pricing proposal
    for proposal in proposals:
        product_id = proposal["product_id"]
        proposed_price = proposal["proposed_price"]
        current_price = proposal["current_price"]
        cost = proposal["cost"]
        
        # 2. PRIORITY 1: MERCHANT LOCKS (Immutable Override)
        if product_id in merchant_locks:
            final_actions.append({
                **proposal,
                "final_price": current_price,
                "status": "LOCKED",
                "note": "Merchant override: price locked"
            })
            continue
        
        # 3. PRIORITY 2: CATALOG INTEGRITY CHECK (New Logic)
        #    If Catalog Agent says data is bad, we CANNOT trust Pricing Agent's output.
        if product_id in critical_error_ids:
            final_actions.append({
                **proposal,
                "final_price": current_price,
                "status": "BLOCKED",
                "note": "Blocked: Catalog Agent flagged critical data error"
            })
            warnings.append(f"Blocked pricing for {product_id} due to catalog data corruption")
            continue
        
        # 4. PRIORITY 3: SENTIMENT CHECK
        if sentiment < -0.3 and proposed_price > current_price:
            final_actions.append({
                **proposal,
                "final_price": current_price,
                "status": "BLOCKED",
                "note": f"Price increase blocked: negative sentiment ({sentiment:.2f})"
            })
            warnings.append(f"Blocked price increase for {product_id} due to sentiment")
            continue
        
        # 5. PRIORITY 4: COST FLOOR CHECK
        if proposed_price < cost:
            final_actions.append({
                **proposal,
                "final_price": cost * 1.05,
                "status": "ADJUSTED",
                "note": f"Price raised to cost floor (${cost * 1.05:.2f})"
            })
            warnings.append(f"Adjusted {product_id} to meet cost floor")
            continue
        
        # 6. APPROVAL
        final_actions.append({
            **proposal,
            "final_price": proposed_price,
            "status": "APPROVED"
        })
    
    # Calculate Final Alert Level
    critical_issues_count = len([i for i in catalog_issues if i.get("type") == "critical"])
    alert_level = "RED" if critical_issues_count > 0 else "YELLOW" if warnings else "GREEN"
    
    print(f"✓ Finalized {len(final_actions)} pricing decisions")
    print(f"✓ Alert Level: {alert_level}")
    
    # Generate final report
    final_report = {
        "status": "COMPLETED",
        "alert_level": alert_level,
        "summary": {
            "total_products": len(proposals),
            "approved_changes": len([a for a in final_actions if a["status"] == "APPROVED"]),
            "blocked_changes": len([a for a in final_actions if a["status"] == "BLOCKED"]),
            "locked_products": len([a for a in final_actions if a["status"] == "LOCKED"])
        },
        "catalog_issues": catalog_issues,
        "support_summary": support_summary,
        "pricing_actions": final_actions,
        "warnings": warnings,
        "recommendations": generate_recommendations(state, final_actions, warnings)
    }
    
    return {
        "final_report": final_report,
        "audit_log": [{
            "action": "workflow_completed",
            "alert_level": alert_level,
            "actions_count": len(final_actions)
        }]
    }


def generate_recommendations(state: Dict, actions: list, warnings: list) -> list:
    """Generate actionable recommendations for the merchant."""
    recommendations = []
    
    sentiment = state.get("sentiment_score", 0.0)
    catalog_issues = state.get("catalog_issues", [])
    
    if sentiment < -0.3:
        recommendations.append("⚠️ Address negative customer sentiment before making price increases")
    
    if catalog_issues:
        recommendations.append(f"📦 Review {len(catalog_issues)} catalog data quality issues")
    
    if warnings:
        recommendations.append(f"⚡ {len(warnings)} pricing proposals required manual adjustment")
    
    approved = len([a for a in actions if a["status"] == "APPROVED"])
    if approved > 0:
        recommendations.append(f"✅ {approved} pricing changes ready to apply")
    
    if not recommendations:
        recommendations.append("✨ All systems operating normally")
    
    return recommendations
