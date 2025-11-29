import sqlite3
import hashlib

class Database:
    def __init__(self, db_name="lost_and_found.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.update_schema() # Helper to add new columns if they don't exist

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)
        # Added image_path column
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                contact TEXT NOT NULL,
                image_path TEXT, 
                owner_id INTEGER,
                FOREIGN KEY(owner_id) REFERENCES users(id)
            )
        """)
        self.conn.commit()

    def update_schema(self):
        # Migrates old database to new version with image_path if it's missing
        try:
            self.cursor.execute("ALTER TABLE items ADD COLUMN image_path TEXT")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass # Column already exists

    def register_user(self, username, password, role):
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            self.cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                                (username, pwd_hash, role))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def login_user(self, username, password):
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        self.cursor.execute("SELECT id, username, role FROM users WHERE username=? AND password=?", 
                            (username, pwd_hash))
        return self.cursor.fetchone()

    def add_item(self, name, description, status, contact, image_path, owner_id):
        self.cursor.execute("""
            INSERT INTO items (name, description, status, contact, image_path, owner_id) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, description, status, contact, image_path, owner_id))
        self.conn.commit()

    def get_items(self, user_id, role):
        self.cursor.execute("""
            SELECT i.id, i.name, i.description, i.status, i.contact, i.image_path, u.username, i.owner_id
            FROM items i 
            JOIN users u ON i.owner_id = u.id
        """)
        return self.cursor.fetchall()

    def update_item(self, item_id, name, description, status, contact, image_path):
        self.cursor.execute("""
            UPDATE items 
            SET name=?, description=?, status=?, contact=?, image_path=? 
            WHERE id=?
        """, (name, description, status, contact, image_path, item_id))
        self.conn.commit()

    def delete_item(self, item_id):
        self.cursor.execute("DELETE FROM items WHERE id=?", (item_id,))
        self.conn.commit()