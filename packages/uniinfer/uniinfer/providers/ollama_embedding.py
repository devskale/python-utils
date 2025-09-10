"""
Ollama embedding provider implementation.
"""
import json
import requests
from typing import List, Dict, Any, Optional

from ..core import EmbeddingProvider, EmbeddingRequest, EmbeddingResponse


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


class OllamaEmbeddingProvider(EmbeddingProvider):
    """
    Provider for Ollama embeddings API.

    Ollama is a local LLM serving tool that allows running various embedding models locally.
    This provider requires a running Ollama instance.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://localhost:11434", **kwargs):
        """
        Initialize the Ollama embedding provider.

        Args:
            api_key (Optional[str]): Not used for Ollama, but kept for API consistency.
            base_url (str): The base URL for the Ollama API (default: http://localhost:11434).
            **kwargs: Additional configuration options.
        """
        super().__init__(api_key)
        self.base_url = base_url

    @classmethod
    def list_models(cls, **kwargs) -> List[str]:
        """
        List available models from Ollama.

        Args:
            **kwargs: Additional configuration options including base_url

        Returns:
            List[str]: A list of available model names.
        """
        try:
            # Use provided base_url or fallback
            raw_url = kwargs.get("base_url") or getattr(
                cls, "base_url", "localhost:11434")
            base_url = _normalize_base_url(raw_url)
            if "molodetz.nl" in base_url:
                # Special case for molodetz.nl, which uses a different endpoint
                endpoint = f"{base_url}/models"
            else:
                endpoint = f"{base_url}/api/tags"
            print(f"Using Ollama endpoint: {endpoint}")  # Verbose logging

            response = requests.get(endpoint)
            response.raise_for_status()

            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            if not models:
                # Fallback to tags if models are not available
                models = [model["id"] for model in data.get("data", [])]
            print(f"Found {len(models)} available models")
            return models

        except Exception as e:
            print(f"Error listing models from Ollama: {str(e)}")
            # Fallback to default models if API call fails
            return [
                "error listing models",
            ]

    def embed(
        self,
        request: EmbeddingRequest,
        **provider_specific_kwargs
    ) -> EmbeddingResponse:
        """
        Make an embedding request to Ollama.

        Args:
            request (EmbeddingRequest): The request to make.
            **provider_specific_kwargs: Additional Ollama-specific parameters.

        Returns:
            EmbeddingResponse: The embedding response.

        Raises:
            Exception: If the request fails.
        """
        # Ensure URL normalized (localhost allowed)
        base_url = _normalize_base_url(self.base_url)
        endpoint = f"{base_url}/api/embed"

        # Prepare the request payload
        payload = {
            # Default to nomic-embed-text if no model specified
            "model": request.model or "nomic-embed-text",
            "input": request.input
        }

        # Add any provider-specific parameters
        if provider_specific_kwargs:
            for key, value in provider_specific_kwargs.items():
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

        # Extract the embeddings
        embeddings = response_data.get("embeddings", [])

        # Create data entries
        data = []
        for i, embedding in enumerate(embeddings):
            data.append({
                "object": "embedding",
                "embedding": embedding,
                "index": i
            })

        # Construct usage information (Ollama doesn't always provide detailed usage for embeddings)
        usage = {
            "prompt_tokens": response_data.get("prompt_eval_count", 0),
            "total_tokens": response_data.get("prompt_eval_count", 0)
        }

        return EmbeddingResponse(
            object="list",
            data=data,
            model=response_data.get('model', request.model),
            usage=usage,
            provider='ollama',
            raw_response=response_data
        )
