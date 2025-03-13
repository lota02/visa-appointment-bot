import sqlite3

DB_PATH = "user_data.db"

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())

def initialize_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Create 'users' table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                chat_id INTEGER NOT NULL UNIQUE,
                username TEXT NOT NULL,
                last_active TEXT NOT NULL
            )
        ''')

        # Add new columns only if they don't exist
        for column, column_type in [
            ("notify_time", "TEXT"),
            ("notify_days", "TEXT"),
            ("active_notifications", "INTEGER DEFAULT 0"),
            ("payment_status", "TEXT DEFAULT 'unpaid'")
        ]:
            if not column_exists(cursor, 'users', column):
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column} {column_type};")

        # Create 'user_details' table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_details (
                user_id INTEGER UNIQUE,
                ds160 TEXT NOT NULL,
                credentials TEXT NOT NULL,
                date_range TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
        ''')

        conn.commit()

if __name__ == "__main__":
    initialize_db()
    print("✅ Database initialized successfully!")

