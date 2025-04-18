import requests
import base64
import argparse
import os
import sys
import json
import time
from pathlib import Path


save_key = False
save_token = False
save_url = True


def decrypt_key(encrypted_key, encryption_key):
    """Decrypt the API key using the encryption key."""
    try:
        # Decode the base64 string
        decoded = base64.b64decode(encrypted_key).decode(
            'utf-8', errors='replace')

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


def encrypt_local_key(api_key, encryption_key):
    """Encrypt the API key for local caching using XOR and Base64."""
    try:
        encrypted_bytes = bytearray()
        key_bytes = encryption_key.encode('utf-8')
        key_len = len(key_bytes)
        for i, char_code in enumerate(api_key.encode('utf-8')):
            key_char_code = key_bytes[i % key_len]
            encrypted_bytes.append(char_code ^ key_char_code)
        return base64.b64encode(encrypted_bytes).decode('utf-8')
    except Exception as e:
        print(f"Local encryption error: {e}")
        return None


def decrypt_local_key(encrypted_api_key, encryption_key):
    """Decrypt the locally cached API key using XOR."""
    try:
        encrypted_bytes = base64.b64decode(encrypted_api_key)
        decrypted_bytes = bytearray()
        key_bytes = encryption_key.encode('utf-8')
        key_len = len(key_bytes)
        for i, byte_val in enumerate(encrypted_bytes):
            key_char_code = key_bytes[i % key_len]
            decrypted_bytes.append(byte_val ^ key_char_code)
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        print(f"Local decryption error: {e}")
        return None


def get_api_key_from_google(service, bearer_token, encryption_key, api_url=None):
    """Retrieve and decrypt an API key for the specified service from Google Sheets."""
    # Use provided URL or fall back to default
    url = api_url

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
            print(
                f"Error: Failed to retrieve key (Status code: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")

    return None


def cache_api_key(service, api_key, encryption_key, cache_dir):
    """Store encrypted API key in service-specific cache file."""
    if not encryption_key:
        print("Warning: Cannot cache API key without an encryption key.")
        return

    encrypted_key_for_cache = encrypt_local_key(api_key, encryption_key)
    if not encrypted_key_for_cache:
        print("Warning: Failed to encrypt API key for caching.")
        return

    try:
        # Ensure directory exists
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Create cache data with service information and encrypted key
        cache_data = {
            "service": service,
            "api_key": encrypted_key_for_cache,
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
        print(f"API key for {service} cached (encrypted) in {cache_file}")
    except Exception as e:
        print(f"Warning: Failed to cache API key: {e}")


def get_cached_api_key(service, encryption_key, cache_dir):
    """Retrieve and decrypt API key for specific service from cache."""
    if not encryption_key:
        print("Warning: Cannot decrypt cached key without an encryption key.")
        return None

    cache_file = cache_dir / 'api_keys.json'

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, 'r') as f:
            cache = json.load(f)

        # Check if requested service exists in cache
        if service in cache:
            encrypted_cached_key = cache[service].get("api_key")
            if encrypted_cached_key:
                # Decrypt the key
                decrypted_key = decrypt_local_key(
                    encrypted_cached_key, encryption_key)
                if decrypted_key:
                    print(f"Cache Hit ", end="")
                    return decrypted_key
                else:
                    print(
                        f"Warning: Failed to decrypt cached key for {service}.")
            else:
                print(
                    f"Warning: No 'api_key' field found in cache for {service}.")

    except Exception as e:
        print(f"Warning: Failed to read or decrypt cached API key: {e}")

    return None


def store_credentials(token, encryption_key, url, cred_file, save_token_flag, save_key_flag, save_url_flag):
    """Store authentication credentials and URL securely based on flags."""
    try:
        # Ensure directory exists
        cred_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing credentials if file exists
        credentials = {}
        if cred_file.exists():
            try:
                with open(cred_file, 'r') as f:
                    credentials = json.load(f)
            except json.JSONDecodeError:
                print(
                    f"Warning: Corrupt credentials file {cred_file}. Starting fresh.")
                credentials = {}  # Start fresh if file is corrupt

        # Update credentials dictionary conditionally based on flags
        if save_token_flag and token is not None:
            credentials["token"] = token
        if save_key_flag and encryption_key is not None:
            credentials["encryption_key"] = encryption_key
        if save_url_flag and url is not None:
            credentials["url"] = url

        # Write updated credentials to file only if there's something to write
        if credentials:
            with open(cred_file, 'w') as f:
                json.dump(credentials, f)

            # Set restrictive permissions
            os.chmod(cred_file, 0o600)  # Read/write for owner only
            print(f"Credentials updated in {cred_file}")
        else:
            print("No credentials to store.")

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
    stored_token, stored_key, stored_url = load_credentials(cred_file)

    # Determine if new credentials were provided
    new_token_provided = bearer_token is not None
    new_key_provided = encryption_key is not None
    new_url_provided = api_url is not None

    # Use provided credentials or fall back to stored ones
    final_token = bearer_token if new_token_provided else stored_token
    final_key = encryption_key if new_key_provided else stored_key
    final_url = api_url if new_url_provided else stored_url

    # Store credentials only if new ones were provided and corresponding flags are set
    should_store = (new_token_provided and save_token) or \
                   (new_key_provided and save_key) or \
                   (new_url_provided and save_url)

    if should_store:
        # Pass only the newly provided values (or None) to store_credentials
        # along with the flags to control which ones get saved.
        store_credentials(
            bearer_token if new_token_provided else None,
            encryption_key if new_key_provided else None,
            api_url if new_url_provided else None,
            cred_file,
            save_token,
            save_key,
            save_url
        )

    # Use the final determined credentials for the API call
    if not final_token or not final_key:
        print("Error: Bearer token and encryption key are required (either provided or stored).")
        return None

    # Check cache first unless no_cache is specified
    if not no_cache:
        cached_key = get_cached_api_key(service, final_key, cache_dir)
        if cached_key:
            return cached_key

    # If no cached key for this service, get from Google Sheets using final credentials
    api_key = get_api_key_from_google(
        service, final_token, final_key, final_url)

    # Cache the key if retrieval was successful
    if api_key and not no_cache:
        cache_api_key(service, api_key, final_key, cache_dir)

    return api_key


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve API keys securely with caching")
    parser.add_argument(
        "service", help="Service name to retrieve the API key for")
    parser.add_argument("--token", help="Bearer token for authentication")
    parser.add_argument("--key", help="Encryption key for decryption")
    parser.add_argument("--url", help="URL of the Google Apps Script web app")
    parser.add_argument(
        "--cache-dir", help="Directory to store cached API keys (default: ~/.config/api_keys/)")
    parser.add_argument("--no-cache", action="store_true",
                        help="Bypass cache and force retrieval from source")

    args = parser.parse_args()

    # print("Starting API key retrieval...")

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
        print(f" API key {args.service}: {api_key}")
        return 0
    else:
        print("Failed to retrieve API key")
        return 1


# This allows the script to be both imported as a module and run as a command-line tool
if __name__ == "__main__":
    sys.exit(main())
