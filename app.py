# app.py (Corrected Version)
import streamlit as st
import os
import uuid # For generating unique business IDs
from dotenv import load_dotenv

# Import our custom modules
import document_processor
import vector_store_manager
import llm_interface

load_dotenv() # Load environment variables

# --- Streamlit Page Configuration ---
st.set_page_config(layout="wide", page_title="AI Business Chatbot Builder")

# --- Session State Initialization ---
if 'business_data' not in st.session_state:
    st.session_state['business_data'] = {} # Stores {business_id: {'name': str, 'index': faiss_index, 'texts': list_of_texts}}
if 'selected_business_id' not in st.session_state:
    st.session_state['selected_business_id'] = None
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = {} # Stores chat history per business_id

# --- Helper Functions ---
def process_uploaded_content(business_id, raw_content):
    """Processes raw text content into chunks, embeddings, and updates FAISS."""
    if not raw_content or not raw_content.strip():
        st.warning(f"No content to process for {business_id}.")
        return

    st.info(f"Processing content for business {business_id}...")
    text_chunks = document_processor.chunk_text(raw_content)
    embeddings = document_processor.generate_embeddings(text_chunks)

    # --- THIS IS THE CORRECTED SECTION ---
    # Get the existing data for the business
    business_info = st.session_state['business_data'].get(business_id, {})
    current_index = business_info.get('index')
    current_texts = business_info.get('texts', [])
    business_name = business_info.get('name', business_id) # Keep the name

    # If this is the first time, create a new index
    if current_index is None:
        embedding_dim = document_processor.EMBEDDING_MODEL.get_sentence_embedding_dimension()
        current_index, current_texts = vector_store_manager.create_or_load_faiss_index(business_id, embedding_dimension=embedding_dim)
    # --- END OF CORRECTION ---

    # Add new data to the index
    new_index, new_texts = vector_store_manager.add_embeddings_to_faiss(
        business_id, embeddings, text_chunks, current_index, current_texts
    )
    # Update the session state with the new index, texts, and preserve the name
    st.session_state['business_data'][business_id] = {
        'name': business_name,
        'index': new_index,
        'texts': new_texts
    }
    st.success(f"Knowledge base updated for {business_id} with {len(text_chunks)} new chunks.")


# --- Sidebar for Navigation ---
st.sidebar.title("Navigation")
page_selection = st.sidebar.radio("Go to", ["Business Dashboard", "Simulated Chat"])

# --- Main Content Area ---
st.title("AI Business Chatbot Builder")

