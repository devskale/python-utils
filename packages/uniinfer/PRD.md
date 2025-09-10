## add support for embedding models

several providers have embedding models
examples
ollama

- embeddinggemma:latest # EMBEDDING MODEL
- nomic-embed-text:latest # EMBEDDING MODEL
  tu
- e5-mistral-7b # EMBEDDING MODEL

Features

- add uniinfer support for embedding models
- add embedding support to uniioai_proxy

### tests

add tests to
./uniinfer/tests/
directory

### Windows Powershell

you have to activate the .venv before running uniinfer
.venv/scripts/activate

## PRD.MD Style

### WRITING STYLE

Each long sentence should be followed by two new line characters.
avoid long bullet lists
write in natural, plain English. be conversational.
avoid using overly complex language, and super long sentences
use simple & easy-to-understand language. be concise.

### TERMINAL

You are on a PC in a PowerShell environment in a Python .venv.

### OUTPUT STYLE

write in complete, clear sentences. like a Senior Developer when talking to a junior engineer
always provide enough context for the user to understand in a simple & short way
make sure to clearly explain your assumptions, and your conclusions

# GOAL

implement embedding support for uniinfer

to understand embeddings access embedding endpoints for ollama and tu and understand their API.
then move over to integrate embedding support.

- add uniinfer embeddings api
- add openai proxy embedding support.

# Coding Tips

credgoo is used to get apikeys. eg get_api_key("tu")
