from fastapi import FastAPI
from .database import get_db_connection, close_db_pool, put_db_connection
from .routers import auth, skill, artisan, job, reviews

# For CORS
from fastapi.middleware.cors import CORSMiddleware

# Create a FastAPI application instance
app = FastAPI()
# Configure CORS - IMPORTANT for frontend communication
# You might need to adjust origins in production
origins = [
    "http://localhost:5173", # Your frontend's URL
    "http://127.0.0.1:5173",
    # Add other origins if your frontend is deployed elsewhere
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allows all headers (including x-auth-token)
)


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
            put_db_connection(conn)

@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutdown: Closing database connection pool...")
    close_db_pool()

@app.get("/")
async def read_root():
    return {"message": "Jua Kali Backend API is running! (FastAPI)"}

app.include_router(auth.router)
app.include_router(skill.router)
app.include_router(artisan.router)
app.include_router(job.router)
app.include_router(reviews.router)

