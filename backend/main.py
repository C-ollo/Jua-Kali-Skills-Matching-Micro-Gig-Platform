from fastapi import FastAPI
from database import get_db_connection, close_db_pool 

# Create a FastAPI application instance
app = FastAPI()

# FastAPI lifecycle events for database connection management
@app.on_event("startup")
async def startup_event():
    print("Application startup: Initializing database...")
    # get_db_connection() will test if pool is working
    conn = None
    try:
        conn = get_db_connection()
        # Optionally run a simple query to confirm connection
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("Database connection verified on startup.")
    except Exception as e:
        print(f"Failed to verify database connection on startup: {e}")
        # Consider exiting if DB connection is critical for startup
    finally:
        if conn:
            close_db_pool()

@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutdown: Closing database connection pool...")
    close_db_pool()

@app.get("/")
async def read_root():
    return {"message": "Jua Kali Backend API is running! (FastAPI)"}