import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import os
import psycopg2
import psycopg2.extras
import document_processor
import vector_store_manager
import llm_interface

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    database_url = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(database_url)
    # Use DictCursor to get results as dictionaries (like sqlite3.Row)
    conn.cursor_factory = psycopg2.extras.DictCursor
    return conn

# --- NEW ENDPOINT: To fetch widget configuration ---
@app.get("/config/{business_id}")
def get_config(business_id: str):
    conn = get_db_connection()
    business = conn.execute('SELECT * FROM businesses WHERE id = ?', (business_id,)).fetchone()
    conn.close()
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found")
    return dict(business)

class ChatRequest(BaseModel):
    question: str
    businessId: str

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    print(f"Received question for business {request.businessId}: {request.question}")
    
    conn = get_db_connection()
    business = conn.execute('SELECT * FROM businesses WHERE id = ?', (request.businessId,)).fetchone()
    if business is None:
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
        system_prompt += "\n\n**Your Instructions:**..." # Add the rest of your detailed instructions here

        user_prompt_with_context = f"Retrieved Information:\n{context}\n\nUser Question:\n{request.question}"
        
        messages_payload = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt_with_context}
        ]
        
        final_answer = llm_interface.generate_response_with_groq(messages_payload)

    # Log the conversation to the database
    conn.execute('INSERT INTO chat_logs (business_id, question, answer) VALUES (?, ?, ?)',
                 (request.businessId, request.question, final_answer))
    conn.commit()
    conn.close()
    
    return {"answer": final_answer}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)