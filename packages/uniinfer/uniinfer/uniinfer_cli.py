# Import uniinfer components
from importlib.metadata import version  # Changed from pkg_resources
from uniinfer.examples.providers_config import PROVIDER_CONFIGS
from uniinfer import (
    ChatMessage,
    ChatCompletionRequest,
    ProviderFactory,
    ChatProvider,
    EmbeddingRequest,
    EmbeddingProviderFactory
)
from credgoo import get_api_key
import argparse
import random
import time
# Cloudflare API Details
from dotenv import load_dotenv
import os
# load_dotenv(verbose=True, override=True)
# Load environment variables from .env file
dotenv_path = os.path.join(os.getcwd(), '.env')  # Explicitly check current dir
# Add verbose=True and override=True
found_dotenv = load_dotenv(dotenv_path=dotenv_path,
                           verbose=True, override=True)

# print(f"DEBUG: Attempted to load .env from: {dotenv_path}")  # Debug print
# print(f"DEBUG: .env file found and loaded: {found_dotenv}")  # Debug print


def main():
    # Initialize argument parser
    parser = argparse.ArgumentParser(description='UniInfer example script')
    parser.add_argument('-l', '--list-providers', '--list', '--list-provides', action='store_true',
                        help='List available providers')
    parser.add_argument('--list-models', action='store_true',
                        help='List available models for the specified provider or all providers when combined with --list-providers')
    parser.add_argument('--embed', action='store_true',
                        help='Use embedding instead of chat completion')
    parser.add_argument('--embed-text', type=str, action='append',
                        help='Text to embed (can be used multiple times)')
    parser.add_argument('--embed-file', type=str,
                        help='File containing text to embed (one text per line)')
    parser.add_argument('-p', '--provider', type=str, default='stepfun',
                        help='Specify which provider to use')
    parser.add_argument('-q', '--query', type=str,
                        help='Specify the query to send to the provider')
    parser.add_argument('-m', '--model', type=str,
                        help='Specify which model to use')
    parser.add_argument('-f', '--file', type=str,
                        help='Specify a file to use as context')
    parser.add_argument('-t', '--tokens', type=int, default=4000,
                        help='Specify token limit for file context (default: 4000)')
    parser.add_argument('--encryption-key', type=str,
                        help='Specify the CREDGOO encryption key')
    parser.add_argument('--bearer-token', type=str,
                        help='Specify the CREDGOO bearer token')
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + version('uniinfer'),
                        help="Show program's version number and exit")

    args = parser.parse_args()

    # Retrieve credentials: prioritize CLI args, then environment variables
    credgoo_encryption_token = args.encryption_key or os.getenv(
        'CREDGOO_ENCRYPTION_KEY')
    credgoo_api_token = args.bearer_token or os.getenv('CREDGOO_BEARER_TOKEN')
    bearer_token = f"{credgoo_api_token}@{credgoo_encryption_token}" if credgoo_api_token and credgoo_encryption_token else None

