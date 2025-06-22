import os, psycopg2
from dotenv import load_dotenv
from psycopg2 import pool
load_dotenv()

# Create a connection pool
# It's generally better to use a threaded or simple connection pool
# depending on your async patterns. For basic FastAPI setup, a simple one is fine.
try:
    db_pool = pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10, # Adjust max connections as needed
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    )
    print("Database connection pool created successfully!")
except Exception as e:
    print(f"Error creating database connection pool: {e}")
    # In a real application, you might want to exit or log this more severely
    db_pool = None # Ensure db_pool is None if connection fails

# Function to get a connection from the pool
def get_db_connection():
    if db_pool is None:
        raise Exception("Database pool is not initialized.")
    conn = db_pool.getconn()
    return conn

# Function to return a connection to the pool
def put_db_connection(conn):
    if db_pool:
        db_pool.putconn(conn)

# Function to close the pool (call this on app shutdown)
def close_db_pool():
    if db_pool:
        db_pool.closeall()
        print("Database connection pool closed.")
