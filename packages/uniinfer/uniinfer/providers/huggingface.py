"""
HuggingFace Inference provider implementation.
"""
from typing import Dict, Any, Iterator, Optional, List

from ..core import ChatProvider, ChatCompletionRequest, ChatCompletionResponse, ChatMessage

try:
    from huggingface_hub import InferenceClient, HfApi
    HAS_HUGGINGFACE = True
except ImportError:
    HAS_HUGGINGFACE = False


class HuggingFaceProvider(ChatProvider):
    """
    Provider for HuggingFace Inference API.
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the HuggingFace provider.

        Args:
            api_key (Optional[str]): The HuggingFace API key.
            **kwargs: Additional configuration options.
        """
        super().__init__(api_key)

        if not HAS_HUGGINGFACE:
            raise ImportError(
                "huggingface_hub package is required for the HuggingFaceProvider. "
                "Install it with: pip install huggingface_hub"
            )

        # Initialize the HuggingFace InferenceClient
        self.client = InferenceClient(
            token=self.api_key
        )

    def complete(
        self,
        request: ChatCompletionRequest,
        **provider_specific_kwargs
    ) -> ChatCompletionResponse:
        """
        Make a chat completion request to HuggingFace Inference API.

        Args:
            request (ChatCompletionRequest): The request to make.
            **provider_specific_kwargs: Additional HuggingFace-specific parameters.

        Returns:
            ChatCompletionResponse: The completion response.

        Raises:
            Exception: If the request fails.
        """
        if self.api_key is None:
            raise ValueError("HuggingFace API key is required")

        if not request.model:
            raise ValueError(
                "Model must be specified for HuggingFace Inference")

        try:
            # Format messages for the text_generation API
            # We'll extract the last user message for simplicity
            last_message = None
            for msg in reversed(request.messages):
                if msg.role == "user":
                    last_message = msg.content
                    break

            if last_message is None:
                raise ValueError("No user message found in the request")

            # Make the completion request using text_generation
            completion = self.client.text_generation(
                prompt=last_message,
                model=request.model,
                max_new_tokens=request.max_tokens or 1024,
                temperature=request.temperature or 0.7,
                **provider_specific_kwargs
            )

            # Create a message from the completion
            message = ChatMessage(
                role="assistant",
                content=completion
            )

            # Create simple usage information (HuggingFace doesn't provide detailed usage)
            usage = {
                "prompt_tokens": len(last_message.split()),
                "completion_tokens": len(completion.split()),
                "total_tokens": len(last_message.split()) + len(completion.split())
            }

            # Create raw response data
            raw_response = {
                "model": request.model,
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": completion
                        }
                    }
                ],
                "usage": usage
            }

            return ChatCompletionResponse(
                message=message,
                provider='huggingface',
                model=request.model,
                usage=usage,
                raw_response=raw_response
            )
        except Exception as e:
            if "too large to be loaded automatically" in str(e):
                model_size = str(e).split("(")[1].split(
                    ">")[0].strip() if "(" in str(e) else "unknown size"
                raise ValueError(
                    f"Model {request.model} is too large for automatic loading ({model_size} > 10GB). "
                    "Please use one of these smaller models: {', '.join(self.list_models(self.api_key)[:5])}\n"
                    "For large models, you need to deploy them separately using Inference Endpoints: "
                    "https://huggingface.co/docs/inference-endpoints/index"
                ) from e
            elif "403 Forbidden" in str(e):
                raise PermissionError(
                    f"Access denied to model {request.model}. "
                    "Possible reasons:\n"
                    "1. Your API key lacks permissions for this model\n"
                    "2. The model requires gated access (may need application)\n"
                    "3. The model is private\n\n"
                    "Check permissions at: https://huggingface.co/settings/tokens\n"
                    "Request access at: https://huggingface.co/{request.model.split('/')[0]}"
                ) from e
            elif "Pro subscription" in str(e):
                raise PermissionError(
                    f"Model {request.model} requires a Pro subscription. \n"
                    "You can either:\n"
                    "1. Upgrade your account at https://huggingface.co/pricing\n"
                    "2. Use one of these free models: {', '.join(self.list_models(self.api_key)[:5])}"
                ) from e
            elif "Pro subscription" in str(e):
                raise PermissionError(
                    f"Model {request.model} requires a Pro subscription. \n"
                    "You can either:\n"
                    "1. Upgrade your account at https://huggingface.co/pricing\n"
                    "2. Use one of these free models: {', '.join(self.list_models(self.api_key)[:5])}"
                ) from e
            raise Exception(f"HuggingFace Inference API error: {str(e)}")

    @classmethod
    def list_models(cls, api_key: Optional[str] = None) -> List[str]:
        """
        List available models from HuggingFace.

        Args:
            api_key (Optional[str]): The HuggingFace API key.

        Returns:
            List[str]: A list of available model names.

        Raises:
            Exception: If the request fails.
        """
        try:
            if not HAS_HUGGINGFACE:
                raise ImportError(
                    "huggingface_hub package is required for the HuggingFaceProvider. "
                    "Install it with: pip install huggingface_hub"
                )

            if not api_key:
                from credgoo.credgoo import get_api_key
                api_key = get_api_key("huggingface")
                if not api_key:
                    raise ValueError(
                        "HuggingFace API key is required for listing models")

            # Initialize HfApi client
            hf_api = HfApi(
                token=api_key,
                library_name="text-generation-inference"
            )

            # Fetch text-generation models sorted by popularity
            models = hf_api.list_models(
                inference="warm",
                sort="likes7d",
                filter="text-generation",
                limit=100
            )
            # Create a list of model dictionaries with relevant information
            model_list = []
            for model in models:
                if model.id and model.pipeline_tag:
                    model_info = f'{model.id} {model.pipeline_tag}'
                    model_list.append(model_info)
            # Extract model IDs
            return model_list
        except Exception as e:
            # Log the error for debugging
            import logging
            logging.warning(f"Failed to fetch HuggingFace models: {str(e)}")

            # Fallback to default models if API call fails
            return [
                "meta-llama/Meta-Llama-3-8B-Instruct",
                "meta-llama/Meta-Llama-3-70B-Instruct",
                "mistralai/Mistral-7B-Instruct-v0.1",
                "google/gemma-7b-it"
            ]

    def stream_complete(
        self,
        request: ChatCompletionRequest,
        **provider_specific_kwargs
    ) -> Iterator[ChatCompletionResponse]:
        """
        Stream a chat completion response from HuggingFace Inference API.

        Args:
            request (ChatCompletionRequest): The request to make.
            **provider_specific_kwargs: Additional HuggingFace-specific parameters.

        Returns:
            Iterator[ChatCompletionResponse]: An iterator of response chunks.

        Raises:
            Exception: If the request fails.
        """
        if self.api_key is None:
            raise ValueError("HuggingFace API key is required")

        if not request.model:
            raise ValueError(
                "Model must be specified for HuggingFace Inference")

        try:
            # Format messages for the text_generation API
            # We'll extract the last user message for simplicity
            last_message = None
            for msg in reversed(request.messages):
                if msg.role == "user":
                    last_message = msg.content
                    break

            if last_message is None:
                raise ValueError("No user message found in the request")

            # Make the streaming request using text_generation with stream=True
            stream = self.client.text_generation(
                prompt=last_message,
                model=request.model,
                max_new_tokens=request.max_tokens or 500,
                temperature=request.temperature or 0.7,
                stream=True,
                **provider_specific_kwargs
            )

            for chunk in stream:
                # Create a message for this chunk
                message = ChatMessage(
                    role="assistant",
                    content=chunk
                )

                # Stream chunks don't have usage information
                usage = {}

                # Create raw response structure
                raw_response = {
                    "model": request.model,
                    "choices": [
                        {
                            "delta": {
                                "content": chunk
                            }
                        }
                    ]
                }

                yield ChatCompletionResponse(
                    message=message,
                    provider='huggingface',
                    model=request.model,
                    usage=usage,
                    raw_response=raw_response
                )
        except Exception as e:
            if "too large to be loaded automatically" in str(e):
                model_size = str(e).split("(")[1].split(
                    ">")[0].strip() if "(" in str(e) else "unknown size"
                raise ValueError(
                    f"Model {request.model} is too large for automatic loading ({model_size} > 10GB). "
                    "Please use one of these smaller models: {', '.join(self.list_models(self.api_key)[:5])}\n"
                    "For large models, you need to deploy them separately using Inference Endpoints: "
                    "https://huggingface.co/docs/inference-endpoints/index"
                ) from e
            elif "403 Forbidden" in str(e):
                raise PermissionError(
                    f"Access denied to model {request.model}. "
                    "Possible reasons:\n"
                    "1. Your API key lacks permissions for this model\n"
                    "2. The model requires gated access (may need application)\n"
                    "3. The model is private\n\n"
                    "Check permissions at: https://huggingface.co/settings/tokens\n"
                    "Request access at: https://huggingface.co/{request.model.split('/')[0]}"
                ) from e
            elif "Pro subscription" in str(e):
                raise PermissionError(
                    f"Model {request.model} requires a Pro subscription. \n"
                    "You can either:\n"
                    "1. Upgrade your account at https://huggingface.co/pricing\n"
                    "2. Use one of these free models: {', '.join(self.list_models(self.api_key)[:5])}"
                ) from e
            elif "Pro subscription" in str(e):
                raise PermissionError(
                    f"Model {request.model} requires a Pro subscription. \n"
                    "You can either:\n"
                    "1. Upgrade your account at https://huggingface.co/pricing\n"
                    "2. Use one of these free models: {', '.join(self.list_models(self.api_key)[:5])}"
                ) from e
            raise Exception(f"HuggingFace Inference API error: {str(e)}")
