"""
Pricing Agent: Generates rule-based pricing recommendations.
"""
from typing import Dict, Any, List


def pricing_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates pricing proposals based on rules and constraints.
    Only runs if safety gates pass.
    
    Hard Constraints:
    - Cannot reduce prices below cost
    - Cannot increase prices if sentiment is negative
    - Must explain every decision
    """
    print("\n--- 💰 Pricing Agent: Calculating Pricing Proposals ---")
    
    products = state.get("normalized_catalog", state.get("product_data", []))
    pricing_context = state.get("pricing_context", [])
    sentiment = state.get("sentiment_score", 0.0)
    
    if not products:
        print("✗ No products to price")
        return {"pricing_proposals": []}
    
    proposals = []
    
    for product in products:
        product_id = product.get("id", "unknown")
        current_price = float(product.get("price", 0))
        cost = float(product.get("cost", current_price * 0.5))
        
        # Find competitor pricing
        competitor_price = None
        for ctx in pricing_context:
            if ctx.get("product_id") == product_id:
                competitor_price = float(ctx.get("competitor_price", 0))
                break
        
        # Rule-based pricing logic
        proposed_price = current_price
        reasoning = []
        signals_used = []
        
        # Signal 1: Competitor pricing
        if competitor_price:
            signals_used.append(f"competitor_price: ${competitor_price:.2f}")
            if competitor_price < current_price * 0.95:
                proposed_price = min(proposed_price, competitor_price + 5)
                reasoning.append("Adjusted to match competitor pricing")
        
        # Signal 2: Sentiment constraint
        signals_used.append(f"sentiment: {sentiment:.2f}")
        if sentiment < 0:
            # Negative sentiment: cannot increase price
            if proposed_price > current_price:
                proposed_price = current_price
                reasoning.append("Price increase blocked due to negative sentiment")
        else:
            # Positive sentiment: can increase by up to 10%
            if not competitor_price or competitor_price > current_price:
                proposed_price = min(proposed_price * 1.10, current_price * 1.10)
                reasoning.append("Standard margin adjustment (+10%)")
        
        # Hard Constraint: Cost floor
        cost_floor = cost * 1.05  # Minimum 5% margin
        if proposed_price < cost_floor:
            proposed_price = cost_floor
            reasoning.append(f"Price raised to cost floor (${cost_floor:.2f})")
            signals_used.append(f"cost_floor: ${cost_floor:.2f}")
        
        # Determine status
        if proposed_price == current_price:
            status = "HOLD"
            if not reasoning:
                reasoning.append("No changes recommended")
        elif proposed_price > current_price:
            status = "INCREASE"
        else:
            status = "DECREASE"
        
        proposal = {
            "product_id": product_id,
            "product_name": product.get("name", "Unknown"),
            "current_price": current_price,
            "proposed_price": round(proposed_price, 2),
            "status": status,
            "reasoning": " | ".join(reasoning),
            "signals_used": signals_used,
            "cost": cost
        }
        
        proposals.append(proposal)
    
    print(f"✓ Generated {len(proposals)} pricing proposals")
    
    return {"pricing_proposals": proposals}
