import os
import sys
import time
import json
import uuid
from typing import List, Optional, Dict, Any, AsyncGenerator
import inspect  # Import inspect for debugging

from fastapi import FastAPI, HTTPException, Request, Depends  # Add Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
# Import run_in_threadpool
from starlette.concurrency import iterate_in_threadpool, run_in_threadpool
from fastapi.security import HTTPBearer  # Import HTTPBearer

# Ensure the uniinfer package directory is in the Python path
# Adjust the path as necessary based on your project structure
script_dir = os.path.dirname(os.path.abspath(__file__))
uniinfer_package_path = os.path.join(script_dir, "packages", "uniinfer")
if uniinfer_package_path not in sys.path:
    sys.path.insert(0, uniinfer_package_path)

# Now import from uniioai (assuming it's inside the uniinfer package structure)
try:
    # Import get_provider_api_key as well
    from uniinfer.uniioai import stream_completion, get_completion, get_provider_api_key
    from uniinfer.errors import UniInferError, AuthenticationError, ProviderError, RateLimitError
except ImportError as e:
    print(f"Error importing from uniinfer.uniioai: {e}")
    print("Please ensure uniioai.py is correctly placed within the uniinfer package structure")
    print(f"Attempted path: {uniinfer_package_path}")
    sys.exit(1)


app = FastAPI(
    title="UniIOAI API",
    description="OpenAI-compatible API wrapper using UniInfer",
    version="0.1.0",
)

# Define the security scheme
security = HTTPBearer()

# --- Pydantic Models for OpenAI Compatibility ---


class ChatMessageInput(BaseModel):
    role: str
    content: str


class ChatCompletionRequestInput(BaseModel):
    model: str  # Expected format: "provider@modelname"
    messages: List[ChatMessageInput]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500
    stream: Optional[bool] = False
    base_url: Optional[str] = None  # Add base_url field
    # Add other common OpenAI parameters if needed, e.g., top_p, frequency_penalty


class ChatMessageOutput(BaseModel):
    role: str
    content: Optional[str] = None


class ChoiceDelta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class StreamingChoice(BaseModel):
    index: int = 0
    delta: ChoiceDelta
    finish_reason: Optional[str] = None


class StreamingChatCompletionChunk(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4()}")
    object: str = "chat.completion.chunk"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[StreamingChoice]


class NonStreamingChoice(BaseModel):
    index: int = 0
    message: ChatMessageOutput
    finish_reason: str = "stop"  # Assuming stop, uniinfer might not provide this


class NonStreamingChatCompletion(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4()}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[NonStreamingChoice]
    # uniinfer doesn't provide usage yet
    usage: Optional[Dict[str, int]] = None


# --- Models for /v1/models endpoint ---

class Model(BaseModel):
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "uniinfer"  # Or determine dynamically if needed


class ModelList(BaseModel):
    object: str = "list"
    data: List[Model]


