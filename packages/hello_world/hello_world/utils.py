import json

def load_config(file_path):
    """Load configuration from a JSON file."""
    with open(file_path, 'r') as file:
        return json.load(file)

def save_config(file_path, config):
    """Save configuration to a JSON file."""
    with open(file_path, 'w') as file:
        json.dump(config, file, indent=4)
