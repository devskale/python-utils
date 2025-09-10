"""
Core classes for the UniInfer package.
"""
from typing import List, Dict, Any, Iterator, Optional


class ChatMessage:
    """
    A message in a chat conversation.

    Attributes:
        role (str): The role of the message sender (user, assistant, system).
        content (str): The content of the message.
    """

    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def to_dict(self) -> Dict[str, str]:
        """Convert to a dictionary format suitable for API requests."""
        return {
            "role": self.role,
            "content": self.content
        }


class ChatCompletionRequest:
    """
    A request for a chat completion.

    Attributes:
        messages (List[ChatMessage]): The conversation history.
        model (Optional[str]): The model to use for completion.
        temperature (float): Controls randomness in generation.
        max_tokens (Optional[int]): Maximum tokens to generate.
        streaming (bool): Whether to stream the response.
    """

    def __init__(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        streaming: bool = False
    ):
        self.messages = messages
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.streaming = streaming


class ChatCompletionResponse:
    """
    A response from a chat completion.

    Attributes:
        message (ChatMessage): The generated message.
        provider (str): The provider that generated the response.
        model (str): The model used for generation.
        usage (Dict): Token usage information.
        raw_response (Any): The raw response from the provider.
    """

    def __init__(
        self,
        message: ChatMessage,
        provider: str,
        model: str,
        usage: Dict,
        raw_response: Any
    ):
        self.message = message
        self.provider = provider
        self.model = model
        self.usage = usage
        self.raw_response = raw_response


class ChatProvider:
    """
    Abstract base class for chat providers.

    All provider implementations must inherit from this class and implement
    the complete and stream_complete methods.
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the provider with an API key and optional configuration.

        Args:
            api_key (Optional[str]): The API key for authentication.
            **kwargs: Additional provider-specific configuration parameters.
        """
        self.api_key = api_key
        # Additional provider-specific configuration can be handled by subclasses

    @classmethod
    def list_models(cls, api_key: Optional[str] = None, **kwargs) -> List[str]:
        """
        Standard interface for listing available models.

        Args:
            api_key (Optional[str]): API key if needed for listing models
            **kwargs: Additional provider-specific parameters

        Returns:
            List[str]: List of available model names
        """
        raise NotImplementedError("Providers must implement list_models")

    def complete(
        self,
        request: ChatCompletionRequest,
        **provider_specific_kwargs
    ) -> ChatCompletionResponse:
        """
        Make a chat completion request.

        Args:
            request (ChatCompletionRequest): The request to make.
            **provider_specific_kwargs: Additional provider-specific parameters.

        Returns:
            ChatCompletionResponse: The completion response.
        """
        raise NotImplementedError(
            "Providers must implement the complete method")

    def stream_complete(
        self,
        request: ChatCompletionRequest,
        **provider_specific_kwargs
    ) -> Iterator[ChatCompletionResponse]:
        """
        Stream a chat completion response.

        Args:
            request (ChatCompletionRequest): The request to make.
            **provider_specific_kwargs: Additional provider-specific parameters.

        Returns:
            Iterator[ChatCompletionResponse]: An iterator of response chunks.
        """
        raise NotImplementedError(
            "Providers must implement the stream_complete method")


class EmbeddingRequest:
    """
    A request for embeddings.

    Attributes:
        input (List[str]): The texts to embed.
        model (Optional[str]): The model to use for embedding.
        encoding_format (str): The format to return the embeddings in.
        dimensions (Optional[int]): The number of dimensions the resulting output embeddings should have.
        user (Optional[str]): A unique identifier representing your end-user.
    """

    def __init__(
        self,
        input: List[str],
        model: Optional[str] = None,
        encoding_format: str = "float",
        dimensions: Optional[int] = None,
        user: Optional[str] = None
    ):
        self.input = input
        self.model = model
        self.encoding_format = encoding_format
        self.dimensions = dimensions
        self.user = user


class EmbeddingResponse:
    """
    A response from an embedding request.

    Attributes:
        object (str): The object type, always "list".
        data (List[Dict]): The embedding data.
        model (str): The model used for embedding.
        usage (Dict): Token usage information.
        provider (str): The provider that generated the response.
        raw_response (Any): The raw response from the provider.
    """

    def __init__(
        self,
        object: str,
        data: List[Dict],
        model: str,
        usage: Dict,
        provider: str,
        raw_response: Any
    ):
        self.object = object
        self.data = data
        self.model = model
        self.usage = usage
        self.provider = provider
        self.raw_response = raw_response


class EmbeddingProvider:
    """
    Abstract base class for embedding providers.

    All embedding provider implementations must inherit from this class and implement
    the embed method.
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the provider with an API key and optional configuration.

        Args:
            api_key (Optional[str]): The API key for authentication.
            **kwargs: Additional provider-specific configuration parameters.
        """
        self.api_key = api_key
        # Additional provider-specific configuration can be handled by subclasses

    @classmethod
    def list_models(cls, **kwargs) -> List[str]:
        """
        Standard interface for listing available models.

        Args:
            **kwargs: Additional provider-specific parameters

        Returns:
            List[str]: List of available model names
        """
        raise NotImplementedError(
            "Embedding providers must implement list_models")

    def embed(
        self,
        request: EmbeddingRequest,
        **provider_specific_kwargs
    ) -> EmbeddingResponse:
        """
        Make an embedding request.

        Args:
            request (EmbeddingRequest): The request to make.
            **provider_specific_kwargs: Additional provider-specific parameters.

        Returns:
            EmbeddingResponse: The embedding response.
        """
        raise NotImplementedError(
            "Embedding providers must implement the embed method")
