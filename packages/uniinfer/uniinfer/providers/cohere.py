"""
Cohere provider implementation.
"""
import os
from typing import Dict, Any, Iterator, Optional

from ..core import ChatProvider, ChatCompletionRequest, ChatCompletionResponse, ChatMessage

try:
    import cohere
    HAS_COHERE = True
except ImportError:
    HAS_COHERE = False


class CohereProvider(ChatProvider):
    """
    Provider for Cohere API.
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the Cohere provider.

        Args:
            api_key (Optional[str]): The Cohere API key.
            **kwargs: Additional configuration options.
        """
        if not api_key:
            from credgoo.credgoo import get_api_key
            api_key = get_api_key("cohere")
            if not api_key:
                raise ValueError("API key is required for CohereProvider")

        super().__init__(api_key)

        if not HAS_COHERE:
            raise ImportError(
                "cohere package is required for the CohereProvider. "
                "Install it with: pip install cohere"
            )

        # Initialize the Cohere client
        self.client = cohere.ClientV2(api_key=self.api_key)

    def complete(
        self,
        request: ChatCompletionRequest,
        **provider_specific_kwargs
    ) -> ChatCompletionResponse:
        """
        Make a chat completion request to Cohere.

        Args:
            request (ChatCompletionRequest): The request to make.
            **provider_specific_kwargs: Additional Cohere-specific parameters.

        Returns:
            ChatCompletionResponse: The completion response.

        Raises:
            Exception: If the request fails.
        """
        if self.api_key is None:
            raise ValueError("Cohere API key is required")

        # Convert messages to Cohere format
        cohere_messages = []
        for msg in request.messages:
            cohere_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Prepare parameters
        params = {
            "model": request.model or "command-r-plus-08-2024",  # Default model
            "messages": cohere_messages,
        }

        # Handle temperature (Cohere uses temperature differently)
        if request.temperature is not None:
            params["temperature"] = request.temperature

        # Add max_tokens if provided
        if request.max_tokens is not None:
            params["max_tokens"] = request.max_tokens

        # Add any provider-specific parameters
        params.update(provider_specific_kwargs)

        try:
            # Make the chat completion request
            response = self.client.chat(**params)

            # Extract the response content
            content = response.text

            # Create a ChatMessage
            message = ChatMessage(
                role="assistant",
                content=content
            )

            # Create usage information
            usage = {
                "input_tokens": getattr(response, "input_tokens", 0),
                "output_tokens": getattr(response, "output_tokens", 0),
                "total_tokens": getattr(response, "input_tokens", 0) + getattr(response, "output_tokens", 0)
            }

            # Create raw response for debugging
            raw_response = {
                "model": params["model"],
                "text": content,
                "usage": usage
            }

            return ChatCompletionResponse(
                message=message,
                provider='cohere',
                model=params["model"],
                usage=usage,
                raw_response=raw_response
            )
        except Exception as e:
            raise Exception(f"Cohere API error: {str(e)}")

    @classmethod
    def list_models(cls, api_key: Optional[str] = None) -> list:
        """
        List available models from Cohere.

        Args:
            api_key (Optional[str]): The Cohere API key. If not provided,
                                     it attempts to retrieve it from the environment
                                     or credgoo.

        Returns:
            list: A list of available model names.

        Raises:
            ImportError: If the cohere package is not installed.
            ValueError: If no API key is provided or found.
            Exception: If the API request fails.
        """
        if not HAS_COHERE:
            raise ImportError(
                "cohere package is required for the CohereProvider. "
                "Install it with: pip install cohere"
            )

        # Determine the API key to use
        if not api_key:
            api_key = os.getenv("COHERE_API_KEY")
            if not api_key:
                try:
                    from credgoo.credgoo import get_api_key
                    api_key = get_api_key("cohere")
                except ImportError:
                    raise ValueError(
                        "credgoo not installed. Please provide an API key, set COHERE_API_KEY, or install credgoo.")
                except Exception as e:
                    raise ValueError(
                        f"Failed to get Cohere API key from credgoo: {e}")

        if not api_key:
            raise ValueError(
                "Cohere API key is required. Provide it directly, set COHERE_API_KEY, or configure credgoo.")

        try:
            client = cohere.ClientV2(api_key=api_key)
            response = client.models.list()

            # Extract just the model names
            return [model.name for model in response.models]
        except Exception as e:
            # Log the error for debugging
            import logging
            logging.warning(f"Failed to fetch Cohere models: {str(e)}")

            # Fallback to default models if API call fails
            return [
                "command",
                "command-r",
                "command-r-plus",
                "command-light",
                "command-nightly"
            ]

    def stream_complete(
        self,
        request: ChatCompletionRequest,
        **provider_specific_kwargs
    ) -> Iterator[ChatCompletionResponse]:
        """
        Stream a chat completion response from Cohere.

        Args:
            request (ChatCompletionRequest): The request to make.
            **provider_specific_kwargs: Additional Cohere-specific parameters.

        Returns:
            Iterator[ChatCompletionResponse]: An iterator of response chunks.

        Raises:
            Exception: If the request fails.
        """
        if self.api_key is None:
            raise ValueError("Cohere API key is required")

        # Convert messages to Cohere format
        cohere_messages = []
        for msg in request.messages:
            cohere_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Prepare parameters
        params = {
            "model": request.model or "command-r-plus-08-2024",  # Default model
            "messages": cohere_messages,
        }

        # Handle temperature (Cohere uses temperature differently)
        if request.temperature is not None:
            params["temperature"] = request.temperature

        # Add max_tokens if provided
        if request.max_tokens is not None:
            params["max_tokens"] = request.max_tokens

        # Add any provider-specific parameters
        params.update(provider_specific_kwargs)

        try:
            # Make the streaming request
            stream = self.client.chat_stream(**params)

            # Process stream events
            for event in stream:
                if event.type == "content-delta":
                    # Extract delta content
                    content = event.delta.message.content.text

                    # Create a message for this chunk
                    message = ChatMessage(
                        role="assistant",
                        content=content
                    )

                    # No detailed usage stats in streaming mode
                    usage = {}

                    # Create a simple raw response
                    raw_response = {
                        "model": params["model"],
                        "delta": {
                            "content": content
                        }
                    }

                    yield ChatCompletionResponse(
                        message=message,
                        provider='cohere',
                        model=params["model"],
                        usage=usage,
                        raw_response=raw_response
                    )
        except Exception as e:
            raise Exception(f"Cohere API streaming error: {str(e)}")
