# llm_interface.py (Updated with the new model)
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv() # Load environment variables from .env file

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env file.")

client = Groq(api_key=GROQ_API_KEY)

# --- The model name has been updated as per your request ---
def generate_response_with_groq(prompt: str, model: str = "llama-3.1-70b-versatile") -> str:
    """
    Generates a response using Groq's chat completion API.
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model,
            temperature=0.7,
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return "Sorry, I'm having trouble generating a response right now."