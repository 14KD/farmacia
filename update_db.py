import sqlite3
import database.connection as db


conn = db.create_connection()

cursor = conn.cursor()

try:

    cursor.execute(
        """
        ALTER TABLE invoices
        ADD COLUMN employee TEXT
        """
    )

    print("Columna employee agregada.")

except Exception as e:

    print("Error:", e)

conn.commit()

conn.close()