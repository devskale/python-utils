import json
import time
from uniinfer import (
    ChatMessage,
    ChatCompletionRequest,
    ProviderFactory
)
from credgoo import get_api_key
from strukt2meta.jsonclean import cleanify_json

# Load configuration from config.json
with open("./config.json", "r") as config_file:
    config = json.load(config_file)


def call_ai_model(prompt, input_text, verbose=False, json_cleanup=False, task_type="default"):
    """Call AI model with task-specific configuration and retry logic.

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
        model_name = kriterien_config.get("model", "glm-4.5-355b")
        max_context_tokens = kriterien_config.get("max_context_tokens", 32768)
        max_response_tokens = kriterien_config.get(
            "max_response_tokens", 16000)
    else:
        # Default configuration for other tasks
        provider_name = config.get("provider", "tu")
        model_name = config.get("model", "mistral-small-3.2-24b")
        max_context_tokens = 24000  # Conservative estimate for default tasks
        max_response_tokens = 2048  # Reduced response tokens for default tasks

    # Get a provider instance (API key is retrieved automatically via Credgoo)
    provider = ProviderFactory.get_provider(
        name=provider_name,
        api_key=get_api_key(provider_name)
    )

    # Set max_retries based on provider (Gemini is more prone to failures)
    max_retries = 5 if provider_name == "gemini" else 3

    # Handle long documents by truncating if necessary

    # Rough token estimation (1 token ≈ 3.5 characters for better safety)
    prompt_tokens = len(prompt) // 3
    input_tokens = len(input_text) // 3
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

    if len(input_text) > max_safe_input_chars or total_input_tokens + max_response_tokens > max_context_tokens:
        # Use the smaller of the two limits
        available_tokens = max_context_tokens - prompt_tokens - \
            max_response_tokens - safety_margin
        max_input_chars = min(max_safe_input_chars, available_tokens * 3)

        if len(input_text) > max_input_chars:
            # Truncate from the middle to keep beginning and end
            keep_start = max_input_chars // 2
            keep_end = max_input_chars // 2

            truncated_text = (
                input_text[:keep_start] +
                f"\n\n[... DOCUMENT TRUNCATED - {len(input_text) - max_input_chars} characters removed for API limits ...]\n\n" +
                input_text[-keep_end:]
            )
            input_text = truncated_text

            if verbose:
                print(
                    f"⚠️  Document truncated due to length (kept {max_input_chars} chars of {len(input_text)} original chars)")

    # Create a chat request
    if provider_name == "gemini":
        # For Gemini, prepend system prompt to user message since system_instruction
        # is not supported in GenerationConfig
        combined_content = f"{prompt}\n\n{input_text}"
        request = ChatCompletionRequest(
            messages=[
                ChatMessage(role="user", content=combined_content)
            ],
            model=model_name,  # Use model from config
            temperature=0.7,  # Adjust randomness
            max_tokens=max_response_tokens,  # Limit the response length
            streaming=verbose  # Enable streaming if verbose mode is on
        )
    else:
        # Standard chat format for other providers
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

    # Try the API call with retries
    for attempt in range(max_retries):
        try:
            if verbose and attempt > 0:
                print(f"🔄 Retry attempt {attempt + 1}/{max_retries}")

            if verbose:
                # Stream the response and write it to the terminal
                print("\n=== Streaming Response ===\n")
                response_text = ""
                try:
                    for chunk in provider.stream_complete(request):
                        content = chunk.message.content
                        print(content, end="", flush=True)
                        response_text += content
                except Exception as e:
                    print(f"\n⚠️ Streaming error: {e}")
                    response_text = ""
                print("\n=== End of Response ===\n")

                # Add cooldown after AI invocation (longer for Gemini due to rate limiting)
                cooldown_time = 5 if provider_name == "gemini" else 2
                time.sleep(cooldown_time)

                if json_cleanup and response_text.strip():
                    # Cleanify the streamed response
                    result = cleanify_json(response_text)
                    if result:
                        return result
                elif response_text.strip():
                    return response_text
            else:
                # Get the completion response
                try:
                    response = provider.complete(request)
                except Exception as e:
                    if verbose:
                        print(f"⚠️ API call error: {e}")
                    # Continue to retry
                    continue

                # Add cooldown after AI invocation (longer for Gemini due to rate limiting)
                cooldown_time = 5 if provider_name == "gemini" else 2
                time.sleep(cooldown_time)

                if json_cleanup and response.message.content.strip():
                    # Cleanify the response
                    result = cleanify_json(response.message.content)
                    if result:
                        return result
                elif response.message.content.strip():
                    return response.message.content

            # If we get here, the response was empty or invalid
            if attempt < max_retries - 1:
                if verbose:
                    print(f"⚠️ Empty or invalid response, retrying in {cooldown_time}s...")
                time.sleep(cooldown_time)
            else:
                if verbose:
                    print("⚠️ All retry attempts failed")
                return None

        except Exception as e:
            if attempt < max_retries - 1:
                if verbose:
                    print(f"⚠️ API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                    cooldown_time = 5 if provider_name == "gemini" else 2
                    time.sleep(cooldown_time)
                continue
            else:
                if verbose:
                    print(f"⚠️ All retry attempts failed: {e}")
                return None

    return None
