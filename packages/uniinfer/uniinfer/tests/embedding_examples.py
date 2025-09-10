#!/usr/bin/env python3
"""
Example script showing how to use Ollama and TU embedding providers.
"""
from uniinfer import EmbeddingProviderFactory, EmbeddingRequest


def example_ollama_embeddings():
    """Example using Ollama embeddings."""
    print("=== Ollama Embeddings Example ===")

    # Get the Ollama embedding provider
    provider = EmbeddingProviderFactory.get_provider(
        'ollama',
        base_url='https://amp1.mooo.com:11444'  # Your Ollama endpoint
    )

    # Create embedding request
    request = EmbeddingRequest(
        input=['Hello world', 'How are you?'],
        model='nomic-embed-text:latest'
    )

    # Get embeddings
    response = provider.embed(request)

    print(f"Model: {response.model}")
    print(f"Embeddings created: {len(response.data)}")
    print(f"Dimensions: {len(response.data[0]['embedding'])}")
    print(f"Usage: {response.usage}")


def example_tu_embeddings():
    """Example using TU embeddings."""
    print("\n=== TU Embeddings Example ===")

    # Note: TU requires an API key
    # You would get this from your TU AI credentials
    api_key = "your_tu_api_key_here"  # Replace with actual key

    if api_key == "your_tu_api_key_here":
        print("Please set your TU API key to run this example")
        return

    # Get the TU embedding provider
    provider = EmbeddingProviderFactory.get_provider(
        'tu',
        api_key=api_key
    )

    # Create embedding request
    request = EmbeddingRequest(
        input=['Hello world', 'How are you?'],
        model='e5-mistral-7b'
    )

    # Get embeddings
    response = provider.embed(request)

    print(f"Model: {response.model}")
    print(f"Embeddings created: {len(response.data)}")
    print(f"Dimensions: {len(response.data[0]['embedding'])}")
    print(f"Usage: {response.usage}")


def example_cli_usage():
    """Show CLI usage examples."""
    print("\n=== CLI Usage Examples ===")

    print("# Ollama embeddings:")
    print('python -m uniinfer.uniinfer_cli -p ollama --embed --embed-text "Hello world" --model nomic-embed-text:latest')
    print()
    print("# TU embeddings (requires API key):")
    print('python -m uniinfer.uniinfer_cli -p tu --embed --embed-text "Hello world" --model e5-mistral-7b')
    print()
    print("# Multiple texts:")
    print('python -m uniinfer.uniinfer_cli -p ollama --embed --embed-text "Text 1" --embed-text "Text 2" --model nomic-embed-text:latest')


if __name__ == '__main__':
    example_ollama_embeddings()
    example_tu_embeddings()
    example_cli_usage()
