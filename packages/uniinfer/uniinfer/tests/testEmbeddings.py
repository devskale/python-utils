#!/usr/bin/env python3
"""
Modern OpenAI-style test script for embedding endpoints.
Tests embedding functionality using the official OpenAI Python client.
"""
from openai import OpenAI
import os
from typing import List, Optional

BASE_URL = "https://amd1.mooo.com:8123/v1"
# BASE_URL = "http://localhost:8123/v1"


def create_client(api_key: str = "test23@test34", base_url: str = BASE_URL) -> OpenAI:
    """
    Create and configure OpenAI client with custom endpoint.

    Args:
        api_key: API key for authentication
        base_url: Base URL for the API endpoint

    Returns:
        Configured OpenAI client instance
    """
    return OpenAI(
        api_key=api_key,
        base_url=base_url
    )


def test_embedding(client: OpenAI, model: str, text: str) -> Optional[dict]:
    """
    Test embedding generation with a specific model.

    Args:
        client: OpenAI client instance
        model: Model name to use for embedding
        text: Text to embed

    Returns:
        Embedding response or None if failed
    """
    try:
        response = client.embeddings.create(
            model=model,
            input=[text],  # Input should be a list
            # Explicit encoding format (modern practice)
            encoding_format="float"
        )

        print(f"  ✅ {model} ({len(response.data[0].embedding)}d)")
        return response.model_dump()

    except Exception as e:
        print(f"  ❌ {model}: {str(e).split(':')[-1].strip()}")
        return None


def test_multiple_texts(client: OpenAI, model: str, texts: List[str]) -> Optional[dict]:
    """
    Test embedding generation with multiple texts (batch processing).

    Args:
        client: OpenAI client instance
        model: Model name to use for embedding
        texts: List of texts to embed

    Returns:
        Embedding response or None if failed
    """
    try:
        response = client.embeddings.create(
            model=model,
            input=texts,
            encoding_format="float"
        )

        print(
            f"✅ Batch: {len(texts)} texts → {len(response.data)} embeddings ({len(response.data[0].embedding)}d)")
        return response.model_dump()

    except Exception as e:
        print(f"❌ Batch failed: {str(e).split(':')[-1].strip()}")
        return None


def test_detailed_response(client: OpenAI, model: str, text: str) -> Optional[dict]:
    """
    Test embedding generation with detailed response analysis.

    Args:
        client: OpenAI client instance
        model: Model name to use for embedding
        text: Text to embed

    Returns:
        Embedding response or None if failed
    """
    try:
        response = client.embeddings.create(
            model=model,
            input=[text],
            encoding_format="float"
        )

        # Analyze response structure
        response_dict = response.model_dump()

        print(f"\n📊 Detailed Response Analysis for {model}:")
        print(f"  Model: {response_dict.get('model', 'N/A')}")
        print(f"  Object: {response_dict.get('object', 'N/A')}")
        print(f"  Data entries: {len(response_dict.get('data', []))}")

        if response_dict.get('data'):
            first_embedding = response_dict['data'][0]
            print(
                f"  Embedding dimensions: {len(first_embedding.get('embedding', []))}")
            print(
                f"  Embedding object: {first_embedding.get('object', 'N/A')}")
            print(f"  Index: {first_embedding.get('index', 'N/A')}")

        # Check for usage/token information
        usage = response_dict.get('usage')
        if usage:
            print(f"  Usage found:")
            print(f"    Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
            print(f"    Total tokens: {usage.get('total_tokens', 'N/A')}")
            if 'completion_tokens' in usage:
                print(
                    f"    Completion tokens: {usage.get('completion_tokens')}")
        else:
            print(f"  Usage: None (no token count available)")

        return response_dict

    except Exception as e:
        print(f"❌ Detailed test failed: {str(e)}")
        return None


def main():
    """
    Main function to test embedding functionality.
    """
    # Create client using modern OpenAI style
    client = create_client()

    # Test models (based on your server setup)
    test_models = [
        "ollama@nomic-embed-text",
        "ollama@jina/jina-embeddings-v2-base-de:latest",
        "ollama@embeddinggemma:latest",
        "ollama@dengcao/Qwen3-Embedding-0.6B:Q8_0",
        "tu@e5-mistral-7b"
    ]

    # Test embedding models
    test_text = "Artificial intelligence and machine learning have revolutionized numerous industries by enabling computers to learn from data and make intelligent decisions without explicit programming. These technologies are transforming healthcare through diagnostic imaging, finance through algorithmic trading, transportation through autonomous vehicles, and communication through natural language processing. The rapid advancement in neural networks, particularly deep learning architectures, has unlocked unprecedented capabilities in pattern recognition, language understanding, and predictive analytics."
    successful_models = []

    print(f"Testing {len(test_models)} models...")
    for model in test_models:
        result = test_embedding(client, model, test_text)
        if result:
            successful_models.append(model)

    # Detailed response analysis on all successful models
    if successful_models:
        print(
            f"\n🔍 Running detailed analysis on all {len(successful_models)} models...")
        detailed_test_text = "This is a shorter test text for detailed API response analysis."
        for model in successful_models:
            test_detailed_response(client, model, detailed_test_text)

        # Batch test with all successful models
        batch_texts = [
            "Climate change represents one of the most pressing challenges of our time, requiring immediate global action to reduce greenhouse gas emissions and transition to renewable energy sources. The scientific consensus is clear that human activities are the primary driver of current climate change.",
            "Quantum computing promises to revolutionize computational capabilities by leveraging quantum mechanical phenomena such as superposition and entanglement. This technology could potentially solve complex problems in cryptography, drug discovery, and optimization that are intractable for classical computers.",
            "The development of sustainable urban planning involves creating cities that balance economic growth, environmental protection, and social equity. Smart city initiatives integrate technology with infrastructure to improve quality of life while reducing resource consumption and environmental impact."
        ]
        print(f"\nBatch testing {len(successful_models)} models:")
        for model in successful_models:
            print(f"  {model}: ", end="")
            test_multiple_texts(client, model, batch_texts)
    else:
        print("\n❌ No working models")


if __name__ == "__main__":
    main()
