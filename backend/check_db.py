import sqlite3
import os

db_path = os.path.join("app", "db", "app.db")

if not os.path.exists(db_path):
    print("❌ База не найдена:", db_path)
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("📦 Таблицы в базе:")
for table in tables:
    print(" -", table[0])

conn.close()
