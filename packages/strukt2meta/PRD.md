strukt2meta

takes structured data or images and generates metadata using AI.

## features
can work with OFS (opinionated file system)
analyzes markdown and converts it into metadata (based on a prompt)
   - can insert this metadata into json of OFS.
can work on OFS files, directories and filetrees recursively

## architecture
uses credgoo for retrieving APIKEYS, github.com/devskale/python-utils
uses uniinfer to access ai models from provider tu (setup via a config file), github.com/devskale/python-utils
python
