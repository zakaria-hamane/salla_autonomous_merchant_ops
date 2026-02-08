"""
LangGraph nodes implementing the orchestration logic.
"""
import re
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


def validator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validator: Performs hallucination checks and contradiction detection.
    This is the verification layer between agent outputs and final resolution.
    """
    print("\n--- 🕵️ Validator Agent: Pipeline Checks ---")
    
    proposals = state.get("pricing_proposals", [])
    pricing_context = state.get("pricing_context", [])
    sentiment = state.get("sentiment_score", 0.0)
    
    validation_flags = []
    
    # Convert pricing context to a lookup map for O(1) access
    # Map: product_id -> competitor_price
    context_map = {
        item.get("product_id"): float(item.get("competitor_price", 0)) 
        for item in pricing_context
    }
    
    for proposal in proposals:
        pid = proposal.get("product_id")
        signals = proposal.get("signals_used", [])
        
        # --- CHECK 1: HALLUCINATION CHECK (Ungrounded Claims) ---
        # Look for claims like "competitor_price: $115.00" in signals
        for signal in signals:
            if "competitor_price" in signal:
                # Extract the number from the string
                match = re.search(r"competitor_price:\s*\$?([\d\.]+)", signal)
                if match:
                    claimed_price = float(match.group(1))
                    
                    # Verify against source of truth
                    actual_price = context_map.get(pid)
                    
                    if actual_price is None:
                        flag = {
                            "product_id": pid,
                            "type": "HALLUCINATION",
                            "severity": "HIGH",
                            "message": f"Agent cited competitor price ${claimed_price}, but no competitor data exists for this product."
                        }
                        validation_flags.append(flag)
                        print(f"🚨 Hallucination detected for {pid}: Claimed context that doesn't exist.")
                    
                    elif abs(claimed_price - actual_price) > 0.01:
                        flag = {
                            "product_id": pid,
                            "type": "DATA_MISMATCH",
                            "severity": "HIGH",
                            "message": f"Agent cited competitor price ${claimed_price}, but source data says ${actual_price}."
                        }
                        validation_flags.append(flag)
                        print(f"🚨 Data Mismatch for {pid}: Claimed ${claimed_price} vs Actual ${actual_price}")
        
        # --- CHECK 2: CONTRADICTION DETECTION ---
        # Check: Positive price action vs Negative Sentiment
        if proposal.get("status") == "INCREASE" and sentiment < -0.3:
            flag = {
                "product_id": pid,
                "type": "CONTRADICTION",
                "severity": "MEDIUM",
                "message": f"Proposed price increase contradicts negative market sentiment ({sentiment:.2f})."
            }
            validation_flags.append(flag)
            print(f"⚠️ Contradiction detected for {pid}: Price hike during negative sentiment.")
    
    print(f"✓ Validation complete. Found {len(validation_flags)} flags.")
    
    return {
        "validation_flags": validation_flags,
        "audit_log": [{
            "action": "validation_run",
            "flags_found": len(validation_flags)
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
    validation_flags = state.get("validation_flags", [])  # <--- GET FLAGS
    
    final_actions = []
    warnings = []
    
    # Create a map of validation failures for quick lookup
    # Map: product_id -> [list of failure types]
    flag_map = {}
    for flag in validation_flags:
        pid = flag.get("product_id")
        if pid not in flag_map:
            flag_map[pid] = []
        flag_map[pid].append(flag)
    
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
        
        # --- NEW LOGIC: Check Validation Flags ---
        if product_id in flag_map:
            flags = flag_map[product_id]
            
            # Critical Validation Failures (Hallucinations)
            hallucinations = [f for f in flags if f["type"] in ["HALLUCINATION", "DATA_MISMATCH"]]
            if hallucinations:
                final_actions.append({
                    **proposal,
                    "final_price": current_price,
                    "status": "BLOCKED",
                    "note": f"Blocked: {hallucinations[0]['message']}"
                })
                warnings.append(f"Security Block {product_id}: Agent hallucinated data source.")
                continue
            
            # Soft Validation Failures (Contradictions)
            contradictions = [f for f in flags if f["type"] == "CONTRADICTION"]
            if contradictions:
                final_actions.append({
                    **proposal,
                    "final_price": current_price,
                    "status": "BLOCKED",
                    "note": f"Blocked: {contradictions[0]['message']}"
                })
                warnings.append(f"Logic Block {product_id}: Proposal contradicted sentiment signals.")
                continue
        # -----------------------------------------
        
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
    
    # --- RELIABILITY METRICS CALCULATION ---
    total_ops = len(proposals)
    approved_ops = len([a for a in final_actions if a["status"] == "APPROVED"])
    blocked_ops = len([a for a in final_actions if a["status"] == "BLOCKED"])
    hallucination_count = len([f for f in validation_flags if f["type"] == "HALLUCINATION"])
    
    metrics = {
        "pricing_pass_rate": round((approved_ops / total_ops * 100), 1) if total_ops > 0 else 0.0,
        "automated_block_rate": round((blocked_ops / total_ops * 100), 1) if total_ops > 0 else 0.0,
        "hallucination_rate": round((hallucination_count / total_ops * 100), 1) if total_ops > 0 else 0.0,
        "sentiment_score": sentiment
    }
    
    # Calculate Final Alert Level
    critical_issues_count = len([i for i in catalog_issues if i.get("type") == "critical"])
    alert_level = "RED" if critical_issues_count > 0 else "YELLOW" if warnings else "GREEN"
    
    print(f"✓ Finalized {len(final_actions)} pricing decisions")
    print(f"✓ Metrics: Pass Rate {metrics['pricing_pass_rate']}%, Hallucinations {metrics['hallucination_rate']}%")
    print(f"✓ Alert Level: {alert_level}")
    
    # Generate final report
    final_report = {
        "status": "COMPLETED",
        "alert_level": alert_level,
        "metrics": metrics,  # Added to report
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
        "recommendations": generate_recommendations(state, final_actions, warnings),
        "validation_flags": validation_flags,  # Added to report for frontend visibility
        "merchant_locks": merchant_locks,  # Added for transparency
        "schema_validation_passed": state.get("schema_validation_passed", True),  # Added for debugging
        "retry_count": state.get("retry_count", 0),  # Added for debugging
        "throttle_mode_active": state.get("throttle_mode_active", False),  # Added for status
        "audit_log": state.get("audit_log", [])  # Added for full transparency
    }
    
    return {
        "final_report": final_report,
        "audit_log": [{
            "action": "workflow_completed",
            "alert_level": alert_level,
            "metrics": metrics
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
