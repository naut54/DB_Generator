from core import Connection

try:
    conn = Connection()
    print("Connection successful")
    if conn.close():
        print("Connection closed successfully")
    else:
        print("Connection close failed")
except Exception as e:
    print("Error: ", e)
