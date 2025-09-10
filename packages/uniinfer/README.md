# UniInfer · [![PyPI Version](https://img.shields.io/pypi/v/uniinfer.svg)](https://pypi.org/project/uniinfer/)

**Unified LLM Inference Interface for Python with Seamless API Key Management**

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/pypi/pyversions/uniinfer.svg)](https://pypi.org/project/uniinfer/)

UniInfer provides a consistent Python interface for LLM chat completions and embeddings across multiple providers with:

- 🚀 Single API for 20+ LLM providers
- 🔑 Seamless API key management with credgoo integration
- ⚡ Real-time streaming support
- 🔄 Automatic fallback strategies
- 📊 Embedding support for semantic search
- 🔧 Extensible provider architecture

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Features](#core-features)
- [API Reference](#api-reference)
- [Supported Providers](#supported-providers)
- [Contributing](#contributing)
- [License](#license)

## Core Features

### 🔑 Secure API Key Management with credgoo

UniInfer integrates with [credgoo](https://github.com/your-org/credgoo) for secure API key management:

- **Centralized Key Storage** - Store all provider API keys in a personal Google Sheet
- **Secure Retrieval** - Keys are encrypted and secured via token authentication
- **Seamless Provider Switching** - Change providers without managing keys in code

```python
# No API keys needed in code - retrieved automatically
openai_provider = ProviderFactory.get_provider("openai")
anthropic_provider = ProviderFactory.get_provider("anthropic")
ollama_provider = ProviderFactory.get_provider("ollama")  # No auth required
```

### ⚡ Real-time Streaming

All providers support real-time token streaming:

```python
request = ChatCompletionRequest(
    messages=[ChatMessage(role="user", content="Write a poem")],
    streaming=True
)

for chunk in provider.stream_complete(request):
    print(chunk.message.content, end="", flush=True)
```

### 📊 Embedding Support

Access embedding models for semantic search and similarity:

```python
# Ollama embeddings
ollama_embed = EmbeddingProviderFactory.get_provider("ollama")
embed_request = EmbeddingRequest(
    input=["machine learning", "artificial intelligence", "data science"],
    model="nomic-embed-text:latest"
)
embed_response = ollama_embed.embed(embed_request)

# TU Wien embeddings
tu_embed = EmbeddingProviderFactory.get_provider("tu")
embed_request.model = "e5-mistral-7b"
tu_response = tu_embed.embed(embed_request)
```

### 🔄 Fallback Strategies

Automatically try multiple providers until one succeeds:

```python
from uniinfer import FallbackStrategy

fallback = FallbackStrategy(["mistral", "anthropic", "openai"])
response, provider_used = fallback.complete(request)
print(f"Response from {provider_used}: {response.message.content}")
```

### 📋 Model Discovery

List available models across all providers:

```python
from uniinfer import ProviderFactory, EmbeddingProviderFactory

# Chat models
chat_models = ProviderFactory.list_models()
print(chat_models["openai"])  # ['gpt-4', 'gpt-3.5-turbo', ...]

# Embedding models
embed_models = EmbeddingProviderFactory.list_models()
print(embed_models["ollama"])  # ['nomic-embed-text:latest', ...]
```

## Installation

```bash
pip install uniinfer credgoo
```

Or install from source:

```bash
git clone https://github.com/skale-dev/uniinfer.git
cd uniinfer
pip install -e .
pip install credgoo  # For seamless API key management
```

## Quick Start

### Basic Chat Completion

```python
from uniinfer import ProviderFactory, ChatMessage, ChatCompletionRequest

# Get provider (API key retrieved automatically via credgoo)
provider = ProviderFactory.get_provider("openai")

# Create request
request = ChatCompletionRequest(
    messages=[ChatMessage(role="user", content="Hello, how are you?")],
    model="gpt-4",
    temperature=0.7
)

# Get response
response = provider.complete(request)
print(response.message.content)
```

### Streaming Chat Completion

```python
from uniinfer import ProviderFactory, ChatMessage, ChatCompletionRequest

provider = ProviderFactory.get_provider("anthropic")

request = ChatCompletionRequest(
    messages=[ChatMessage(role="user", content="Tell me a story")],
    model="claude-3-sonnet-20240229",
    streaming=True
)

# Stream response
for chunk in provider.stream_complete(request):
    print(chunk.message.content, end="", flush=True)
```

### Text Embeddings

```python
from uniinfer import EmbeddingProviderFactory, EmbeddingRequest

# Get embedding provider
provider = EmbeddingProviderFactory.get_provider("ollama")

# Create embedding request
request = EmbeddingRequest(
    input=["Hello world", "How are you?"],
    model="nomic-embed-text:latest"
)

# Get embeddings
response = provider.embed(request)
print(f"Embeddings: {len(response.data)} vectors")
print(f"Dimensions: {len(response.data[0]['embedding'])}")
```

## CLI Usage

UniInfer provides a comprehensive command-line interface:

### Chat Completions
```bash
# Basic chat
uniinfer -p openai -q "Hello, how are you?" -m gpt-4

# With file context
uniinfer -p anthropic -q "Summarize this document" -f document.txt -m claude-3-sonnet-20240229

# List available models
uniinfer -p openai --list-models
```

### Embeddings
```bash
# Single text embedding
uniinfer -p ollama --embed --embed-text "Hello world" --model nomic-embed-text:latest

# Multiple texts
uniinfer -p ollama --embed --embed-text "Text 1" --embed-text "Text 2" --model nomic-embed-text:latest

# From file
uniinfer -p tu --embed --embed-file texts.txt --model e5-mistral-7b
```

### Provider Management
```bash
# List all providers
uniinfer -l

# List models for all providers
uniinfer -l --list-models
```

## API Server (OpenAI-Compatible)

UniInfer includes an OpenAI-compatible API server for easy integration:

### Running the Server

```bash
# Install additional dependencies
pip install fastapi uvicorn

# Run the server
uvicorn uniinfer.uniioai_proxy:app --host 0.0.0.0 --port 8123
```

### API Endpoints

#### POST /v1/chat/completions
OpenAI-compatible chat completions endpoint.

**Request Format:**
```json
{
  "model": "openai@gpt-4",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "stream": false
}
```

**Model Format:** `provider@model` (e.g., `openai@gpt-4`, `anthropic@claude-3-sonnet-20240229`)

**Authentication:** Bearer token (managed by credgoo)

**Streaming:** Set `"stream": true` for real-time responses

#### Example Usage

```python
import openai

# Point to your UniInfer server
client = openai.OpenAI(
    base_url="http://localhost:8123/v1",
    api_key="your-credgoo-bearer-token"
)

# Use like regular OpenAI API
response = client.chat.completions.create(
    model="openai@gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

### Docker Deployment

```dockerfile
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install uniinfer fastapi uvicorn credgoo
EXPOSE 8123
CMD ["uvicorn", "uniinfer.uniioai_proxy:app", "--host", "0.0.0.0", "--port", "8123"]
```

## Supported Providers

| Provider | Chat Models | Embedding Models | Streaming | Auth Required |
|----------|-------------|------------------|-----------|---------------|
| **OpenAI** | GPT-4, GPT-3.5 | text-embedding-ada-002 | ✅ | ✅ |
| **Anthropic** | Claude 3 Opus/Sonnet/Haiku | - | ✅ | ✅ |
| **Mistral** | Mistral Large/Small | mistral-embed | ✅ | ✅ |
| **Ollama** | Llama2, Mistral, etc. | nomic-embed-text, jina-embed | ✅ | ❌ |
| **Google Gemini** | Gemini Pro/Flash | text-embedding-004 | ✅ | ✅ |
| **TU Wien** | DeepSeek, Qwen, etc. | e5-mistral-7b | ✅ | ✅ |
| **OpenRouter** | 60+ models | Various | ✅ | ✅ |
| **HuggingFace** | Llama, Mistral | sentence-transformers | ✅ | ✅ |
| **Cohere** | Command R+ | embed-english-v3.0 | ✅ | ✅ |
| **Groq** | Llama 3.1 | - | ✅ | ✅ |
| **AI21** | Jamba | - | ✅ | ✅ |
| **Cloudflare** | Workers AI | - | ✅ | ✅ |
| **NVIDIA NGC** | Various | Various | ✅ | ✅ |
| **And 10+ more...** | | | | |



## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Adding a New Provider

1. Create `uniinfer/providers/your_provider.py`
2. Implement `ChatProvider` or `EmbeddingProvider` interface
3. Register in the appropriate factory
4. Add tests

## License

MIT License - see [LICENSE](LICENSE) for details

---

**UniInfer** makes working with multiple LLM providers simple and secure. Focus on building applications, not managing API keys.
