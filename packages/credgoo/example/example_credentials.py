# Import the get_api_key function from your package
from credgoo import get_api_key

def main():
    # Option 1: With previously stored credentials
    api_key = get_api_key("ollamatest")
    if api_key:
        print(f"Retrieved API key: {api_key}")
        # Use the API key in your application
        call_api_with_key(api_key)
    else:
        print("Failed to retrieve API key")

    # Option 2: First-time setup with explicit credentials
    # api_key = get_api_key( insta
    #     service="ollama",
    #     bearer_token="YOUR_TOKEN",
    #     encryption_key="YOUR_ENCRYPTION_KEY",
    #     api_url="YOUR_URL"  # Optional
    # )

def call_api_with_key(api_key):
    # Your API call implementation
    pass

if __name__ == "__main__":
    main()