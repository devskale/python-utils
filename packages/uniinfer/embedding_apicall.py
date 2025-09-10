#!/usr/bin/env python3
"""
Simple test script for Ollama embeddings via the UniIOAI proxy server.
"""
import requests
import json


def main():
    # Proxy server URL
    base_url = "http://localhost:8123"

    # Test data
    model = "ollama@nomic-embed-text"
    text = "Hello world"

    # Prepare the request payload
    payload = {
        "model": model,
        "input": [text]
    }

    # Make the request (no auth header for Ollama)
    response = requests.post(
        f"{base_url}/v1/embeddings",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload)
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200:
        data = response.json()
        print("\nSuccess!")
        print(f"Model: {data.get('model')}")
        print(f"Number of embeddings: {len(data.get('data', []))}")
        if data.get('data'):
            embedding = data['data'][0]['embedding']
            print(f"Embedding dimensions: {len(embedding)}")
            print(f"First 5 values: {embedding[:5]}")
    else:
        print("Error occurred!")


if __name__ == "__main__":
    main()
