"""
A OpenAI compliance wrapper for LLM APIs using uniinfer, supporting streaming and non-streaming.
"""
import os
from typing import Optional, List, Dict, Any  # Import Optional, List, Dict, Any
import random  # Import random

from uniinfer import ProviderFactory, ChatMessage, ChatCompletionRequest, ChatCompletionResponse
from uniinfer import EmbeddingProviderFactory, EmbeddingRequest, EmbeddingResponse
from uniinfer.errors import UniInferError, AuthenticationError
from dotenv import load_dotenv
from credgoo import get_api_key
from uniinfer.examples.providers_config import PROVIDER_CONFIGS  # added
# Import the helper functions
from uniinfer.json_utils import update_models, update_model_accessed
# Load environment variables from .env file
dotenv_path = os.path.join(os.getcwd(), '.env')  # Explicitly check current dir
# Add verbose=True and override=True
found_dotenv = load_dotenv(dotenv_path=dotenv_path,
                           verbose=True, override=True)

print(f"DEBUG: Attempted to load .env from: {dotenv_path}")  # Debug print
print(f"DEBUG: .env file found and loaded: {found_dotenv}")  # Debug print


# --- Helper Function for API Key Retrieval ---

# Rename to make it public
def get_provider_api_key(api_bearer_token: str, provider_name: str) -> Optional[str]:
    """
    Determines the provider API key based on the input token format.

    Args:
        api_bearer_token (str): The API token. Can be a direct provider API key
                                or a combined credgoo token ('bearer@encryption').
                                Can be None or empty for providers like Ollama.
        provider_name (str): The name of the provider (e.g., 'openai', 'ollama').

    Returns:
        str | None: The determined provider API key (can be None for providers like Ollama).

    Raises:
        ValueError: If the combined credgoo token format is invalid or api_bearer_token is missing.
        AuthenticationError: If credgoo fails to retrieve a key using a combined token.
    """
    # For Ollama, no authentication is required
    if provider_name == 'ollama':
        return None

    if not api_bearer_token:
        raise ValueError(
            "API Bearer Token is required (provider key or credgoo combo).")

    provider_api_key = None
    if '@' in api_bearer_token:
        # Treat as credgoo combined token: bearer@encryption
        try:
            credgoo_bearer, credgoo_encryption = api_bearer_token.split('@', 1)
            if not credgoo_bearer or not credgoo_encryption:
                raise ValueError(
                    "Invalid combined credgoo token format. Both parts are required.")
            provider_api_key = get_api_key(
                service=provider_name,
                encryption_key=credgoo_encryption,
                bearer_token=credgoo_bearer,
            )
            if not provider_api_key and provider_name not in ['ollama']:
                raise AuthenticationError(
                    f"Failed to retrieve API key for '{provider_name}' using the provided credgoo token.")
#            print(
#                f"DEBUG: Successfully retrieved key for {provider_name}@{provider_api_key} via credgoo.")
        except ValueError as e:
            raise ValueError(
                f"Invalid combined credgoo token format ('bearer@encryption'): {e}")
        except Exception as e:
            raise AuthenticationError(
                f"Error retrieving key from credgoo for '{provider_name}': {e}")
    else:
        print(
            f"DEBUG: Using provided token directly as API key for {provider_name}.")
        provider_api_key = api_bearer_token

    if not provider_api_key and provider_name not in ['ollama']:
        print(
            f"Warning: API key for {provider_name} is missing or empty after processing.")

    return provider_api_key


# --- Main Completion Functions ---