# --- Predefined Models ---
# TODO: Consider making this list configurable or dynamically generated
PREDEFINED_MODELS = [
    "mistral@mistral-tiny-latest",
    "mistral@mistral-small-latest",
    "mistral@mistral-medium-latest",
    "mistral@mistral-large-latest",
    "mistral@codestral-latest",

    "ollama@moondream:v2",
    "ollama@phi4-mini:latest",
    "ollama@gemma3:4b",
    "ollama@nomic-embed-text:latest",
    "ollama@deepseek-r1:1.5b",

    "openrouter@nvidia/llama-3.3-nemotron-super-49b-v1:free",
    "openrouter@deepseek/deepseek-chat-v3-0324:free",
    "openrouter@google/gemma-3-12b-it:free",
    "openrouter@meta-llama/llama-3.3-70b-instruct:free",
    "openrouter@mistralai/mistral-small-3.1-24b-instruct:free",

    "arli@Mistral-Nemo-12B-ArliAI-RPMax-v1.3",
    "arli@Mistral-Nemo-12B-Instruct-2407",
    "arli@Mistral-Nemo-12B-Nemomix-v4.0",
    "arli@Mistral-Nemo-12B-Pantheon-RP-1.6.1",
    "arli@Mistral-Nemo-12B-UnslopNemo-v4.1",

    "internlm@internlm3-latest",
    "internlm@internlm3-8b-instruct",
    "internlm@internvl3-latest",
    "internlm@internvl3-78b",
    "internlm@internvl-latest",

    "stepfun@step-1-256k",
    "stepfun@step-1v-32k",
    "stepfun@step-1-flash",
    "stepfun@step-1x-medium",
    "stepfun@step-1o-vision-32k",

    "upstage@solar-pro-250414",
    "upstage@solar-mini-250401",
    "upstage@openai/gpt-4o",
    "upstage@mistral/mixtral-8x7b-instruct-v0.1",
    "upstage@naver/hcx-003",

    "ngc@meta/llama-3.3-70b-instruct",
    "ngc@mistralai/mixtral-8x22b-instruct-v0.1",
    "ngc@google/gemma-3-27b-it",
    "ngc@nvidia/llama-3.1-nemotron-ultra-253b-v1",
    "ngc@deepseek-ai/deepseek-r1",

    "cloudflare@cf/meta-llama/llama-2-7b-chat-hf-lora",
    "cloudflare@cf/mistral/mistral-7b-instruct-v0.2-lora",
    "cloudflare@cf/google/gemma-7b-it-lora",
    "cloudflare@cf/openai/whisper-tiny-en",
    "cloudflare@cf/llava-hf/llava-1.5-7b-hf",

    "huggingface@meta-llama/Llama-3.3-70B-Instruct",
    "huggingface@mistralai/Mixtral-8x7B-Instruct-v0.1",
    "huggingface@google/gemma-2-27b-it",
    "huggingface@deepseek-ai/DeepSeek-V3",
    "huggingface@Qwen/Qwen2.5-72B-Instruct",

    "cohere@command-r",
    "cohere@command-a-03-2025",
    "cohere@command-r-plus",
    "cohere@embed-v4.0",
    "cohere@rerank-v3.5",

    "moonshot@moonshot-v1-128k",
    "moonshot@moonshot-v1-32k",
    "moonshot@moonshot-v1-128k-vision-preview",
    "moonshot@moonshot-v1-8k",
    "moonshot@kimi-latest",

    "groq@llama3-70b-8192",
    "groq@llama3-8b-8192",
    "groq@meta-llama/llama-4-maverick-17b-128e-instruct",
    "groq@whisper-large-v3",
    "groq@deepseek-r1-distill-llama-70b",

    "gemini@models/gemini-1.5-pro-latest",
    "gemini@models/gemini-1.5-flash-latest",
    "gemini@models/gemini-2.5-pro-exp-03-25",
    "gemini@models/gemini-2.0-flash-exp",
    "gemini@models/gemma-3-27b-it",

    "ai21@jamba-1.6-mini",
    "ai21@jamba-1.6-large",
]


# --- Helper Functions ---

