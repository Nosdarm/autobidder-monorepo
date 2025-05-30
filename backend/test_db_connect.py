import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        database="autobidderdb",
        user="testuser",
        password="testpass123"
    )
    print("✅ Connection successful!")
    conn.close()
except Exception as e:
    print("❌ Connection failed:")
    print(repr(e))
    if isinstance(e, UnicodeDecodeError):
        print("Encoding:", e.encoding)
        print("Reason:", e.reason)
