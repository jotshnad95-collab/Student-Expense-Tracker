import sqlite3

conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()

# USERS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

# EXPENSES TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    category TEXT,
    note TEXT,
    expense_date TEXT
)
""")

# BUDGET TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS budget (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    monthly_budget REAL,
    month INTEGER,
    year INTEGER
)
""")

conn.commit()
conn.close()               