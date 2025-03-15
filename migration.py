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

def add_is_admin_column():
    # Connect to the SQLite database
    conn = sqlite3.connect('learnbyemail.db')
    cursor = conn.cursor()
    
    # Check if is_admin column exists in users table
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    # Add the is_admin column if it doesn't exist
    if 'is_admin' not in column_names:
        print("Adding 'is_admin' column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0 NOT NULL")
        
        # Set the first user as admin for initial access
        cursor.execute("SELECT id FROM users ORDER BY id LIMIT 1")
        first_user = cursor.fetchone()
        if first_user:
            user_id = first_user[0]
            cursor.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
            print(f"Set user with ID {user_id} as admin")
        
        conn.commit()
        print("is_admin column added successfully!")
    else:
        print("'is_admin' column already exists in users table")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    add_difficulty_column()
    add_is_admin_column()