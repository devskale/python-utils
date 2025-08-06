import json
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


def call_ai_model(prompt, input_text, verbose=False, json_cleanup=False):
    # Get provider and model from config
    # Default to TU if not specified
    provider_name = config.get("provider", "tu")
    # Default to deepseek-r1 if not specified
    model_name = config.get("model", "deepseek-r1")

    # Get a provider instance (API key is retrieved automatically via Credgoo)
    provider = ProviderFactory.get_provider(
        name=provider_name,
        api_key=get_api_key(provider_name)
    )

    # Handle long documents by truncating if necessary
    # Be very conservative with mistral-small-3.1-24b context window
    max_context_tokens = 24000  # Conservative estimate for mistral-small-3.1-24b
    max_response_tokens = 2048  # Reduced response tokens to leave more room for input

    # Rough token estimation (1 token ≈ 3.5 characters for better safety)
    prompt_tokens = len(prompt) // 3
    input_tokens = len(input_text) // 3
    total_input_tokens = prompt_tokens + input_tokens

    # Be very aggressive with truncation to avoid API errors
    max_safe_input_chars = 40000  # Hard limit on input characters

    if len(input_text) > max_safe_input_chars or total_input_tokens + max_response_tokens > max_context_tokens:
        # Use the smaller of the two limits
        available_tokens = max_context_tokens - prompt_tokens - \
            max_response_tokens - 500  # Large safety margin
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
        if json_cleanup:
            # Cleanify the streamed response
            return cleanify_json(response_text)
        else:
            return response_text
    else:
        # Get the completion response
        response = provider.complete(request)
        if json_cleanup:
            # Cleanify the response
            return cleanify_json(response.message.content)
        else:
            return response.message.content
