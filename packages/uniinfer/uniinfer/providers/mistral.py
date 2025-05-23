"""
Mistral AI provider implementation.
"""
import json
import requests
from typing import Dict, Any, Iterator, Optional

from ..core import ChatProvider, ChatCompletionRequest, ChatCompletionResponse, ChatMessage


class MistralProvider(ChatProvider):
    """
    Provider for Mistral AI API.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Mistral provider.

        Args:
            api_key (Optional[str]): The Mistral API key.
        """
        super().__init__(api_key)
        self.base_url = "https://api.mistral.ai/v1"

    @classmethod
    def list_models(cls, api_key: Optional[str] = None) -> list:
        """
        List available models from Mistral AI.

        Args:
            api_key (Optional[str]): The Mistral API key. If not provided,
                                     it attempts to retrieve it using credgoo.

        Returns:
            list: A list of available model names.

        Raises:
            ValueError: If no API key is provided or found.
            Exception: If the API request fails.
        """
        if not api_key:
            try:
                from credgoo.credgoo import get_api_key
                # Get API key from credgoo
                api_key = get_api_key("mistral")
            except ImportError:
                raise ValueError(
                    "credgoo not installed. Please provide an API key or install credgoo.")
            except Exception as e:
                raise ValueError(
                    f"Failed to get Mistral API key from credgoo: {e}")

        if not api_key:
            raise ValueError(
                "Mistral API key is required. Provide it directly or configure credgoo.")

        endpoint = "https://api.mistral.ai/v1/models"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        response = requests.get(endpoint, headers=headers)

        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch models: {response.status_code} - {response.text}")

        models_data = response.json()
        return [model["id"] for model in models_data["data"]]

    def complete(
        self,
        request: ChatCompletionRequest,
        **provider_specific_kwargs
    ) -> ChatCompletionResponse:
        """
        Make a chat completion request to Mistral AI.

        Args:
            request (ChatCompletionRequest): The request to make.
            **provider_specific_kwargs: Additional Mistral-specific parameters.

        Returns:
            ChatCompletionResponse: The completion response.

        Raises:
            Exception: If the request fails.
        """
        if self.api_key is None:
            raise ValueError("Mistral API key is required")

        endpoint = f"{self.base_url}/chat/completions"

        # Prepare the request payload
        payload = {
            "model": request.model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
            "temperature": request.temperature,
            "stream": False
        }

        # Add max_tokens if provided
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens

        # Add any provider-specific parameters
        payload.update(provider_specific_kwargs)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        response = requests.post(
            endpoint,
            headers=headers,
            data=json.dumps(payload)
        )

        # Handle error response
        if response.status_code != 200:
            error_msg = f"Mistral API error: {response.status_code} - {response.text}"
            raise Exception(error_msg)

        # Parse the response
        response_data = response.json()
        choice = response_data['choices'][0]
        message = ChatMessage(
            role=choice['message']['role'],
            content=choice['message']['content']
        )

        return ChatCompletionResponse(
            message=message,
            provider='mistral',
            model=response_data.get('model', request.model),
            usage=response_data.get('usage', {}),
            raw_response=response_data
        )

    def stream_complete(
        self,
        request: ChatCompletionRequest,
        **provider_specific_kwargs
    ) -> Iterator[ChatCompletionResponse]:
        """
        Stream a chat completion response from Mistral AI.

        Args:
            request (ChatCompletionRequest): The request to make.
            **provider_specific_kwargs: Additional Mistral-specific parameters.

        Returns:
            Iterator[ChatCompletionResponse]: An iterator of response chunks.

        Raises:
            Exception: If the request fails.
        """
        if self.api_key is None:
            raise ValueError("Mistral API key is required")

        endpoint = f"{self.base_url}/chat/completions"

        # Prepare the request payload
        payload = {
            "model": request.model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
            "temperature": request.temperature,
            "stream": True
        }

        # Add max_tokens if provided
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens

        # Add any provider-specific parameters
        payload.update(provider_specific_kwargs)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        with requests.post(
            endpoint,
            headers=headers,
            data=json.dumps(payload),
            stream=True
        ) as response:
            # Handle error response
            if response.status_code != 200:
                error_msg = f"Mistral API error: {response.status_code} - {response.text}"
                raise Exception(error_msg)

            # Process the streaming response
            for line in response.iter_lines():
                if line:
                    # Parse the JSON data from the stream
                    try:
                        data = line.decode('utf-8')
                        if data.startswith('data: '):
                            data = data[6:]  # Remove 'data: ' prefix

                        # Skip empty lines or [DONE]
                        if not data or data == '[DONE]':
                            continue

                        chunk = json.loads(data)

                        if 'choices' in chunk:
                            choice = chunk['choices'][0]
                            role = choice['delta'].get('role', 'assistant')
                            content = choice['delta'].get('content', '')

                            # Create a message for this chunk
                            message = ChatMessage(role=role, content=content)

                            yield ChatCompletionResponse(
                                message=message,
                                provider='mistral',
                                model=chunk.get('model', request.model),
                                usage=chunk.get('usage', {}),
                                raw_response=chunk
                            )
                    except json.JSONDecodeError:
                        # Skip invalid JSON lines
                        continue
