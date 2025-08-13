# OFS (Opinionated Filesystem)

A Python package for accessing, editing, and navigating opinionated filesystem structures suited for handling tender documentation with rich options for indexes and metadata sidecar files.

## Installation

### Development Installation

1. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
```

2. Install in development mode:

```bash
pip install -e .
```

## Usage

### Command Line Interface

```bash
# Get path for a project (AUSSCHREIBUNGNAME) or bidder (BIETERNAME)
ofs get-path "Demoprojekt1"
ofs get-path "Demo2"

# List all available items (projects, bidders, files)
ofs list

# List all projects (AUSSCHREIBUNGNAME)
ofs list-projects

# List all bidders in a specific project
ofs list-bidders "Demoprojekt1"

# Find a specific bidder within a project
ofs find-bidder "Demoprojekt1" "Demo2"

# Get OFS root directory
ofs root

# Get paths in JSON format
ofs get-paths-json "Demoprojekt1"

# List projects in JSON format
ofs list-projects-json
```

### Python API

```python
import ofs

# Get path for a project or bidder
project_path = ofs.get_path("Demoprojekt1")
print(project_path)  # Output: .dir/Demoprojekt1

bidder_path = ofs.get_path("Demo2")
print(bidder_path)  # Output: .dir/Demoprojekt1/B/Demo2

# List all items (includes projects, bidders, files from filesystem and index files)
items = ofs.list_ofs_items()
print(items)

# List all projects
projects = ofs.list_projects()
print(projects)  # Output: ['2025-04 Lampen', 'Demoprojekt1', ...]

# List bidders in a project
bidders = ofs.list_bidders("Demoprojekt1")
print(bidders)  # Output: ['Demo2', 'Demo4', 'Siemens AG', ...]

# Find specific bidder in project
bidder_path = ofs.find_bidder_in_project("Demoprojekt1", "Demo2")
print(bidder_path)  # Output: .dir/Demoprojekt1/B/Demo2

# Get OFS root
root = ofs.get_ofs_root()
print(root)

# Access paths in JSON format
paths_json = ofs.get_paths_json("Demoprojekt1")
print(paths_json)

# List projects in JSON format
projects_json = ofs.list_projects_json()
print(projects_json)

# Access configuration
config = ofs.get_config()
base_dir = config.get("BASE_DIR")
print(base_dir)  # Output: .dir
```

## OFS Structure

OFS is designed to handle tender documentation with a specific directory structure:

```
.dir/                           # BASE_DIR (configurable)
├── .pdf2md_index.json         # Index file with project listings
├── ProjectName1/              # AUSSCHREIBUNGNAME (project directory)
│   ├── .pdf2md_index.json    # Project-level index
│   ├── A/                    # Ausschreibung (tender documents)
│   │   └── documents...
│   └── B/                    # Bieter (bidders)
│       ├── .pdf2md_index.json
│       ├── BidderName1/      # BIETERNAME (bidder directory)
│       ├── BidderName2/
│       └── ...
├── ProjectName2/
└── ...
```

### Search Algorithm

The `get_path` function uses an intelligent search algorithm:

1. **Direct filesystem match**: Searches for exact directory/file names
2. **Index file search**: Looks in `.pdf2md_index.json` files for entries
3. **Recursive search**: Traverses subdirectories to find nested items
4. **Bidder-specific search**: Automatically searches in `B/` subdirectories for bidder names

This allows you to find both projects (`AUSSCHREIBUNGNAME`) and bidders (`BIETERNAME`) regardless of their exact location in the filesystem.

## Configuration

OFS uses a priority-based configuration system to load settings:

1. **Environment variables** (highest priority)
2. **Local config file** (`./ofs.config.json`)
3. **User home config file** (`~/.ofs.config.json`)
4. **Default values** (lowest priority)

### Configurable Options

- `BASE_DIR`: Base directory for OFS structure (default: `.dir`)
- `INDEX_FILE`: Name of index files (default: `index.json`)
- `METADATA_SUFFIX`: Suffix for metadata files (default: `.meta.json`)

### Environment Variables

```bash
# Override BASE_DIR
export OFS_BASE_DIR="/path/to/custom/dir"

# Override INDEX_FILE
export OFS_INDEX_FILE="custom_index.json"

# Override METADATA_SUFFIX
export OFS_METADATA_SUFFIX=".custom.meta.json"
```

## Development

This package is currently in early development. The main functionality includes:

- `get_path(name)`: Returns a path for a given name using configured BASE_DIR
- `get_paths_json(name)`: Retrieves paths for a name in JSON format.
- `list_projects_json()`: Retrieves all projects in JSON format.
- Configuration system with file and environment variable support.
- CLI interface for basic operations
- Extensible structure for future OFS features

## Requirements

- Python >= 3.12

## Project Structure

```
ofs/
├── ofs/
│   ├── __init__.py
│   ├── core.py
│   └── cli.py
├── tests/
├── docs/
├── setup.py
├── README.md
└── PRD.md
```

## legacy code

we are trying to rebuild and replicate certain functions from strukt2meta and from pdf2md library

`pdf --index un` stores unparsed and unkategorized items into a file called un_items.json

````shell
pdf2md .disk --index un --recursive --json```
````

```
Found 119 unparsed or uncategorized item(s).
Unparsed and uncategorized items list saved to: .disk/un_items.json
```

strukt2umeta unlist kategorizes 119 items from the list and updates the ofs index.

```bash
strukt2meta unlist 119 .disk2/un_items.json
```
