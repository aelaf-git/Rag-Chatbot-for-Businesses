import sqlite3
import psycopg2
import psycopg2.extras
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from dotenv import load_dotenv

# This will load the .env file for local development
if os.path.exists('.env'):
    load_dotenv()

# Import our custom modules
import document_processor
import vector_store_manager
import llm_interface

app = FastAPI()

# --- THE DEFINITIVE CORS CONFIGURATION ---
# This list explicitly allows your frontend domains and local testing origins.
origins = [
    "https://brilliant-halva-3b002a.netlify.app",  # Your Netlify frontend
    "http://localhost",                          # For XAMPP
    "http://localhost:8080",                     # Common local dev port
    "http://127.0.0.1",
    "null"                                       # For file:/// local testing
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods, including OPTIONS, GET, POST
    allow_headers=["*"],  # Allows all headers
)

def get_db_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not found.")
    if "sslmode" not in database_url:
        database_url += "?sslmode=require"
    conn = psycopg2.connect(database_url)
    return conn

# --- API ENDPOINTS ---
@app.get("/config/{business_id}")
def get_config(business_id: str):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM businesses WHERE id = %s', (business_id,))
    business = cursor.fetchone()
    cursor.close()
    conn.close()
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found")
    return dict(business)

class ChatRequest(BaseModel):
    question: str
    businessId: str

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM businesses WHERE id = %s', (request.businessId,))
    business = cursor.fetchone()
    if business is None:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Business configuration not found")

    query_embedding = document_processor.generate_embeddings([request.question])[0]
    retrieved_texts = vector_store_manager.search_faiss_index(request.businessId, query_embedding)

    if not retrieved_texts:
        final_answer = "I'm sorry, but I couldn't find specific information about that. Would you like me to connect you with our team?"
    else:
        context = "\n\n".join(retrieved_texts)
        personality_map = {
            "friendly": "You are a friendly, helpful, and professional customer service AI assistant for the company '{name}'. Your personality should be welcoming and conversational.",
            "formal": "You are a formal and direct AI assistant for '{name}'. Provide precise information without unnecessary pleasantries.",
            "concise": "You are a concise AI assistant for '{name}'. Get straight to the point and provide short, clear answers."
        }
        system_prompt = personality_map.get(business['personality'], personality_map['friendly']).format(name=business['name'])
        system_prompt += "\n\n**Your Instructions:**..." # Add your detailed instructions here
        user_prompt_with_context = f"Retrieved Information:\n{context}\n\nUser Question:\n{request.question}"
        messages_payload = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt_with_context}]
        
        # The backend uses its own environment variable for the API key
        groq_api_key = os.getenv("GROQ_API_KEY")
        final_answer = llm_interface.generate_response_with_groq(messages_payload, api_key=groq_api_key)

    cursor.execute('INSERT INTO chat_logs (business_id, question, answer) VALUES (%s, %s, %s)', (request.businessId, request.question, final_answer))
    conn.commit()
    cursor.close()
    conn.close()
    return {"answer": final_answer}

# This endpoint is no longer needed as we are serving from Netlify
# but we can keep it for fallback testing.
@app.get("/script.js")
async def get_script():
    return FileResponse('static/script.js')

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)