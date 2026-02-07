"""
Data loader for sample datasets.
"""
import pandas as pd
import os
from typing import Tuple, List, Dict


def load_sample_data() -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Load sample data from CSV files.
    Returns: (product_data, customer_messages, pricing_context)
    """
    # Try backend/data first, then fall back to ../data (root data directory)
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    if not os.path.exists(data_dir) or not os.listdir(data_dir):
        # Try parent directory's data folder
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        print(f"Using data directory: {data_dir}")
    
    # Load products
    try:
        products_df = pd.read_csv(os.path.join(data_dir, "products_raw.csv"))
        product_data = products_df.to_dict('records')
    except FileNotFoundError:
        # Fallback sample data
        product_data = [
            {
                "id": "P001",
                "name": "Espresso Maker",
                "price": 120.00,
                "cost": 60.00,
                "category": "Kitchen",
                "description": "High quality espresso maker"
            },
            {
                "id": "P002",
                "name": "Coffee Grinder",
                "price": 45.00,
                "cost": 20.00,
                "category": "Kitchen",
                "description": "Burr coffee grinder"
            }
        ]
    
    # Load customer messages
    try:
        messages_df = pd.read_csv(os.path.join(data_dir, "customer_messages.csv"))
        customer_messages = messages_df.to_dict('records')
    except FileNotFoundError:
        customer_messages = [
            {
                "id": "M001",
                "message": "When will my order arrive?",
                "timestamp": "2026-02-05 10:30:00"
            },
            {
                "id": "M002",
                "message": "The espresso maker is leaking water!",
                "timestamp": "2026-02-05 11:15:00"
            }
        ]
    
    # Load pricing context
    try:
        pricing_df = pd.read_csv(os.path.join(data_dir, "pricing_context.csv"))
        pricing_context = pricing_df.to_dict('records')
    except FileNotFoundError:
        pricing_context = [
            {
                "product_id": "P001",
                "competitor_price": 115.00,
                "market_trend": "stable"
            }
        ]
    
    return product_data, customer_messages, pricing_context
