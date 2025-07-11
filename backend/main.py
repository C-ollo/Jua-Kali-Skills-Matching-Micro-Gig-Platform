from fastapi import FastAPI, HTTPException
# Use relative imports if main.py is in the same package root as database.py
from .database import init_db_pool, get_db_connection, close_db_pool # Removed put_db_connection from here, it's not needed for manual calls as much
from dotenv import load_dotenv
load_dotenv()
from .routers import auth, skill, artisan, job, reviews, notification, admin

# For CORS
from fastapi.middleware.cors import CORSMiddleware

# For loading environment variables (e.g., from .env file)

import os # To access environment variables for DB pool configuration
import sys # For writing error messages to stderr

# Load environment variables from .env file (if it exists)


# Create a FastAPI application instance
app = FastAPI()

# Configure CORS - IMPORTANT for frontend communication
origins = [
    "http://localhost:5173", # Your frontend's URL
    "http://127.0.0.1:5173",
    # Add other origins if your frontend is deployed elsewhere, e.g., "https://your-frontend-domain.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allows all headers (including Authorization header for tokens)
)

# FastAPI lifecycle events for database connection management
@app.on_event("startup")
async def startup_event():
    print("Application startup: Initializing database...")
    try:
        # Get min/max connections from environment variables, with defaults
        min_connections = int(os.getenv("DB_MIN_CONNECTIONS", 1))
        max_connections = int(os.getenv("DB_MAX_CONNECTIONS", 10))

        # --- CRITICAL FIX: Initialize the database pool first ---
        init_db_pool(min_connections, max_connections)
        print("Database connection pool initialized.")

        # --- OPTIONAL: Verify connection by acquiring and releasing one ---
        # We need to explicitly manage the generator context to ensure its 'finally' block runs
        db_conn_generator = get_db_connection()
        conn_for_test = None # Initialize to None

        try:
            # Acquire the connection from the generator
            conn_for_test = db_conn_generator.__next__()
            # Perform a simple query to verify
            with conn_for_test.cursor() as cursor:
                cursor.execute("SELECT 1")
            print("Database connection verified on startup.")
        except StopIteration:
            # This means the generator finished without yielding anything, which shouldn't happen
            print("WARNING: get_db_connection did not yield a connection during startup verification.", file=sys.stderr)
        except Exception as e:
            # Catch specific database errors if desired, e.g., psycopg2.Error
            print(f"ERROR: Failed to verify database connection on startup: {e}", file=sys.stderr)
            # Raise an HTTPException if DB connection is truly critical for app startup
            # raise HTTPException(status_code=500, detail="Failed to connect to database at startup.")
        finally:
            # --- CRITICAL FIX: Explicitly close the generator to ensure its 'finally' block runs ---
            # This ensures the connection is returned to the pool by get_db_connection's own cleanup.
            # DO NOT call put_db_connection() manually here.
            if db_conn_generator:
                try:
                    db_conn_generator.throw(StopIteration) # Forces the generator to close, running its finally block
                except StopIteration:
                    pass # This is an expected exception when using throw(StopIteration) to close a generator
                except Exception as close_exc:
                    print(f"ERROR: Exception while explicitly closing database connection generator: {close_exc}", file=sys.stderr)

    except Exception as e:
        print(f"CRITICAL ERROR: Failed to initialize database pool: {e}", file=sys.stderr)
        # Re-raise to prevent the FastAPI application from starting if DB initialization fails
        raise

@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutdown: Closing database connection pool...")
    close_db_pool()

@app.get("/")
async def read_root():
    return {"message": "Jua Kali Backend API is running! (FastAPI)"}

# Include routers
app.include_router(auth.router)
app.include_router(skill.router)
app.include_router(artisan.router)
app.include_router(job.router)
app.include_router(reviews.router)
app.include_router(notification.router)
app.include_router(admin.router)