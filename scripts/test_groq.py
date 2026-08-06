import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env
load_dotenv()

# Initialize the Groq client
# This will automatically pick up GROQ_API_KEY from environment variables
client = Groq()

model_name = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
print(f"Testing Groq client with model: {model_name}")

try:
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
          {
            "role": "user",
            "content": "Say hello!"
          }
        ],
        temperature=1,
        max_completion_tokens=2048,
        top_p=1,
        stream=True,
        stop=None
    )

    print("Response: ", end="")
    for chunk in completion:
        text = chunk.choices[0].delta.content or ""
        try:
            print(text, end="", flush=True)
        except UnicodeEncodeError:
            # Fallback to ascii representation or stripping
            print(text.encode('ascii', 'ignore').decode('ascii'), end="", flush=True)
    print()
except Exception as e:
    print(f"\nError running Groq test: {e}")
