import sqlite3
conn = sqlite3.connect('health_app.db')
cursor = conn.cursor()
cursor.execute('SELECT sql FROM sqlite_master WHERE type="table" AND name="doctor_availability";')
print(cursor.fetchone()[0])
conn.close()
