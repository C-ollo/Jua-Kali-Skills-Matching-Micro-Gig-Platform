# backend/routers/admin.py

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from psycopg2.extras import RealDictCursor

from backend.database import get_db_connection, put_db_connection
from backend.routers.auth import get_current_user
from backend.schemas import *

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

# --- Dependency for Admin User ---
async def get_current_admin_user(current_user: UserBase = Depends(get_current_user)):
    if current_user.user_type != UserType.admin.value: # Check against the Enum value
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators are allowed to perform this action.")
    return current_user

# --- 1. Get All Users (Admin Only) ---
@router.get("/users", response_model=List[UserProfile])
async def get_all_users_admin(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_type: Optional[UserType] = Query(None, description="Filter by user type (client or artisan)"),
    current_admin_user: UserBase = Depends(get_current_admin_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                u.id, u.full_name, u.email, u.phone_number, u.user_type, u.location,
                ad.bio, ad.years_experience, ad.average_rating, ad.total_reviews, ad.is_available,
                (SELECT array_agg(s.name) FROM artisan_skills us JOIN skills s ON us.skill_id = s.id WHERE us.artisan_id = u.id) AS skills
            FROM users u
            LEFT JOIN artisan_details ad ON u.id = ad.user_id
        """
        count_query = "SELECT COUNT(u.id) FROM users u"
        where_clauses = []
        query_params = []

        if user_type:
            where_clauses.append("u.user_type = %s")
            query_params.append(user_type.value)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            count_query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY u.created_at DESC LIMIT %s OFFSET %s;"
        query_params.extend([limit, offset])

        cursor.execute(query, query_params)
        users_data = cursor.fetchall()

        # Execute count query separately
        cursor.execute(count_query, query_params[:-2]) # Remove limit/offset from count query params
        total_count = cursor.fetchone()['count']

        # Manually map to UserProfile due to nested structure (artisan_details and skills)
        user_profiles = []
        for user_row in users_data:
            artisan_details = None
            if user_row['user_type'] == UserType.artisan.value:
                artisan_details = ArtisanDetails(
                    bio=user_row.get('bio'),
                    years_experience=user_row.get('years_experience'),
                    average_rating=user_row.get('average_rating'),
                    total_reviews=user_row.get('total_reviews'),
                    is_available=user_row.get('is_available')
                )
            user_profiles.append(UserProfile(
                id=user_row['id'],
                full_name=user_row['full_name'],
                email=user_row['email'],
                phone_number=user_row['phone_number'],
                user_type=user_row['user_type'],
                location=user_row['location'],
                artisan_details=artisan_details,
                skills=user_row.get('skills') # `array_agg` returns a list, which Pydantic handles
            ))

        # You might want a JobsListResponse style wrapper here if you want total_count, page, size info
        # For now, returning just the list of users as requested by response_model=List[UserProfile]
        return user_profiles # Or wrap in a pagination schema if created

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching all users for admin: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error fetching users.")
    finally:
        if conn:
            put_db_connection(conn)

# --- 2. Get All Jobs (Admin Only) ---
@router.get("/jobs", response_model=JobsListResponse)
async def get_all_jobs_admin(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[JobStatus] = Query(None, alias="status", description="Filter by job status"),
    client_id: Optional[int] = Query(None, description="Filter by client ID"),
    assigned_artisan_id: Optional[int] = Query(None, description="Filter by assigned artisan ID"),
    current_admin_user: UserBase = Depends(get_current_admin_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query_base = """
            SELECT
                j.id, j.title, j.description, j.client_id, j.status, j.location, j.budget,
                j.created_at, j.updated_at, j.assigned_artisan_id,
                (SELECT array_agg(s.name) FROM job_required_skills jrs JOIN skills s ON jrs.skill_id = s.id WHERE jrs.job_id = j.id) AS required_skills
            FROM jobs j
        """
        count_query_base = "SELECT COUNT(j.id) FROM jobs j"

        where_clauses = []
        query_params = []

        if status_filter:
            where_clauses.append("j.status = %s")
            query_params.append(status_filter.value)
        if client_id:
            where_clauses.append("j.client_id = %s")
            query_params.append(client_id)
        if assigned_artisan_id:
            where_clauses.append("j.assigned_artisan_id = %s")
            query_params.append(assigned_artisan_id)

        full_query = query_base
        count_full_query = count_query_base
        if where_clauses:
            full_query += " WHERE " + " AND ".join(where_clauses)
            count_full_query += " WHERE " + " AND ".join(where_clauses)

        full_query += " ORDER BY j.created_at DESC LIMIT %s OFFSET %s;"
        query_params.extend([limit, offset])

        cursor.execute(full_query, query_params)
        jobs_data = cursor.fetchall()

        cursor.execute(count_full_query, query_params[:-2]) # Params excluding limit/offset
        total_count = cursor.fetchone()['count']

        # Map to JobResponse schema
        jobs = [JobResponse(**job) for job in jobs_data]

        return JobsListResponse(jobs=jobs, total_count=total_count, page=offset // limit + 1, size=limit)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching all jobs for admin: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error fetching jobs.")
    finally:
        if conn:
            put_db_connection(conn)

@router.post("/skills", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: SkillCreate,
    current_admin_user: UserBase = Depends(get_current_admin_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if skill already exists
        cursor.execute("SELECT id FROM skills WHERE name = %s", (skill_data.name,))
        if cursor.fetchone():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Skill with this name already exists.")

        cursor.execute(
            "INSERT INTO skills (name) VALUES (%s) RETURNING id, name;",
            (skill_data.name,)
        )
        new_skill = cursor.fetchone()
        conn.commit()

        return SkillResponse(**new_skill)

    except HTTPException:
        if conn: conn.rollback()
        raise
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error creating skill: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error creating skill.")
    finally:
        if conn:
            put_db_connection(conn)


@router.get("/skills", response_model=List[SkillResponse])
async def get_all_skills_admin(
    current_admin_user: UserBase = Depends(get_current_admin_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT id, name FROM skills ORDER BY name;")
        skills = cursor.fetchall()

        return [SkillResponse(**skill) for skill in skills]

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching all skills for admin: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error fetching skills.")
    finally:
        if conn:
            put_db_connection(conn)


@router.get("/skills/{skill_id}", response_model=SkillResponse)
async def get_skill_by_id_admin(
    skill_id: int,
    current_admin_user: UserBase = Depends(get_current_admin_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT id, name FROM skills WHERE id = %s;", (skill_id,))
        skill = cursor.fetchone()

        if not skill:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found.")

        return SkillResponse(**skill)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching skill {skill_id} for admin: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error fetching skill.")
    finally:
        if conn:
            put_db_connection(conn)


@router.put("/skills/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: int,
    skill_data: SkillCreate, # Reuse SkillCreate for update, as it only has 'name'
    current_admin_user: UserBase = Depends(get_current_admin_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if the skill to be updated exists
        cursor.execute("SELECT id FROM skills WHERE id = %s;", (skill_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found.")

        # Check for unique name conflict if changing name
        cursor.execute("SELECT id FROM skills WHERE name = %s AND id != %s;", (skill_data.name, skill_id))
        if cursor.fetchone():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Another skill with this name already exists.")

        cursor.execute(
            "UPDATE skills SET name = %s WHERE id = %s RETURNING id, name;",
            (skill_data.name, skill_id)
        )
        updated_skill = cursor.fetchone()
        conn.commit()

        return SkillResponse(**updated_skill)

    except HTTPException:
        if conn: conn.rollback()
        raise
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error updating skill {skill_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error updating skill.")
    finally:
        if conn:
            put_db_connection(conn)


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: int,
    current_admin_user: UserBase = Depends(get_current_admin_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor() # No need for RealDictCursor for DELETE

        # Check if skill exists before attempting to delete
        cursor.execute("SELECT id FROM skills WHERE id = %s;", (skill_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found.")

        cursor.execute("DELETE FROM skills WHERE id = %s;", (skill_id,))
        conn.commit()

        # No content to return for 204
        return

    except HTTPException:
        if conn: conn.rollback()
        raise
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error deleting skill {skill_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error deleting skill.")
    finally:
        if conn:
            put_db_connection(conn)