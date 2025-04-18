# UniInfer with Credgoo Integration Examples

This directory contains examples demonstrating how to use UniInfer with Credgoo for secure API key management.

## What is Credgoo?

Credgoo is a package that provides a secure way to manage API keys by retrieving them from Google Sheets and implementing local caching for better performance. This approach allows teams to centrally manage API credentials while providing secure access to individual developers.

## Examples

### Basic Example (`credgoo_example.py`)

A simple example showing how to:

- Use credgoo to retrieve API keys securely
- Initialize different providers using those keys
- Make chat completion requests with the providers

```python
# Example usage
from uniinfer import ChatMessage, ChatCompletionRequest, ProviderFactory
from credgoo import get_api_key

# Get API key securely from credgoo
api_key = get_api_key("openai")

# Initialize provider with the key
provider = ProviderFactory.get_provider("openai", api_key=api_key)

# Create and send a request
messages = [ChatMessage(role="user", content="Hello, how are you?")]
request = ChatCompletionRequest(messages=messages, model="gpt-3.5-turbo")
response = provider.complete(request)
print(response.message.content)
```

### Comprehensive Example (`credgoo_integration.py`)

A more comprehensive example demonstrating:

- Using credgoo with multiple providers
- Implementing fallback strategies
- Command-line arguments for testing different providers
- Error handling for API key retrieval

## Running the Examples

1. Ensure you have both packages installed:

   ```bash
   pip install -e /path/to/packages/credgoo
   pip install -e /path/to/packages/uniinfer
   ```

2. Set up your credgoo credentials (first time only):

   ```bash
   python -m credgoo.credgoo --setup
   ```

3. Run the examples:
   ```bash
   python examples/credgoo_example.py
   # or
   python examples/credgoo_integration.py --provider openai --prompt "Tell me a joke"
   ```

## Benefits of Using Credgoo with UniInfer

1. **Security**: API keys are not hardcoded in your code
2. **Centralized Management**: Keys can be managed in a single location (Google Sheets)
3. **Caching**: Improved performance with local caching
4. **Flexibility**: Easy to switch between different providers
5. **Fallback Support**: Implement robust fallback strategies when a provider is unavailable
