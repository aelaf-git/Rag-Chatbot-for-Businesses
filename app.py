import streamlit as st
import sqlite3
import uuid
import os
import llm_interface
import psycopg2
import psycopg2.extras

# Import our custom modules
import document_processor
import vector_store_manager

st.set_page_config(layout="wide", page_title="AI Agent Dashboard")

def get_db_connection():
    # This will read the secret from the Streamlit Cloud's secrets manager
    database_url = st.secrets["DATABASE_URL"]
    
    # --- THIS IS THE CRUCIAL FIX ---
    # Append the SSL requirement to the URL if it's not already there.
    if "sslmode" not in database_url:
        database_url += "?sslmode=require"
    # --- END OF FIX ---

    conn = psycopg2.connect(database_url)
    conn.cursor_factory = psycopg2.extras.DictCursor
    return conn

# --- Business Management Functions ---
def get_all_businesses():
    conn = get_db_connection()
    businesses = conn.execute('SELECT * FROM businesses').fetchall()
    conn.close()
    return businesses

def update_business_settings(business_id, agent_name, welcome_message, personality, brand_color):
    conn = get_db_connection()
    conn.execute('''
        UPDATE businesses 
        SET agent_name = ?, welcome_message = ?, personality = ?, brand_color = ?
        WHERE id = ?
    ''', (agent_name, welcome_message, personality, brand_color, business_id))
    conn.commit()
    conn.close()

# --- Content Processing Function ---
def process_and_store_content(business_id, raw_content):
    if not raw_content or not raw_content.strip():
        st.warning(f"No content to process for {business_id}.")
        return

    st.info(f"Processing content for business {business_id}...")
    with st.spinner("Chunking text, generating embeddings, and updating knowledge base..."):
        text_chunks = document_processor.chunk_text(raw_content)
        embeddings = document_processor.generate_embeddings(text_chunks)
        
        # This logic is from our old app.py, adapted for the new structure
        index_dir = os.path.join("data", business_id)
        os.makedirs(index_dir, exist_ok=True)
        embedding_dim = document_processor.get_embedding_model().get_sentence_embedding_dimension()
        current_index, current_texts = vector_store_manager.create_or_load_faiss_index(business_id, embedding_dimension=embedding_dim)

        vector_store_manager.add_embeddings_to_faiss(
            business_id, embeddings, text_chunks, current_index, current_texts
        )
    st.success(f"Knowledge base updated for {business_id} with {len(text_chunks)} new chunks.")

# --- Main App ---
st.title("🤖 AI Agent Dashboard")

st.sidebar.header("Business Selection")
businesses = get_all_businesses()

# --- THIS IS THE CORRECTED SECTION ---
business_options = {b['name']: b['id'] for b in businesses} if businesses else {}
selected_name = None

if business_options:
    selected_name = st.sidebar.selectbox("Select a Business", list(business_options.keys()))
else:
    st.sidebar.info("No businesses found. Please register one below.")
# --- END OF CORRECTION ---

# New Business Registration
with st.sidebar.expander("Register New Business"):
    new_business_name = st.text_input("Enter New Business Name")
    if st.button("Register"):
        if new_business_name:
            if new_business_name in business_options:
                st.sidebar.error("A business with this name already exists.")
            else:
                new_id = str(uuid.uuid4())
                conn = get_db_connection()
                conn.execute('INSERT INTO businesses (id, name) VALUES (?, ?)', (new_id, new_business_name))
                conn.commit()
                conn.close()
                st.sidebar.success(f"Business '{new_business_name}' registered!")
                st.rerun()
        else:
            st.sidebar.error("Business name cannot be empty.")

