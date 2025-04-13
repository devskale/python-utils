"""
Provider factory for managing and instantiating chat providers.
"""
from typing import Dict, Type, Optional, Any
from .core import ChatProvider

# Try to import credgoo for API key management
try:
    from credgoo import get_api_key
    HAS_CREDGOO = True
except ImportError:
    HAS_CREDGOO = False


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
            name (str): The name of the provider.
            api_key (Optional[str]): The API key for authentication.
                If None and credgoo is available, will attempt to get the key from credgoo.
            **kwargs: Additional provider-specific arguments (e.g., base_url for Ollama).

        Returns:
            ChatProvider: The provider instance.

        Raises:
            ValueError: If the provider is not registered.
        """
        if name not in ProviderFactory._providers:
            raise ValueError(f"Provider '{name}' not registered")

        # If API key not provided, try to get it from credgoo or environment
        if api_key is None and name != "ollama":  # Ollama doesn't need an API key
            if HAS_CREDGOO:
                try:
                    api_key = get_api_key(name)
                except Exception:
                    pass  # Fall through to env var check

            if api_key is None:
                api_key = os.getenv(f"{name.upper()}_API_KEY")

        provider_class = ProviderFactory._providers[name]
        try:
            return provider_class(api_key=api_key, **kwargs)
        except ValueError as e:
            raise  # Re-raise explicit value errors
        except Exception as e:
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
