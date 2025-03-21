import requests
import base64
import argparse
import os
import sys
import json
import time
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

def cache_api_key(service, api_key, cache_dir):
    """Store API key in service-specific cache file."""
    try:
        # Ensure directory exists
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create cache data with service information
        cache_data = {
            "service": service,
            "api_key": api_key,
            "timestamp": str(int(time.time()))
        }
        
        # Define cache file path - now using JSON format
        cache_file = cache_dir / 'api_keys.json'
        
        # Load existing cache if it exists
        existing_cache = {}
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    existing_cache = json.load(f)
            except json.JSONDecodeError:
                # If file is corrupt, start with empty cache
                existing_cache = {}
        
        # Update cache with new key
        existing_cache[service] = cache_data
        
        # Write updated cache to file
        with open(cache_file, 'w') as f:
            json.dump(existing_cache, f, indent=2)
        
        # Set restrictive permissions
        os.chmod(cache_file, 0o600)  # Read/write for owner only
        print(f"API key for {service} cached in {cache_file}")
    except Exception as e:
        print(f"Warning: Failed to cache API key: {e}")

def get_cached_api_key(service, cache_dir):
    """Retrieve API key for specific service from cache."""
    cache_file = cache_dir / 'api_keys.json'
    
    if not cache_file.exists():
        return None
    
    try:
        with open(cache_file, 'r') as f:
            cache = json.load(f)
        
        # Check if requested service exists in cache
        if service in cache:
            cached_key = cache[service].get("api_key")
            if cached_key:
                print(f"Using cached API key for {service}")
                return cached_key
    except Exception as e:
        print(f"Warning: Failed to read cached API key: {e}")
    
    return None

def store_credentials(token, encryption_key, url, cred_file):
    """Store authentication credentials and URL securely."""
    try:
        # Ensure directory exists
        cred_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create credentials dictionary
        credentials = {
            "token": token,
            "encryption_key": encryption_key,
            "url": url
        }
        
        # Write credentials to file
        with open(cred_file, 'w') as f:
            json.dump(credentials, f)
        
        # Set restrictive permissions
        os.chmod(cred_file, 0o600)  # Read/write for owner only
        print(f"Credentials stored in {cred_file}")
    except Exception as e:
        print(f"Warning: Failed to store credentials: {e}")

def load_credentials(cred_file):
    """Load authentication credentials and URL from file."""
    try:
        if cred_file.exists():
            with open(cred_file, 'r') as f:
                credentials = json.load(f)
            return credentials.get("token"), credentials.get("encryption_key"), credentials.get("url")
        return None, None, None
    except Exception as e:
        print(f"Warning: Failed to load credentials: {e}")
        return None, None, None

def get_api_key(service, bearer_token=None, encryption_key=None, api_url=None, cache_dir=None, no_cache=False):
    """
    Get API key with service-specific caching support.
    First checks for a cached key, then falls back to Google Sheets if needed.
    This function can be imported and used in other Python scripts.
    """
    # Set default cache directory if not provided
    if cache_dir is None:
        cache_dir = Path.home() / '.config' / 'api_keys'
    else:
        cache_dir = Path(cache_dir)
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    cred_file = cache_dir / 'credgoo.txt'
    
    # Handle credentials
    if not bearer_token or not encryption_key:
        stored_token, stored_key, stored_url = load_credentials(cred_file)
        bearer_token = bearer_token or stored_token
        encryption_key = encryption_key or stored_key
        api_url = api_url or stored_url
        
        if not bearer_token or not encryption_key:
            print("Error: Bearer token and encryption key are required.")
            return None
    else:
        # Store new credentials when provided
        store_credentials(bearer_token, encryption_key, api_url, cred_file)
    
    # Check cache first unless no_cache is specified
    if not no_cache:
        cached_key = get_cached_api_key(service, cache_dir)
        if cached_key:
            return cached_key
    
    # If no cached key for this service, get from Google Sheets
    api_key = get_api_key_from_google(service, bearer_token, encryption_key, api_url)
    
    # Cache the key if retrieval was successful
    if api_key:
        cache_api_key(service, api_key, cache_dir)
    
    return api_key

def main():
    parser = argparse.ArgumentParser(description="Retrieve API keys securely with caching")
    parser.add_argument("service", help="Service name to retrieve the API key for")
    parser.add_argument("--token", help="Bearer token for authentication")
    parser.add_argument("--key", help="Encryption key for decryption")
    parser.add_argument("--url", help="URL of the Google Apps Script web app")
    parser.add_argument("--cache-dir", help="Directory to store cached API keys (default: ~/.config/api_keys/)")
    parser.add_argument("--no-cache", action="store_true", help="Bypass cache and force retrieval from source")
    
    args = parser.parse_args()
    
    print("Starting API key retrieval...")
    
    # Determine cache directory
    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    
    # Get API key using the more flexible function
    api_key = get_api_key(
        args.service,
        bearer_token=args.token,
        encryption_key=args.key,
        api_url=args.url,
        cache_dir=cache_dir,
        no_cache=args.no_cache
    )
    
    if api_key:
        print(f"API Key for {args.service}: {api_key}")
        return 0
    else:
        print("Failed to retrieve API key")
        return 1

# This allows the script to be both imported as a module and run as a command-line tool
if __name__ == "__main__":
    sys.exit(main())