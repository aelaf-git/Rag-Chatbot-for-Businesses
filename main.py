# main.py - Your Production API Backend
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# --- NEW: Import the CORS middleware ---
from fastapi.middleware.cors import CORSMiddleware

# Import our existing RAG modules
import document_processor
import vector_store_manager
import llm_interface

app = FastAPI()

# --- NEW: Add the CORS middleware to your app ---
# This is the "permission slip" that tells browsers it's okay to connect.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (e.g., 'null', 'http://localhost:3000')
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)
# --- END OF NEW SECTION ---


# Define the request data structure
class ChatRequest(BaseModel):
    question: str
    businessId: str

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    """This function is called by the JavaScript widget."""
    print(f"Received question for business {request.businessId}: {request.question}")
    
    query_embedding = document_processor.generate_embeddings([request.question])[0]
    retrieved_texts = vector_store_manager.search_faiss_index(request.businessId, query_embedding)

    if not retrieved_texts:
        return {"answer": "I'm sorry, but I couldn't find any information related to that question."}
    
    context = "\n\n".join(retrieved_texts)
    
    # The full system prompt for the bot's personality
    system_prompt = f"""
    You are a friendly, helpful, and professional customer service AI assistant.
    Your personality should be welcoming and conversational.

    **Your Instructions:**
    1.  **Primary Goal:** Your main purpose is to answer the user's question based *only* on the "Retrieved Information" provided below.
    2.  **Detailed Answers:** When the user asks about the company, use the retrieved information to provide a detailed, clear, and comprehensive explanation. Use formatting like bullet points or bold text if it helps make the answer easier to understand.
    3.  **Friendly Tone:** Always maintain a positive and friendly tone. Start your answers with a friendly greeting (e.g., "Great question!", "Certainly!", "I can help with that!").
    4.  **Handling Unknowns:** If the answer to a question cannot be found in the "Retrieved Information," you MUST say: "I'm sorry, but I couldn't find specific information about that in our knowledge base. Is there anything else I can help you with?" DO NOT make up answers.
    5.  **General Conversation:** If the user's question is a simple greeting or small talk (like "hello", "how are you?"), respond naturally and friendly without mentioning the retrieved information.
    """

    user_prompt_with_context = f"Retrieved Information: {context}\n\nUser Question: {request.question}"
    
    messages_payload = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_with_context}
    ]
    
    response = llm_interface.generate_response_with_groq(messages_payload)
    
    return {"answer": response}

if __name__ == "__main__":
    # This runs the API server on localhost port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)