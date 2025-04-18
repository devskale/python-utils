"""
Groq provider implementation.
"""
import os
from typing import Dict, Any, Iterator, Optional, List

from ..core import ChatProvider, ChatCompletionRequest, ChatCompletionResponse, ChatMessage

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False


class GroqProvider(ChatProvider):
    """
    Provider for Groq API.

    Groq is a high-performance LLM inference provider.
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the Groq provider.

        Args:
            api_key (Optional[str]): The Groq API key.
            **kwargs: Additional configuration options.
        """
        if not api_key:
            from credgoo.credgoo import get_api_key
            api_key = get_api_key("groq")

        super().__init__(api_key)

        if not HAS_GROQ:
            raise ImportError(
                "groq package is required for the GroqProvider. "
                "Install it with: pip install groq"
            )

        # Initialize the Groq client
        # If api_key is None, groq will use GROQ_API_KEY environment variable
        self.client = Groq(api_key=self.api_key)

    def complete(
        self,
        request: ChatCompletionRequest,
        **provider_specific_kwargs
    ) -> ChatCompletionResponse:
        """
        Make a chat completion request to Groq.

        Args:
            request (ChatCompletionRequest): The request to make.
            **provider_specific_kwargs: Additional Groq-specific parameters.

        Returns:
            ChatCompletionResponse: The completion response.

        Raises:
            Exception: If the request fails.
        """
        # Convert messages to Groq format
        messages = [{"role": msg.role, "content": msg.content}
                    for msg in request.messages]

        # Prepare parameters
        params = {
            "model": request.model or "llama-3.1-8b",  # Default model
            "messages": messages,
            "temperature": request.temperature,
            "stream": False,
        }

        # Add max_tokens if provided (Groq uses max_tokens)
        if request.max_tokens is not None:
            params["max_tokens"] = request.max_tokens

        # Add any provider-specific parameters
        params.update(provider_specific_kwargs)

        try:
            # Make the chat completion request
            completion = self.client.chat.completions.create(**params)

            # Extract the response content
            message = ChatMessage(
                role=completion.choices[0].message.role,
                content=completion.choices[0].message.content
            )

            # Extract usage information
            usage = {}
            if hasattr(completion, 'usage'):
                usage = {
                    "prompt_tokens": completion.usage.prompt_tokens,
                    "completion_tokens": completion.usage.completion_tokens,
                    "total_tokens": completion.usage.total_tokens
                }

            # Create raw response (the groq library might not support model_dump_json())
            try:
                raw_response = completion.model_dump_json()
            except AttributeError:
                # Fallback to constructing a simple dict
                raw_response = {
                    "model": params["model"],
                    "choices": [{"message": {"role": message.role, "content": message.content}}],
                    "usage": usage
                }

            return ChatCompletionResponse(
                message=message,
                provider='groq',
                model=params["model"],
                usage=usage,
                raw_response=raw_response
            )
        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")

    @classmethod
    def list_models(cls, api_key: Optional[str] = None) -> List[str]:
        """
        List available models from Groq.

        Args:
            api_key (Optional[str]): The Groq API key. If not provided,
                it will try GROQ_API_KEY environment variable or credgoo.

        Returns:
            List[str]: A list of available model names.

        Raises:
            ValueError: If no API key can be found.
            Exception: If the API request fails.
        """
        try:
            # Prioritize the provided api_key parameter
            if not api_key:
                api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                try:
                    from credgoo.credgoo import get_api_key
                    api_key = get_api_key("groq")
                except ImportError:
                    api_key = None  # credgoo not available

            if not api_key:
                raise ValueError(
                    "API key is required to list Groq models. Provide it as an argument, set GROQ_API_KEY, or configure credgoo.")

            # Initialize client and fetch models
            client = Groq(api_key=api_key)
            models = client.models.list()

            # Extract model IDs
            return [model.id for model in models.data]
        except Exception as e:
            # Log the error for debugging
            import logging
            logging.warning(f"Failed to fetch Groq models: {str(e)}")

            # Fallback to default models if API call fails
            return [
                "llama-3.1-8b",
                "llama-3.1-70b",
                "llama-3.1-405b",
                "mixtral-8x7b-32768",
                "gemma-7b-it"
            ]

    def stream_complete(
        self,
        request: ChatCompletionRequest,
        **provider_specific_kwargs
    ) -> Iterator[ChatCompletionResponse]:
        """
        Stream a chat completion response from Groq.

        Args:
            request (ChatCompletionRequest): The request to make.
            **provider_specific_kwargs: Additional Groq-specific parameters.

        Returns:
            Iterator[ChatCompletionResponse]: An iterator of response chunks.

        Raises:
            Exception: If the request fails.
        """
        # Convert messages to Groq format
        messages = [{"role": msg.role, "content": msg.content}
                    for msg in request.messages]

        # Prepare parameters
        params = {
            "model": request.model or "llama-3.1-8b",
            "messages": messages,
            "temperature": request.temperature,
            "stream": True,
        }

        # Add max_tokens if provided (Groq uses max_tokens)
        if request.max_tokens is not None:
            params["max_tokens"] = request.max_tokens

        # Add any provider-specific parameters
        params.update(provider_specific_kwargs)

        try:
            # Make the streaming request
            completion_stream = self.client.chat.completions.create(**params)

            for chunk in completion_stream:
                content = chunk.choices[0].delta.content

                # Skip empty content chunks
                if not content:
                    continue

                # Create a message for this chunk
                message = ChatMessage(
                    role="assistant",  # Default role for streaming
                    content=content
                )

                # No usage stats in streaming mode
                usage = {}

                yield ChatCompletionResponse(
                    message=message,
                    provider='groq',
                    model=params["model"],
                    usage=usage,
                    raw_response={"delta": {"content": content}}
                )
        except Exception as e:
            raise Exception(f"Groq API streaming error: {str(e)}")
