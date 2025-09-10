#!/usr/bin/env python3
"""
Test script for comparing Ollama and TU embedding providers.
"""
from uniinfer import EmbeddingProviderFactory, EmbeddingRequest


def test_provider(provider_name, model_name, texts, base_url=None):
    """Test an embedding provider with given texts."""
    print(f"\n=== Testing {provider_name.upper()} Provider ===")
    print(f"Model: {model_name}")

    try:
        # Get the embedding provider
        kwargs = {}
        if base_url:
            kwargs['base_url'] = base_url

        provider = EmbeddingProviderFactory.get_provider(
            provider_name, **kwargs)

        # Create embedding request
        request = EmbeddingRequest(
            input=texts,
            model=model_name
        )

        # Get embeddings
        response = provider.embed(request)

        print(f"Provider: {response.provider}")
        print(f"Number of embeddings: {len(response.data)}")
        print(f"Usage: {response.usage}")

        for i, embedding_data in enumerate(response.data):
            print(f"\nText {i+1}: '{texts[i]}'")
            print(f"Embedding dimensions: {len(embedding_data['embedding'])}")
            print(f"First 5 values: {embedding_data['embedding'][:5]}")
            if len(embedding_data['embedding']) > 5:
                print(f"Last 5 values: {embedding_data['embedding'][-5:]}")

        return True

    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    # Test texts
    test_texts = [
        "Hello world",
        "This is a test sentence",
        "Machine learning is fascinating"
    ]

    print("Comparing Embedding Providers")
    print("=" * 50)

    # Test Ollama provider
    success_ollama = test_provider(
        "ollama",
        "nomic-embed-text:latest",
        test_texts,
        base_url="https://amp1.mooo.com:11444"
    )

    # Test TU provider
    success_tu = test_provider(
        "tu",
        "e5-mistral-7b",
        test_texts
    )

    print("\n" + "=" * 50)
    print("Summary:")
    print(f"Ollama: {'✓ Success' if success_ollama else '✗ Failed'}")
    print(f"TU: {'✓ Success' if success_tu else '✗ Failed'}")


if __name__ == '__main__':
    main()
