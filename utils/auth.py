import sqlite3
import bcrypt

# REGISTER USER

def register_user(username, password):

    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    hashed_password = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    )

    try:

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_password)
        )

        conn.commit()

        return True
    except:

        return False

    finally:

        conn.close()

# LOGIN USER

def login_user(username, password):

    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    )

    user = cursor.fetchone()

    conn.close()

    if user:

        stored_password = user[2]

        if bcrypt.checkpw(
            password.encode(),
            stored_password
        ):

            return user
    return None