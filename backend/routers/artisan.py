# backend/routers/artisan.py

from fastapi import APIRouter, HTTPException, status, Depends
from backend.database import get_db_connection, put_db_connection
from backend.schemas import UserProfile, ArtisanDetails, UserBase # Import relevant schemas
from typing import List, Optional # Import Optional for fields that might be None

router = APIRouter(
    prefix="/api/artisans", # All routes in this router will start with /api/artisans
    tags=["Artisans"]        # For API documentation
)

@router.get("/", response_model=List[UserProfile]) # Will return a list of UserProfile objects
async def get_all_artisans():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query to fetch all artisans with their details and skills
        cursor.execute(
            """
            SELECT
                u.id, u.full_name, u.email, u.phone_number, u.location, u.user_type,
                ad.bio, ad.years_experience, ad.average_rating, ad.total_reviews, ad.is_available,
                ARRAY_AGG(s.name ORDER BY s.name) AS skills_array
            FROM users u
            LEFT JOIN artisan_details ad ON u.id = ad.user_id
            LEFT JOIN artisan_skills ass ON u.id = ass.artisan_id
            LEFT JOIN skills s ON ass.skill_id = s.id
            WHERE u.user_type = 'artisan'
            GROUP BY u.id, ad.bio, ad.years_experience, ad.average_rating, ad.total_reviews, ad.is_available
            ORDER BY u.full_name;
            """
        )
        artisan_rows = cursor.fetchall()

        artisans_list = []
        for row in artisan_rows:
            # Map SQL row to Pydantic models
            # Ensure correct indexing based on your SELECT statement
            user_id, full_name, email, phone_number, location, user_type, \
            bio, years_experience, average_rating, total_reviews, is_available, \
            skills_array = row

            # Create UserBase part
            user_base = UserBase(
                id=user_id,
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                user_type=user_type,
                location=location
            )

            # Create ArtisanDetails part
            artisan_details = None
            if bio is not None: # Check if artisan_details exist (LEFT JOIN might return NULLs)
                artisan_details = ArtisanDetails(
                    bio=bio,
                    years_experience=years_experience,
                    average_rating=average_rating,
                    total_reviews=total_reviews,
                    is_available=is_available
                )

            # Prepare skills list (handle case where skills_array might be None or contains None if no skills)
            # ARRAY_AGG with no matching rows typically returns {NULL} or an empty array, handle it.
            parsed_skills = [s for s in (skills_array if skills_array else []) if s is not None]


            # Create UserProfile
            user_profile = UserProfile(
                **user_base.model_dump(), # Pydantic V2 method to convert to dict
                artisan_details=artisan_details,
                skills=parsed_skills
            )
            artisans_list.append(user_profile)

        return artisans_list

    except Exception as e:
        print(f"Error fetching artisans: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error fetching artisans")
    finally:
        if conn:
            put_db_connection(conn)

@router.get("/{artisan_id}", response_model=UserProfile) # Path parameter: artisan_id
async def get_artisan_by_id(artisan_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # First, fetch basic user data and ensure they are an artisan
        cursor.execute(
            "SELECT id, full_name, email, phone_number, user_type, location FROM users WHERE id = %s",
            (artisan_id,)
        )
        user_row = cursor.fetchone()

        if user_row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Check if the user is actually an artisan
        if user_row[4] != 'artisan': # user_type is at index 4
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not an artisan")

        user_base = UserBase(
            id=user_row[0],
            full_name=user_row[1],
            email=user_row[2],
            phone_number=user_row[3],
            user_type=user_row[4],
            location=user_row[5]
        )

        artisan_details = None
        skills_list = []

        # Fetch artisan details
        cursor.execute(
            """
            SELECT bio, years_experience, average_rating, total_reviews, is_available
            FROM artisan_details WHERE user_id = %s
            """,
            (artisan_id,)
        )
        artisan_row = cursor.fetchone()
        if artisan_row:
            artisan_details = ArtisanDetails(
                bio=artisan_row[0],
                years_experience=artisan_row[1],
                average_rating=artisan_row[2],
                total_reviews=artisan_row[3],
                is_available=artisan_row[4]
            )

        # Fetch skills
        cursor.execute(
            """
            SELECT s.name FROM skills s
            JOIN artisan_skills ass ON s.id = ass.skill_id
            WHERE ass.artisan_id = %s
            ORDER BY s.name
            """,
            (artisan_id,)
        )
        skill_rows = cursor.fetchall()
        skills_list = [skill[0] for skill in skill_rows]

        # Construct the UserProfile response
        user_profile_data = user_base.model_dump() # Pydantic V2 method
        user_profile_data["artisan_details"] = artisan_details
        user_profile_data["skills"] = skills_list

        return UserProfile(**user_profile_data)

    except HTTPException:
        raise # Re-raise HTTP exceptions
    except Exception as e:
        print(f"Error fetching artisan profile by ID {artisan_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error fetching artisan profile")
    finally:
        if conn:
            put_db_connection(conn)            