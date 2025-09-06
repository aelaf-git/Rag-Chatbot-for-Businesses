# main.py - Your Production API Backend
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import our existing RAG modules
import document_processor
import vector_store_manager
import llm_interface

app = FastAPI()

# --- IMPORTANT: CORS Middleware ---
# This allows your JavaScript widget (running on a different domain)
# to make requests to this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the request data structure
class ChatRequest(BaseModel):
    question: str
    businessId: str

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    """This function is called by the JavaScript widget."""
    print(f"Received question for business {request.businessId}: {request.question}")
    
    # --- RE-USE ALL OUR EXISTING RAG LOGIC ---
    query_embedding = document_processor.generate_embeddings([request.question])[0]
    retrieved_texts = vector_store_manager.search_faiss_index(request.businessId, query_embedding)

    if not retrieved_texts:
        return {"answer": "I couldn't find any relevant information for that question."}
    
    context = "\n\n".join(retrieved_texts)
    
    # This is the same prompt engineering we did in app.py
    system_prompt = "..." # (Copy the detailed system prompt from app.py here)
    user_prompt_with_context = f"Retrieved Info: {context}\n\nUser Question: {request.question}"
    
    messages_payload = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_with_context}
    ]
    
    response = llm_interface.generate_response_with_groq(messages_payload)
    
    return {"answer": response}

if __name__ == "__main__":
    # This runs the API server on localhost port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)