# backend/routers/job.py

from fastapi import APIRouter, HTTPException, Depends, status
from backend.database import get_db_connection, put_db_connection
from backend.schemas import *
from backend.routers.auth import get_current_user # To get the authenticated user
from psycopg2.extras import execute_values
from typing import List

router = APIRouter(
    prefix="/api/jobs", # All routes in this router will start with /api/jobs
    tags=["Jobs"]       # For API documentation
)

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    current_user: UserBase = Depends(get_current_user)
):
    # Ensure only clients can post jobs
    if current_user.user_type != UserType.client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clients can post jobs."
        )

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Validate required skills
        found_skill_ids = []
        invalid_skills = []

        if job_data.required_skills:
            for skill_name in job_data.required_skills:
                cursor.execute("SELECT id FROM skills WHERE name = %s", (skill_name,))
                skill_row = cursor.fetchone()
                if skill_row:
                    found_skill_ids.append(skill_row[0])
                else:
                    invalid_skills.append(skill_name)

        if invalid_skills:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The following required skills are not recognized: {', '.join(invalid_skills)}. Please choose from available skills."
            )

        # 2. Insert into jobs table
        cursor.execute(
            """
            INSERT INTO jobs (client_id, title, description, location, budget, status)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id, created_at
            """,
            (current_user.id, job_data.title, job_data.description,
             job_data.location, job_data.budget, job_data.status.value)
        )
        job_id, created_at = cursor.fetchone()

        # 3. Insert into job_required_skills linking table
        if found_skill_ids:
            job_skill_values = [(job_id, skill_id) for skill_id in found_skill_ids]
            execute_values(cursor,
                "INSERT INTO job_required_skills (job_id, skill_id) VALUES %s",
                job_skill_values
            )

        conn.commit()

        # 4. Prepare JobResponse
        return JobResponse(
            id=job_id,
            client_id=current_user.id,
            title=job_data.title,
            description=job_data.description,
            location=job_data.location,
            budget=job_data.budget,
            required_skills=job_data.required_skills, # We use the original names for response
            status=job_data.status,
            created_at=created_at
        )

    except HTTPException:
        raise # Re-raise HTTP exceptions
    except Exception as e:
        conn.rollback()
        print(f"Error creating job: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create job due to server error")
    finally:
        if conn:
            put_db_connection(conn)

