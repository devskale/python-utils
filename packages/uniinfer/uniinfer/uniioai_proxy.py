import os
import sys
import time
import json
import uuid
from typing import List, Optional, Dict, Any, AsyncGenerator
import inspect  # Import inspect for debugging

from fastapi import FastAPI, HTTPException, Request, Depends  # Add Depends
# Add FileResponse and CORSMiddleware imports
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
# Import run_in_threadpool
from starlette.concurrency import iterate_in_threadpool, run_in_threadpool
from fastapi.security import HTTPBearer  # Import HTTPBearer
from uniinfer.examples.providers_config import PROVIDER_CONFIGS  # Add this import

# Ensure the uniinfer package directory is in the Python path
# Adjust the path as necessary based on your project structure
script_dir = os.path.dirname(os.path.abspath(__file__))
uniinfer_package_path = os.path.join(script_dir, "packages", "uniinfer")
if uniinfer_package_path not in sys.path:
    sys.path.insert(0, uniinfer_package_path)

# Now import from uniioai (assuming it's inside the uniinfer package structure)
try:
    # Import get_provider_api_key as well
    from uniinfer.uniioai import stream_completion, get_completion, get_provider_api_key, list_providers, list_models_for_provider
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

# --- Add CORS Middleware ---
# Allow requests from any origin for the web demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
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
    owned_by: str = "skaledev"  # Or determine dynamically if needed


class ModelList(BaseModel):
    object: str = "list"
    data: List[Model]


# --- Add ProviderList model for OpenAI‐style list response ---
class ProviderList(BaseModel):
    object: str = "list"
    data: List[str]


# --- Predefined Models ---
# TODO: Consider making this list configurable or dynamically generated
PREDEFINED_MODELS = [
    "mistral@mistral-tiny-latest",
    "ollama@qwen2.5:3b",
    "openrouter@google/gemma-3-12b-it:free",
    "arli@Mistral-Nemo-12B-Instruct-2407",
    "internlm@internlm3-latest",
    "stepfun@step-1-flash",
    "upstage@solar-mini-250401",
    "bigmodel@glm-4-flash",
    "ngc@google/gemma-3-27b-it",
    "cohere@command-r",
    "moonshot@kimi-latest",
    "groq@llama3-8b-8192",
    "gemini@models/gemma-3-27b-it",
    "chutes@Qwen/Qwen3-235B-A22B",
    "pollinations@grok"
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

    except NameError as e:
        # Specific catch for missing 'payload' or similar undefined names
        print(f"NameError during streaming: {e}")
        error_chunk = {
            "error": {
                "message": f"Stream internal error: {e}",
                "type": "NameError",
                "code": None
            }
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"
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

# --- Add Endpoint to Serve Web Demo HTML ---
@app.get("/webdemo", include_in_schema=False)
async def get_web_demo():
    """Serves the web demo HTML file."""
    # Calculate the path relative to this script file
    html_file_path = os.path.join(
        script_dir, "examples", "webdemo", "webdemo.html")
    if not os.path.exists(html_file_path):
        raise HTTPException(status_code=404, detail="webdemo.html not found")
    return FileResponse(html_file_path)
# --- End Web Demo Endpoint ---


@app.get("/v1/models", response_model=ModelList)
async def list_models():
    """
    OpenAI-compatible endpoint to list available models.
    Returns a predefined list of models supported by UniInfer.
    """
    model_data = [Model(id=model_id) for model_id in PREDEFINED_MODELS]
    return ModelList(data=model_data)


# --- Update /v1/providers to return ProviderList ---
@app.get("/v1/providers", response_model=ProviderList)
async def get_providers(token: str = Depends(security)):
    """
    OpenAI‐style endpoint to list available providers.
    """
    try:
        providers = list_providers()
        return ProviderList(data=providers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            base_url = PROVIDER_CONFIGS.get("ollama", {}).get(
                "extra_params", {}).get("base_url")
        print(f"DEBUG: Using base_url: {base_url}")

        try:
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


# --- Change dynamic list models to return ModelList ---
@app.get("/v1/models/{provider_name}", response_model=ModelList)
async def dynamic_list_models(provider_name: str, token: str = Depends(security)):
    """
    List available models for a specific provider, formatted OpenAI‐style.
    """
    try:
        raw_models = list_models_for_provider(provider_name, token.credentials)
        model_objs = [Model(id=m) for m in raw_models]
        return ModelList(data=model_objs)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {"message": "UniIOAI API is running. Visit /webdemo for the interactive demo, or use POST /v1/chat/completions or GET /v1/models"}


# --- Run the API (for local development) ---
def main():
    import uvicorn
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Run the UniIOAI API server.")
    parser.add_argument('--reload', action='store_true',
                        help='Enable auto-reloading')
    parser.add_argument('--port', type=int, default=8123,
                        help='Port to run the server on')

    args = parser.parse_args()

    print(
        f"Starting UniIOAI API server (reload={args.reload} at port {args.port})..."
    )
    uvicorn.run(
        "uniinfer.uniioai_proxy:app",
        host="0.0.0.0",
        port=args.port,
        workers=1,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
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
