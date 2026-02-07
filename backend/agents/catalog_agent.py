"""
Catalog Agent: Normalizes product data and detects issues.
"""
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from llm_config import get_llm


class CatalogAnalysis(BaseModel):
    """Structured output for catalog analysis."""
    normalized_products: List[Dict[str, Any]] = Field(description="Normalized product list")
    issues: List[Dict[str, Any]] = Field(description="Detected issues")
    confidence_score: float = Field(description="Overall confidence 0-1")


def catalog_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes and normalizes product catalog data.
    Detects missing attributes, duplicates, and inconsistencies.
    """
    print("\n--- 📦 Catalog Agent: Normalizing Product Data ---")
    
    products = state.get("product_data", [])
    
    if not products:
        return {
            "normalized_catalog": [],
            "catalog_issues": [{"type": "error", "message": "No product data provided"}],
            "schema_validation_passed": False
        }
    
    # Initialize LLM (supports both OpenAI and Azure)
    # Note: temperature will be auto-adjusted for GPT-5
    # For Azure, model parameter is ignored (uses deployment name from env)
    llm = get_llm(temperature=0)
    
    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a product catalog normalization expert.
Analyze the product data and:
1. Normalize attributes (fix spelling, standardize units)
2. Detect missing or inconsistent information
3. Identify potential duplicates
4. Flag low-quality descriptions

Return JSON with:
- normalized_products: cleaned product list
- issues: list of problems found
- confidence_score: 0-1 score for data quality"""),
        ("user", "Products to analyze:\n{products}")
    ])
    
    # Create chain
    parser = JsonOutputParser(pydantic_object=CatalogAnalysis)
    chain = prompt | llm | parser
    
    try:
        # Run analysis
        result = chain.invoke({"products": str(products[:5])})  # Limit for token efficiency
        
        normalized = result.get("normalized_products", [])
        issues = result.get("issues", [])
        confidence = result.get("confidence_score", 0.8)
        
        # Determine if schema validation passed
        schema_passed = confidence > 0.6 and len([i for i in issues if i.get("type") == "critical"]) == 0
        
        print(f"✓ Normalized {len(normalized)} products")
        print(f"✓ Found {len(issues)} issues")
        print(f"✓ Confidence: {confidence:.2f}")
        
        return {
            "normalized_catalog": normalized,
            "catalog_issues": issues,
            "schema_validation_passed": schema_passed
        }
        
    except Exception as e:
        print(f"✗ Catalog Agent Error: {e}")
        return {
            "normalized_catalog": products,  # Fallback to raw data
            "catalog_issues": [{"type": "error", "message": str(e)}],
            "schema_validation_passed": False
        }
