"""
Test script to verify LLM configuration.
"""
import os
from dotenv import load_dotenv
from llm_config import get_llm, get_provider_info

# Load environment variables
load_dotenv()


def test_llm_config():
    """Test LLM configuration and basic functionality."""
    print("="*70)
    print("LLM CONFIGURATION TEST")
    print("="*70)
    
    # Get provider info
    info = get_provider_info()
    
    print("\n📋 Provider Information:")
    print("-"*70)
    print(f"Provider: {info['provider']}")
    print(f"Configured: {info['configured']}")
    
    if info['provider'] == 'azure':
        print(f"Endpoint: {info['endpoint']}")
        print(f"Deployment: {info['deployment']}")
        print(f"API Version: {info['api_version']}")
    
    if not info['configured']:
        print("\n❌ LLM is not properly configured!")
        print("\nPlease set the required environment variables:")
        if info['provider'] == 'azure':
            print("  - AZURE_OPENAI_API_KEY")
            print("  - AZURE_OPENAI_ENDPOINT")
            print("  - AZURE_OPENAI_DEPLOYMENT_NAME")
        else:
            print("  - OPENAI_API_KEY")
        return False
    
    # Test LLM initialization
    print("\n🧪 Testing LLM Initialization...")
    print("-"*70)
    
    try:
        llm = get_llm(temperature=0)
        print(f"✓ LLM initialized successfully")
        print(f"  Type: {type(llm).__name__}")
        print(f"  Model: {getattr(llm, 'model_name', getattr(llm, 'deployment_name', 'N/A'))}")
        
    except Exception as e:
        print(f"✗ Failed to initialize LLM: {e}")
        return False
    
    # Test LLM invocation
    print("\n🚀 Testing LLM Invocation...")
    print("-"*70)
    
    try:
        response = llm.invoke("Say 'Hello from Salla!' in exactly 3 words.")
        print(f"✓ LLM invocation successful")
        print(f"  Response: {response.content}")
        
    except Exception as e:
        print(f"✗ Failed to invoke LLM: {e}")
        return False
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70)
    print("\nYour LLM configuration is working correctly.")
    print("You can now run the full system.")
    
    return True


if __name__ == "__main__":
    success = test_llm_config()
    exit(0 if success else 1)
