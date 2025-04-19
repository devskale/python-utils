from openai import OpenAI

provider = 'arli'
model = 'Mistral-Nemo-12B-Instruct-2407'

provider = 'groq'
model = 'qwen-qwq-32b'

# provider = 'ollama'
# model = 'gemma3:4b'
# model = 'phi4-mini:latest'

# the baseurl where uniinfer oai proxy server is running
baseurl = 'http://localhost:8000/v1'

# IMPORTANT
# the key is required for underlying uniinfer package to retrieve provider specific apikeys
# see credgoo package for more details
api_key = "test23@test34"
# api_key = None

client = OpenAI(
    base_url=baseurl,
    api_key=api_key,
)

# Get user input dynamically
user_message = input("Please enter your message (ENTER for default): ").strip()
if not user_message:
    user_message = "Berlin, Sao Paulo or Mumbai? Out of these choose a winner! Explain your winner decision briefly in the style: WINNERCITY: Because: EXPLANATIONSENTENCE"
print('\n\n--')
print(f"{provider}@{model}")
print(f"User message: {user_message}")

completion = client.chat.completions.create(
    model=f"{provider}@{model}",  # Specify the model here
    messages=[{"role": "user",
               "content": user_message}],
    stream=True,  # Enable streaming
    max_tokens=1024,
)


for chunk in completion:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