# Update signature: remove api_bearer_token, add provider_api_key
def stream_completion(messages, provider_model_string, temperature=0.7, max_tokens=500, provider_api_key: Optional[str] = None, base_url: Optional[str] = None):
    """
    Initiates a streaming chat completion request via uniinfer.

    Args:
        messages (list[dict]): A list of message dictionaries, e.g.,
                               [{'role': 'user', 'content': 'Hello!'}]
        provider_model_string (str): Combined provider and model name,
                                     e.g., "openai@gpt-4", "arli@Mistral-Nemo-12B-Instruct-2407".
        temperature (float): The sampling temperature.
        max_tokens (int): The maximum number of tokens to generate.
        provider_api_key (str, optional): The pre-retrieved API key for the provider. Defaults to None.
        base_url (str, optional): The base URL for the provider's API (e.g., for Ollama). Defaults to None.
    Yields:
        str: Chunks of the generated content.

    Raises:
        ValueError: If the provider_model_string format is invalid.
        UniInferError: If there's an issue with the provider or the request.
    """
    try:
        # Parse provider and model from the combined string
        if '@' not in provider_model_string:
            raise ValueError(
                "Invalid provider_model_string format. Expected 'provider@modelname'.")
        provider_name, model_name = provider_model_string.split('@', 1)

        if not provider_name or not model_name:
            raise ValueError(
                "Invalid provider_model_string format. Provider or model name is empty.")

        # Get the specified provider, passing base_url if provided
        provider_kwargs = {'api_key': provider_api_key}  # Use passed key
        if base_url:
            provider_kwargs['base_url'] = base_url

        provider = ProviderFactory.get_provider(
            provider_name,
            **provider_kwargs
        )

        # Prepare uniinfer messages
        uniinfer_messages = [ChatMessage(**msg) for msg in messages]

        # Create the streaming request
        request = ChatCompletionRequest(
            messages=uniinfer_messages,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=True
        )

        # Stream the response
        print(
            f"--- Streaming response from {provider_name} ({model_name}) ---")
        for chunk in provider.stream_complete(request):
            if chunk.message and chunk.message.content:
                yield chunk.message.content
        # Update model accessed time after successful streaming completion
        update_model_accessed(model_name, provider_name)

    except (UniInferError, ValueError) as e:
        print(f"An error occurred: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise UniInferError(
            f"An unexpected error occurred in stream_completion: {e}")


# Update signature: remove api_bearer_token, add provider_api_key
def get_completion(messages, provider_model_string, temperature=0.7, max_tokens=500, provider_api_key: Optional[str] = None, base_url: Optional[str] = None) -> str:
    """
    Initiates a non-streaming chat completion request via uniinfer.

    Args:
        messages (list[dict]): A list of message dictionaries.
        provider_model_string (str): Combined provider and model name, e.g., "openai@gpt-4".
        temperature (float): The sampling temperature.
        max_tokens (int): The maximum number of tokens to generate.
        provider_api_key (str, optional): The pre-retrieved API key for the provider. Defaults to None.
        base_url (str, optional): The base URL for the provider's API (e.g., for Ollama). Defaults to None.
    Returns:
        str: The complete generated content.

    Raises:
        ValueError: If the provider_model_string format is invalid.
        UniInferError: If there's an issue with the provider or the request.
    """
    try:
        # Parse provider and model from the combined string
        if '@' not in provider_model_string:
            raise ValueError(
                "Invalid provider_model_string format. Expected 'provider@modelname'.")
        provider_name, model_name = provider_model_string.split('@', 1)

        if not provider_name or not model_name:
            raise ValueError(
                "Invalid provider_model_string format. Provider or model name is empty.")

        # Get the specified provider, passing base_url if provided
        provider_kwargs = {'api_key': provider_api_key}  # Use passed key
        if base_url:
            provider_kwargs['base_url'] = base_url

        provider = ProviderFactory.get_provider(
            provider_name,
            **provider_kwargs
        )

        # Prepare uniinfer messages
        uniinfer_messages = [ChatMessage(**msg) for msg in messages]

        # Create the non-streaming request
        request = ChatCompletionRequest(
            messages=uniinfer_messages,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=False
        )

        # Get the response
        print(
            f"--- Requesting non-streaming response from {provider_name} ({model_name}) ---")
        response: ChatCompletionResponse = provider.complete(request)
        print("--- Response received ---")

        if response.message and response.message.content:
            # Update model accessed time after successful non-streaming completion
            update_model_accessed(model_name, provider_name)
            return response.message.content
        else:
            print("Warning: Received empty content in response.")
            return ""

    except (UniInferError, ValueError) as e:
        print(f"An error occurred during non-streaming completion: {e}")
        raise
    except Exception as e:
        print(
            f"An unexpected error occurred during non-streaming completion: {e}")
        raise UniInferError(
            f"An unexpected error occurred in get_completion: {e}")


