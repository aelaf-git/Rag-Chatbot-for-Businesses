import sqlite3

def setup_database():
    conn = sqlite3.connect('chatbot_app.db')
    cursor = conn.cursor()

    # Table to store business information and customizations
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

    # Table to log chat interactions for analytics
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_id TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (business_id) REFERENCES businesses (id)
    )
    ''')

    conn.commit()
    conn.close()
    print("Database setup complete. 'chatbot_app.db' is ready.")

if __name__ == '__main__':
    setup_database()