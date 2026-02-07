"""
Simple test to verify Azure OpenAI connection.
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("="*70)
print("AZURE OPENAI CONNECTION TEST")
print("="*70)

# Check environment variables
print("\n1. Environment Variables:")
print(f"   LLM_PROVIDER: {os.getenv('LLM_PROVIDER')}")
print(f"   AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
print(f"   AZURE_OPENAI_DEPLOYMENT_NAME: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')}")
print(f"   AZURE_OPENAI_API_VERSION: {os.getenv('AZURE_OPENAI_API_VERSION')}")
print(f"   API Key present: {bool(os.getenv('AZURE_OPENAI_API_KEY'))}")

# Test LLM initialization
print("\n2. Testing LLM Initialization...")
try:
    from llm_config import get_llm
    llm = get_llm(temperature=0)
    print(f"   ✓ LLM Type: {type(llm).__name__}")
    print(f"   ✓ Deployment: {llm.deployment_name}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test simple invocation
print("\n3. Testing Simple Invocation...")
try:
    response = llm.invoke("Say 'Hello' in one word.")
    print(f"   ✓ Response: {response.content}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test with structured output
print("\n4. Testing Structured Output...")
try:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import JsonOutputParser
    from pydantic import BaseModel, Field
    
    class TestOutput(BaseModel):
        message: str = Field(description="A greeting message")
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. Return JSON with a 'message' field."),
        ("user", "Say hello")
    ])
    
    parser = JsonOutputParser(pydantic_object=TestOutput)
    chain = prompt | llm | parser
    
    result = chain.invoke({})
    print(f"   ✓ Result: {result}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*70)
print("✅ ALL TESTS PASSED!")
print("="*70)
print("\nYour Azure OpenAI connection is working correctly.")
print("The issue must be elsewhere in the code.")
