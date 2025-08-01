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

def call_ai_model(prompt, input_text, verbose=False):
    # Get provider and model from config
    provider_name = config.get("provider", "tu")  # Default to TU if not specified
    model_name = config.get("model", "deepseek-r1")  # Default to deepseek-r1 if not specified

    # Get a provider instance (API key is retrieved automatically via Credgoo)
    provider = ProviderFactory.get_provider(
        name=provider_name,
        api_key=get_api_key(provider_name)
    )

    # Create a chat request
    request = ChatCompletionRequest(
        messages=[
            ChatMessage(role="system", content=prompt),
            ChatMessage(role="user", content=input_text)
        ],
        model=model_name,  # Use model from config
        temperature=0.7,  # Adjust randomness
        max_tokens=4096,  # Limit the response length
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
        return cleanify_json(response_text)  # Cleanify the streamed response
    else:
        # Get the completion response
        response = provider.complete(request)
        return cleanify_json(response.message.content)  # Cleanify the response