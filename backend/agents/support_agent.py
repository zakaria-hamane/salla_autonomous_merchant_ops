"""
Support Agent: Analyzes customer messages and detects sentiment/spikes.
"""
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from llm_config import get_llm


class SupportAnalysis(BaseModel):
    """Structured output for support analysis."""
    message_classifications: List[Dict[str, str]] = Field(description="Classified messages")
    overall_sentiment: float = Field(description="Sentiment score -1 to 1")
    complaint_velocity: float = Field(description="Complaint rate 0-10")
    trending_topics: List[str] = Field(description="Common issues")
    spike_detected: bool = Field(description="Anomaly spike detected")


def support_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes customer messages to classify intent and detect sentiment trends.
    Detects viral complaint spikes that trigger safety throttling.
    """
    print("\n--- 🎧 Support Agent: Analyzing Customer Messages ---")
    
    messages = state.get("customer_messages", [])
    
    if not messages:
        return {
            "support_summary": {"status": "no_data"},
            "sentiment_score": 0.0,
            "complaint_spike_detected": False
        }
    
    # Initialize LLM (supports both OpenAI and Azure)
    # Note: temperature will be auto-adjusted for GPT-5
    # For Azure, model parameter is ignored (uses deployment name from env)
    llm = get_llm(temperature=0)
    
    # Create prompt with explicit JSON format for GPT-5
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a customer support analyst.
Classify each message as: Inquiry, Complaint, Suggestion, or Transactional Request.
Analyze sentiment and detect anomalies.

You MUST return valid JSON with this exact structure:
{{
  "message_classifications": [
    {{"id": "M001", "type": "Complaint", "sentiment": "negative"}}
  ],
  "overall_sentiment": -0.5,
  "complaint_velocity": 5.0,
  "trending_topics": ["issue1", "issue2"],
  "spike_detected": false
}}

Rules:
- overall_sentiment: number between -1 and 1
- complaint_velocity: number between 0 and 10
- spike_detected: boolean (true or false)
- Return ONLY valid JSON, no other text"""),
        ("user", "Customer messages:\n{messages}")
    ])
    
    # Create chain
    parser = JsonOutputParser(pydantic_object=SupportAnalysis)
    chain = prompt | llm | parser
    
    try:
        # Run analysis with better error handling
        messages_str = str(messages[:20])  # Limit for efficiency
        print(f"Analyzing {len(messages[:20])} messages...")
        
        # Debug: Show what we're sending
        print(f"Debug: Sending {len(messages_str)} characters to LLM")
        
        # Try to invoke the LLM
        try:
            result = chain.invoke({"messages": messages_str})
        except Exception as llm_error:
            print(f"✗ LLM Invocation Error: {type(llm_error).__name__}")
            print(f"✗ Error message: {str(llm_error)}")
            
            # Check for specific Azure OpenAI errors
            error_str = str(llm_error).lower()
            if "api version" in error_str or "version" in error_str:
                print("⚠️  Possible API version issue. Try using 2024-02-15-preview")
            elif "deployment" in error_str:
                print("⚠️  Possible deployment name issue. Check AZURE_OPENAI_DEPLOYMENT_NAME")
            elif "authentication" in error_str or "401" in error_str:
                print("⚠️  Authentication error. Check AZURE_OPENAI_API_KEY")
            elif "temperature" in error_str:
                print("⚠️  Temperature parameter issue with GPT-5")
            
            raise  # Re-raise to be caught by outer exception handler
        
        # Debug: Show what we got back
        print(f"Debug: Received result type: {type(result)}")
        print(f"Debug: Result keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
        
        # Validate result structure
        if not isinstance(result, dict):
            print(f"✗ Invalid result type: {type(result)}")
            print(f"✗ Result content: {result}")
            raise ValueError(f"Expected dict, got {type(result)}")
        
        classifications = result.get("message_classifications", [])
        sentiment = float(result.get("overall_sentiment", 0.0))
        velocity = float(result.get("complaint_velocity", 0.0))
        topics = result.get("trending_topics", [])
        spike = bool(result.get("spike_detected", False))
        
        # Additional spike detection logic
        complaint_count = len([c for c in classifications if c.get("type") == "Complaint"])
        complaint_ratio = complaint_count / len(classifications) if classifications else 0
        
        # Trigger spike if velocity > 7 OR complaint ratio > 50%
        spike_detected = spike or velocity > 7.0 or complaint_ratio > 0.5
        
        print(f"✓ Classified {len(classifications)} messages")
        print(f"✓ Sentiment: {sentiment:.2f}")
        print(f"✓ Complaint Velocity: {velocity:.1f}/10")
        print(f"✓ Spike Detected: {spike_detected}")
        
        summary = {
            "classifications": classifications,
            "sentiment": sentiment,
            "velocity": velocity,
            "topics": topics,
            "total_messages": len(messages),
            "complaint_count": complaint_count
        }
        
        return {
            "support_summary": summary,
            "sentiment_score": sentiment,
            "complaint_spike_detected": spike_detected
        }
        
    except Exception as e:
        print(f"✗ Support Agent Error: {e}")
        print(f"✗ Error type: {type(e).__name__}")
        import traceback
        print(f"✗ Traceback:")
        traceback.print_exc()
        return {
            "support_summary": {"error": str(e), "error_type": type(e).__name__},
            "sentiment_score": 0.0,
            "complaint_spike_detected": False
        }
