import sqlite3
import hashlib
import secrets
import sys
import os

def hash_password(password):
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def init_database():
    conn = None
    try:
        print("Initializing database...")
        db_exists = os.path.exists('users.db')
        if db_exists:
            print("Found existing users.db file")
        else:
            print("Creating new users.db file")

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        print("Creating users table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL CHECK(length(name) > 0 AND length(name) <= 100),
            email TEXT NOT NULL UNIQUE CHECK(length(email) > 0 AND length(email) <= 254),
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        print("Creating database indexes...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')

        print("Checking existing data...")
        try:
            cursor.execute("SELECT COUNT(*) FROM users")
            result = cursor.fetchone()
            count = result[0] if result and result[0] is not None else 0
        except sqlite3.Error as e:
            print(f"Error checking user count: {e}")
            count = 0

        print(f"Found {count} existing users in database")

        if count == 0:
            print("Adding sample users...")
            sample_users = [
                ('John Doe', 'john@example.com', 'password123'),
                ('Jane Smith', 'jane@example.com', 'secret456'),
                ('Bob Johnson', 'bob@example.com', 'qwerty789')
            ]

            for name, email, password in sample_users:
                try:
                    hashed_password = hash_password(password)
                    cursor.execute(
                        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                        (name, email, hashed_password)
                    )
                    print(f"Added user: {name} ({email})")
                except sqlite3.IntegrityError as e:
                    print(f"Skipped user {email}: {e}")

            print(f"\nDatabase initialized with {len(sample_users)} sample users")
            print("\nSample login credentials:")
            print("- john@example.com (password: password123)")
            print("- jane@example.com (password: secret456)")
            print("- bob@example.com (password: qwerty789)")
        else:
            print(f"Database already contains {count} users - skipping sample data insertion")

        conn.commit()
        print("Database changes committed")
        
        print("\nVerifying database setup...")
        try:
            cursor.execute("SELECT id, name, email, created_at FROM users ORDER BY id")
            users = cursor.fetchall()
            
            if users:
                print(f"\nCurrent users in database:")
                print("-" * 60)
                for user in users:
                    print(f"ID: {user[0]:<3} | Name: {user[1]:<15} | Email: {user[2]}")
            else:
                print("No users found in database")
                
        except sqlite3.Error as e:
            print(f"Error verifying setup: {e}")
        
        print(f"\nDatabase initialization completed successfully!")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
        sys.exit(1)
    
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if conn:
            conn.close()
            print("Database connection closed")

if __name__ == "__main__":
    init_database()
    