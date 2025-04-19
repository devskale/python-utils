"""
A simple wrapper for LLM APIs using uniinfer, supporting streaming and non-streaming.
"""
import os

from uniinfer import ProviderFactory, ChatMessage, ChatCompletionRequest, ChatCompletionResponse
from uniinfer.errors import UniInferError
from dotenv import load_dotenv
from credgoo import get_api_key
# Load environment variables from .env file
dotenv_path = os.path.join(os.getcwd(), '.env')  # Explicitly check current dir
# Add verbose=True and override=True
found_dotenv = load_dotenv(dotenv_path=dotenv_path,
                           verbose=True, override=True)

# Retrieve credgoo tokens from environment variables once
credgoo_api_token = os.getenv("CREDGOO_BEARER_TOKEN")
credgoo_encryption_token = os.getenv("CREDGOO_ENCRYPTION_KEY")

print(f"DEBUG: Attempted to load .env from: {dotenv_path}")  # Debug print
print(f"DEBUG: .env file found and loaded: {found_dotenv}")  # Debug print
# Debug print for credgoo tokens (consider removing in production)
print(f"DEBUG: CREDGOO_BEARER_TOKEN: {credgoo_api_token}")
print(f"DEBUG: CREDGOO_ENCRYPTION_KEY: {credgoo_encryption_token}")


def stream_completion(messages, provider_model_string, temperature=0.7, max_tokens=500):
    """
    Initiates a streaming chat completion request via uniinfer.

    Args:
        messages (list[dict]): A list of message dictionaries, e.g.,
                               [{'role': 'user', 'content': 'Hello!'}]
        provider_model_string (str): Combined provider and model name,
                                     e.g., "openai@gpt-4", "arli@Mistral-Nemo-12B-Instruct-2407".
        temperature (float): The sampling temperature.
        max_tokens (int): The maximum number of tokens to generate.

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

        # Get API key using credgoo
        api_key = get_api_key(
            service=provider_name,  # Use provider_name here
            encryption_key=credgoo_encryption_token,
            bearer_token=credgoo_api_token,
        )
        # Ollama might not need a key
        if not api_key and provider_name not in ['ollama']:
            print(
                f"Warning: Could not retrieve API key for {provider_name} via credgoo.")
            # Optionally, you could raise an error here or rely on the factory's env var fallback

        # Get the specified provider
        provider = ProviderFactory.get_provider(
            provider_name,
            api_key=api_key  # Pass the retrieved key
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
        # print("\n--- Stream finished ---")

    except (UniInferError, ValueError) as e:
        print(f"An error occurred: {e}")
        raise  # Re-raise the exception for handling upstream if needed
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise  # Re-raise


def get_completion(messages, provider_model_string, temperature=0.7, max_tokens=500) -> str:
    """
    Initiates a non-streaming chat completion request via uniinfer.

    Args:
        messages (list[dict]): A list of message dictionaries.
        provider_model_string (str): Combined provider and model name, e.g., "openai@gpt-4".
        temperature (float): The sampling temperature.
        max_tokens (int): The maximum number of tokens to generate.

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

        # Get API key using credgoo
        api_key = get_api_key(
            service=provider_name,
            encryption_key=credgoo_encryption_token,
            bearer_token=credgoo_api_token,
        )
        # Ollama might not need a key
        if not api_key and provider_name not in ['ollama']:
            print(
                f"Warning: Could not retrieve API key for {provider_name} via credgoo.")
            # Optionally, you could raise an error here or rely on the factory's env var fallback

        # Get the specified provider
        provider = ProviderFactory.get_provider(
            provider_name,
            api_key=api_key  # Pass the retrieved key
        )

        # Prepare uniinfer messages
        uniinfer_messages = [ChatMessage(**msg) for msg in messages]

        # Create the non-streaming request
        request = ChatCompletionRequest(
            messages=uniinfer_messages,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=False  # Explicitly set streaming to False
        )

        # Get the response
        print(
            f"--- Requesting non-streaming response from {provider_name} ({model_name}) ---")
        response: ChatCompletionResponse = provider.complete(request)
        print("--- Response received ---")

        if response.message and response.message.content:
            return response.message.content
        else:
            # Handle cases where the response might be empty or malformed
            print("Warning: Received empty content in response.")
            return ""

    except (UniInferError, ValueError) as e:
        print(f"An error occurred during non-streaming completion: {e}")
        raise
    except Exception as e:
        print(
            f"An unexpected error occurred during non-streaming completion: {e}")
        raise


# Example Usage
if __name__ == "__main__":
    example_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain the concept of reinforcement learning in AI/ML in simple terms and in 3 sentences."}
    ]

    # Define the provider and model to use
    # provider_model = "openai@gpt-3.5-turbo"
    # provider_model = "ollama@gemma3:4b"
    provider_model = "groq@llama3-8b-8192"  # Example for Groq
    # provider_model = "cloudflare@meta/llama-3-8b-instruct" # Example for Cloudflare

    # credgoo tokens are retrieved from environment variables at the start of the script
    # No need for bearer_token_example anymore

    # --- Streaming Example ---
    print("\n--- Running Streaming Example ---")
    try:
        # Call stream_completion without bearer_token
        full_streamed_response = ""
        for content_chunk in stream_completion(
            example_messages,
            provider_model_string=provider_model
        ):
            print(content_chunk, end="", flush=True)
            full_streamed_response += content_chunk  # Accumulate response if needed later
        print("\n")  # Add a newline after streaming finishes
    except (UniInferError, ValueError) as e:
        print(f"\nError during streaming example: {e}")
    except Exception as e:
        print(f"\nUnexpected error during streaming example: {e}")

    # --- Non-Streaming Example ---
    print("\n--- Running Non-Streaming Example ---")
    try:
        # Call get_completion without bearer_token
        full_response = get_completion(
            example_messages,
            provider_model_string=provider_model
        )
        print("\nFull Response:")
        print(full_response)
    except (UniInferError, ValueError) as e:
        print(f"Error during non-streaming example: {e}")
    except Exception as e:
        print(f"Unexpected error during non-streaming example: {e}")
