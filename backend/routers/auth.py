from typing import Optional, List, Any
from fastapi import APIRouter, HTTPException, Depends, status
# Explicitly import all necessary schemas for clarity
from backend.schemas import (
    RegisterUser, LoginUser, UserBase, ArtisanDetails, UserProfile,
    ProfileUpdate, UserType, JobResponse, ArtisansListResponse,
    ReviewCreate, ReviewResponse, NotificationType, NotificationResponse,
    NotificationUpdate, SkillCreate, SkillResponse, JobApplicationStatus,
    JobApplicationResponse, JobApplicationDetailResponse, JobForApplicationResponse,
    ClientForApplicationResponse, ArtisanApplicationDetails, ApplicationStatusUpdate,
    ArtisanApplicationListResponse # Added any missing schemas from your file
)
from backend.database import get_db_connection, put_db_connection # Import DB utilities
import os
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext # For password hashing
from jose import JWTError, jwt # For JWT handling
from datetime import datetime, timedelta, timezone # For token expiration
from psycopg2.extras import RealDictCursor, execute_values # Make sure execute_values is here

# OAuth2 scheme for JWT token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Secret and Algorithm (from .env)
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"


router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"]
)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=dict) # Response model can be a dict for simplicity here
async def register_user(user_data: RegisterUser, db: Any = Depends(get_db_connection)):
    conn = db # Use the injected connection
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor) # Use RealDictCursor

        cursor.execute("SELECT id FROM users WHERE email = %s OR phone_number = %s", (user_data.email, user_data.phone_number))
        if cursor.fetchone():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email or phone number already exists")

        hashed_password = get_password_hash(user_data.password)
        current_utc_time = datetime.now(timezone.utc)

        cursor.execute(
            """
            INSERT INTO users (full_name, email, phone_number, password_hash, user_type, location, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, full_name, email, phone_number, user_type, location, created_at, updated_at
            """,
            (user_data.full_name, user_data.email, user_data.phone_number, hashed_password,
             user_data.user_type, user_data.location, current_utc_time, current_utc_time)
        )
        new_user_data = cursor.fetchone() # This will be a dict from RealDictCursor
        user_id = new_user_data['id']

        if user_data.user_type == UserType.artisan: # Corrected from 'artisan' string literal
            if not user_data.bio or not user_data.skills:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Artisan registration requires bio and skills.")

            cursor.execute(
                """
                INSERT INTO artisan_details (user_id, bio, years_experience, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, user_data.bio, user_data.years_experience or 0, current_utc_time, current_utc_time)
            )

            if user_data.skills:
                skill_ids = []
                for skill_name in user_data.skills:
                    # Use ON CONFLICT DO UPDATE to ensure idempotency if skill exists
                    cursor.execute(
                        "INSERT INTO skills (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id",
                        (skill_name,)
                    )
                    skill_row = cursor.fetchone()
                    skill_ids.append(skill_row['id'])

                if skill_ids:
                    artisan_skills_values = [(user_id, skill_id) for skill_id in skill_ids]
                    execute_values(cursor,
                        "INSERT INTO artisan_skills (artisan_id, skill_id) VALUES %s",
                        artisan_skills_values
                    )

        conn.commit()

        access_token_expires = timedelta(minutes=60)
        access_token = create_access_token(
            data={"user_id": user_id, "user_type": user_data.user_type, "email": user_data.email},
            expires_delta=access_token_expires
        )

        # Construct UserProfile for response (using the dict from new_user_data)
        response_user_profile = UserProfile(
            **new_user_data, # Unpack all fields directly
            artisan_details=None, # For initial registration, details are not fully fetched for response
            skills=[] # Skills are separate and will be populated on /me
        )

        return {
            "msg": "User registered successfully!",
            "token": access_token,
            "user": response_user_profile.model_dump() # Convert to dict
        }

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"Error during registration: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error during registration")
    finally:
        # FastAPI's Depends(get_db_connection) handles putting the connection back.
        pass

@router.options("/login")
async def options_login():
    return {}

@router.post("/login", response_model=dict) # Updated response model
async def login_for_access_token(form_data: LoginUser, db: Any = Depends(get_db_connection)):
    conn = db # Use the injected connection
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            "SELECT id, full_name, email, phone_number, password_hash, user_type, location, created_at, updated_at FROM users WHERE email = %s",
            (form_data.email,)
        )
        user_data = cursor.fetchone()

        if not user_data or not verify_password(form_data.password, user_data["password_hash"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Credentials")

        access_token_expires = timedelta(minutes=60)
        access_token = create_access_token(
            data={"user_id": user_data["id"], "user_type": user_data["user_type"], "email": user_data["email"]},
            expires_delta=access_token_expires
        )

        # Construct UserProfile for login response, including artisan details if applicable
        artisan_details_instance = None
        current_skills = []

        if user_data['user_type'] == UserType.artisan:
            cursor.execute("SELECT * FROM artisan_details WHERE user_id = %s", (user_data['id'],))
            artisan_details_data = cursor.fetchone()

            cursor.execute("""
                SELECT s.name
                FROM artisan_skills AS ASkills
                JOIN skills AS s ON ASkills.skill_id = s.id
                WHERE ASkills.artisan_id = %s
            """, (user_data['id'],))
            current_skills = [row['name'] for row in cursor.fetchall()]

            if artisan_details_data:
                artisan_details_instance = ArtisanDetails(
                    **artisan_details_data, # Unpack all fields directly
                    skills=current_skills
                )

        response_user_profile = UserProfile(
            **user_data, # Unpack all fields directly
            artisan_details=artisan_details_instance,
            skills=current_skills # Assign skills here
        )

        return {
            "msg": "Logged in successfully!",
            "token": access_token,
            "user": response_user_profile.model_dump()
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during login: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error during login")
    finally:
        # FastAPI's Depends(get_db_connection) handles putting the connection back.
        pass

# This function will be used as a dependency to protect routes
async def get_current_user(token: str = Depends(oauth2_scheme), db: Any = Depends(get_db_connection)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    conn = db # Use the injected connection
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Fetch basic user data including created_at and updated_at
        cursor.execute(
            "SELECT id, full_name, email, phone_number, user_type, location, created_at, updated_at FROM users WHERE id = %s",
            (user_id,)
        )
        user_data = cursor.fetchone()
        if user_data is None:
            raise credentials_exception

        artisan_details_instance = None
        current_skills = []

        if user_data['user_type'] == UserType.artisan:
            cursor.execute("SELECT * FROM artisan_details WHERE user_id = %s", (user_id,))
            artisan_details_data = cursor.fetchone()

            cursor.execute("""
                SELECT s.name
                FROM artisan_skills AS ASkills
                JOIN skills AS s ON ASkills.skill_id = s.id
                WHERE ASkills.artisan_id = %s
            """, (user_id,))
            current_skills = [row['name'] for row in cursor.fetchall()]

            if artisan_details_data:
                artisan_details_instance = ArtisanDetails(
                    **artisan_details_data, # Unpack all fields directly
                    skills=current_skills
                )

        return UserProfile(
            **user_data, # Unpack all fields directly
            artisan_details=artisan_details_instance,
            skills=current_skills
        )

    except JWTError:
        raise credentials_exception
    except Exception as e:
        print(f"Error in get_current_user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error during authentication")
    finally:
        # FastAPI's Depends(get_db_connection) handles putting the connection back.
        pass

@router.get("/me", response_model=UserProfile)
async def read_users_me(current_user: UserProfile = Depends(get_current_user)):
    # get_current_user now returns a fully populated UserProfile, so just return it
    return current_user

@router.put("/me", response_model=UserProfile)
async def update_my_profile(
    profile_update: ProfileUpdate,
    current_user: UserProfile = Depends(get_current_user),
    db: Any = Depends(get_db_connection)
):
    conn = db
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        conn.autocommit = False # Start a transaction

        user_updates = {}
        if profile_update.full_name is not None:
            user_updates['full_name'] = profile_update.full_name
        if profile_update.email is not None:
            user_updates['email'] = profile_update.email
        if profile_update.phone_number is not None:
            user_updates['phone_number'] = profile_update.phone_number
        if profile_update.location is not None:
            user_updates['location'] = profile_update.location

        if user_updates:
            user_updates['updated_at'] = datetime.now(timezone.utc)
            set_clauses = [f"{key} = %s" for key in user_updates.keys()]
            query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = %s RETURNING id, full_name, email, phone_number, user_type, location, created_at, updated_at"
            values = list(user_updates.values()) + [current_user.id]
            cursor.execute(query, values)
            updated_user_data = cursor.fetchone()
            if not updated_user_data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        else:
            # If no user updates, just get the current user data for the response
            updated_user_data = current_user.model_dump()


        if current_user.user_type == UserType.artisan and profile_update.artisan_details:
            artisan_details_updates = {}
            if profile_update.artisan_details.bio is not None:
                artisan_details_updates['bio'] = profile_update.artisan_details.bio
            if profile_update.artisan_details.years_experience is not None:
                artisan_details_updates['years_experience'] = profile_update.artisan_details.years_experience
            if profile_update.artisan_details.is_available is not None:
                artisan_details_updates['is_available'] = profile_update.artisan_details.is_available

            if artisan_details_updates:
                artisan_details_updates['updated_at'] = datetime.now(timezone.utc)
                set_clauses = [f"{key} = %s" for key in artisan_details_updates.keys()]
                query = f"UPDATE artisan_details SET {', '.join(set_clauses)} WHERE user_id = %s RETURNING *"
                values = list(artisan_details_updates.values()) + [current_user.id]
                cursor.execute(query, values)
                updated_artisan_data = cursor.fetchone()
                if not updated_artisan_data:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artisan details not found.")
            else:
                cursor.execute("SELECT * FROM artisan_details WHERE user_id = %s", (current_user.id,))
                updated_artisan_data = cursor.fetchone()


            if profile_update.artisan_details.skills is not None:
                cursor.execute("DELETE FROM artisan_skills WHERE artisan_id = %s", (current_user.id,))

                if profile_update.artisan_details.skills:
                    new_skill_names = profile_update.artisan_details.skills
                    skills_to_insert_ids = []
                    for skill_name in new_skill_names:
                        cursor.execute(
                            "INSERT INTO skills (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id",
                            (skill_name,)
                        )
                        skills_to_insert_ids.append(cursor.fetchone()['id'])

                    if skills_to_insert_ids:
                        insert_values = []
                        for skill_id in skills_to_insert_ids:
                            insert_values.append(cursor.mogrify("(%s, %s)", (current_user.id, skill_id)).decode('utf-8'))
                        
                        insert_query = "INSERT INTO artisan_skills (artisan_id, skill_id) VALUES " + ",".join(insert_values)
                        cursor.execute(insert_query)

        conn.commit()

        # Re-fetch the user and artisan details to get the most current state for the response
        cursor.execute("SELECT * FROM users WHERE id = %s", (current_user.id,))
        final_user_data_from_db = cursor.fetchone()

        final_artisan_details_instance = None
        final_skills_list = []

        if final_user_data_from_db and final_user_data_from_db['user_type'] == UserType.artisan:
            cursor.execute("SELECT * FROM artisan_details WHERE user_id = %s", (current_user.id,))
            final_artisan_details_from_db = cursor.fetchone()

            cursor.execute("""
                SELECT s.name
                FROM artisan_skills AS ASkills
                JOIN skills AS s ON ASkills.skill_id = s.id
                WHERE ASkills.artisan_id = %s
            """, (current_user.id,))
            final_skills_list = [row['name'] for row in cursor.fetchall()]

            if final_artisan_details_from_db:
                final_artisan_details_instance = ArtisanDetails(
                    **final_artisan_details_from_db,
                    skills=final_skills_list
                )
        
        return UserProfile(
            **final_user_data_from_db,
            artisan_details=final_artisan_details_instance,
            skills=final_skills_list
        )

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"Error updating user profile: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Server error updating profile: {e}")
    finally:
        # FastAPI's Depends(get_db_connection) handles putting the connection back.
        pass