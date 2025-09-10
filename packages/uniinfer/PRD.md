## add support for embedding models

several providers have embedding models

Features

- add uniinfer support for embedding models
- add embedding support to uniioai_proxy

### example embedding models

(.venv) uniinfer> uniinfer -p ollama --list-models
[*] Using Ollama endpoint: https://amp1.mooo.com:11444/api/tags
Found 4 available models
Available models for ollama:

- jina/jina-embeddings-v2-base-de:latest # EMBEDDING MODEL
- dengcao/Qwen3-Embedding-0.6B:Q8_0 # EMBEDDING MODEL
- embeddinggemma:latest # EMBEDDING MODEL
- nomic-embed-text:latest # EMBEDDING MODEL

(.venv) uniinfer> uniinfer -p tu --list-models  
[*] Available models for tu:

- deepseek-r1
- qwen-coder-32b
- qwen-coder-3b
- mistral-small-3.1-24b
- mistral-large-123b
- qwen-32b
- e5-mistral-7b # EMBEDDING MODEL
