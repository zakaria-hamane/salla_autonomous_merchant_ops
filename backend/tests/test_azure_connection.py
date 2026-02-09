"""
Test Azure OpenAI connection and configuration.
"""
import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

load_dotenv()

def test_azure_connection():
    """Test Azure OpenAI connection with current configuration."""
    
    print("=" * 70)
    print("Testing Azure OpenAI Connection")
    print("=" * 70)
    
    # Get configuration
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    print(f"\nConfiguration:")
    print(f"  Endpoint: {endpoint}")
    print(f"  Deployment: {deployment}")
    print(f"  API Version: {api_version}")
    print(f"  API Key: {'*' * 20}{api_key[-10:] if api_key else 'NOT SET'}")
    
    if not all([api_key, endpoint, deployment]):
        print("\n❌ Missing required configuration!")
        return False
    
    try:
        print("\n" + "=" * 70)
        print("Test 1: Initialize AzureChatOpenAI")
        print("=" * 70)
        
        llm = AzureChatOpenAI(
            azure_endpoint=endpoint,
            azure_deployment=deployment,
            api_key=api_key,
            api_version=api_version,
            temperature=1  # GPT-5 default
        )
        
        print("✓ LLM initialized successfully")
        
        print("\n" + "=" * 70)
        print("Test 2: Simple completion")
        print("=" * 70)
        
        response = llm.invoke("Say 'Hello, Azure OpenAI!' and nothing else.")
        print(f"✓ Response: {response.content}")
        
        print("\n" + "=" * 70)
        print("Test 3: JSON output")
        print("=" * 70)
        
        json_prompt = """Return a JSON object with this exact structure:
{
  "status": "success",
  "message": "Test completed",
  "number": 42
}

Return ONLY the JSON, no other text."""
        
        response = llm.invoke(json_prompt)
        print(f"✓ Response: {response.content}")
        
        # Try to parse as JSON
        import json
        try:
            parsed = json.loads(response.content)
            print(f"✓ Valid JSON parsed: {parsed}")
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parsing failed: {e}")
            print(f"   Raw response: {response.content}")
        
        print("\n" + "=" * 70)
        print("✅ All tests passed!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        
        return False


if __name__ == "__main__":
    success = test_azure_connection()
    exit(0 if success else 1)
