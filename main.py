import os
import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from dotenv import load_dotenv

# --- CRITICAL: LOAD ENVIRONMENT VARIABLES ---
# This will load a local .env file if it exists (for testing).
# On Render, it does nothing, and we rely on the environment variables
# set in the Render dashboard.
load_dotenv()

# Import our custom modules
import document_processor
import vector_store_manager
import llm_interface

app = FastAPI()

# --- CORS CONFIGURATION ---
origins = [
    "https://brilliant-halva-3b002a.netlify.app", # Your Netlify frontend
    "http://localhost",                          # For XAMPP
    "http://localhost:8080",
    "http://127.0.0.1",
    "null"                                       # For file:/// local testing
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATABASE CONNECTION ---
def get_db_connection():
    # Read the database URL directly from the environment.
    # This works both locally (with .env) and on Render.
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # This will cause a clean crash with a clear error if the variable is missing.
        raise ValueError("DATABASE_URL environment variable not found.")
    
    if "sslmode" not in database_url:
        database_url += "?sslmode=require"
        
    conn = psycopg2.connect(database_url)
    return conn

# --- API ENDPOINTS ---
@app.get("/config/{business_id}")
def get_config(business_id: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT * FROM businesses WHERE id = %s', (business_id,))
        business = cursor.fetchone()
        cursor.close()
        conn.close()
        if business is None:
            raise HTTPException(status_code=404, detail="Business not found")
        return dict(business)
    except Exception as e:
        print(f"ERROR in /config endpoint: {e}")
        raise HTTPException(status_code=500, detail="Database connection error.")

class ChatRequest(BaseModel):
    question: str
    businessId: str

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT * FROM businesses WHERE id = %s', (request.businessId,))
        business = cursor.fetchone()
        
        if business is None:
            raise HTTPException(status_code=404, detail="Business configuration not found")

        query_embedding = document_processor.generate_embeddings([request.question])[0]
        retrieved_texts = vector_store_manager.search_faiss_index(request.businessId, query_embedding)

        if not retrieved_texts:
            final_answer = "I'm sorry, but I couldn't find specific information about that. Would you like me to connect you with our team?"
        else:
            context = "\n\n".join(retrieved_texts)
            personality_map = {
                "friendly": "You are a friendly, helpful, and professional customer service AI assistant for '{name}'. Your personality should be welcoming and conversational.",
                "formal": "You are a formal and direct AI assistant for '{name}'. Provide precise information.",
                "concise": "You are a concise AI assistant for '{name}'. Get straight to the point."
            }
            system_prompt = personality_map.get(business['personality'], personality_map['friendly']).format(name=business['name'])
            user_prompt_with_context = f"Retrieved Information:\n{context}\n\nUser Question:\n{request.question}"
            messages_payload = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt_with_context}]
            
            groq_api_key = os.getenv("GROQ_API_KEY")
            final_answer = llm_interface.generate_response_with_groq(messages_payload, api_key=groq_api_key)

        cursor.execute('INSERT INTO chat_logs (business_id, question, answer) VALUES (%s, %s, %s)', (request.businessId, request.question, final_answer))
        conn.commit()
        cursor.close()
        conn.close()
        return {"answer": final_answer}
    except Exception as e:
        print(f"ERROR in /chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred.")

# Fallback endpoint for the script, though Netlify is preferred
@app.get("/script.js")
async def get_script():
    return FileResponse('static/script.js')

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)