# md2blank

Markdown to Blank Converter - A tool for anonymizing markdown content with AI model support

## Features

- Convert markdown to anonymized/blank templates
- Support for multiple AI backends (OpenAI, Anthropic, etc.)
- Preserve markdown structure while removing sensitive content
- Customizable anonymization rules

## Installation

```bash
pip install md2blank
```

## Basic Usage

```bash
md2blank input.md output.md
```

## Configuration

Set your preferred AI backend in `config.json`:

```json
{
  "ai_backend": "openai",
  "openai_key": "your_api_key_here"
}
```

Supported backends:

- OpenAI
- Anthropic
- Local LLMs (via Ollama)

## Requirements

- Python 3.8+
- See `setup.py` for required dependencies

## Development

```bash
pip install -e .
```
