"""
Cloudflare Workers AI provider implementation.
"""
import json
import requests
from typing import Dict, Any, Iterator, Optional, List

from ..core import ChatProvider, ChatCompletionRequest, ChatCompletionResponse, ChatMessage
from ..errors import map_provider_error, AuthenticationError


class CloudflareProvider(ChatProvider):
    """
    Provider for Cloudflare Workers AI.
    """

    def __init__(self, api_key: Optional[str] = None, account_id: Optional[str] = None, **kwargs):
        """
        Initialize the Cloudflare Workers AI provider.

        Args:
            api_key (Optional[str]): The Cloudflare API token.
            account_id (Optional[str]): The Cloudflare account ID.
            **kwargs: Additional provider-specific configuration parameters.
        """
        super().__init__(api_key)

        if not api_key:
            raise AuthenticationError("Cloudflare API token is required")

        if not account_id:
            raise AuthenticationError("Cloudflare account ID is required")

        self.account_id = account_id
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Save any additional configuration
        self.config = kwargs

    @classmethod
    def list_models(cls, api_key: Optional[str] = None, account_id: Optional[str] = None) -> list:
        """
        List available models from Cloudflare Workers AI.

        Args:
            api_key (Optional[str]): The Cloudflare API token.
            account_id (Optional[str]): The Cloudflare account ID.

        Returns:
            list: A list of available model names with readable format.
        """
        if api_key is None:
            try:
                from credgoo.credgoo import get_api_key
                api_key = get_api_key("cloudflare")
                if api_key is None:
                    raise ValueError(
                        "Failed to retrieve Cloudflare API key from credgoo")
            except ImportError:
                raise ValueError(
                    "Cloudflare API key is required when credgoo is not available")

        if account_id is None:
            raise ValueError("Cloudflare account ID is required")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(
                f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/models/search",
                headers=headers
            )
            response.raise_for_status()

            models_data = response.json()
            print(
                f"Full Cloudflare API response: {json.dumps(models_data, indent=2)}")

            # Extract model details from the response
            model_list = []
            if models_data.get("success", False) and "result" in models_data:
                for model in models_data["result"]:
                    if isinstance(model, dict) and "id" in model:
                        model_id = model["id"]

                        # Skip UUIDs
                        if len(model_id) == 36 and model_id.count("-") == 4:
                            continue

                        # Get model name or use ID as fallback
                        model_name = model.get("name", model_id)

                        # Check if model has price = 0 in properties
                        has_free_price = False
                        if "properties" in model:
                            for prop in model["properties"]:
                                if prop.get("property_id") == "price" and isinstance(prop.get("value"), list):
                                    for price_item in prop["value"]:
                                        if price_item.get("price") == 0:
                                            has_free_price = True
                                            break
                                    if has_free_price:
                                        break

                        # Only include models with @ prefix or valid names AND price = 0
                        if (model_id.startswith("@") or model["id"][0].isalpha()) and has_free_price:
                            model_list.append(model_name)

                # Sort models alphabetically by name
                model_list.sort()

            return model_list
        except Exception as e:
            raise Exception(f"Failed to fetch Cloudflare models: {str(e)}")

    def _prepare_messages(self, messages: List[ChatMessage]) -> str:
        """
        Prepare messages for Cloudflare Workers AI.

        Args:
            messages (List[ChatMessage]): The messages to convert.

        Returns:
            str: The formatted prompt for Workers AI.
        """
        # For single message, just return the content directly
        if len(messages) == 1 and messages[0].role == "user":
            return messages[0].content

        # Extract system message if present
        system_content = None
        for msg in messages:
            if msg.role == "system":
                system_content = msg.content
                break

        # For chat models, format as a conversation
        formatted_messages = []
        for msg in messages:
            if msg.role == "system":
                continue  # System message will be handled separately

            # Format based on role
            if msg.role == "user":
                formatted_messages.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                formatted_messages.append(f"Assistant: {msg.content}")

        # Add a final prompt for the assistant to respond
        formatted_messages.append("Assistant:")

        # Combine with system message if present
        if system_content:
            prompt = f"System: {system_content}\n\n" + \
                "\n".join(formatted_messages)
        else:
            prompt = "\n".join(formatted_messages)

        return prompt

    def complete(
        self,
        request: ChatCompletionRequest,
        **provider_specific_kwargs
    ) -> ChatCompletionResponse:
        """
        Make a chat completion request to Cloudflare Workers AI.

        Args:
            request (ChatCompletionRequest): The request to make.
            **provider_specific_kwargs: Additional Cloudflare-specific parameters.

        Returns:
            ChatCompletionResponse: The completion response.

        Raises:
            Exception: If the request fails.
        """
        try:
            # Get the model from the request - keep the @ symbol
            model = request.model or "@cf/meta/llama-3-8b-instruct"

            # Prepare the messages
            prompt = self._prepare_messages(request.messages)

            # Prepare the request data - Cloudflare doesn't expect a 'model' field in the body
            data = {
                "prompt": prompt,
            }

            # Add temperature if provided
            if request.temperature is not None:
                data["temperature"] = request.temperature

            # Add max_tokens if provided
            if request.max_tokens is not None:
                data["max_tokens"] = request.max_tokens

            # Add any provider-specific parameters
            for key, value in provider_specific_kwargs.items():
                data[key] = value

            # Make the API call - exactly as in the working example
            response = requests.post(
                self.base_url + model,
                headers=self.headers,
                json=data
            )

            # Check for errors
            if response.status_code != 200:
                error_msg = f"Cloudflare API error: {response.status_code} - {response.text}"
                raise Exception(error_msg)

            # Parse the response
            response_data = response.json()

            # Extract the completion text - Cloudflare usually returns directly in result field
            content = ""
            if "result" in response_data:
                if isinstance(response_data["result"], str):
                    content = response_data["result"]
                elif isinstance(response_data["result"], dict) and "response" in response_data["result"]:
                    content = response_data["result"]["response"]
                else:
                    content = str(response_data["result"])

            # Create a ChatMessage from the response
            message = ChatMessage(
                role="assistant",
                content=content
            )

            # Create usage information (Cloudflare may not provide detailed token counts)
            usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }

            return ChatCompletionResponse(
                message=message,
                provider='cloudflare',
                model=model,
                usage=usage,
                raw_response=response_data
            )

        except Exception as e:
            # Map the error to a standardized format
            mapped_error = map_provider_error("cloudflare", e)
            raise mapped_error

    def stream_complete(
        self,
        request: ChatCompletionRequest,
        **provider_specific_kwargs
    ) -> Iterator[ChatCompletionResponse]:
        """
        Stream a chat completion response from Cloudflare Workers AI.

        Args:
            request (ChatCompletionRequest): The request to make.
            **provider_specific_kwargs: Additional Cloudflare-specific parameters.

        Returns:
            Iterator[ChatCompletionResponse]: An iterator of response chunks.

        Raises:
            Exception: If the request fails.
        """
        try:
            # Get the model from the request - keep the @ symbol
            model = request.model or "@cf/meta/llama-3-8b-instruct"

            # Prepare the messages
            prompt = self._prepare_messages(request.messages)

            # Prepare the request data - Cloudflare doesn't expect a 'model' field in the body
            data = {
                "prompt": prompt,
                "stream": True,  # Enable streaming
            }

            # Add temperature if provided
            if request.temperature is not None:
                data["temperature"] = request.temperature

            # Add max_tokens if provided
            if request.max_tokens is not None:
                data["max_tokens"] = request.max_tokens

            # Add any provider-specific parameters
            for key, value in provider_specific_kwargs.items():
                data[key] = value

            print(f"Streaming request URL: {self.base_url + model}")
            print(f"Streaming data: {data}")

            # Make the streaming API call with stream=True
            response = requests.post(
                self.base_url + model,
                headers=self.headers,
                json=data,
                stream=True
            )

            # Check for errors
            if response.status_code != 200:
                error_msg = f"Cloudflare API error: {response.status_code} - {response.text}"
                raise Exception(error_msg)

            # Process the streaming response line by line
            accumulated_text = ""
            for line in response.iter_lines():
                if line:
                    chunk_data = line.decode("utf-8").strip()
                    if chunk_data.startswith("data: "):
                        chunk_data = chunk_data[len("data: "):]
                    try:
                        # Parse the JSON (may raise JSONDecodeError)
                        json_chunk = json.loads(chunk_data)

                        # Extract the chunk text based on the response format
                        chunk_text = ""
                        if "response" in json_chunk:  # Most common format
                            chunk_text = json_chunk["response"]
                        elif "result" in json_chunk:
                            if isinstance(json_chunk["result"], str):
                                chunk_text = json_chunk["result"]
                            elif isinstance(json_chunk["result"], dict) and "response" in json_chunk["result"]:
                                chunk_text = json_chunk["result"]["response"]

                        if not chunk_text:
                            continue

                        # Extract the chunk text based on the response format
                        chunk_text = ""
                        if "response" in json_chunk:  # Most common format
                            chunk_text = json_chunk["response"]
                        elif "result" in json_chunk:
                            if isinstance(json_chunk["result"], str):
                                chunk_text = json_chunk["result"]
                            elif isinstance(json_chunk["result"], dict) and "response" in json_chunk["result"]:
                                chunk_text = json_chunk["result"]["response"]

                        if not chunk_text:
                            continue

                        # Create a message for this chunk
                        message = ChatMessage(
                            role="assistant",
                            content=chunk_text
                        )

                        # Yield the chunk as a response
                        yield ChatCompletionResponse(
                            message=message,
                            provider='cloudflare',
                            model=model,
                            usage={},
                            raw_response=json_chunk
                        )

                        # Accumulate the text for potential error recovery
                        accumulated_text += chunk_text

                    except json.JSONDecodeError:
                        # Skip malformed chunks
                        continue
                    except Exception as chunk_error:
                        print(f"Error processing chunk: {str(chunk_error)}")
                        continue

            # If we didn't yield any chunks but got a response, handle as fallback
            if not accumulated_text and response.content:
                try:
                    # Try to parse the complete response
                    full_response = response.json()

                    # Extract content from the full response
                    content = ""
                    if "result" in full_response:
                        if isinstance(full_response["result"], str):
                            content = full_response["result"]
                        elif isinstance(full_response["result"], dict) and "response" in full_response["result"]:
                            content = full_response["result"]["response"]
                        else:
                            content = str(full_response["result"])

                    if content:
                        # Create a message for the entire response
                        message = ChatMessage(
                            role="assistant",
                            content=content
                        )

                        # Yield the complete response as a single chunk
                        yield ChatCompletionResponse(
                            message=message,
                            provider='cloudflare',
                            model=model,
                            usage={},
                            raw_response=full_response
                        )
                except Exception:
                    # If all else fails, return any raw text we can extract
                    if response.content:
                        try:
                            raw_text = response.content.decode('utf-8')
                            if raw_text:
                                # Create a message with whatever we got
                                message = ChatMessage(
                                    role="assistant",
                                    content=f"[Raw response: {raw_text[:500]}...]"
                                )

                                # Yield as a last resort
                                yield ChatCompletionResponse(
                                    message=message,
                                    provider='cloudflare',
                                    model=model,
                                    usage={},
                                    raw_response={"raw": raw_text}
                                )
                        except:
                            pass

        except Exception as e:
            # Map the error to a standardized format
            mapped_error = map_provider_error("cloudflare", e)
            raise mapped_error
