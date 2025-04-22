"""
Ollama provider implementation.
"""
import json
import requests
from typing import Dict, Any, Iterator, Optional

from ..core import ChatProvider, ChatCompletionRequest, ChatCompletionResponse, ChatMessage


def _normalize_base_url(base_url: str) -> str:
    """
    Normalize the base URL to ensure it has a scheme and upgrade non-localhost http to https.

    Args:
        base_url (str): The base URL to normalize.

    Returns:
        str: The normalized base URL.
    """
    # Ensure scheme present; allow plain URLs
    if not base_url.startswith(("http://", "https://")):
        base_url = "http://" + base_url
    # Upgrade non-localhost http to https
    if base_url.startswith("http://") and not base_url.startswith(("http://localhost", "http://127.0.0.1")):
        base_url = "https://" + base_url[len("http://"):]
    return base_url


class OllamaProvider(ChatProvider):
    """
    Provider for Ollama API.

    Ollama is a local LLM serving tool that allows running various models locally.
    This provider requires a running Ollama instance.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://localhost:11434", **kwargs):
        """
        Initialize the Ollama provider.

        Args:
            api_key (Optional[str]): Not used for Ollama, but kept for API consistency.
            base_url (str): The base URL for the Ollama API (default: http://localhost:11434).
            **kwargs: Additional configuration options.
        """
        super().__init__(api_key)
        self.base_url = base_url

    @classmethod
    def list_models(cls, **kwargs) -> list:
        """
        List available models from Ollama.

        Args:
            **kwargs: Additional configuration options including base_url

        Returns:
            list: A list of available model names.
        """
        try:
            # Use provided base_url or fallback
            raw_url = kwargs.get("base_url") or getattr(
                cls, "base_url", "localhost:11434")
            base_url = _normalize_base_url(raw_url)
            endpoint = f"{base_url}/api/tags"
            print(f"Using Ollama endpoint: {endpoint}")  # Verbose logging

            response = requests.get(endpoint)
            response.raise_for_status()

            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            print(f"Found {len(models)} available models")
            return models

        except Exception as e:
            print(f"Error listing models from Ollama: {str(e)}")
            # Fallback to default models if API call fails
            return [
                "error listing models",
            ]

    def complete(
        self,
        request: ChatCompletionRequest,
        **provider_specific_kwargs
    ) -> ChatCompletionResponse:
        """
        Make a chat completion request to Ollama.

        Args:
            request (ChatCompletionRequest): The request to make.
            **provider_specific_kwargs: Additional Ollama-specific parameters.

        Returns:
            ChatCompletionResponse: The completion response.

        Raises:
            Exception: If the request fails.
        """
        # Ensure URL normalized (localhost allowed)
        base_url = _normalize_base_url(self.base_url)
        endpoint = f"{base_url}/api/chat"

        # Prepare the request payload
        payload = {
            "model": request.model or "llama2",  # Default to llama2 if no model specified
            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
            "stream": False,
            "options": {}
        }

        # Add temperature if provided
        if request.temperature is not None:
            payload["options"]["temperature"] = request.temperature

        # Add token limit if provided
        if request.max_tokens is not None:
            payload["options"]["num_predict"] = request.max_tokens

        # Add any provider-specific parameters
        if provider_specific_kwargs:
            for key, value in provider_specific_kwargs.items():
                if key == "options" and isinstance(value, dict):
                    # Merge options dictionaries
                    payload["options"].update(value)
                else:
                    # Add top-level parameters
                    payload[key] = value

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(
            endpoint,
            headers=headers,
            data=json.dumps(payload)
        )

        # Handle error response
        if response.status_code != 200:
            error_msg = f"Ollama API error: {response.status_code} - {response.text}"
            raise Exception(error_msg)

        # Parse the response
        response_data = response.json()

        # Extract the message content
        assistant_message = response_data["message"]

        message = ChatMessage(
            role=assistant_message.get("role", "assistant"),
            content=assistant_message.get("content", "")
        )

        # Construct usage information (Ollama doesn't always provide detailed usage)
        usage = {
            "prompt_tokens": response_data.get("prompt_eval_count", 0),
            "completion_tokens": response_data.get("eval_count", 0),
            "total_tokens": (
                response_data.get("prompt_eval_count", 0) +
                response_data.get("eval_count", 0)
            )
        }

        return ChatCompletionResponse(
            message=message,
            provider='ollama',
            model=response_data.get('model', request.model),
            usage=usage,
            raw_response=response_data
        )

    def stream_complete(
        self,
        request: ChatCompletionRequest,
        **provider_specific_kwargs
    ) -> Iterator[ChatCompletionResponse]:
        """
        Stream a chat completion response from Ollama.

        Args:
            request (ChatCompletionRequest): The request to make.
            **provider_specific_kwargs: Additional Ollama-specific parameters.

        Returns:
            Iterator[ChatCompletionResponse]: An iterator of response chunks.

        Raises:
            Exception: If the request fails.
        """
        # Ensure URL normalized (localhost allowed)
        base_url = _normalize_base_url(self.base_url)
        endpoint = f"{base_url}/api/chat"

        # Prepare the request payload
        payload = {
            "model": request.model or "llama2",  # Default to llama2 if no model specified
            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
            "stream": True,
            "options": {}
        }

        # Add temperature if provided
        if request.temperature is not None:
            payload["options"]["temperature"] = request.temperature

        # Add token limit if provided
        if request.max_tokens is not None:
            payload["options"]["num_predict"] = request.max_tokens

        # Add any provider-specific parameters
        if provider_specific_kwargs:
            for key, value in provider_specific_kwargs.items():
                if key == "options" and isinstance(value, dict):
                    # Merge options dictionaries
                    payload["options"].update(value)
                else:
                    # Add top-level parameters
                    payload[key] = value

        headers = {
            "Content-Type": "application/json"
        }

        with requests.post(
            endpoint,
            headers=headers,
            data=json.dumps(payload),
            stream=True
        ) as response:
            # Handle error response
            if response.status_code != 200:
                error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                raise Exception(error_msg)

            # Process the streaming response
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))

                        # Check if this is a message or a done event
                        if "done" in data and data["done"]:
                            continue

                        # Extract content
                        content = ""
                        if "message" in data and "content" in data["message"]:
                            content = data["message"]["content"]

                        # Create a message for this chunk
                        message = ChatMessage(
                            role="assistant", content=content)

                        # Basic usage stats (Ollama stream doesn't have detailed usage per chunk)
                        usage = {}

                        yield ChatCompletionResponse(
                            message=message,
                            provider='ollama',
                            model=data.get('model', request.model),
                            usage=usage,
                            raw_response=data
                        )
                    except json.JSONDecodeError:
                        # Skip invalid JSON lines
                        continue