# Update signature: remove api_bearer_token, add provider_api_key
async def stream_response_generator(messages: List[Dict], provider_model: str, temp: float, max_tok: int, provider_api_key: Optional[str], base_url: Optional[str]) -> AsyncGenerator[str, None]:
    """Generates OpenAI-compatible SSE chunks from uniioai.stream_completion using a thread pool."""
    completion_id = f"chatcmpl-{uuid.uuid4()}"
    created_time = int(time.time())
    model_name = provider_model

    # First chunk sends the role
    first_chunk_data = StreamingChatCompletionChunk(
        id=completion_id,
        created=created_time,
        model=model_name,
        choices=[StreamingChoice(delta=ChoiceDelta(role="assistant"))]
    )
    yield f"data: {first_chunk_data.model_dump_json()}\n\n"

    try:
        # Create the synchronous generator instance, passing the retrieved key
        sync_generator = stream_completion(
            # Pass provider_api_key
            messages, provider_model, temp, max_tok, provider_api_key=provider_api_key, base_url=base_url)

        # --- Debugging ---
        print(f"DEBUG: Type of sync_generator: {type(sync_generator)}")
        print(
            f"DEBUG: Is sync_generator a generator? {inspect.isgenerator(sync_generator)}")
        iterator_obj = iterate_in_threadpool(sync_generator)
        print(
            f"DEBUG: Type of iterator_obj from iterate_in_threadpool: {type(iterator_obj)}")
        print(
            f"DEBUG: Is iterator_obj an async generator? {inspect.isasyncgen(iterator_obj)}")
        print(
            f"DEBUG: iterator_obj has __aiter__: {hasattr(iterator_obj, '__aiter__')}")
        print(
            f"DEBUG: iterator_obj has __anext__: {hasattr(iterator_obj, '__anext__')}")
        # --- End Debugging ---

        # Iterate over the synchronous generator in a thread pool
        async for content_chunk in iterator_obj:  # Use the debugged object
            if content_chunk:  # Ensure we don't send empty chunks
                chunk_data = StreamingChatCompletionChunk(
                    id=completion_id,
                    created=created_time,
                    model=model_name,
                    choices=[StreamingChoice(
                        delta=ChoiceDelta(content=content_chunk))]
                )
                yield f"data: {chunk_data.model_dump_json()}\n\n"

        # Last chunk signals completion
        final_chunk_data = StreamingChatCompletionChunk(
            id=completion_id,
            created=created_time,
            model=model_name,
            choices=[StreamingChoice(
                delta=ChoiceDelta(), finish_reason="stop")]
        )
        yield f"data: {final_chunk_data.model_dump_json()}\n\n"

    except (UniInferError, ValueError) as e:
        print(f"Error during streaming: {e}")
        # Optionally yield an error chunk (though not standard OpenAI)
        error_chunk = {"error": {"message": str(
            e), "type": type(e).__name__, "code": None}}
        yield f"data: {json.dumps(error_chunk)}\n\n"
    except Exception as e:
        print(f"Unexpected error during streaming: {e}")
        import traceback
        traceback.print_exc()
        error_chunk = {"error": {
            "message": f"Unexpected server error: {type(e).__name__}", "type": "internal_server_error", "code": None}}
        yield f"data: {json.dumps(error_chunk)}\n\n"

    yield "data: [DONE]\n\n"


# --- API Endpoints ---

@app.get("/v1/models", response_model=ModelList)
async def list_models():
    """
    OpenAI-compatible endpoint to list available models.
    Returns a predefined list of models supported by UniInfer.
    """
    model_data = [Model(id=model_id) for model_id in PREDEFINED_MODELS]
    return ModelList(data=model_data)


