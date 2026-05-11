from database.connection import create_connection


# ==========================================
# USUARIOS
# ==========================================

def get_user_by_username(username):

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    )

    user = cursor.fetchone()

    conn.close()

    return user