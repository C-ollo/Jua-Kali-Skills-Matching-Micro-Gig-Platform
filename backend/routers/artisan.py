# backend/routers/artisan.py

from fastapi import APIRouter, HTTPException, status, Depends, Query
from backend.database import get_db_connection, put_db_connection
from backend.routers.auth import get_current_user 
from backend.schemas import *# Import relevant schemas
from psycopg2.extras import execute_values 
from typing import List, Optional # Import Optional for fields that might be None

router = APIRouter(
    prefix="/api/artisans", # All routes in this router will start with /api/artisans
    tags=["Artisans"]        # For API documentation
)

@router.get("/", response_model=ArtisansListResponse) # <--- Change response_model here
async def get_all_artisans(
    location: Optional[str] = Query(None, description="Filter artisans by location"),
    skills: Optional[str] = Query(None, description="Comma-separated list of skills (e.g., 'Plumbing,Electrical')"),
    min_years_experience: Optional[int] = Query(None, ge=0, description="Minimum years of experience for the artisan"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    current_user: UserBase = Depends(get_current_user) # Keep authentication
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Base query parts for artisan profiles (joining users, artisan_details, and skills)
        # This complex query selects all details needed for UserProfile
        main_query_base = """
            SELECT
                u.id, u.full_name, u.email, u.phone_number, u.location, u.user_type, u.created_at,
                ad.bio, ad.years_experience,
                ARRAY_AGG(s.name ORDER BY s.name) FILTER (WHERE s.name IS NOT NULL) AS skill_names
            FROM users u
            LEFT JOIN artisan_details ad ON u.id = ad.user_id
            LEFT JOIN artisan_skills ars ON u.id = ars.artisan_id
            LEFT JOIN skills s ON ars.skill_id = s.id
        """

        count_query_base = "SELECT COUNT(DISTINCT u.id) FROM users u"

        # Filter conditions and parameters
        where_clauses = ["u.user_type = 'artisan'"] # Always filter for artisans
        query_params = []

        if location:
            where_clauses.append("u.location ILIKE %s")
            query_params.append(f"%{location}%")
        if min_years_experience is not None:
            # Filter by years_experience. Assumes artisan_details might not exist for all.
            where_clauses.append("ad.years_experience >= %s")
            query_params.append(min_years_experience)

        # Skills filtering logic (similar to jobs, requiring all specified skills)
        if skills:
            required_skill_names = [s.strip() for s in skills.split(',') if s.strip()]
            if required_skill_names:
                skill_filter_clause = f"""
                    u.id IN (
                        SELECT ars_sub.artisan_id
                        FROM artisan_skills ars_sub
                        JOIN skills s_sub ON ars_sub.skill_id = s_sub.id
                        WHERE s_sub.name IN ({', '.join(['%s'] * len(required_skill_names))})
                        GROUP BY ars_sub.artisan_id
                        HAVING COUNT(DISTINCT s_sub.id) = %s
                    )
                """
                where_clauses.append(skill_filter_clause)
                query_params.extend(required_skill_names)
                query_params.append(len(required_skill_names))

        # Construct the WHERE clause
        full_where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""


        # -------------------------------------------------------------
        # Pagination Logic
        # -------------------------------------------------------------
        offset = (page - 1) * size

        # 1. Get total count of artisans matching filters
        # For count query, we only need to join users and artisan_skills for skill filtering
        count_query_full = f"""
            {count_query_base}
            LEFT JOIN artisan_details ad ON u.id = ad.user_id
            LEFT JOIN artisan_skills ars ON u.id = ars.artisan_id
            LEFT JOIN skills s ON ars.skill_id = s.id
            {full_where_clause}
        """
        cursor.execute(count_query_full, query_params)
        total_count = cursor.fetchone()[0]

        # 2. Get the artisans for the current page
        final_query = f"""
            {main_query_base}
            {full_where_clause}
            GROUP BY u.id, u.full_name, u.email, u.phone_number, u.location, u.user_type, u.created_at, ad.bio, ad.years_experience
            ORDER BY u.created_at DESC
            LIMIT %s OFFSET %s;
        """
        # Append pagination params to the existing filters
        paged_query_params = query_params + [size, offset]

        cursor.execute(final_query, paged_query_params)
        artisan_rows = cursor.fetchall()

        artisans_list = []
        for row in artisan_rows:
            (user_id, full_name, email, phone_number, location, user_type_str, created_at,
             bio, years_experience, skill_names_array) = row

            # Handle ARRAY_AGG returning {NULL} for no skills or empty array
            parsed_skills = [s for s in (skill_names_array if skill_names_array else []) if s is not None]

            artisans_list.append(
                UserProfile(
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
                        # average_rating, total_reviews, is_available are not yet handled, will be None
                    ),
                    skills=parsed_skills
                )
            )

        return ArtisansListResponse(
            artisans=artisans_list,
            total_count=total_count,
            page=page,
            size=size
        )

    except HTTPException:
        raise # Re-raise HTTP exceptions
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

@router.get("/{artisan_id}/reviews", response_model=List[ReviewResponse])
async def get_reviews_for_artisan(
    artisan_id: int,
    current_user: UserBase = Depends(get_current_user) # Authentication is still required
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Optional: Check if artisan_id exists and is actually an artisan
        cursor.execute("SELECT user_type FROM users WHERE id = %s", (artisan_id,))
        user_type_row = cursor.fetchone()
        if not user_type_row or UserType(user_type_row[0]) != UserType.artisan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artisan not found.")

        cursor.execute(
            "SELECT id, job_id, client_id, artisan_id, rating, comment, created_at, updated_at FROM job_reviews WHERE artisan_id = %s ORDER BY created_at DESC",
            (artisan_id,)
        )
        review_rows = cursor.fetchall()

        reviews_list = []
        for row in review_rows:
            (id, job_id, client_id, reviewed_artisan_id, rating, comment, created_at, updated_at) = row
            reviews_list.append(
                ReviewResponse(
                    id=id, job_id=job_id, client_id=client_id, artisan_id=reviewed_artisan_id,
                    rating=rating, comment=comment, created_at=created_at, updated_at=updated_at
                )
            )
        return reviews_list

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching reviews for artisan {artisan_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error fetching reviews.")
    finally:
        if conn:
            put_db_connection(conn)            