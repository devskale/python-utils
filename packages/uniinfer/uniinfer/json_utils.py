import json
import os
import datetime
# Save models to a JSON file


def touch_json(json_file='models.json'):
    # ensure directory exists and file is present
    json_path = os.path.expanduser(f"~/.uniinfer/{json_file}")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    if not os.path.exists(json_path):
        with open(json_path, 'w') as f:
            json.dump({}, f)
    # load and return data + path
    with open(json_path, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    return data, json_path


def update_models(models, provider_name, json_file='models.json'):
    print(f"Updating models for provider: {provider_name} in {json_file}")
    # load or initialize JSON
    existing_models, json_path = touch_json(json_file)

    # ensure top-level structure
    providers = existing_models.get("providers", {})

    # preserve old entries
    old_entries = providers.get(provider_name, {}).get("modellist", [])
    old_map = {e["name"]: e for e in old_entries}

    now = datetime.datetime.now().isoformat()
    model_entries = []
    for m in models:
        if m in old_map:
            model_entries.append(old_map[m])
        else:
            model_entries.append({"name": m, "created": now, "accessed": None})

    providers[provider_name] = {"modellist": model_entries}
    existing_models["providers"] = providers

    # persist back
    with open(json_path, 'w') as f:
        json.dump(existing_models, f, indent=2)
    print(f"Models saved to {json_path}")


def update_model_accessed(model_name, provider_name, json_file='models.json'):
    # load or initialize JSON
    existing_models, json_path = touch_json(json_file)

    # ensure top-level structure
    providers = existing_models.get("providers", {})
    provider_data = providers.get(provider_name, {})
    modellist = provider_data.get("modellist", [])

    found = False
    for model_entry in modellist:
        if model_entry.get("name") == model_name:
            model_entry["accessed"] = datetime.datetime.now().isoformat()
            model_entry["accessed_count"] = model_entry.get(
                "accessed_count", 0) + 1
            found = True
            break

    if not found:
        print(
            f"Warning: Model '{model_name}' not found for provider '{provider_name}'.")

    # Persist back
    with open(json_path, 'w') as f:
        json.dump(existing_models, f, indent=2)
    print(
        f"Model '{model_name}' accessed time and count updated in {json_path}")
