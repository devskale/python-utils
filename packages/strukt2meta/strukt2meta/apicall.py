import json
from uniinfer import (
    ChatMessage,
    ChatCompletionRequest,
    ProviderFactory
)
from credgoo import get_api_key

# Load configuration from config.json
with open("./config.json", "r") as config_file:
    config = json.load(config_file)

def call_ai_model(prompt, input_text):
    # Get provider and model from config
    provider_name = config.get("provider", "openai")  # Default to OpenAI if not specified
    model_name = config.get("model", "gpt-4")  # Default to GPT-4 if not specified

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
        max_tokens=100  # Limit the response length
    )

    # Get the completion response
    response = provider.complete(request)

    # Return the response content
    return response.message.content