#    if not credgoo_api_token or not credgoo_encryption_token:
#        print("Error: CREDGOO_ENCRYPTION_KEY or CREDGOO_BEARER_TOKEN not found.")
#        print("Please provide them either via command-line arguments (--encryption-key, --bearer-token) or environment variables.")
#        return
    provider = args.provider
    retrieved_api_key = get_api_key(
        service=provider,
        encryption_key=credgoo_encryption_token,
        bearer_token=credgoo_api_token,)

    if args.list_providers and args.list_models:
        providers = ProviderFactory.list_providers()
        for provider in providers:
            try:
                provider_class = ProviderFactory.get_provider_class(provider)
                retrieved_api_key = get_api_key(
                    service=provider,
                    encryption_key=credgoo_encryption_token,
                    bearer_token=credgoo_api_token,)
                # models = ProviderFactory.list_models(
                #    provider=provider,
                #    api_key=retrieved_api_key,
                #    **({} if provider not in ['cloudflare', 'ollama'] else PROVIDER_CONFIGS[provider].get('extra_params', {}))
                # )
                models = provider_class.list_models(
                    api_key=retrieved_api_key,
                    **({} if provider not in ['cloudflare', 'ollama'] else PROVIDER_CONFIGS[provider].get('extra_params', {}))
                )
                print(f"\nAvailable models for {provider}:")
                for model in models:
                    print(f"- {model}")
            except Exception as e:
                print(f"\nError listing models for {provider}: {str(e)}")
        return

    if args.list_providers:
        providers = ProviderFactory.list_providers()
        print("Available providers:")
        for provider in providers:
            print(f"- {provider}")
        return

    if args.list_models:
        try:
            provider_class = ProviderFactory.get_provider_class(args.provider)
            models = provider_class.list_models(
                api_key=retrieved_api_key,
                **({} if args.provider not in ['cloudflare', 'ollama'] else PROVIDER_CONFIGS[args.provider].get('extra_params', {}))
            )

            print(f"Available models for {args.provider}:")
            for model in models:
                print(f"- {model}")
            return
        except Exception as e:
            print(f"Error listing models for {args.provider}: {str(e)}")
            return

    # Initialize the provider factory
    # for that i need credgoo api token and credgoo encryption key
    uni = ProviderFactory().get_provider(
        name=provider,
        api_key=retrieved_api_key,
        **({} if provider not in ['cloudflare', 'ollama'] else PROVIDER_CONFIGS[provider].get('extra_params', {}))
    )

    # Handle embedding requests
    if args.embed:
        texts_to_embed = []

        # Add texts from --embed-text arguments
        if args.embed_text:
            texts_to_embed.extend(args.embed_text)

        # Add texts from --embed-file
        if args.embed_file:
            try:
                with open(args.embed_file, 'r', encoding='utf-8') as f:
                    file_texts = [line.strip() for line in f if line.strip()]
                    texts_to_embed.extend(file_texts)
            except Exception as e:
                print(f"Error reading embed file: {e}")
                return

        if not texts_to_embed:
            print("Error: --embed-text or --embed-file is required when using --embed")
            return

        try:
            embedding_provider = EmbeddingProviderFactory().get_provider(
                name=provider,
                api_key=retrieved_api_key,
                **({} if provider not in ['cloudflare', 'ollama'] else PROVIDER_CONFIGS[provider].get('extra_params', {}))
            )

            model = args.model if args.model else PROVIDER_CONFIGS[provider]['default_model']
            print(
                f"Embedding {len(texts_to_embed)} text(s) using {provider}@{model}")

            # Create embedding request
            request = EmbeddingRequest(
                input=texts_to_embed,
                model=model
            )

            # Make the request
            response = embedding_provider.embed(request)

            print("\n=== Embedding Response ===")
            print(f"Model: {response.model}")
            print(f"Provider: {response.provider}")
            print(f"Number of embeddings: {len(response.data)}")
            print(f"Usage: {response.usage}")

            for i, embedding_data in enumerate(response.data):
                print(f"\nText {i+1}: '{texts_to_embed[i]}'")
                print(
                    f"Embedding dimensions: {len(embedding_data['embedding'])}")
                print(f"First 5 values: {embedding_data['embedding'][:5]}")
                if len(embedding_data['embedding']) > 5:
                    print(f"Last 5 values: {embedding_data['embedding'][-5:]}")

        except Exception as e:
            print(f"Error creating embeddings: {e}")
        return

    # List of machine learning topics in German
    ml_topics = [
        "Transformer in maschinellem Lernen",
        "Neuronale Netze",
        "Convolutional Neural Networks (CNNs)",
        "Recurrent Neural Networks (RNNs)",
        "Support Vector Machines (SVMs)",
        "Entscheidungsbäume",
        "Random Forests",
        "Gradient Boosting",
        "Unüberwachtes Lernen",
        "Bestärkendes Lernen",
        "Natural Language Processing (NLP)",
        "Computer Vision",
        "Generative Adversarial Networks (GANs)",
        "Transfer Learning",
        "Anomalie-Erkennung",
        "Zeitreihenanalyse",
        "Empfehlungssysteme",
        "Clustering-Algorithmen",
        "Deep Reinforcement Learning",
        "Federated Learning"
    ]

    prompt = args.query if args.query else f"Erkläre mir bitte {random.choice(ml_topics)} in einfachen Worten und auf deutsch."

    if args.file:
        try:
            with open(args.file, 'r') as f:
                file_content = f.read()
                # Simple token estimation (4 chars ~ 1 token)
                max_chars = args.tokens * 4
                if len(file_content) > max_chars:
                    file_content = file_content[:max_chars]
                prompt = f"File context: {file_content}\n\nUser query: {prompt}"
        except Exception as e:
            print(f"Error reading file: {e}")

    model = args.model if args.model else PROVIDER_CONFIGS[provider]['default_model']
    print(
        f"Prompt: {prompt} ( {provider}@{model} )")
    # Create a simple chat request
    messages = [
        ChatMessage(role="user", content=prompt)
    ]
    request = ChatCompletionRequest(
        messages=messages,
        model=model,
        streaming=True
    )
    # Make the request with timing statistics
    response_text = ""
    token_count = 0
    start_time = time.time()
    first_token_time = None
    
    print("\n=== Response ===\n")
    for chunk in uni.stream_complete(request):
        content = chunk.message.content
        if content:  # Only count non-empty content
            if first_token_time is None:
                first_token_time = time.time()
            # Estimate token count (rough approximation: 4 chars = 1 token)
            token_count += len(content) / 4
            print(content, end="", flush=True)
            response_text += content
    
    end_time = time.time()
    
    # Calculate statistics
    time_to_first_token = first_token_time - start_time if first_token_time else 0
    # Calculate tokens per second from first token to end (excluding initial latency)
    token_generation_time = end_time - first_token_time if first_token_time else 0
    tokens_per_second = token_count / token_generation_time if token_generation_time > 0 else 0
    
    # Print statistics
    print(f"\n\ntok/s: {tokens_per_second:.2f}          tft: {time_to_first_token:.2f} s")


if __name__ == "__main__":
    main()
