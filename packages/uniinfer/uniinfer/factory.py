"""
Provider factory for managing and instantiating chat providers.
"""
import os  # Added import
from typing import Dict, Type, Optional, Any
from .core import ChatProvider

# Try to import credgoo for API key management


class ProviderFactory:
    """
    Factory for creating provider instances.
    """
    _providers: Dict[str, Type[ChatProvider]] = {}

    @staticmethod
    def register_provider(name: str, provider_class: Type[ChatProvider]) -> None:
        """
        Register a provider.

        Args:
            name (str): The name of the provider.
            provider_class (Type[ChatProvider]): The provider class.
        """
        ProviderFactory._providers[name] = provider_class

    @staticmethod
    def get_provider(name: str, api_key: Optional[str] = None, **kwargs) -> ChatProvider:
        """
        Get a provider instance.

        Args:
            name (str): The name of the provider (e.g., 'openai', 'ollama').
            api_key (Optional[str]): The API key for authentication.
                If None, will attempt to get the key from the environment
                variable formatted as PROVIDERNAME_API_KEY (e.g., OPENAI_API_KEY).
            **kwargs: Additional provider-specific arguments (e.g., base_url for Ollama).

        Returns:
            ChatProvider: The provider instance.

        Raises:
            ValueError: If the provider is not registered or initialization fails.
        """
        provider_name_lower = name.lower()  # Ensure consistent casing for lookup
        if provider_name_lower not in ProviderFactory._providers:
            raise ValueError(f"Provider '{name}' not registered")

        # If API key not provided, try to get it from environment
        # Ollama typically doesn't require an API key in the standard sense
        if api_key is None and provider_name_lower != "ollama":
            env_var_name = f"{provider_name_lower.upper()}_API_KEY"
            api_key = os.getenv(env_var_name)
            if not api_key:
                # Optionally print a warning if the key is not found in env either
                print(
                    f"Warning: API key for '{name}' not provided and not found in environment variable '{env_var_name}'.")

        provider_class = ProviderFactory._providers[provider_name_lower]
        try:
            # Pass the potentially retrieved api_key and other kwargs
            # Ensure api_key is only passed if it's expected by the constructor or not None
            # Most provider classes should accept api_key=None gracefully if not needed
            return provider_class(api_key=api_key, **kwargs)
        except TypeError as e:
            # Catch TypeError if api_key is passed unexpectedly or required but None
            # This might indicate an issue with the specific provider's __init__ signature
            raise ValueError(
                f"Failed to initialize provider '{name}' due to argument mismatch: {str(e)}") from e
        except ValueError as e:
            raise  # Re-raise explicit value errors from provider init
        except Exception as e:
            # Catch other potential initialization errors
            raise ValueError(
                f"Failed to initialize provider '{name}': {str(e)}") from e

    @staticmethod
    def list_providers() -> list:
        """
        List all registered providers.

        Returns:
            list: A list of provider names.
        """
        return list(ProviderFactory._providers.keys())

    @staticmethod
    def list_models() -> Dict[str, list]:
        """
        List available models for all providers.

        Returns:
            Dict[str, list]: A dictionary mapping provider names to their available models.
            Returns an empty list for providers that don't implement list_models.
        """
        result = {}
        for name, provider_class in ProviderFactory._providers.items():
            try:
                result[name] = provider_class.list_models()
            except AttributeError:
                result[name] = []
        return result

    @staticmethod
    def get_provider_class(name: str) -> Type[ChatProvider]:
        """
        Get the provider class for a given provider name.

        Args:
            name (str): The name of the provider.

        Returns:
            Type[ChatProvider]: The provider class.

        Raises:
            ValueError: If the provider is not registered.
        """
        if name not in ProviderFactory._providers:
            raise ValueError(f"Provider '{name}' not registered")
        return ProviderFactory._providers[name]
