import sqlite3
import os

def add_difficulty_column():
    # Connect to the SQLite database
    conn = sqlite3.connect('learnbyemail.db')
    cursor = conn.cursor()
    
    # Check if difficulty column exists
    cursor.execute("PRAGMA table_info(subscriptions)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    # Add the difficulty column if it doesn't exist
    if 'difficulty' not in column_names:
        print("Adding 'difficulty' column to subscriptions table...")
        cursor.execute("ALTER TABLE subscriptions ADD COLUMN difficulty TEXT DEFAULT 'medium' NOT NULL")
        conn.commit()
        print("Column added successfully!")
    else:
        print("'difficulty' column already exists in subscriptions table")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    add_difficulty_column()