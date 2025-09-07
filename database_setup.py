import os
import psycopg2
from dotenv import load_dotenv

if os.path.exists('.env'):
    load_dotenv()

database_url = os.getenv("DATABASE_URL")

def setup_database():
    # Render provides the database URL in an environment variable
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set.")
    
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS businesses (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        agent_name TEXT DEFAULT 'AI Assistant',
        welcome_message TEXT DEFAULT 'Hi! How can I help you today?',
        personality TEXT DEFAULT 'friendly',
        brand_color TEXT DEFAULT '#007bff'
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_logs (
        log_id SERIAL PRIMARY KEY,
        business_id TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (business_id) REFERENCES businesses (id)
    )
    ''')

    conn.commit()
    cursor.close()
    conn.close()
    print("Database setup or verification complete.")

if __name__ == '__main__':
    setup_database()