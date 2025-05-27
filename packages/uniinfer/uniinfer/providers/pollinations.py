"""
Pollinations provider implementation.

Pollinations is a unified API to access multiple AI models from different providers.
"""
from typing import Optional, Iterator
import requests
import urllib.parse
import json

from ..core import ChatProvider, ChatCompletionRequest, ChatCompletionResponse, ChatMessage


class PollinationsProvider(ChatProvider):
    """
    Provider for Pollinations API.

    Pollinations provides a unified interface to access multiple AI models from
    different providers, including Anthropic, OpenAI, and more.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Pollinations provider.

        Args:
            api_key (Optional[str]): The Pollinations API key.
        """
        super().__init__(api_key)
        self.base_url = "https://text.pollinations.ai"  # Updated to match API docs

    @classmethod
    def list_models(cls, api_key: Optional[str] = None) -> list:
        """
        List available models from Pollinations.

        Args:
            api_key (Optional[str]): The Pollinations API key. If not provided,
                                     it attempts to retrieve it using credgoo.

        Returns:
            list: A list of available model IDs.

        Raises:
            ValueError: If no API key is provided or found.
            Exception: If the API request fails.
        """
        # Determine the API key to use
        if not api_key:
            try:
                from credgoo.credgoo import get_api_key
                api_key = get_api_key('pollinations')
            except ImportError:
                raise ValueError(
                    "credgoo not installed. Please provide an API key or install credgoo.")
            except Exception as e:
                raise ValueError(
                    f"Failed to get Pollinations API key from credgoo: {e}")
        if not api_key:
            raise ValueError(
                "Pollinations API key is required. Provide it directly or configure credgoo.")

        endpoint = "https://text.pollinations.ai/models"  # Updated endpoint

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        response = requests.get(endpoint, headers=headers)

        if response.status_code != 200:
            error_msg = f"Pollinations API error: {response.status_code} - {response.text}"
            raise Exception(error_msg)

        models = response.json()
        # Handle the API response format which is a list of model objects with 'name' field
        if isinstance(models, list) and len(models) > 0 and isinstance(models[0], dict):
            return [model.get('name', '') for model in models if model.get('name')]
        return []

    def complete(
        self,
        request: ChatCompletionRequest,
        **provider_specific_kwargs
    ) -> ChatCompletionResponse:
        """
        Make a text generation request to Pollinations.

        Args:
            request (ChatCompletionRequest): The request to make.
            **provider_specific_kwargs: Additional Pollinations-specific parameters.

        Returns:
            ChatCompletionResponse: The completion response.

        Raises:
            Exception: If the request fails.
        """
        # Get last user message
        last_user_message = next((msg.content for msg in reversed(
            request.messages) if msg.role == "user"), None)
        if not last_user_message:
            raise ValueError(
                "At least one user message is required for Pollinations API.")

        # Prepare parameters
        params = {
            "model": request.model or "grok",
            "seed": 42,  # Default seed
        }
        if request.temperature is not None:
            params["temperature"] = request.temperature
        if request.max_tokens is not None:
            params["max_tokens"] = request.max_tokens

        # Handle system message if present
        system_message = next(
            (msg.content for msg in request.messages if msg.role == "system"), None)
        if system_message:
            params["system"] = system_message

        params.update(provider_specific_kwargs)

        # Encode prompt and system message
        encoded_prompt = urllib.parse.quote(last_user_message)
        if system_message:
            params["system"] = urllib.parse.quote(system_message)

        # Build URL
        url = f"{self.base_url}/{encoded_prompt}"

        try:
            response = requests.get(url, params=params)

            if response.status_code != 200:
                error_msg = f"Pollinations API error: {response.status_code} - {response.text}"
                raise Exception(error_msg)

            # Handle JSON response if requested
            if params.get("json") == "true":
                try:
                    response_data = json.loads(response.text)
                except json.JSONDecodeError:
                    raise Exception("API returned invalid JSON string")
            else:
                response_data = {"result": response.text}

            message = ChatMessage(
                role="assistant",
                content=response_data.get("result", "")
            )

            return ChatCompletionResponse(
                message=message,
                provider='pollinations',
                model=request.model,
                usage={},
                raw_response=response_data
            )

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching text: {e}")

    def stream_complete(
        self,
        request: ChatCompletionRequest,
        **provider_specific_kwargs
    ) -> Iterator[ChatCompletionResponse]:
        """
        Stream a chat completion response from Pollinations.

        Args:
            request (ChatCompletionRequest): The request to make.
            **provider_specific_kwargs: Additional Pollinations-specific parameters.

        Returns:
            Iterator[ChatCompletionResponse]: An iterator of response chunks.

        Raises:
            Exception: If the request fails.
        """
        if self.api_key is None:
            raise ValueError("Pollinations API key is required")

        # Get last user message
        last_user_message = next((msg.content for msg in reversed(
            request.messages) if msg.role == "user"), None)
        if not last_user_message:
            raise ValueError(
                "At least one user message is required for Pollinations API.")

        # Prepare parameters
        params = {
            "model": request.model or "openai",
            "seed": 42,  # Default seed
            "stream": True
        }
        if request.temperature is not None:
            params["temperature"] = request.temperature
        if request.max_tokens is not None:
            params["max_tokens"] = request.max_tokens

        # Handle system message if present
        system_message = next(
            (msg.content for msg in request.messages if msg.role == "system"), None)
        if system_message:
            params["system"] = system_message

        params.update(provider_specific_kwargs)

        # Encode prompt and system message
        encoded_prompt = urllib.parse.quote(last_user_message)
        if system_message:
            params["system"] = urllib.parse.quote(system_message)

        # Build URL
        url = f"{self.base_url}/{encoded_prompt}"

        # Add max_tokens if provided
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens

        # Add any provider-specific parameters
        params.update(provider_specific_kwargs)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        with requests.get(
            url,
            params=params,
            headers=headers,
            stream=True
        ) as response:
            if response.status_code != 200:
                error_msg = f"Pollinations API error: {response.status_code} - {response.text}"
                raise Exception(error_msg)

            for line in response.iter_lines():
                if line:
                    try:
                        line = line.decode('utf-8').strip()
                        if not line or not line.startswith('data: '):
                            continue
                        data = line[6:]
                        if data == '[DONE]':
                            break
                        chunk = data.strip()
                        if not chunk:
                            continue
                        data_json = json.loads(chunk)
                        if 'choices' not in data_json or not data_json['choices']:
                            continue
                        choice = data_json['choices'][0]
                        # Pollinations streaming: content is in delta.content
                        if 'delta' not in choice or 'content' not in choice['delta'] or not choice['delta']['content']:
                            continue
                        content = choice['delta']['content']
                        role = choice['delta'].get('role', 'assistant')
                        message = ChatMessage(role=role, content=content)
                        usage = {}
                        model = data_json.get('model', request.model)
                        yield ChatCompletionResponse(
                            message=message,
                            provider='pollinations',
                            model=model,
                            usage=usage,
                            raw_response=data_json
                        )
                    except json.JSONDecodeError:
                        continue
                    except json.JSONDecodeError:
                        continue
                        content = choice['delta']['content']

                        # Get role from delta or default to assistant
                        role = choice['delta'].get('role', 'assistant')

                        # Create a message for this chunk
                        message = ChatMessage(role=role, content=content)

                        # Usage stats typically not provided in stream chunks
                        usage = {}

                        # Get model info if available
                        model = data.get('model', request.model)

                        yield ChatCompletionResponse(
                            message=message,
                            provider='pollinations',
                            model=model,
                            usage=usage,
                            raw_response=data
                        )
                    except json.JSONDecodeError:
                        # Skip invalid JSON lines
                        continue
