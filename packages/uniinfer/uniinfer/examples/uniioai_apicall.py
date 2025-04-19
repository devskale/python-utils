from credgoo import get_api_key
from openai import OpenAI

provider = 'arli'
model = 'Mistral-Nemo-12B-Instruct-2407'

provider = 'groq'
model = 'qwen-qwq-32b'

provider = 'ollama'
model = 'gemma3:4b'

baseurl = 'http://localhost:8000/v1'

api_key = "test23@test34"

client = OpenAI(
    base_url=baseurl,
    api_key=api_key,
)

# Get user input dynamically
user_message = input("Please enter your message (ENTER for default): ").strip()
if not user_message:
    user_message = "Berlin, Sao Paulo or Mumbai. choose only one. explain your decision briefly in the style: CITY: Because: EXPLANATIONSENTENCE"
print('\n\n--')
print(f"{provider}@{model}")
print(f"User message: {user_message}")

completion = client.chat.completions.create(
    model=f"{provider}@{model}",  # Specify the model here
    messages=[{"role": "user",
               "content": user_message}],
    stream=True  # Enable streaming
)


for chunk in completion:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