# --- Embedding Functions ---

def get_embeddings(input_texts: List[str], provider_model_string: str, provider_api_key: Optional[str] = None, base_url: Optional[str] = None) -> List[List[float]]:
    """
    Initiates an embedding request via uniinfer.

    Args:
        input_texts (List[str]): A list of texts to embed.
        provider_model_string (str): Combined provider and model name, e.g., "ollama@nomic-embed-text:latest".
        provider_api_key (str, optional): The pre-retrieved API key for the provider. Defaults to None.
        base_url (str, optional): The base URL for the provider's API (e.g., for Ollama). Defaults to None.

    Returns:
        List[List[float]]: A list of embedding vectors, where each vector is a list of floats.

    Raises:
        ValueError: If the provider_model_string format is invalid.
        UniInferError: If there's an issue with the provider or the request.
    """
    try:
        # Parse provider and model from the combined string
        if '@' not in provider_model_string:
            raise ValueError(
                "Invalid provider_model_string format. Expected 'provider@modelname'.")
        provider_name, model_name = provider_model_string.split('@', 1)

        if not provider_name or not model_name:
            raise ValueError(
                "Invalid provider_model_string format. Provider or model name is empty.")

        # Get the specified embedding provider, passing base_url if provided
        provider_kwargs = {'api_key': provider_api_key}  # Use passed key
        if base_url:
            provider_kwargs['base_url'] = base_url

        provider = EmbeddingProviderFactory.get_provider(
            provider_name,
            **provider_kwargs
        )

        # Create the embedding request
        request = EmbeddingRequest(
            input=input_texts,
            model=model_name
        )

        # Get the response
        print(
            f"--- Requesting embeddings from {provider_name} ({model_name}) ---")
        response: EmbeddingResponse = provider.embed(request)
        print("--- Embeddings received ---")

        # Extract just the embedding vectors from the response
        embeddings = []
        for embedding_data in response.data:
            embeddings.append(embedding_data["embedding"])

        return embeddings

    except (UniInferError, ValueError) as e:
        print(f"An error occurred during embedding request: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred during embedding request: {e}")
        raise UniInferError(
            f"An unexpected error occurred in get_embeddings: {e}")


# --- New Helper to List Embedding Providers ---
def list_embedding_providers() -> List[str]:
    """
    Return the names of all available embedding providers.
    """
    return EmbeddingProviderFactory.list_providers()


# --- New Helper to List Embedding Models for a Provider ---
def list_embedding_models_for_provider(provider_name: str, api_bearer_token: str) -> List[str]:
    """
    Return available embedding model names for the given provider, using the bearer token.
    For Ollama, api_bearer_token can be empty or None.
    """
    # retrieve actual api key
    if provider_name == 'ollama':
        api_key = None
    else:
        api_key = get_provider_api_key(api_bearer_token, provider_name)
    # determine extra params if needed
    extra = {}
    if provider_name in ['cloudflare', 'ollama']:
        extra = PROVIDER_CONFIGS.get(provider_name, {}).get('extra_params', {})
    # get the provider class and list models
    provider_cls = EmbeddingProviderFactory.get_provider_class(provider_name)
    modellist = provider_cls.list_models(api_key=api_key, **extra)
    return modellist


# --- New Helper to List Providers ---
def list_providers() -> List[str]:
    """
    Return the names of all available providers.
    """
    return ProviderFactory.list_providers()


# --- New Helper to List Models for a Provider ---
def list_models_for_provider(provider_name: str, api_bearer_token: str) -> List[str]:
    """
    Return available model names for the given provider, using the bearer token.
    """
    # retrieve actual api key
    api_key = get_provider_api_key(api_bearer_token, provider_name)
    # determine extra params if needed
    extra = {}
    if provider_name in ['cloudflare', 'ollama']:
        extra = PROVIDER_CONFIGS.get(provider_name, {}).get('extra_params', {})
    # get the provider class and list models
    provider_cls = ProviderFactory.get_provider_class(provider_name)
    modellist = provider_cls.list_models(api_key=api_key, **extra)
    update_models(modellist, provider_name)
    return modellist


