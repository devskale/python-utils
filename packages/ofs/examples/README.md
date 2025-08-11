# OFS Package Usage Examples

This directory contains examples showing how to import and use the OFS package in your own Python code.

## Files

- **`list_projects_example.py`** - Simple, focused example for listing projects
- **`usage_examples.py`** - Comprehensive examples covering all major OFS functions

## Quick Start

### 1. Install the OFS package

```bash
# If you're in the OFS development directory
pip install -e .

# Or if installed from PyPI (when available)
pip install ofs
```

### 2. Basic Usage

```python
from ofs import list_projects, list_projects_json

# Get simple list of project names
projects = list_projects()
print(projects)  # ['Project1', 'Project2', ...]

# Get structured data with metadata
data = list_projects_json()
print(data)  # {'projects': [...], 'count': 5}
```

### 3. Run the Examples

```bash
# Run the simple project listing example
python examples/list_projects_example.py

# Run the comprehensive examples
python examples/usage_examples.py
```

## Available Functions

### Project Functions
- `list_projects()` → `list[str]` - Simple list of project names
- `list_projects_json()` → `Dict[str, Any]` - Structured project data

### Bidder Functions  
- `list_bidders(project_name)` → `list[str]` - Simple list of bidders
- `list_bidders_json(project_name)` → `Dict[str, Any]` - Structured bidder data

### Search Functions
- `get_paths_json(name)` → `Dict[str, Any]` - Find all paths for a name
- `find_bidder_in_project(project, bidder)` → `str` - Find specific bidder path

### Configuration Functions
- `get_base_dir()` → `str` - Get OFS base directory
- `get_config()` → `Dict[str, Any]` - Get OFS configuration

## JSON Output Structure

### Projects
```json
{
  "projects": ["Project1", "Project2"],
  "count": 2
}
```

### Bidders
```json
{
  "project": "ProjectName",
  "bidder_directories": ["Bidder1", "Bidder2"],
  "all_files": ["file1.pdf", "file2.pdf"],
  "total_bidders": 2,
  "total_files": 2
}
```

### Paths
```json
{
  "name": "SearchTerm",
  "paths": [
    {"path": ".dir/Project/A", "type": "A"},
    {"path": ".dir/Project/B/Bidder", "type": "B"}
  ],
  "count": 2
}
```