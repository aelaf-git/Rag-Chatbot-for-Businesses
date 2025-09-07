import streamlit as st
import sqlite3 # Keep for potential fallback, though not used
import psycopg2
import psycopg2.extras
import uuid
import os

# Import our custom modules
import document_processor
import vector_store_manager
import llm_interface

st.set_page_config(layout="wide", page_title="AI Agent Dashboard")

def get_db_connection():
    database_url = st.secrets["DATABASE_URL"]
    if "sslmode" not in database_url:
        database_url += "?sslmode=require"
    conn = psycopg2.connect(database_url)
    return conn

# --- Business Management Functions ---
def get_all_businesses():
    conn = get_db_connection()
    # --- FIX: Create a cursor ---
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM businesses')
    businesses = cursor.fetchall()
    cursor.close()
    conn.close()
    return businesses

def update_business_settings(business_id, agent_name, welcome_message, personality, brand_color):
    conn = get_db_connection()
    # --- FIX: Create a cursor ---
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE businesses 
        SET agent_name = %s, welcome_message = %s, personality = %s, brand_color = %s
        WHERE id = %s
    ''', (agent_name, welcome_message, personality, brand_color, business_id))
    conn.commit()
    cursor.close()
    conn.close()

# --- Content Processing Function ---
# (This function is correct, no changes needed here)
def process_and_store_content(business_id, raw_content):
    # ... (no changes)

# --- Main App ---
st.title("🤖 AI Agent Dashboard")
st.sidebar.header("Business Selection")
businesses = get_all_businesses()
business_options = {b['name']: b['id'] for b in businesses} if businesses else {}
selected_name = None

if business_options:
    selected_name = st.sidebar.selectbox("Select a Business", list(business_options.keys()))
else:
    st.sidebar.info("No businesses found. Please register one below.")

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
                # --- FIX: Create a cursor ---
                cursor = conn.cursor()
                cursor.execute('INSERT INTO businesses (id, name) VALUES (%s, %s)', (new_id, new_business_name))
                conn.commit()
                cursor.close()
                conn.close()
                st.sidebar.success(f"Business '{new_business_name}' registered!")
                st.rerun()
        else:
            st.sidebar.error("Business name cannot be empty.")

# --- Main Dashboard Area ---
if selected_name:
    business_id = business_options[selected_name]
    conn = get_db_connection()
    # --- FIX: Create a cursor ---
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM businesses WHERE id = %s', (business_id,))
    current_business = cursor.fetchone()
    cursor.close()
    conn.close()

    st.header(f"Managing: {current_business['name']}")

    tab1, tab2, tab5, tab3, tab4 = st.tabs(["📚 Knowledge Sources", "🎨 Customize Agent", "🧪 Test Your Agent", "🚀 Deploy", "📊 Analytics"])

    # (The code for tab1, tab2, and tab5 is correct and needs no changes)
    with tab1:
        # ... your tab1 code ...
    with tab2:
        # ... your tab2 code ...
    with tab5:
        # ... your tab5 code ...

    with tab3:
        # (The code for tab3 is correct and needs no changes)
        # ...

    with tab4:
        st.subheader("Analytics")
        conn = get_db_connection()
        # --- FIX: Create a cursor ---
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT question, COUNT(*) as count FROM chat_logs WHERE business_id = %s GROUP BY question ORDER BY count DESC LIMIT 10', (business_id,))
        logs = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE business_id = %s AND DATE(timestamp) = CURRENT_DATE", (business_id,))
        daily_queries_result = cursor.fetchone()
        daily_queries = daily_queries_result[0] if daily_queries_result else 0
        cursor.close()
        conn.close()
        
        st.metric("Queries Today", daily_queries)
        st.write("**Most Asked Questions:**")
        if logs:
            for log in logs:
                st.write(f"- {log['question']} ({log['count']} times)")
        else:
            st.write("No questions have been asked yet.")

# You need to paste the full code for tab1, tab2, and tab5 back in.
# For example, the full tab2:
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