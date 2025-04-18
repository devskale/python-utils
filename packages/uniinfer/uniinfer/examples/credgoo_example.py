#!/usr/bin/env python3
"""
Example demonstrating how to use uniinfer with credgoo for API key management.

This example shows how to:
1. Use credgoo to retrieve API keys securely
2. Initialize different providers using those keys
3. Make chat completion requests with the providers

Requirements:
- uniinfer package
- credgoo package
"""
import sys
import os
from typing import Optional, List

# Add the parent directory to the Python path to make the uniinfer package importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import uniinfer components
from uniinfer import (
    ChatMessage, 
    ChatCompletionRequest, 
    ProviderFactory,
    ChatProvider
)

# Try to import credgoo for API key management
try:
    from credgoo import get_api_key
    HAS_CREDGOO = True
except ImportError:
    HAS_CREDGOO = False
    print("Warning: credgoo not found, you'll need to provide API keys manually")


def get_provider_with_credgoo(provider_name: str, api_key: Optional[str] = None, **kwargs) -> ChatProvider:
    """
    Get a provider instance using credgoo for API key management if available.
    
    Args:
        provider_name: The name of the provider (e.g., 'openai', 'anthropic')
        api_key: Optional API key to use instead of retrieving from credgoo
        **kwargs: Additional provider-specific arguments
        
    Returns:
        ChatProvider: An initialized provider instance
    """
    # If API key is not provided and credgoo is available, try to get it from credgoo
    if api_key is None and HAS_CREDGOO:
        try:
            # This will automatically use cached keys if available
            api_key = get_api_key(provider_name)
            print(f"Using API key from credgoo for {provider_name}")
        except Exception as e:
            print(f"Failed to get API key from credgoo: {str(e)}")
            api_key = input(f"Enter your {provider_name} API key: ")
    elif api_key is None:
        # If credgoo is not available, prompt for API key
        api_key = input(f"Enter your {provider_name} API key: ")
    
    # Initialize the provider with the API key
    return ProviderFactory.get_provider(provider_name, api_key=api_key, **kwargs)


def run_chat_completion(provider: ChatProvider, model: str, prompt: str) -> str:
    """
    Run a simple chat completion with the given provider and model.
    
    Args:
        provider: The provider instance
        model: The model to use
        prompt: The user prompt
        
    Returns:
        str: The assistant's response
    """
    # Create a simple chat request
    messages = [
        ChatMessage(role="user", content=prompt)
    ]
    
    request = ChatCompletionRequest(
        messages=messages,
        model=model,
        temperature=0.7,
        max_tokens=500
    )
    
    # Make the request
    try:
        response = provider.complete(request)
        return response.message.content
    except Exception as e:
        return f"Error: {str(e)}"


def main():
    # Example providers and models
    providers_to_try = [
        {"name": "openai", "model": "gpt-3.5-turbo"},
        {"name": "anthropic", "model": "claude-instant-1"},
        # Add more providers as needed
    ]
    
    # User prompt
    prompt = "Explain how to use API keys securely in Python applications."
    
    # Try each provider
    for provider_config in providers_to_try:
        provider_name = provider_config["name"]
        model = provider_config["model"]
        
        print(f"\n=== Testing {provider_name} with model {model} ===")
        
        # Get provider instance with credgoo
        provider = get_provider_with_credgoo(provider_name)
        
        # Run chat completion
        print("Sending prompt:", prompt)
        response = run_chat_completion(provider, model, prompt)
        
        print("\nResponse:")
        print(response)
        print("\n" + "-" * 80)


if __name__ == "__main__":
    main()