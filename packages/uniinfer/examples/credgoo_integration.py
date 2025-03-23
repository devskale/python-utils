#!/usr/bin/env python3
"""
Comprehensive example demonstrating how to use uniinfer with credgoo for API key management.

This example shows how to:
1. Use credgoo to retrieve API keys securely
2. Initialize different providers using those keys
3. Make chat completion requests with the providers
4. Handle fallbacks if a provider is unavailable

Requirements:
- uniinfer package
- credgoo package
"""
from uniinfer.errors import UniInferError
from uniinfer import (
    ChatMessage,
    ChatCompletionRequest,
    ProviderFactory,
    ChatProvider,
    FallbackStrategy
)
import sys
import os
import argparse
from typing import Optional, List, Dict, Any

# Add the parent directory to the Python path to make the uniinfer package importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import uniinfer components

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
    if api_key is None and HAS_CREDGOO and provider_name != "ollama":  # Ollama doesn't need an API key
        try:
            # This will automatically use cached keys if available
            api_key = get_api_key(provider_name)
            print(f"Using API key from credgoo for {provider_name}")
        except Exception as e:
            print(f"Failed to get API key from credgoo: {str(e)}")
            if provider_name != "ollama":  # Only prompt for key if not ollama
                api_key = input(f"Enter your {provider_name} API key: ")
    elif api_key is None and provider_name != "ollama":
        # If credgoo is not available, prompt for API key
        api_key = input(f"Enter your {provider_name} API key: ")

    # Initialize the provider with the API key
    return ProviderFactory.get_provider(provider_name, api_key=api_key, **kwargs)


def run_chat_completion(provider: ChatProvider, model: str, prompt: str) -> Dict[str, Any]:
    """
    Run a simple chat completion with the given provider and model.

    Args:
        provider: The provider instance
        model: The model to use
        prompt: The user prompt

    Returns:
        Dict: A dictionary containing the response and metadata
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
        return {
            "success": True,
            "content": response.message.content,
            "provider": response.provider,
            "model": response.model,
            "usage": response.usage
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def create_fallback_strategy() -> FallbackStrategy:
    """
    Create a fallback strategy with multiple providers.

    Returns:
        FallbackStrategy: A configured fallback strategy
    """
    providers = []

    # Try to add OpenAI provider
    try:
        openai_provider = get_provider_with_credgoo("openai")
        providers.append((openai_provider, "gpt-3.5-turbo"))
    except Exception as e:
        print(f"Failed to initialize OpenAI provider: {e}")

    # Try to add Anthropic provider
    try:
        anthropic_provider = get_provider_with_credgoo("anthropic")
        providers.append((anthropic_provider, "claude-instant-1"))
    except Exception as e:
        print(f"Failed to initialize Anthropic provider: {e}")

    # Try to add Ollama provider as a fallback (doesn't require API key)
    try:
        ollama_provider = get_provider_with_credgoo(
            "ollama", base_url="http://localhost:11434")
        providers.append((ollama_provider, "llama2"))
    except Exception as e:
        print(f"Failed to initialize Ollama provider: {e}")

    # Create and return the fallback strategy
    return FallbackStrategy(providers)


def test_single_provider(provider_name: str, model: str, prompt: str):
    """
    Test a single provider with the given model and prompt.

    Args:
        provider_name: The name of the provider
        model: The model to use
        prompt: The user prompt
    """
    print(f"\n=== Testing {provider_name} with model {model} ===")

    try:
        # Get provider instance with credgoo
        provider = get_provider_with_credgoo(provider_name)

        # Run chat completion
        print("Sending prompt:", prompt)
        response = run_chat_completion(provider, model, prompt)

        if response["success"]:
            print("\nResponse:")
            print(response["content"])
            print(
                f"\nProvider: {response['provider']}, Model: {response['model']}")
            print(f"Usage: {response['usage']}")
        else:
            print(f"\nError: {response['error']}")
    except Exception as e:
        print(f"Failed to test {provider_name}: {e}")

    print("\n" + "-" * 80)


def test_fallback_strategy(prompt: str):
    """
    Test the fallback strategy with the given prompt.

    Args:
        prompt: The user prompt
    """
    print("\n=== Testing Fallback Strategy ===")

    try:
        # Create fallback strategy
        strategy = create_fallback_strategy()

        # Create request
        messages = [ChatMessage(role="user", content=prompt)]
        request = ChatCompletionRequest(
            messages=messages, temperature=0.7, max_tokens=500)

        # Run completion with fallback strategy
        print("Sending prompt with fallback strategy:", prompt)
        response = strategy.complete(request)

        print("\nResponse:")
        print(response.message.content)
        print(f"\nProvider: {response.provider}, Model: {response.model}")
        print(f"Usage: {response.usage}")
    except UniInferError as e:
        print(f"All providers failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    print("\n" + "-" * 80)


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Test uniinfer with credgoo for API key management")
    parser.add_argument("--provider", help="Specific provider to test")
    parser.add_argument("--model", help="Specific model to use")
    parser.add_argument("--prompt", default="Explain how to use API keys securely in Python applications.",
                        help="Prompt to send to the LLM")
    parser.add_argument("--fallback", action="store_true",
                        help="Test fallback strategy")
    args = parser.parse_args()

    # Print available providers
    print("Available providers:", ProviderFactory.list_providers())

    # If specific provider is requested
    if args.provider:
        model = args.model or get_default_model(args.provider)
        test_single_provider(args.provider, model, args.prompt)
    elif args.fallback:
        # Test fallback strategy
        test_fallback_strategy(args.prompt)
    else:
        # Default: test multiple providers
        providers_to_try = [
            {"name": "openai", "model": "gpt-3.5-turbo"},
            {"name": "anthropic", "model": "claude-instant-1"},
            # Add more providers as needed
        ]

        for provider_config in providers_to_try:
            test_single_provider(
                provider_config["name"], provider_config["model"], args.prompt)

        # Also test fallback strategy
        test_fallback_strategy(args.prompt)


def get_default_model(provider_name: str) -> str:
    """
    Get a default model for the given provider.

    Args:
        provider_name: The name of the provider

    Returns:
        str: A default model name
    """
    defaults = {
        "openai": "gpt-3.5-turbo",
        "anthropic": "claude-instant-1",
        "ollama": "llama2",
        "mistral": "mistral-tiny",
        "cohere": "command",
        "gemini": "gemini-pro",
        "groq": "llama2-70b-4096",
        "openrouter": "openai/gpt-3.5-turbo"
    }

    return defaults.get(provider_name, "default")


if __name__ == "__main__":
    main()
