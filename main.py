# main.py (Final Production Version for Render)
import os
import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# This loads environment variables from Render's dashboard
load_dotenv()

import document_processor
import vector_store_manager
import llm_interface

app = FastAPI()

# --- CRITICAL: CORS CONFIGURATION FOR PRODUCTION ---
# This list MUST include the URL of your live frontend on Netlify.
origins = [
    "https://brilliant-halva-3b002a.netlify.app", # <-- IMPORTANT: REPLACE with your actual Netlify URL
    # You can add other domains here later if needed, e.g., "https://www.my-customer.com"
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
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not found.")
    if "sslmode" not in database_url:
        database_url += "?sslmode=require"
    conn = psycopg2.connect(database_url)
    return conn

# --- API ENDPOINTS (No changes needed here) ---
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
            final_answer = "I'm sorry, I couldn't find information on that topic in the knowledge base."
        else:
            context = "\n\n".join(retrieved_texts)
            personality_map = {
                "friendly": "You are a friendly, helpful AI assistant for '{name}'.",
                "formal": "You are a formal and direct AI assistant for '{name}'.",
                "concise": "You are a concise AI assistant for '{name}'."
            }
            system_prompt = personality_map.get(business['personality'], 'friendly').format(name=business['name'])
            user_prompt_with_context = f"Retrieved Information:\n{context}\n\nUser Question: {request.question}"
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
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

if __name__ == "__main__":
    # This part is mostly for local testing, Render will use the Procfile/Start Command
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)