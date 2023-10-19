import sqlite3
import os
from schemas import Users,User_Roles

# Connect to the SQLite database
conn = sqlite3.connect('mydatabase.db')
cursor = conn.cursor()

# Create tables in the database
cursor.execute('''
    CREATE TABLE IF NOT EXISTS roles (
        role_id INTEGER PRIMARY KEY,
        name TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        uid INTEGER PRIMARY KEY,
        name TEXT,
        password TEXT,
        role_id INTEGER
    )
''')



# Add data to the database
def add_data():
    # Add roles
    role_data = [
        (1, "Admin"),
        (2, "User"),
    ]
    cursor.executemany('INSERT INTO roles (role_id, name) VALUES (?, ?)', role_data)

    # Add users
    user_data = [
        (1, "John", "password123", 1),
        (2, "Alice", "secret456", 2),
    ]
    cursor.executemany('INSERT INTO users (uid, name, password, role_id) VALUES (?, ?, ?, ?)', user_data)

    # Commit the changes to the database
    conn.commit()

# Call the function to add data
add_data()

# Close the database connection
conn.close()
