import os
import json
import re
from ofs.core import read_json_file, read_audit_json


def get_nested_value(data, key_path):
    """Get nested value from dict using dot-separated key path, case insensitive."""
    keys = key_path.split('.')
    current = data
    for key in keys:
        if isinstance(current, dict):
            # Find key case insensitively
            matching_key = None
            for k in current.keys():
                if k.lower() == key.lower():
                    matching_key = k
                    break
            if matching_key is not None:
                current = current[matching_key]
            else:
                return None
        else:
            return None
    return current

def kontextBuilder(identifier, promptid, **kwargs):
    """
    A utility function to load a prompt template and inject OFS data for @projekt.KEY and @audit.KEY patterns.

    Parameters:
    identifier: A unique identifier in the form PROJEKT(@BIETER). Used to fetch project and audit data.
    promptid: The prompt ID, corresponding to the filename in the prompts directory (without .md extension).
    **kwargs: Not used in this version.
    Returns:
        The prompt template string with injected data.
    """
    if "@" not in identifier:
        raise ValueError("Identifier must be in the form PROJEKT(@BIETER)")
    project, bidder = identifier.split("@", 1)

    # Load full project and audit data
    projekt_data = read_json_file(project, "projekt.json")
    audit_data = read_audit_json(project, bidder)

    def replace_placeholder(match):
        """Replace @projekt.KEY or @audit.KEY with JSON value."""
        full_match = match.group(0)
        source = match.group(1)  # 'projekt' or 'audit'
        key_path = match.group(2)  # the key path like 'meta' or 'meta.schema_version'

        if source == 'projekt':
            data = projekt_data
        elif source == 'audit':
            data = audit_data
        else:
            return full_match  # unknown source, leave as is

        value = get_nested_value(data, key_path)
        if value is None:
            return full_match  # key not found, leave placeholder

        return json.dumps(value, indent=2, ensure_ascii=False)

    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", f"{promptid}.md")
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        raise ValueError(f"Prompt template '{promptid}.md' not found in prompts directory.")

    # Inject data using regex replacement
    template = re.sub(r'@(\w+)\.([^@\s]+)', replace_placeholder, template)

    print(f"Identifier: {identifier}")
    print(f"Kwargs: {kwargs}")
    print(f"Loaded and injected prompt template for {identifier} using {promptid}:")
    print(template)
    return template
