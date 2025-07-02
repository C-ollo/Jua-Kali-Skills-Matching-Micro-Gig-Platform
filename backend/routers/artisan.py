# backend/routers/artisan.py

from fastapi import APIRouter, HTTPException, status, Depends
from backend.database import get_db_connection, put_db_connection
from backend.routers.auth import get_current_user 
from backend.schemas import *# Import relevant schemas
from psycopg2.extras import execute_values 
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

@router.put("/me", response_model=UserProfile)
async def update_my_artisan_profile(
    artisan_details_update: ArtisanDetailsUpdate,
    current_user: UserBase = Depends(get_current_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Authorization Check: Only Artisans can update their artisan profile
        if current_user.user_type != UserType.artisan:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only artisans can update their artisan profile."
            )

        # 2. Update artisan_details (UPSERT logic)
        update_fields = []
        update_values = []

        if artisan_details_update.bio is not None:
            update_fields.append("bio = %s")
            update_values.append(artisan_details_update.bio)
        if artisan_details_update.years_experience is not None:
            update_fields.append("years_experience = %s")
            update_values.append(artisan_details_update.years_experience)

        if update_fields:
            # Build UPSERT query for artisan_details table
            # Check if artisan_details already exists for this user_id
            cursor.execute("SELECT user_id FROM artisan_details WHERE user_id = %s", (current_user.id,))
            existing_details = cursor.fetchone()

            if existing_details:
                # Update existing details
                update_values.append(current_user.id)
                query = f"UPDATE artisan_details SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s;"
                cursor.execute(query, update_values)
            else:
                # Insert new details if they don't exist
                # This means we need the user_id for insert, plus potentially bio and years_experience
                insert_fields = ["user_id"]
                insert_placeholders = ["%s"]
                insert_values = [current_user.id]

                if artisan_details_update.bio is not None:
                    insert_fields.append("bio")
                    insert_placeholders.append("%s")
                    insert_values.append(artisan_details_update.bio)
                if artisan_details_update.years_experience is not None:
                    insert_fields.append("years_experience")
                    insert_placeholders.append("%s")
                    insert_values.append(artisan_details_update.years_experience)

                if len(insert_fields) > 1: # If at least one detail is provided besides user_id
                    query = f"INSERT INTO artisan_details ({', '.join(insert_fields)}) VALUES ({', '.join(insert_placeholders)});"
                    cursor.execute(query, insert_values)


        # 3. Update artisan_skills (Delete existing, then re-insert new ones)
        if artisan_details_update.skills is not None:
            # First, delete all existing skills for this artisan
            cursor.execute("DELETE FROM artisan_skills WHERE artisan_id = %s", (current_user.id,))

            # Then, insert the new skills
            if artisan_details_update.skills:
                found_skill_ids = []
                invalid_skills = []

                for skill_name in artisan_details_update.skills:
                    cursor.execute("SELECT id FROM skills WHERE name = %s", (skill_name,))
                    skill_row = cursor.fetchone()
                    if skill_row:
                        found_skill_ids.append(skill_row[0])
                    else:
                        invalid_skills.append(skill_name)

                if invalid_skills:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"The following skills are not recognized: {', '.join(invalid_skills)}. Please choose from available skills."
                    )

                # Use execute_values for batch insertion
                artisan_skill_values = [(current_user.id, skill_id) for skill_id in found_skill_ids]
                execute_values(cursor,
                    "INSERT INTO artisan_skills (artisan_id, skill_id) VALUES %s",
                    artisan_skill_values
                )

        conn.commit()

        # 4. Fetch and return the complete updated ArtisanProfileResponse
        # Re-use logic from get_artisan_by_id or construct it fully
        cursor.execute(
            """
            SELECT
                u.id, u.full_name, u.email, u.phone_number, u.location, u.user_type, u.created_at,
                ad.bio, ad.years_experience,
                ARRAY_AGG(s.name ORDER BY s.name) AS skill_names
            FROM users u
            LEFT JOIN artisan_details ad ON u.id = ad.user_id
            LEFT JOIN artisan_skills ars ON u.id = ars.artisan_id
            LEFT JOIN skills s ON ars.skill_id = s.id
            WHERE u.id = %s
            GROUP BY u.id, u.full_name, u.email, u.phone_number, u.location, u.user_type, u.created_at, ad.bio, ad.years_experience;
            """,
            (current_user.id,)
        )
        artisan_row = cursor.fetchone()

        if artisan_row is None: # Should not happen if current_user is valid
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve updated artisan data.")

        (user_id, full_name, email, phone_number, location, user_type_str, created_at,
         bio, years_experience, skill_names_array) = artisan_row

        parsed_skills = [s for s in (skill_names_array if skill_names_array else []) if s is not None]

        return UserProfile(
            id=user_id,
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            location=location,
            user_type=UserType(user_type_str),
            created_at=created_at,
            artisan_details=ArtisanDetails(
                bio=bio,
                years_experience=years_experience,
                # average_rating, total_reviews, is_available are not handled in this update,
                # so they will be None or default as per schema
            ),
            skills=parsed_skills
        )

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"Error updating artisan profile {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update artisan profile due to server error.")
    finally:
        if conn:
            put_db_connection(conn)