import json
import re

def cleanify_json(json_string):
    """
    Cleans AI-generated JSON strings by removing extraneous formatting like triple backticks and ensuring valid JSON.
    """
    # Remove triple backticks and any surrounding whitespace
    json_string = re.sub(r"```json\n|```", "", json_string).strip()

    if not json_string:
        raise ValueError("The JSON string is empty or invalid.")

    try:
        # Parse the cleaned string to ensure it's valid JSON
        parsed_json = json.loads(json_string)
        return parsed_json
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")