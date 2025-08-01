"""
Module containing provider configurations and related utilities.
"""

# Check if HuggingFace support is available
try:
    from uniinfer import HuggingFaceProvider
    HAS_HUGGINGFACE = True
except ImportError:
    HAS_HUGGINGFACE = False

# Check if Cohere support is available
try:
    from uniinfer import CohereProvider
    HAS_COHERE = True
except ImportError:
    HAS_COHERE = False

# Check if Moonshot support is available
try:
    from uniinfer import MoonshotProvider
    HAS_MOONSHOT = True
except ImportError:
    HAS_MOONSHOT = False

# Check if OpenAI client is available (for StepFun)
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# Check if Groq support is available
try:
    from uniinfer import GroqProvider
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

# Check if AI21 support is available
try:
    from uniinfer import AI21Provider
    HAS_AI21 = True
except ImportError:
    HAS_AI21 = False

# Check if Gemini support is available
try:
    from uniinfer import GeminiProvider
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


PROVIDER_CONFIGS = {
    'mistral': {
        'name': 'Mistral AI',
        'default_model': 'mistral-small-latest',
        'needs_api_key': True,
    },
    'anthropic': {
        'name': 'Anthropic (Claude)',
        'default_model': 'claude-3-sonnet-20240229',
        'needs_api_key': True,
    },
    'openai': {
        'name': 'OpenAI',
        'default_model': 'gpt-3.5-turbo',
        'needs_api_key': True,
    },
    'ollama': {
        'name': 'Ollama',
        'default_model': 'gemma3:4b',
        'needs_api_key': False,
        'extra_params': {
            # 'base_url': 'http://amp1.mooo.com:11444'
            'base_url': 'https://ollama.molodetz.nl'
        }
    },
    'arli': {
        'name': 'ArliAI',
        'default_model': 'Qwen3-14B',
        'needs_api_key': True,
    },
    'openrouter': {
        'name': 'OpenRouter',
        'default_model': 'moonshotai/moonlight-16b-a3b-instruct:free',
        'needs_api_key': True,
    },
    'internlm': {
        'name': 'InternLM',
        'default_model': 'internlm3-latest',
        'needs_api_key': True,
        'extra_params': {
            'top_p': 0.9
        }
    },
    'stepfun': {
        'name': 'StepFun AI',
        'default_model': 'step-1-8k',
        'needs_api_key': True,
    },
    'sambanova': {
        'name': 'SambaNova',
        'default_model': 'Meta-Llama-3.1-8B-Instruct',
        'needs_api_key': True,
    },
    'upstage': {
        'name': 'Upstage AI',
        'default_model': 'solar-pro',
        'needs_api_key': True,
    },
    'ngc': {
        'name': 'NVIDIA GPU Cloud (NGC)',
        'default_model': 'nvidia/llama-3.3-nemotron-super-49b-v1',
        'needs_api_key': True,
    },
    'chutes': {
        'name': 'Chutes AI',
        'default_model': 'deepseek-ai/DeepSeek-V3-0324',
        'needs_api_key': True,
    },
    'bigmodel': {
        'name': 'Bigmodel',
        'default_model': 'glm-4-flash',
        'needs_api_key': True,
    },
    'tu': {
        'name': 'tu',
        'default_model': 'deepseek-r1',
        'needs_api_key': True,
    },
    'pollinations': {
        'name': 'Pollinations AI',
        'default_model': 'grok',
        'needs_api_key': False,
    },
    'cloudflare': {
        'name': 'Cloudflare Workers AI',
        'default_model': '@cf/meta/llama-4-scout-17b-16e-instruct',
        'needs_api_key': True,
        'extra_params': {
            'account_id': '1ee331dfd225ac49d67c521a73ca7fe8'  # Will be prompted during setup
        }
    }
}

# Add HuggingFace if available
if HAS_HUGGINGFACE:
    PROVIDER_CONFIGS['huggingface'] = {
        'name': 'HuggingFace Inference',
        'default_model': 'mistralai/Mistral-7B-Instruct-v0.3',
        'needs_api_key': True,
    }

# Add Cohere if available
if HAS_COHERE:
    PROVIDER_CONFIGS['cohere'] = {
        'name': 'Cohere',
        'default_model': 'command-r-plus-08-2024',
        'needs_api_key': True,
    }

# Add Moonshot if available
if HAS_MOONSHOT:
    PROVIDER_CONFIGS['moonshot'] = {
        'name': 'Moonshot AI',
        'default_model': 'moonshot-v1-8k',
        'needs_api_key': True,
    }

# Add Groq if available
if HAS_GROQ:
    PROVIDER_CONFIGS['groq'] = {
        'name': 'Groq',
        'default_model': 'llama-3.1-8b',
        'needs_api_key': True,
    }

# Add AI21 if available
if HAS_AI21:
    PROVIDER_CONFIGS['ai21'] = {
        'name': 'AI21 Labs',
        'default_model': 'jamba-mini-1.6-2025-03',
        'needs_api_key': True,
    }

# Add Gemini if available
if HAS_GENAI:
    PROVIDER_CONFIGS['gemini'] = {
        'name': 'Google Gemini',
        'default_model': 'gemini-2.5-flash',
        'needs_api_key': True,
    }


def add_provider(provider_id, config):
    """Add or update a provider configuration."""
    PROVIDER_CONFIGS[provider_id] = config


def get_provider_config(provider_id):
    """Get configuration for a specific provider."""
    return PROVIDER_CONFIGS.get(provider_id)


def get_all_providers():
    """Get all available provider configurations."""
    return PROVIDER_CONFIGS
