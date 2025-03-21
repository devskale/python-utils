import requests
import base64
import argparse
import os
import sys
from pathlib import Path

def decrypt_key(encrypted_key, encryption_key):
    """Decrypt the API key using the encryption key."""
    try:
        # Decode the base64 string
        decoded = base64.b64decode(encrypted_key).decode('utf-8', errors='replace')
        
        # Perform XOR decryption with key
        result = ""
        for i in range(len(decoded)):
            # Match the encryption algorithm's key usage pattern
            key_char = ord(encryption_key[(i * 7) % len(encryption_key)])
            decoded_char = ord(decoded[i])
            result += chr(decoded_char ^ key_char)
        
        # Remove the 8-character initialization vector
        if len(result) > 8:
            return result[8:]
        else:
            print("Warning: Decrypted result too short")
            return result
    except Exception as e:
        print(f"Decryption error: {e}")
        return None

def get_api_key_from_google(service, bearer_token, encryption_key, api_url=None):
    """Retrieve and decrypt an API key for the specified service from Google Sheets."""
    # Use provided URL or fall back to default
    url = api_url or "https://script.google.com/macros/s/AKfycbxMGfhXS9GNFyoMtwXNryXykxZ0sWXgPv_R4MTyiXOQNexfRzzly64c5IDjLAm8rGczww/exec"
    
    print(f"Fetching key for service: {service} from Google Sheets")
    print(f"Using URL: {url}")
    
    params = {
        "service": service,
        "token": bearer_token
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") == "success":
                encrypted_key = data.get("encryptedKey")
                if encrypted_key:
                    api_key = decrypt_key(encrypted_key, encryption_key)
                    return api_key
                else:
                    print("Error: No encrypted key in response")
            else:
                print(f"Error: {data.get('message', 'Unknown error')}")
        else:
            print(f"Error: Failed to retrieve key (Status code: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    
    return None

def cache_api_key(api_key, cache_file):
    """Store API key in local cache file."""
    try:
        # Ensure directory exists
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write API key to file
        with open(cache_file, 'w') as f:
            f.write(api_key)
        
        # Set restrictive permissions
        os.chmod(cache_file, 0o600)  # Read/write for owner only
        print(f"API key cached in {cache_file}")
    except Exception as e:
        print(f"Warning: Failed to cache API key: {e}")

def get_api_key(service, bearer_token, encryption_key, api_url=None, cache_dir=None):
    """
    Get API key with caching support.
    First checks for a cached key, then falls back to Google Sheets if needed.
    """
    # Set default cache directory if not provided
    if cache_dir is None:
        cache_dir = Path.home() / '.config' / 'api_keys'
    else:
        cache_dir = Path(cache_dir)
    
    # Define cache file path
    cache_file = cache_dir / 'api.key'
    
    # Check for cached key
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                cached_key = f.read().strip()
                
            if cached_key:
                print(f"Using API key from cache: {cache_file}")
                return cached_key
        except Exception as e:
            print(f"Warning: Failed to read cached API key: {e}")
    
    # If no cached key, get from Google Sheets
    api_key = get_api_key_from_google(service, bearer_token, encryption_key, api_url)
    
    # Cache the key if retrieval was successful
    if api_key:
        cache_api_key(api_key, cache_file)
    
    return api_key

def main():
    parser = argparse.ArgumentParser(description="Retrieve API keys securely with caching")
    parser.add_argument("service", help="Service name to retrieve the API key for")
    parser.add_argument("--token", required=True, help="Bearer token for authentication")
    parser.add_argument("--key", required=True, help="Encryption key for decryption")
    parser.add_argument("--url", help="URL of the Google Apps Script web app")
    parser.add_argument("--cache-dir", help="Directory to store cached API keys (default: ~/.config/api_keys/)")
    parser.add_argument("--no-cache", action="store_true", help="Bypass cache and force retrieval from source")
    
    args = parser.parse_args()
    
    print("Starting API key retrieval...")
    
    if args.no_cache:
        # Force retrieval from Google Sheets
        api_key = get_api_key_from_google(args.service, args.token, args.key, args.url)
        # Update cache with new key
        if api_key and not args.no_cache:
            cache_dir = args.cache_dir or (Path.home() / '.config' / 'api_keys')
            cache_file = Path(cache_dir) / 'api.key'
            cache_api_key(api_key, cache_file)
    else:
        # Use caching logic
        api_key = get_api_key(args.service, args.token, args.key, args.url, args.cache_dir)
    
    if api_key:
        print(f"API Key for {args.service}: {api_key}")
        return 0
    else:
        print("Failed to retrieve API key")
        return 1

if __name__ == "__main__":
    sys.exit(main())