@router.get("/", response_model=List[JobResponse])
async def get_all_jobs():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # SQL to fetch all jobs with their associated skills
        # We use a similar ARRAY_AGG pattern as for artisans
        cursor.execute(
            """
            SELECT
                j.id,
                j.client_id,
                j.title,
                j.description,
                j.location,
                j.budget,
                j.status,
                j.created_at,
                ARRAY_AGG(s.name ORDER BY s.name) AS required_skills_array
            FROM jobs j
            LEFT JOIN job_required_skills jrs ON j.id = jrs.job_id
            LEFT JOIN skills s ON jrs.skill_id = s.id
            GROUP BY j.id, j.client_id, j.title, j.description, j.location, j.budget, j.status, j.created_at
            ORDER BY j.created_at DESC;
            """
        )
        job_rows = cursor.fetchall()

        jobs_list = []
        for row in job_rows:
            (job_id, client_id, title, description, location, budget,
             status_str, created_at, required_skills_array) = row

            # Ensure status is converted to the Enum
            status_enum = JobStatus(status_str)

            # Handle skills array that might be {NULL} if no skills or empty
            parsed_skills = [s for s in (required_skills_array if required_skills_array else []) if s is not None]

            jobs_list.append(
                JobResponse(
                    id=job_id,
                    client_id=client_id,
                    title=title,
                    description=description,
                    location=location,
                    budget=budget,
                    status=status_enum,
                    created_at=created_at,
                    required_skills=parsed_skills
                )
            )
        return jobs_list

    except Exception as e:
        print(f"Error fetching all jobs: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error fetching jobs")
    finally:
        if conn:
            put_db_connection(conn)  


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_by_id(job_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                j.id,
                j.client_id,
                j.title,
                j.description,
                j.location,
                j.budget,
                j.status,
                j.created_at,
                ARRAY_AGG(s.name ORDER BY s.name) AS required_skills_array
            FROM jobs j
            LEFT JOIN job_required_skills jrs ON j.id = jrs.job_id
            LEFT JOIN skills s ON jrs.skill_id = s.id
            WHERE j.id = %s
            GROUP BY j.id, j.client_id, j.title, j.description, j.location, j.budget, j.status, j.created_at;
            """,
            (job_id,)
        )
        job_row = cursor.fetchone()

        if job_row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        (job_id, client_id, title, description, location, budget,
         status_str, created_at, required_skills_array) = job_row

        status_enum = JobStatus(status_str)
        parsed_skills = [s for s in (required_skills_array if required_skills_array else []) if s is not None]

        return JobResponse(
            id=job_id,
            client_id=client_id,
            title=title,
            description=description,
            location=location,
            budget=budget,
            status=status_enum,
            created_at=created_at,
            required_skills=parsed_skills
        )

    except HTTPException:
        raise # Re-raise HTTP exceptions
    except Exception as e:
        print(f"Error fetching job by ID {job_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error fetching job")
    finally:
        if conn:
            put_db_connection(conn)                      

@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_data: JobCreate, # Expects a full update of the job
    current_user: UserBase = Depends(get_current_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Fetch the existing job to check ownership and existence
        cursor.execute("SELECT client_id FROM jobs WHERE id = %s", (job_id,))
        job_owner_row = cursor.fetchone()

        if job_owner_row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        existing_client_id = job_owner_row[0]

        # 2. Authorization Check: Ensure current user is the job owner
        if current_user.id != existing_client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this job")

        # 3. Validate required skills (same logic as create_job)
        found_skill_ids = []
        invalid_skills = []

        if job_data.required_skills:
            for skill_name in job_data.required_skills:
                cursor.execute("SELECT id FROM skills WHERE name = %s", (skill_name,))
                skill_row = cursor.fetchone()
                if skill_row:
                    found_skill_ids.append(skill_row[0])
                else:
                    invalid_skills.append(skill_name)

        if invalid_skills:
            # No rollback needed here yet, as no changes were made to the DB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The following required skills are not recognized: {', '.join(invalid_skills)}. Please choose from available skills."
            )

        # 4. Update the main jobs table
        cursor.execute(
            """
            UPDATE jobs
            SET title = %s, description = %s, location = %s, budget = %s, status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s RETURNING id, client_id, created_at
            """,
            (job_data.title, job_data.description, job_data.location,
             job_data.budget, job_data.status.value, job_id)
        )
        updated_job_id, client_id, created_at = cursor.fetchone() # Fetch updated values

        # 5. Update job_required_skills linking table
        #    (Delete existing skills and then re-insert new ones)
        cursor.execute("DELETE FROM job_required_skills WHERE job_id = %s", (job_id,))

        if found_skill_ids:
            job_skill_values = [(job_id, skill_id) for skill_id in found_skill_ids]
            execute_values(cursor,
                "INSERT INTO job_required_skills (job_id, skill_id) VALUES %s",
                job_skill_values
            )

        conn.commit()

        # 6. Prepare and return the updated JobResponse
        return JobResponse(
            id=updated_job_id,
            client_id=client_id,
            title=job_data.title,
            description=job_data.description,
            location=job_data.location,
            budget=job_data.budget,
            required_skills=job_data.required_skills,
            status=job_data.status,
            created_at=created_at # created_at doesn't change on update
        )

    except HTTPException:
        conn.rollback() # Ensure rollback on HTTPException
        raise
    except Exception as e:
        conn.rollback() # Rollback on any other unexpected error
        print(f"Error updating job {job_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update job due to server error")
    finally:
        if conn:
            put_db_connection(conn)            

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT) # No content on successful deletion
async def delete_job(
    job_id: int,
    current_user: UserBase = Depends(get_current_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Fetch the existing job to check ownership
        cursor.execute("SELECT client_id FROM jobs WHERE id = %s", (job_id,))
        job_owner_row = cursor.fetchone()

        if job_owner_row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        existing_client_id = job_owner_row[0]

        # 2. Authorization Check: Ensure current user is the job owner
        if current_user.id != existing_client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this job")

        # 3. Delete the job
        cursor.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
        conn.commit()

        # No content to return for 204
        return

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"Error deleting job {job_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete job due to server error")
    finally:
        if conn:
            put_db_connection(conn)

@router.post("/{job_id}/apply", response_model=JobApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_for_job(
    job_id: int,
    application_data: JobApplicationCreate,
    current_user: UserBase = Depends(get_current_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Authorization Check: Only Artisans can apply
        if current_user.user_type != UserType.artisan:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only artisans can apply for jobs."
            )

        # 2. Check if the job exists and is 'open'
        cursor.execute("SELECT status FROM jobs WHERE id = %s", (job_id,))
        job_row = cursor.fetchone()

        if job_row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

        job_status = job_row[0]
        if job_status != JobStatus.open.value: # Check against the value of the enum
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job is not open for applications. Current status: {job_status}"
            )

        # 3. Check if artisan has already applied to this job (UNIQUE constraint handles this, but explicit check provides better error message)
        cursor.execute(
            "SELECT id FROM job_applications WHERE job_id = %s AND artisan_id = %s",
            (job_id, current_user.id)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, # 409 Conflict indicates a duplicate resource
                detail="You have already applied for this job."
            )

        # 4. Insert the job application
        cursor.execute(
            """
            INSERT INTO job_applications (job_id, artisan_id, bid_amount, message, status)
            VALUES (%s, %s, %s, %s, %s) RETURNING id, created_at
            """,
            (job_id, current_user.id, application_data.bid_amount,
             application_data.message, JobApplicationStatus.pending.value)
        )
        application_id, created_at = cursor.fetchone()

        conn.commit()

        # 5. Prepare JobApplicationResponse
        return JobApplicationResponse(
            id=application_id,
            job_id=job_id,
            artisan_id=current_user.id,
            bid_amount=application_data.bid_amount,
            message=application_data.message,
            status=JobApplicationStatus.pending,
            created_at=created_at
        )

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"Error applying for job {job_id} by artisan {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to submit application due to server error")
    finally:
        if conn:
            put_db_connection(conn)
