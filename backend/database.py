import psycopg2
from psycopg2.pool import ThreadedConnectionPool, PoolError
import os
import sys
from fastapi import HTTPException # Make sure HTTPException is imported here!

# Global variable to hold the connection pool
db_pool = None

def init_db_pool(min_conn: int = 1, max_conn: int = 10):
    """
    Initializes the PostgreSQL connection pool.
    This function should be called once at application startup.
    """
    global db_pool
    if db_pool is None:
        try:
            db_pool = ThreadedConnectionPool(
                min_conn,
                max_conn,
                host=os.getenv("DB_HOST", "localhost"),
                database=os.getenv("DB_NAME", "your_database_name"),
                user=os.getenv("DB_USER", "your_username"),
                password=os.getenv("DB_PASSWORD", "your_password"),
                port=os.getenv("DB_PORT", "5432")
            )
            print(f"Database connection pool initialized with min={min_conn}, max={max_conn} connections.")
        except Exception as e:
            print(f"ERROR: Could not initialize database connection pool: {e}", file=sys.stderr)
            # Depending on your application's requirements, you might want to exit here
            # sys.exit(1)

def close_db_pool():
    """
    Closes the PostgreSQL connection pool.
    This function should be called at application shutdown.
    """
    global db_pool
    if db_pool:
        try:
            db_pool.closeall()
            print("Database connection pool closed.")
        except Exception as e:
            print(f"ERROR: Could not close database connection pool: {e}", file=sys.stderr)
        finally:
            db_pool = None

def get_db_connection():
    """
    FastAPI dependency that provides a database connection from the pool.
    Ensures the connection is clean before yielding and cleans up afterwards.
    """
    if db_pool is None:
        raise HTTPException(status_code=500, detail="Database pool not initialized.")

    conn = None
    try:
        conn = db_pool.getconn()

        # Ensure the connection is in autocommit mode
        if conn.autocommit is False:
            conn.autocommit = True

        yield conn # <--- The generator yields here

    # --- CRITICAL FIX: Order of exception handling ---
    # Handle StopIteration first, as it's a normal signal for generator termination
    except StopIteration:
        pass # This is expected when the generator is closed via throw(StopIteration)
    # Handle PoolError next
    except PoolError as e:
        print(f"ERROR: Could not get connection from pool: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail="Database connection error: Pool acquisition failed.")
    # Handle any other general exceptions last
    except Exception as e:
        print(f"ERROR: Unhandled exception in get_db_connection before yield: {type(e).__name__}: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail="An unexpected database error occurred during connection handling.")
    finally:
        if conn:
            # Ensure any active transaction is rolled back before returning the connection.
            if conn.autocommit is False:
                try:
                    conn.rollback()
                except Exception as e:
                    print(f"WARNING: Error during rollback before returning connection: {e}", file=sys.stderr)
            
            # Ensure conn is not already closed or invalid before putting back
            if not conn.closed:
                db_pool.putconn(conn)
            else:
                print("WARNING: Tried to put a closed connection back to the pool.", file=sys.stderr)

# This helper function is generally not needed if you always use Depends(get_db_connection)
# in your FastAPI routes. It's included for completeness or specific manual scenarios.
def put_db_connection(conn):
    """
    Returns a database connection to the pool.
    This function is implicitly handled by FastAPI's dependency injection for `get_db_connection`.
    Only call this manually if you manually acquired a connection outside of the FastAPI dependency system.
    """
    if db_pool and conn:
        try:
            # Ensure the connection is in a clean state (autocommit=True) before returning
            if conn.autocommit is False:
                conn.rollback() # Always rollback before putting back if in transaction
            conn.autocommit = True # Ensure it's autocommit when returned
            db_pool.putconn(conn)
        except PoolError as e:
            print(f"ERROR: Could not put connection back to pool: {e}", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: Unhandled exception putting connection back: {e}", file=sys.stderr)