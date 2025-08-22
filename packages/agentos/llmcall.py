import json
import time
import os
from uniinfer import (
    ChatMessage,
    ChatCompletionRequest,
    ProviderFactory
)
from credgoo import get_api_key
try:
    from strukt2meta.jsonclean import cleanify_json  # preferred if available
except Exception:
    try:
        from json_repair import repair_json as _repair_json

        def cleanify_json(text: str) -> str:
            try:
                return _repair_json(text)
            except Exception:
                return text
    except Exception:

        def cleanify_json(text: str) -> str:
            # Last-resort no-op if no cleaner available
            return text

# Load configuration from config.json
with open("./config.json", "r") as config_file:
    config = json.load(config_file)


def call_ai_model(prompt, input_text, verbose=False, json_cleanup=False, task_type="default"):
    """Call AI model with task-specific configuration.

    Args:
        prompt: The system prompt
        input_text: The user input text
        verbose: Whether to enable verbose output
        json_cleanup: Whether to clean up JSON response
        task_type: Type of task ("default", "kriterien") to determine model config
    """
    # Get provider and model based on task type
    if task_type == "kriterien":
        # Use kriterien-specific configuration from config.json
        kriterien_config = config.get("kriterien", {})
        provider_name = kriterien_config.get("provider", "tu")
        model_name = kriterien_config.get("model", "deepseek-r1")
        max_context_tokens = kriterien_config.get("max_context_tokens", 32768)
        max_response_tokens = kriterien_config.get(
            "max_response_tokens", 16000)
    else:
        # Default configuration for other tasks
        provider_name = config.get("provider", "tu")
        model_name = config.get("model", "mistral-small-3.1-24b")
        max_context_tokens = 24000  # Conservative estimate for default tasks
        max_response_tokens = 2048  # Reduced response tokens for default tasks

    # Environment variable override ALWAYS wins (so .env can force deepseek etc.)
    env_provider = os.getenv("PROVIDER")
    env_model = os.getenv("MODEL")
    if env_provider:
        provider_name = env_provider
    if env_model:
        model_name = env_model

    # Known model hard limits (extend as needed)
    MODEL_CONTEXT_LIMITS = {
        "deepseek-r1": 32768,
    }
    if model_name in MODEL_CONTEXT_LIMITS:
        # Never trust an oversized config value if we know the real window.
        max_context_tokens = min(max_context_tokens, MODEL_CONTEXT_LIMITS[model_name])

    # Cap absurd response requests early (e.g. config had 64000 for a 32k model)
    if max_response_tokens > max_context_tokens // 2:
        max_response_tokens = max_context_tokens // 2

    # Get a provider instance (API key is retrieved automatically via Credgoo)
    provider = ProviderFactory.get_provider(
        name=provider_name,
        api_key=get_api_key(provider_name)
    )

    # Handle long documents by truncating if necessary

    # --- Token Estimation Helpers -------------------------------------------------
    # Use a conservative ratio (≈4 chars per token) for safety; adjust easily here.
    def estimate_tokens(text: str) -> int:
        return max(1, len(text) // 4)

    prompt_tokens = estimate_tokens(prompt)
    input_tokens = estimate_tokens(input_text)
    total_input_tokens = prompt_tokens + input_tokens

    # Set input character limits based on task type
    if task_type == "kriterien":
        # Use kriterien-specific limits from config.json
        kriterien_config = config.get("kriterien", {})
        max_safe_input_chars = kriterien_config.get(
            "max_safe_input_chars", 400000)
        safety_margin = kriterien_config.get("safety_margin", 5000)
    else:
        max_safe_input_chars = 40000  # Conservative limit for default tasks
        safety_margin = 500  # Smaller safety margin for default tasks

    # Ensure response size fits context: shrink response first if excessive.
    def clamp_response():
        nonlocal max_response_tokens
        # Guarantee minimal breathing room for a response
        available_for_response = max_context_tokens - (prompt_tokens + input_tokens) - safety_margin
        if available_for_response < 256:
            # Force input shrinking later; keep a minimal response window
            max_response_tokens = 256
        else:
            max_response_tokens = min(max_response_tokens, available_for_response)

    clamp_response()

    # Iterative truncation strategy: keep head and tail, reduce until fits.
    def truncate_middle(text: str, target_chars: int) -> str:
        if len(text) <= target_chars:
            return text
        keep_head = target_chars // 2
        keep_tail = target_chars - keep_head
        removed = len(text) - target_chars
        return (
            text[:keep_head] +
            f"\n\n[... TRUNCATED {removed} chars ...]\n\n" +
            text[-keep_tail:]
        )

    # Hard upper bound by chars from config, then adjust for context window.
    if len(input_text) > max_safe_input_chars:
        input_text = truncate_middle(input_text, max_safe_input_chars)
        input_tokens = estimate_tokens(input_text)
        total_input_tokens = prompt_tokens + input_tokens

    # Now loop while context would overflow.
    max_loops = 8
    loop = 0
    while (prompt_tokens + input_tokens + max_response_tokens + safety_margin) > max_context_tokens and loop < max_loops:
        # Reduce input size progressively (exponential decay toward fit)
        available_for_input_tokens = max_context_tokens - prompt_tokens - max_response_tokens - safety_margin
        if available_for_input_tokens < 200:  # if too tiny, also shrink response
            max_response_tokens = max(256, max_response_tokens // 2)
            available_for_input_tokens = max_context_tokens - prompt_tokens - max_response_tokens - safety_margin
        # Convert to char budget (approx 4 chars/token)
        target_chars = max(500, available_for_input_tokens * 4)
        if len(input_text) > target_chars:
            input_text = truncate_middle(input_text, target_chars)
            input_tokens = estimate_tokens(input_text)
            total_input_tokens = prompt_tokens + input_tokens
            clamp_response()
        else:
            break
        loop += 1

    if verbose:
        debug_total = prompt_tokens + input_tokens + max_response_tokens
        print(
            f"[DEBUG] model={model_name} prompt={prompt_tokens} input={input_tokens} response={max_response_tokens} total={debug_total} window={max_context_tokens} safety_margin={safety_margin} loops={loop}"
        )

    # Create a chat request
    request = ChatCompletionRequest(
        messages=[
            ChatMessage(role="system", content=prompt),
            ChatMessage(role="user", content=input_text)
        ],
        model=model_name,  # Use model from config
        temperature=0.7,  # Adjust randomness
        max_tokens=max_response_tokens,  # Limit the response length
        streaming=verbose  # Enable streaming if verbose mode is on
    )

    if verbose:
        # Stream the response and write it to the terminal
        print("\n=== Streaming Response ===\n")
        response_text = ""
        for chunk in provider.stream_complete(request):
            content = chunk.message.content
            print(content, end="", flush=True)
            response_text += content
        print("\n=== End of Response ===\n")

        # Add 2-second cooldown after AI invocation
        time.sleep(2)

        if json_cleanup:
            # Cleanify the streamed response
            return cleanify_json(response_text)
        else:
            return response_text
    else:
        # Get the completion response
        response = provider.complete(request)

        # Add 2-second cooldown after AI invocation
        time.sleep(2)

        if json_cleanup:
            # Cleanify the response
            return cleanify_json(response.message.content)
        else:
            return response.message.content
