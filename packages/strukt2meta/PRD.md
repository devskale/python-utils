strukt2meta

takes structured data or images and generates metadata using AI.

## features
- Can work with OFS (opinionated file system).
- Analyzes markdown and converts it into metadata (based on a prompt).
  - Can insert this metadata into JSON of OFS.
- Can work on OFS files, directories, and file trees recursively.
- Retrieves a file path (strukt context).
- Accepts a prompt (e.g., from a template).
- queries an AI model with context (strukt) and the provided prompt.
- Typically returns a JSON response.
- Injects the JSON response into a JSON file.

## architecture
uses credgoo for retrieving APIKEYS, github.com/devskale/python-utils
uses uniinfer to access ai models from provider tu (setup via a config file), github.com/devskale/python-utils
python

## STATUS / TODO
[x] Setup basic package structure
[ ] Basic Setup
    [x] install uniinfer, credgoo
    [x] config (provider, model, tokens)
    [x] prompts file
    [ ] json output schema
    [ ] calling api with uniinfer


## Lessons Learned

