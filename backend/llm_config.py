"""
LLM Configuration - Supports both OpenAI and Azure OpenAI
"""
import os
from typing import Optional
from langchain_openai import ChatOpenAI, AzureChatOpenAI


def get_llm(
    model: str = "gpt-4o-mini",
    temperature: float = 0,
    **kwargs
) -> ChatOpenAI:
    """
    Get configured LLM instance based on environment variables.
    
    Supports:
    - OpenAI (default)
    - Azure OpenAI
    
    Environment Variables:
    - LLM_PROVIDER: "openai" or "azure" (default: "openai")
    
    For OpenAI:
    - OPENAI_API_KEY: Your OpenAI API key
    
    For Azure OpenAI:
    - AZURE_OPENAI_API_KEY: Your Azure OpenAI API key
    - AZURE_OPENAI_ENDPOINT: Your Azure OpenAI endpoint
    - AZURE_OPENAI_DEPLOYMENT_NAME: Your deployment name (e.g., gpt-5, gpt-4o-mini)
    - AZURE_OPENAI_API_VERSION: API version (default: 2024-02-15-preview)
    
    Args:
        model: Model name (for OpenAI) or ignored (for Azure, uses deployment)
        temperature: Temperature for generation (Note: GPT-5 only supports default value of 1)
        **kwargs: Additional arguments passed to the LLM
    
    Returns:
        Configured ChatOpenAI or AzureChatOpenAI instance
    
    Note: For Azure, the model parameter is ignored and the deployment name
          from AZURE_OPENAI_DEPLOYMENT_NAME is used instead.
          GPT-5 models only support temperature=1 (default).
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    # Check if using GPT-5 and adjust temperature
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")
    if provider == "azure" and "gpt-5" in deployment.lower():
        # GPT-5 only supports default temperature
        if temperature != 1:
            print(f"⚠️  GPT-5 only supports temperature=1. Adjusting from {temperature} to 1.")
            temperature = 1
    
    if provider == "azure":
        return get_azure_llm(temperature=temperature, **kwargs)
    else:
        return get_openai_llm(model=model, temperature=temperature, **kwargs)


def get_openai_llm(
    model: str = "gpt-4o-mini",
    temperature: float = 0,
    **kwargs
) -> ChatOpenAI:
    """
    Get OpenAI LLM instance.
    
    Args:
        model: Model name (e.g., "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo")
        temperature: Temperature for generation
        **kwargs: Additional arguments
    
    Returns:
        ChatOpenAI instance
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required when LLM_PROVIDER=openai"
        )
    
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
        **kwargs
    )


def get_azure_llm(
    temperature: float = 0,
    **kwargs
) -> AzureChatOpenAI:
    """
    Get Azure OpenAI LLM instance.
    
    Args:
        temperature: Temperature for generation
        **kwargs: Additional arguments
    
    Returns:
        AzureChatOpenAI instance
    """
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    if not api_key:
        raise ValueError(
            "AZURE_OPENAI_API_KEY environment variable is required when LLM_PROVIDER=azure"
        )
    
    if not endpoint:
        raise ValueError(
            "AZURE_OPENAI_ENDPOINT environment variable is required when LLM_PROVIDER=azure"
        )
    
    if not deployment:
        raise ValueError(
            "AZURE_OPENAI_DEPLOYMENT_NAME environment variable is required when LLM_PROVIDER=azure"
        )
    
    print(f"🔧 Initializing Azure OpenAI:")
    print(f"   Endpoint: {endpoint}")
    print(f"   Deployment: {deployment}")
    print(f"   API Version: {api_version}")
    print(f"   Temperature: {temperature}")
    
    return AzureChatOpenAI(
        azure_endpoint=endpoint,
        azure_deployment=deployment,
        api_key=api_key,
        api_version=api_version,
        temperature=temperature,
        **kwargs
    )


def get_provider_info() -> dict:
    """
    Get information about the configured LLM provider.
    
    Returns:
        Dictionary with provider information
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if provider == "azure":
        return {
            "provider": "azure",
            "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", "not_configured"),
            "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "not_configured"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            "configured": bool(
                os.getenv("AZURE_OPENAI_API_KEY") and
                os.getenv("AZURE_OPENAI_ENDPOINT") and
                os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
            )
        }
    else:
        return {
            "provider": "openai",
            "configured": bool(os.getenv("OPENAI_API_KEY"))
        }


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    print("LLM Provider Configuration:")
    print("-" * 50)
    
    info = get_provider_info()
    print(f"Provider: {info['provider']}")
    print(f"Configured: {info['configured']}")
    
    if info['provider'] == 'azure':
        print(f"Endpoint: {info['endpoint']}")
        print(f"Deployment: {info['deployment']}")
        print(f"API Version: {info['api_version']}")
    
    print("\nTesting LLM initialization...")
    try:
        llm = get_llm()
        print(f"✓ LLM initialized successfully: {type(llm).__name__}")
    except Exception as e:
        print(f"✗ Error initializing LLM: {e}")
