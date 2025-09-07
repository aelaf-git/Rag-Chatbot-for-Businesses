# llm_interface.py (Updated for better conversation control)
import os
from typing import List, Dict
from dotenv import load_dotenv
from groq import Groq

# --- THIS IS THE KEY CHANGE ---
# Load .env file ONLY if the script is run locally for testing.
# On a server like Render, the environment variables are set directly.
if os.path.exists('.env'):
    load_dotenv()

# Get the API key from the environment variables.
# os.getenv() will read the secret file you set on Render.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Now, check if the key was found.
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set in the environment or .env file.")
# --- END OF CHANGE ---

client = Groq(api_key=GROQ_API_KEY)
# --- Function now accepts a list of messages for role-playing ---
def generate_response_with_groq(messages: List[Dict], model: str = "openai/gpt-oss-120b") -> str:
    """
    Generates a response using Groq's chat completion API.
    Accepts a list of message dictionaries with 'role' and 'content'.
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=messages, # Pass the structured message list directly
            model=model,
            temperature=0.7, # Keep a little creativity
            max_tokens=2048,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return "Sorry, I'm having trouble generating a response right now."