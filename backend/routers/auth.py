# backend/routers/auth.py
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from schemas import RegisterUser, LoginUser, UserProfile, UserBase # Import your Pydantic models
from database import get_db_connection, put_db_connection # Import DB utilities
import os
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext # For password hashing
from jose import JWTError, jwt # For JWT handling
from datetime import datetime, timedelta, timezone # For token expiration

# OAuth2 scheme for JWT token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Secret and Algorithm (from .env)
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256" # Same as Node.js (HMAC-SHA256)

router = APIRouter(
    prefix="/api/auth", # All routes in this router will start with /api/auth
    tags=["Auth"] # For API documentation
)

# Helper function to create JWT (will be used by both register and login)
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=60) # 1 hour default
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Helper function to verify password (used by login)
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Helper function to hash password (used by register)
def get_password_hash(password):
    return pwd_context.hash(password)

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: RegisterUser): # FastAPI automatically validates against RegisterUser schema
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check for existing user
        cursor.execute("SELECT id FROM users WHERE email = %s OR phone_number = %s", (user_data.email, user_data.phone_number))
        if cursor.fetchone():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email or phone number already exists")

        # Hash password
        hashed_password = get_password_hash(user_data.password)

        # Insert new user
        cursor.execute(
            """
            INSERT INTO users (full_name, email, phone_number, password_hash, user_type, location)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id, full_name, email, phone_number, user_type, location
            """,
            (user_data.full_name, user_data.email, user_data.phone_number, hashed_password, user_data.user_type, user_data.location)
        )
        new_user = cursor.fetchone()
        user_id = new_user[0] # The ID of the newly created user

        # Handle artisan details if user_type is artisan
        if user_data.user_type == 'artisan':
            if not user_data.bio or not user_data.skills:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Artisan registration requires bio and skills.")

            cursor.execute(
                """
                INSERT INTO artisan_details (user_id, bio, years_experience)
                VALUES (%s, %s, %s)
                """,
                (user_id, user_data.bio, user_data.years_experience or 0)
            )

            # Insert skills
            if user_data.skills:
                # Fetch skill IDs from database
                # NOTE: This assumes skills already exist in your 'skills' table
                # You might need to add logic to create skills if they don't exist
                skill_ids = []
                for skill_name in user_data.skills:
                    cursor.execute("SELECT id FROM skills WHERE name = %s", (skill_name,))
                    skill_row = cursor.fetchone()
                    if skill_row:
                        skill_ids.append(skill_row[0])
                    else:
                        # Handle unknown skills, e.g., log, or raise error
                        print(f"Warning: Skill '{skill_name}' not found in database.")

                if skill_ids:
                    # Prepare values for bulk insert into artisan_skills
                    artisan_skills_values = [(user_id, skill_id) for skill_id in skill_ids]
                    from psycopg2.extras import execute_values
                    execute_values(cursor,
                        "INSERT INTO artisan_skills (artisan_id, skill_id) VALUES %s",
                        artisan_skills_values
                    )

        conn.commit() # Commit changes to the database

        # Generate JWT
        access_token_expires = timedelta(minutes=60)
        access_token = create_access_token(
            data={"user_id": user_id, "user_type": user_data.user_type, "email": user_data.email},
            expires_delta=access_token_expires
        )

        # Return response
        return {
            "msg": "User registered successfully!",
            "token": access_token,
            "user": {
                "id": new_user[0],
                "full_name": new_user[1],
                "email": new_user[2],
                "phone_number": new_user[3],
                "user_type": new_user[4],
                "location": new_user[5]
            }
        }

    except HTTPException:
        raise # Re-raise HTTP exceptions caught from within this block
    except Exception as e:
        conn.rollback() # Rollback on error
        print(f"Error during registration: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error during registration")
    finally:
        if conn:
            put_db_connection(conn)

@router.post("/login")
async def login_for_access_token(form_data: LoginUser): # Using LoginUser schema
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch user by email
        cursor.execute(
            "SELECT id, full_name, email, phone_number, password_hash, user_type FROM users WHERE email = %s",
            (form_data.email,)
        )
        user_row = cursor.fetchone()

        if not user_row:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Credentials")

        user_dict = {
            "id": user_row[0],
            "full_name": user_row[1],
            "email": user_row[2],
            "phone_number": user_row[3],
            "password_hash": user_row[4],
            "user_type": user_row[5]
        }

        # Verify password
        if not verify_password(form_data.password, user_dict["password_hash"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Credentials")

        # Generate JWT
        access_token_expires = timedelta(minutes=60)
        access_token = create_access_token(
            data={"user_id": user_dict["id"], "user_type": user_dict["user_type"], "email": user_dict["email"]},
            expires_delta=access_token_expires
        )

        return {
            "msg": "Logged in successfully!",
            "token": access_token,
            "user": {
                "id": user_dict["id"],
                "full_name": user_dict["full_name"],
                "email": user_dict["email"],
                "phone_number": user_dict["phone_number"],
                "user_type": user_dict["user_type"]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during login: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error during login")
    finally:
        if conn:
            put_db_connection(conn)


# This function will be used as a dependency to protect routes
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    conn = None # Initialize conn to None
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception

        # You can also get user_type and email from payload if needed
        # user_type: str = payload.get("user_type")
        # email: str = payload.get("email")

        # Fetch user from database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch basic user data
        cursor.execute(
            "SELECT id, full_name, email, phone_number, user_type, location FROM users WHERE id = %s",
            (user_id,)
        )
        user_row = cursor.fetchone()
        if user_row is None:
            raise credentials_exception

        # Convert row to UserBase schema for consistency
        current_user_base = UserBase(
            id=user_row[0],
            full_name=user_row[1],
            email=user_row[2],
            phone_number=user_row[3],
            user_type=user_row[4],
            location=user_row[5]
        )

        # Return the UserBase object (or a more complete UserProfile later)
        return current_user_base

    except JWTError:
        raise credentials_exception
    except Exception as e:
        print(f"Error in get_current_user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error during authentication")
    finally:
        if conn:
            put_db_connection(conn)

          
