import requests
import json
import os

# Test script for multiple embedding providers
baseurl = 'http://localhost:8123/v1'

# IMPORTANT: Use the same auth format as uniioai_apicall.py
# This should be your credgoo token in format: bearer_token@encryption_key
api_key = "test23@test34"  # Same as uniioai_apicall.py

# Test data
texts = ["Hello world", "This is a test sentence",
         "Embeddings are useful for AI"]

# Models to test
models_to_test = [
    {
        "name": "Ollama (nomic-embed-text)",
        "model": "ollama@nomic-embed-text",
        "requires_auth": False
    },
    {
        "name": "TU AI (e5-mistral-7b)",
        "model": "tu@e5-mistral-7b",
        "requires_auth": True
    }
]


def test_embedding_model(model_config, texts, api_key):
    """Test a specific embedding model"""
    print(f"\n{'='*50}")
    print(f"Testing: {model_config['name']}")
    print(f"Model: {model_config['model']}")
    print(f"Requires Auth: {model_config['requires_auth']}")
    print(f"{'='*50}")

    # Prepare headers
    headers = {"Content-Type": "application/json"}

    # Add authorization if required (using same format as uniioai_apicall.py)
    if model_config['requires_auth']:
        if not api_key:
            print("❌ API key not provided")
            return

        headers["Authorization"] = f"Bearer {api_key}"
        # Show first 10 chars for security
        print(f"Using API key: {api_key[:10]}...")

    # Make the request
    payload = {
        "model": model_config['model'],
        "input": texts
    }

    print(f"Sending {len(texts)} texts to embed...")
    print(f"Sample text: '{texts[0]}'")

    try:
        response = requests.post(
            f"{baseurl}/embeddings",
            headers=headers,
            json=payload,
            timeout=30
        )

        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")

            # Print response details
            print(f"Model: {result.get('model')}")
            print(f"Data length: {len(result.get('data', []))}")
            print(f"Usage: {result.get('usage', {})}")

            if result.get('data'):
                first_item = result['data'][0]
                embedding = first_item.get('embedding', [])
                print(f"Embedding dimensions: {len(embedding)}")
                print(
                    f"First 5 values: {embedding[:5] if len(embedding) >= 5 else embedding}")
                print(f"Embedding type: {type(embedding)}")

                # Test all embeddings
                for i, item in enumerate(result['data']):
                    emb = item.get('embedding', [])
                    print(f"  Text {i+1}: {len(emb)} dimensions")
            else:
                print("❌ No embedding data in response")

        elif response.status_code == 401:
            print("❌ Authentication failed")
            print(
                "Make sure your credgoo token format is correct: bearer_token@encryption_key")

        elif response.status_code == 400:
            print("❌ Bad request")
            print(f"Error details: {response.text}")

        else:
            print(f"❌ HTTP {response.status_code}")
            print(f"Error: {response.text}")

    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the proxy server running?")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def main():
    print("🚀 Testing Multiple Embedding Providers")
    print(f"Proxy server: {baseurl}")
    print(f"API Key: {api_key[:10]}..." if api_key else "No API key")
    print(f"Number of texts to embed: {len(texts)}")

    for model_config in models_to_test:
        test_embedding_model(model_config, texts, api_key)

    print(f"\n{'='*50}")
    print("Testing complete!")
    print("Note: Make sure the proxy server is running with: python -m uniinfer.uniioai_proxy")


if __name__ == "__main__":
    main()