# Example Usage
if __name__ == "__main__":
    test_credgootoken = f"{os.getenv('CREDGOO_BEARER_TOKEN')}@{os.getenv('CREDGOO_ENCRYPTION_KEY')}"
#    test_provider_model = os.getenv("TEST_PROVIDER_MODEL", "ollama@gemma3:4b")
    test_provider_model = os.getenv(
        "TEST_PROVIDER_MODEL", "mistral@mistral-tiny-latest")
    test_base_url = "http://amp1.mooo.com:11444" if "ollama" in test_provider_model else None

    # List of cities
    cities = [
        "Tokyo", "Delhi", "Shanghai", "Sao Paulo", "Mumbai", "Mexico City",
        "Beijing", "Osaka", "Cairo", "New York", "Dhaka", "Karachi",
        "Buenos Aires", "Kolkata", "Istanbul", "Chongqing", "Lagos",
        "Rio de Janeiro", "Tianjin", "Kinshasa", "Guangzhou", "Los Angeles",
        "Moscow", "Shenzhen", "Lahore", "Bangalore", "Paris", "Bogota",
        "Jakarta", "Chennai", "Lima", "Bangkok", "Seoul", "Nagoya", "Hyderabad", "Vienna",
        "London", "Chennai", "Hangzhou", "Wuhan", "Ahmedabad", "Hong Kong", "Berlin"
    ]

    # Select 3 unique random cities
    if len(cities) >= 3:
        chosen_cities = random.sample(cities, 3)
        city_a, city_b, city_c = chosen_cities
    else:
        city_a, city_b, city_c = "CityA", "CityB", "CityC"

    # Construct the dynamic prompt
    user_prompt = f"{city_a}, {city_b} or {city_c}. choose one. explain by just using one word in the style: CITY: Because: \"EXPLANATIONWORD\""

    example_messages = [
        {"role": "system", "content": "You follow instructions precisely and provide concise answers in the requested format."},
        {"role": "user", "content": user_prompt}
    ]
    print(f"Using prompt: {user_prompt}")

    provider_model = test_provider_model
    provider_name_example = provider_model.split('@')[0]

    try:
        print(
            f"Retrieving API key for '{provider_name_example}' using token {test_credgootoken}")
        test_provider_api_key = get_provider_api_key(
            test_credgootoken, provider_name_example)
        # print("API Key retrieval successful (or not needed).")

        # --- Streaming Example ---
        print("\n--- Running Streaming Example ---")
#        if test_base_url:
#            print(f"Using TEST_BASE_URL: {test_base_url}")
        try:
            full_streamed_response = ""
            for content_chunk in stream_completion(
                example_messages,
                provider_model_string=provider_model,
                provider_api_key=test_provider_api_key,
                base_url=test_base_url
            ):
                print(content_chunk, end="", flush=True)
                full_streamed_response += content_chunk
            print("\n")
        except (UniInferError, ValueError) as e:
            print(f"\nError during streaming example: {e}")
        except Exception as e:
            print(f"\nUnexpected error during streaming example: {e}")

        # --- Non-Streaming Example ---
        print("\n--- Running Non-Streaming Example ---")
#        if test_base_url:
#            print(f"Using TEST_BASE_URL: {test_base_url}")
        try:
            full_response = get_completion(
                example_messages,
                provider_model_string=provider_model,
                provider_api_key=test_provider_api_key,
                base_url=test_base_url
            )
            print("\nFull Response:")
            print(full_response)
        except (UniInferError, ValueError) as e:
            print(f"Error during non-streaming example: {e}")
        except Exception as e:
            print(f"Unexpected error during non-streaming example: {e}")

    except (ValueError, AuthenticationError) as e:
        print(f"\nFATAL ERROR during API key retrieval: {e}")
    except Exception as e:
        print(f"\nUNEXPECTED FATAL ERROR during setup/key retrieval: {e}")
