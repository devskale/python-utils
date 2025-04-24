"""
Google Gemini provider implementation.
"""
from typing import Dict, Any, Iterator, Optional, List

from ..core import ChatProvider, ChatCompletionRequest, ChatCompletionResponse, ChatMessage
from ..errors import map_provider_error

# Try to import the google.generativeai package
try:
    import google.generativeai as genai
    from google.generativeai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


class GeminiProvider(ChatProvider):
    """
    Provider for Google Gemini API.
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the Gemini provider.

        Args:
            api_key (Optional[str]): The Gemini API key.
            **kwargs: Additional provider-specific configuration parameters.
        """
        super().__init__(api_key)

        if not HAS_GENAI:
            raise ImportError(
                "The 'google-generativeai' package is required to use the Gemini provider. "
                "Install it with 'pip install google-generativeai'"
            )

        # Configure the Gemini client
        genai.configure(api_key=self.api_key)

        # Save any additional configuration
        self.config = kwargs

    def _prepare_content_and_config(self, request: ChatCompletionRequest) -> tuple:
        """
        Prepare content and config for Gemini API from our messages.

        Args:
            request (ChatCompletionRequest): The request to prepare for.

        Returns:
            tuple: (content, config) for the Gemini API.
        """
        # Extract all messages
        messages = request.messages

        # Look for system message
        system_message = None
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
                break

        # Prepare config with generation parameters
        config_params = {}
        if request.temperature is not None:
            config_params["temperature"] = request.temperature
        if request.max_tokens is not None:
            config_params["max_output_tokens"] = request.max_tokens

        # Add system message to config if present
        if system_message:
            config_params["system_instruction"] = system_message

        # Create the config object
        config = types.GenerateContentConfig(**config_params)

        # Prepare the content based on non-system messages
        # For simple queries with just one user message, use a simple string
        if len(messages) == 1 and messages[0].role == "user":
            content = messages[0].content
        else:
            # For more complex exchanges, format as a conversation
            content = []
            for msg in messages:
                if msg.role == "system":
                    # System messages handled in config
                    continue
                elif msg.role == "user":
                    content.append(
                        {"role": "user", "parts": [{"text": msg.content}]})
                elif msg.role == "assistant":
                    content.append(
                        {"role": "model", "parts": [{"text": msg.content}]})

        return content, config

    def complete(
        self,
        request: ChatCompletionRequest,
        **provider_specific_kwargs
    ) -> ChatCompletionResponse:
        """
        Make a chat completion request to Gemini.

        Args:
            request (ChatCompletionRequest): The request to make.
            **provider_specific_kwargs: Additional Gemini-specific parameters.

        Returns:
            ChatCompletionResponse: The completion response.

        Raises:
            Exception: If the request fails.
        """
        if self.api_key is None:
            raise ValueError("Gemini API key is required")

        try:
            # Get the model from the request or use a default
            model = request.model or "gemini-1.5-pro"

            # Prepare the content and config
            content, config = self._prepare_content_and_config(request)

            # Get the model instance
            model_instance = genai.GenerativeModel(model)

            # Make the API call
            response = model_instance.generate_content(
                contents=content,
                generation_config=config
            )

            # Extract response text
            content = response.text if hasattr(response, "text") else ""

            # Create a ChatMessage from the response
            message = ChatMessage(
                role="assistant",
                content=content
            )

            # Create usage information (Gemini doesn't provide detailed token counts)
            usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }

            return ChatCompletionResponse(
                message=message,
                provider='gemini',
                model=model,
                usage=usage,
                raw_response=response
            )

        except Exception as e:
            # Map the error to a standardized format
            mapped_error = map_provider_error("gemini", e)
            raise mapped_error

    @classmethod
    def list_models(cls, api_key: Optional[str] = None) -> list:
        """
        List available models from Gemini.

        Args:
            api_key (Optional[str]): The Gemini API key.

        Returns:
            list: A list of available model names.
        """
        if not HAS_GENAI:
            raise ImportError(
                "The 'google-generativeai' package is required to use the Gemini provider. "
                "Install it with 'pip install google-generativeai'"
            )

        # Try to get API key from credgoo if not provided
        if api_key is None:
            try:
                from credgoo.credgoo import get_api_key
                api_key = get_api_key("gemini")
                if api_key is None:
                    raise ValueError(
                        "Failed to retrieve Gemini API key from credgoo")
            except ImportError:
                raise ValueError(
                    "Gemini API key is required when credgoo is not available")

        genai.configure(api_key=api_key)
        models = []

        # Get models that support generateContent
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                models.append(m.name)

        return models

    def stream_complete(
        self,
        request: ChatCompletionRequest,
        **provider_specific_kwargs
    ) -> Iterator[ChatCompletionResponse]:
        """
        Stream a chat completion response from Gemini.

        Args:
            request (ChatCompletionRequest): The request to make.
            **provider_specific_kwargs: Additional Gemini-specific parameters.

        Returns:
            Iterator[ChatCompletionResponse]: An iterator of response chunks.

        Raises:
            Exception: If the request fails.
        """
        if self.api_key is None:
            raise ValueError("Gemini API key is required")

        try:
            # Get the model from the request or use a default
            model = request.model or "gemini-1.5-pro"

            # Prepare the content and config
            content, config = self._prepare_content_and_config(request)

            # Get the model instance
            model_instance = genai.GenerativeModel(model)

            # Make the streaming API call
            stream = model_instance.generate_content(
                contents=content,
                generation_config=config,
                stream=True
            )

            # Process the streaming response
            for chunk in stream:
                if hasattr(chunk, "text"):
                    # Create a message for this chunk
                    message = ChatMessage(
                        role="assistant",
                        content=chunk.text
                    )

                    # Create a response for this chunk
                    yield ChatCompletionResponse(
                        message=message,
                        provider='gemini',
                        model=model,
                        usage={},
                        raw_response=chunk
                    )

        except Exception as e:
            # Map the error to a standardized format
            mapped_error = map_provider_error("gemini", e)
            raise mapped_error