if page_selection == "Business Dashboard":
    st.header("Business Onboarding & Knowledge Base Management")

    with st.expander("Register New Business / Manage Existing", expanded=True):
        new_business_name = st.text_input("New Business Name (e.g., 'Acme Corp')", key="new_biz_name")
        if st.button("Register Business"):
            if new_business_name:
                business_id = str(uuid.uuid4()) # Generate unique ID
                st.session_state['business_data'][business_id] = {
                    'name': new_business_name,
                    'index': None, # Will be loaded/created on first upload
                    'texts': []
                }
                st.success(f"Business '{new_business_name}' registered with ID: {business_id}")
                st.session_state['selected_business_id'] = business_id
                # Use st.rerun() to immediately reflect the change in the selectbox
                st.rerun()
            else:
                st.error("Please enter a business name.")

        st.subheader("Select Existing Business")
        if st.session_state['business_data']:
            business_options = {
                data.get('name', biz_id): biz_id
                for biz_id, data in st.session_state['business_data'].items()
            }
            # Find the index of the currently selected business for the selectbox default
            current_selection_index = 0
            if st.session_state['selected_business_id']:
                try:
                    selected_name = st.session_state['business_data'][st.session_state['selected_business_id']].get('name')
                    current_selection_index = list(business_options.keys()).index(selected_name)
                except (ValueError, KeyError):
                    current_selection_index = 0

            selected_display_name = st.selectbox(
                "Choose a business to manage:",
                options=list(business_options.keys()),
                index=current_selection_index
            )
            st.session_state['selected_business_id'] = business_options[selected_display_name]
            st.info(f"Currently managing: **{st.session_state['business_data'][st.session_state['selected_business_id']].get('name', st.session_state['selected_business_id'])}**")
        else:
            st.warning("No businesses registered yet. Register one above!")

    if st.session_state['selected_business_id']:
        current_business_id = st.session_state['selected_business_id']
        st.subheader(f"Knowledge Base for {st.session_state['business_data'][current_business_id].get('name', current_business_id)}")

        st.write("---")
        st.subheader("Upload Documents")
        uploaded_files = st.file_uploader("Upload PDFs or Text files", type=["pdf", "txt"], accept_multiple_files=True, key=f"upload_{current_business_id}")
        if st.button("Process Uploaded Files"):
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    file_content = ""
                    if uploaded_file.type == "application/pdf":
                        temp_file_path = os.path.join("data", current_business_id, uploaded_file.name)
                        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
                        with open(temp_file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        file_content = document_processor.get_text_from_pdf(temp_file_path)
                        os.remove(temp_file_path)
                    elif uploaded_file.type == "text/plain":
                        file_content = uploaded_file.getvalue().decode("utf-8")

                    if file_content:
                        process_uploaded_content(current_business_id, file_content)
            else:
                st.warning("Please upload files before processing.")


        st.write("---")
        st.subheader("Scrape Website URL")
        url_to_scrape = st.text_input("Enter URL to scrape (e.g., https://example.com/faq)", key="url_scrape")
        if st.button("Scrape and Add to KB"):
            if url_to_scrape:
                with st.spinner(f"Scraping {url_to_scrape}..."):
                    scraped_text = document_processor.get_text_from_url(url_to_scrape)
                    if scraped_text:
                        process_uploaded_content(current_business_id, scraped_text)
                    else:
                        st.error(f"Could not scrape content from {url_to_scrape}.")
            else:
                st.warning("Please enter a URL to scrape.")

        st.write("---")
        st.subheader("Your Embed Code (Simulated)")
        st.code(f"""
<script src="https://yourdomain.com/chatbot-widget.js?businessId={current_business_id}"></script>
<div id="chatbot-container"></div>
        """, language="html")
        st.caption("This code snippet would be placed on your business website.")

elif page_selection == "Simulated Chat":
    st.header("Simulated Chat with Your AI Agent")

    if not st.session_state['business_data']:
        st.warning("No businesses registered. Please go to the 'Business Dashboard' to register one and upload content.")
    else:
        business_options = {
            data.get('name', biz_id): biz_id
            for biz_id, data in st.session_state['business_data'].items()
        }
        selected_chat_business_display_name = st.selectbox(
            "Select a business to chat with:",
            options=list(business_options.keys()),
            key="chat_biz_select"
        )
        selected_chat_business_id = business_options[selected_chat_business_display_name]

        if selected_chat_business_id not in st.session_state['chat_history']:
            st.session_state['chat_history'][selected_chat_business_id] = []

        st.subheader(f"Chat with {st.session_state['business_data'][selected_chat_business_id].get('name', selected_chat_business_id)} Bot")

        # Display chat messages from history
        for message in st.session_state['chat_history'][selected_chat_business_id]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Ask your question here..."):
            st.session_state['chat_history'][selected_chat_business_id].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate bot response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # 1. Embed user query
                    query_embedding = document_processor.generate_embeddings([prompt])[0]

                    # 2. Retrieve relevant info from FAISS
                    retrieved_texts = vector_store_manager.search_faiss_index(selected_chat_business_id, query_embedding)

                    if not retrieved_texts:
                        response = "I couldn't find any relevant information in the knowledge base for that question. Please try rephrasing or ask about something else."
                    else:
                        context = "\n\n".join(retrieved_texts)
                        full_prompt = (
                            f"You are a helpful AI assistant for the business '{selected_chat_business_display_name}'. "
                            "Answer the user's question ONLY based on the following retrieved information. "
                            "If the answer cannot be found in the provided information, state that you don't know.\n\n"
                            f"Retrieved Information:\n{context}\n\n"
                            f"User Question: {prompt}"
                        )
                        # 3. LLM generates natural reply
                        response = llm_interface.generate_response_with_groq(full_prompt)

                st.markdown(response)
                st.session_state['chat_history'][selected_chat_business_id].append({"role": "assistant", "content": response})