@app.post("/v1/chat/completions")
# Add the security dependency
async def chat_completions(request_input: ChatCompletionRequestInput, token: str = Depends(security)):
    """
    OpenAI-compatible chat completions endpoint.
    Uses the 'model' field in the format 'provider@modelname'.
    Requires Bearer token authentication (used for key retrieval).
    Optionally accepts a 'base_url'. If provider is 'ollama' and no base_url is provided,
    it defaults to 'https://amp1.mooo.com:11444'.
    """
    api_bearer_token = token.credentials  # This is the token from the header
    base_url = request_input.base_url  # Get base_url from request first
    provider_model = request_input.model
    messages_dict = [msg.model_dump() for msg in request_input.messages]

    try:
        # --- API Key Retrieval & Base URL Logic ---
        if '@' not in provider_model:
            raise HTTPException(
                status_code=400, detail="Invalid model format. Expected 'provider@modelname'.")
        provider_name = provider_model.split('@', 1)[0]

        # Set default base_url for ollama if not provided
        if provider_name == "ollama" and base_url is None:
            base_url = "https://amp1.mooo.com:11444"

        try:
            # Call the helper function from uniioai.py
            provider_api_key = get_provider_api_key(
                api_bearer_token, provider_name)
        except (ValueError, AuthenticationError) as e:
            # Handle errors during key retrieval specifically
            raise HTTPException(
                status_code=401, detail=f"API Key Retrieval Failed: {e}")
        # --- End API Key Retrieval & Base URL Logic ---

        if request_input.stream:
            # Use the async generator with StreamingResponse
            return StreamingResponse(
                stream_response_generator(
                    messages=messages_dict,
                    provider_model=provider_model,
                    temp=request_input.temperature,
                    max_tok=request_input.max_tokens,
                    provider_api_key=provider_api_key,  # Pass retrieved key
                    base_url=base_url  # Pass potentially modified base_url
                ),
                media_type="text/event-stream"
            )
        else:
            # Wrap synchronous get_completion in run_in_threadpool
            full_content = await run_in_threadpool(
                get_completion,  # The sync function
                messages=messages_dict,
                provider_model_string=provider_model,
                temperature=request_input.temperature,
                max_tokens=request_input.max_tokens,
                provider_api_key=provider_api_key,  # Pass retrieved key
                base_url=base_url  # Pass potentially modified base_url
            )

            # Format the response according to OpenAI spec
            response_data = NonStreamingChatCompletion(
                model=provider_model,
                choices=[
                    NonStreamingChoice(
                        message=ChatMessageOutput(
                            role="assistant", content=full_content)
                    )
                ]
                # Usage data is not available from uniioai currently
            )
            return response_data

    # Catches ValueErrors from uniioai completion functions (e.g., model format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # Note: AuthenticationError from uniioai.py key retrieval is handled above
    except AuthenticationError as e:
        # This might now only catch auth errors *within* the provider call itself, if any
        raise HTTPException(
            status_code=401, detail=f"Provider Authentication Error: {e}")
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=f"Rate Limit Error: {e}")
    except ProviderError as e:
        raise HTTPException(
            status_code=500, detail=f"Provider Error ({provider_name}): {e}")
    except UniInferError as e:  # Catches general uniinfer errors
        raise HTTPException(status_code=500, detail=f"UniInfer Error: {e}")
    except Exception as e:
        # Catch-all for unexpected errors
        print(
            f"Unexpected error in /v1/chat/completions: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {type(e).__name__}")


@app.get("/")
async def root():
    return {"message": "UniIOAI API is running. Use POST /v1/chat/completions or GET /v1/models"}


# --- Run the API (for local development) ---

if __name__ == "__main__":
    import uvicorn
    print("Starting UniIOAI API server...")
    # Ensure the path adjustment happens before this point if running directly
    # The sys.path modification at the top should handle this.
    # Set workers to 1 for low-memory environments
    uvicorn.run(app, host="0.0.0.0", port=8123, workers=1)

    # Example curl commands:
    # List models:
    # curl http://localhost:8123/v1/models

    # Non-streaming (replace YOUR_API_TOKEN):
    # curl -X POST http://localhost:8123/v1/chat/completions -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_API_TOKEN" -d '{"model": "groq@llama3-8b-8192", "messages": [{"role": "user", "content": "Say hello!"}], "stream": false}'
    # Non-streaming with base_url (e.g., for Ollama):
    # curl -X POST http://localhost:8123/v1/chat/completions -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_API_TOKEN_OR_CREDGOO_COMBO" -d '{"model": "ollama@llama3", "messages": [{"role": "user", "content": "Say hello!"}], "stream": false, "base_url": "http://localhost:11434"}'

    # Streaming (replace YOUR_API_TOKEN):
    # curl -N -X POST http://localhost:8123/v1/chat/completions -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_API_TOKEN" -d '{"model": "groq@llama3-8b-8192", "messages": [{"role": "user", "content": "Tell me a short story about a robot learning to paint."}], "stream": true}'
    # Streaming with base_url (e.g., for Ollama):
    # curl -N -X POST http://localhost:8123/v1/chat/completions -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_API_TOKEN_OR_CREDGOO_COMBO" -d '{"model": "ollama@llama3", "messages": [{"role": "user", "content": "Tell me a short story."}], "stream": true, "base_url": "http://localhost:11434"}'
