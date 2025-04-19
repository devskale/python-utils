from openai import OpenAI
import sys  # Import sys for exiting

# provider = 'arli'
# model = 'Mistral-Nemo-12B-Instruct-2407'
#
# provider = 'groq'
# model = 'qwen-qwq-32b'

# provider = 'ollama'
# model = 'gemma3:4b'
# model = 'phi4-mini:latest'

# the baseurl where uniinfer oai proxy server is running
baseurl = 'http://localhost:8123/v1'

# IMPORTANT
# the key is required for underlying uniinfer package to retrieve provider specific apikeys
# see credgoo package for more details
api_key = "test23@test34"
# api_key = None

# --- Define a Default Model ---
DEFAULT_MODEL_ID = "groq@llama3-8b-8192"  # Choose a sensible default

client = OpenAI(
    base_url=baseurl,
    api_key=api_key,
)

# --- Example: List and Select Models ---
print("--- Available Models ---")
available_models = []
try:
    models = client.models.list()
    for i, model_obj in enumerate(models.data):
        print(f"{i + 1}: {model_obj.id}")
        available_models.append(model_obj.id)
except Exception as e:
    print(f"Error listing models: {e}")
    sys.exit(1)  # Exit if models cannot be listed

if not available_models:
    print("No models available from the API.")
    sys.exit(1)

print("------------------------\n")

selected_model_str = None
while selected_model_str is None:
    try:
        model_choice = input(
            # Updated prompt
            f"Select a model number (1-{len(available_models)}) or press ENTER for default ({DEFAULT_MODEL_ID}): ").strip()
        if not model_choice:  # Check for empty input
            selected_model_str = DEFAULT_MODEL_ID
            print(f"No selection made, defaulting to {DEFAULT_MODEL_ID}")
            break  # Exit loop if default is chosen
        model_index = int(model_choice) - 1
        if 0 <= model_index < len(available_models):
            selected_model_str = available_models[model_index]
        else:
            print("Invalid number. Please try again.")
    except ValueError:
        print("Invalid input. Please enter a number or press ENTER.")

# --- End Example ---

# Get user input dynamically
user_message = input("Please enter your message (ENTER for default): ").strip()
if not user_message:
    user_message = "Berlin, Sao Paulo or Mumbai? Out of these choose a winner! Explain your winner decision briefly in the style: WINNERCITY: Because: EXPLANATIONSENTENCE"
print('\n\n--')
print(f"Model: {selected_model_str}")
print(f"User message: {user_message}")

completion = client.chat.completions.create(
    model=selected_model_str,
    messages=[{"role": "user",
               "content": user_message}],
    stream=True,  # Enable streaming
    max_tokens=2048,
)

for chunk in completion:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
