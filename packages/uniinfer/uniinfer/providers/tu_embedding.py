"""
TU embedding provider implementation.
"""
import json
import requests
from typing import List, Dict, Any, Optional

from ..core import EmbeddingProvider, EmbeddingRequest, EmbeddingResponse


class TuAIEmbeddingProvider(EmbeddingProvider):
    """
    Provider for TU AI embeddings API.

    TU AI provides OpenAI-compatible embedding endpoints.
    """

    BASE_URL = "https://aqueduct.ai.datalab.tuwien.ac.at/v1"

    def __init__(self, api_key: Optional[str] = None, organization: Optional[str] = None):
        """
        Initialize the TU AI embedding provider.

        Args:
            api_key (Optional[str]): The TU AI API key.
            organization (Optional[str]): The TU AI organization ID.
        """
        super().__init__(api_key)
        self.organization = organization

    @classmethod
    def list_models(cls, api_key: Optional[str] = None) -> List[str]:
        """
        List available models from TU AI using the API.

        Returns:
            List[str]: A list of available model IDs.
        """
        if not api_key:
            raise ValueError("API key is required to list models")
        url = f"{cls.BASE_URL}/models"
        headers = {
            "Authorization": f"Bearer {api_key}",
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(
                f"TU AI API error: {response.status_code} - {response.text}")

        data = response.json()
        return [model["id"] for model in data.get("data", [])]

    def embed(
        self,
        request: EmbeddingRequest,
        **provider_specific_kwargs
    ) -> EmbeddingResponse:
        """
        Make an embedding request to TU AI.

        Args:
            request (EmbeddingRequest): The request to make.
            **provider_specific_kwargs: Additional TU AI-specific parameters.

        Returns:
            EmbeddingResponse: The embedding response.

        Raises:
            Exception: If the request fails.
        """
        if self.api_key is None:
            raise ValueError("TU AI API key is required")

        endpoint = f"{self.BASE_URL}/embeddings"

        # Prepare the request payload
        payload = {
            "model": request.model or "e5-mistral-7b",  # Default embedding model
            "input": request.input
        }

        # Add any provider-specific parameters
        payload.update(provider_specific_kwargs)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # Add organization header if provided
        if self.organization:
            headers["TUW-Organization"] = self.organization

        response = requests.post(
            endpoint,
            headers=headers,
            data=json.dumps(payload)
        )

        # Handle error response
        if response.status_code != 200:
            error_msg = f"TU AI API error: {response.status_code} - {response.text}"
            raise Exception(error_msg)

        # Parse the response
        response_data = response.json()

        # Extract the embeddings
        embeddings_data = response_data.get("data", [])

        # Create data entries
        data = []
        for item in embeddings_data:
            data.append({
                "object": "embedding",
                "embedding": item["embedding"],
                "index": item["index"]
            })

        # Construct usage information
        usage = response_data.get("usage", {})

        return EmbeddingResponse(
            object="list",
            data=data,
            model=response_data.get('model', request.model),
            usage=usage,
            provider='tu',
            raw_response=response_data
        )