# --- Main Dashboard Area ---
if selected_name:
    business_id = business_options[selected_name]
    conn = get_db_connection()
    current_business = conn.execute('SELECT * FROM businesses WHERE id = ?', (business_id,)).fetchone()
    conn.close()

    st.header(f"Managing: {current_business['name']}")

    # REPLACE the st.tabs line with THIS BLOCK

    tab1, tab2, tab5, tab3, tab4 = st.tabs(["📚 Knowledge Sources", "🎨 Customize Agent", "🧪 Test Your Agent", "🚀 Deploy", "📊 Analytics"])

    with tab1:
        st.subheader("Upload Knowledge Sources")
        st.write("Add PDFs, text files, or scrape a website URL to build your agent's knowledge.")
        
        uploaded_files = st.file_uploader("Upload PDFs or Text files", type=["pdf", "txt"], accept_multiple_files=True, key=f"upload_{business_id}")
        if st.button("Process Uploaded Files", key=f"process_upload_{business_id}"):
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    # Logic to save and process files
                    temp_dir = os.path.join("data", business_id, "temp")
                    os.makedirs(temp_dir, exist_ok=True)
                    temp_file_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(temp_file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    if uploaded_file.type == "application/pdf":
                        raw_content = document_processor.get_text_from_pdf(temp_file_path)
                    else:
                        raw_content = uploaded_file.getvalue().decode("utf-8")
                    
                    process_and_store_content(business_id, raw_content)
                    os.remove(temp_file_path) # Clean up
            else:
                st.warning("Please upload files before processing.")

        st.subheader("Scrape a Website")
        url_to_scrape = st.text_input("Enter URL to scrape", key=f"url_{business_id}")
        if st.button("Scrape and Add", key=f"scrape_{business_id}"):
            if url_to_scrape:
                raw_content = document_processor.get_text_from_url(url_to_scrape)
                process_and_store_content(business_id, raw_content)
            else:
                st.warning("Please enter a URL.")

        st.info("Status: ✅ Agent is Ready.", icon="✅")
        st.button("Retrain Agent", help="This will re-process all existing sources. (Functionality to be added)")

    with tab2:
        st.subheader("Customize Your Agent")
        with st.form("customization_form"):
            agent_name = st.text_input("Agent Name", value=current_business['agent_name'])
            welcome_message = st.text_area("Welcome Message", value=current_business['welcome_message'], height=150)
            personality = st.selectbox("Personality", ["friendly", "formal", "concise"], index=["friendly", "formal", "concise"].index(current_business['personality']))
            brand_color = st.color_picker("Brand Color", value=current_business['brand_color'])
            
            submitted = st.form_submit_button("Save Customizations")
            if submitted:
                update_business_settings(business_id, agent_name, welcome_message, personality, brand_color)
                st.success("Settings saved successfully!")
                st.rerun()

    # --- THIS IS THE NEW TAB'S LOGIC ---
    with tab5:
        st.subheader("Test Your Agent in Real-time")
        st.write("Interact with your AI agent here to see how it responds with the current knowledge and personality settings.")

        # Initialize chat history in session state for this specific business
        if f"chat_history_{business_id}" not in st.session_state:
            st.session_state[f"chat_history_{business_id}"] = []

        # Display existing messages
        for message in st.session_state[f"chat_history_{business_id}"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input(f"Ask {current_business['agent_name']} a question..."):
            # Add user message to history
            st.session_state[f"chat_history_{business_id}"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate and display bot response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # This logic is copied from main.py and adapted for Streamlit
                    query_embedding = document_processor.generate_embeddings([prompt])[0]
                    retrieved_texts = vector_store_manager.search_faiss_index(business_id, query_embedding)

                    if not retrieved_texts:
                        final_answer = "I'm sorry, but I couldn't find specific information about that. Would you like me to connect you with our team?"
                    else:
                        context = "\n\n".join(retrieved_texts)
                        personality_map = {
                            "friendly": "You are a friendly, helpful, and professional customer service AI assistant for the company '{name}'. Your personality should be welcoming and conversational.",
                            "formal": "You are a formal and direct AI assistant for '{name}'. Provide precise information without unnecessary pleasantries.",
                            "concise": "You are a concise AI assistant for '{name}'. Get straight to the point and provide short, clear answers."
                        }
                        
                        system_prompt = personality_map.get(current_business['personality'], personality_map['friendly']).format(name=current_business['name'])
                        
                        # Add the detailed instructions for the AI
                        system_prompt += """
                        \n\n**Your Instructions:**
                        1.  **Primary Goal:** Your main purpose is to answer the user's question based *only* on the "Retrieved Information" provided below.
                        2.  **Detailed Answers:** When the user asks about the company, use the retrieved information to provide a detailed, clear, and comprehensive explanation. Use formatting like bullet points or bold text if it helps make the answer easier to understand.
                        3.  **Handling Unknowns:** If the answer to a question cannot be found in the "Retrieved Information," you MUST say: "I'm sorry, but I couldn't find specific information about that in our knowledge base. Is there anything else I can help you with?" DO NOT make up answers.
                        4.  **General Conversation:** If the user's question is a simple greeting or small talk (like "hello", "how are you?"), respond naturally and friendly without mentioning the retrieved information.
                        """

                        user_prompt_with_context = f"Retrieved Information:\n{context}\n\nUser Question:\n{prompt}"
                        
                        messages_payload = [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt_with_context}
                        ]
                        groq_api_key = st.secrets["GROQ_API_KEY"]
                        
                        final_answer = llm_interface.generate_response_with_groq(messages_payload, api_key=groq_api_key)

                    st.markdown(final_answer)
                    # Add bot response to history
                    st.session_state[f"chat_history_{business_id}"].append({"role": "assistant", "content": final_answer})
    # --- END OF NEW TAB ---

    with tab3:
        st.subheader("Get Your Embed Code")
        st.write("Copy this code snippet and paste it into your website's HTML, just before the closing `</body>` tag.")
        # Note: In a real product, this URL would be your public server's domain
        embed_code = f"""
<div id="chatbot-container"></div>
<script src="http://your_public_ip:8000/script.js" data-business-id="{business_id}"></script>
        """
        st.code(embed_code, language="html")

    with tab4:
        st.subheader("Analytics")
        conn = get_db_connection()
        logs = conn.execute('SELECT question, COUNT(*) as count FROM chat_logs WHERE business_id = ? GROUP BY question ORDER BY count DESC LIMIT 10', (business_id,)).fetchall()
        daily_queries = conn.execute("SELECT COUNT(*) FROM chat_logs WHERE business_id = ? AND DATE(timestamp) = DATE('now')", (business_id,)).fetchone()[0]
        conn.close()
        
        st.metric("Queries Today", daily_queries)
        st.write("**Most Asked Questions:**")
        if logs:
            for log in logs:
                st.write(f"- {log['question']} ({log['count']} times)")
        else:
            st.write("No questions have been asked yet.")
