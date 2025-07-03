# backend/routers/job.py

from fastapi import APIRouter, HTTPException, Depends, status, Query
from backend.database import get_db_connection, put_db_connection
from backend.schemas import *
from backend.routers.notification import create_notification
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

@router.get("/", response_model=JobsListResponse) # <--- Change response_model here
async def get_all_jobs(
    location: Optional[str] = Query(None, description="Filter jobs by location"),
    skills: Optional[str] = Query(None, description="Comma-separated list of required skills (e.g., 'Plumbing,Electrical')"),
    min_budget: Optional[float] = Query(None, ge=0, description="Minimum budget for the job"),
    max_budget: Optional[float] = Query(None, ge=0, description="Maximum budget for the job"),
    status_filter: Optional[JobStatus] = Query(None, description="Filter jobs by status (open, assigned, completed, cancelled)"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    current_user: UserBase = Depends(get_current_user) # Keep authentication
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Base query parts
        count_query_base = "SELECT COUNT(DISTINCT j.id) FROM jobs j"
        main_query_base = """
            SELECT
                j.id,
                j.client_id,
                j.title,
                j.description,
                j.location,
                j.budget,
                j.status,
                j.created_at,
                j.assigned_artisan_id,
                ARRAY_AGG(s.name ORDER BY s.name) FILTER (WHERE s.name IS NOT NULL) AS required_skills_array
            FROM jobs j
            LEFT JOIN job_required_skills jrs ON j.id = jrs.job_id
            LEFT JOIN skills s ON jrs.skill_id = s.id
        """
        where_clauses = []
        query_params = []

        # Add filters based on query parameters
        if location:
            where_clauses.append("j.location ILIKE %s") # ILIKE for case-insensitive search
            query_params.append(f"%{location}%")
        if min_budget is not None:
            where_clauses.append("j.budget >= %s")
            query_params.append(min_budget)
        if max_budget is not None:
            where_clauses.append("j.budget <= %s")
            query_params.append(max_budget)
        if status_filter:
            where_clauses.append("j.status = %s")
            query_params.append(status_filter.value) # Use .value for Enum

        # Skills filtering logic (requires a subquery or EXISTS for proper filtering)
        if skills:
            required_skill_names = [s.strip() for s in skills.split(',') if s.strip()]
            if required_skill_names:
                # This complex JOIN/WHERE clause ensures all specified skills are present for a job
                # It counts how many of the *required_skill_names* are associated with the job
                # and ensures that count matches the number of skills requested.
                skill_filter_clause = f"""
                    j.id IN (
                        SELECT jrs_sub.job_id
                        FROM job_required_skills jrs_sub
                        JOIN skills s_sub ON jrs_sub.skill_id = s_sub.id
                        WHERE s_sub.name IN ({', '.join(['%s'] * len(required_skill_names))})
                        GROUP BY jrs_sub.job_id
                        HAVING COUNT(DISTINCT s_sub.id) = %s
                    )
                """
                where_clauses.append(skill_filter_clause)
                query_params.extend(required_skill_names)
                query_params.append(len(required_skill_names)) # The count for HAVING clause


        # Construct the WHERE clause if filters exist
        full_where_clause = ""
        if where_clauses:
            full_where_clause = " WHERE " + " AND ".join(where_clauses)

        # -------------------------------------------------------------
        # Pagination Logic
        # -------------------------------------------------------------
        offset = (page - 1) * size

        # 1. Get total count of jobs matching filters
        cursor.execute(f"{count_query_base} {full_where_clause}", query_params)
        total_count = cursor.fetchone()[0]

        # 2. Get the jobs for the current page
        final_query = f"""
            {main_query_base}
            {full_where_clause}
            GROUP BY j.id, j.client_id, j.title, j.description, j.location, j.budget, j.status, j.created_at, j.assigned_artisan_id
            ORDER BY j.created_at DESC
            LIMIT %s OFFSET %s;
        """
        # Append limit and offset params
        paged_query_params = query_params + [size, offset]

        cursor.execute(final_query, paged_query_params)
        job_rows = cursor.fetchall()

        jobs_list = []
        for row in job_rows:
            (job_id, client_id, title, description, location, budget,
             status_str, created_at, assigned_artisan_id, required_skills_array) = row

            status_enum = JobStatus(status_str)
            # Handle ARRAY_AGG returning {NULL} for no skills or empty array
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
                    assigned_artisan_id=assigned_artisan_id,
                    required_skills=parsed_skills
                )
            )

        return JobsListResponse(
            jobs=jobs_list,
            total_count=total_count,
            page=page,
            size=size
        )

    except HTTPException:
        raise # Re-raise HTTP exceptions
    except Exception as e:
        print(f"Error fetching jobs: {e}")
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

@router.get("/{job_id}/applications", response_model=List[JobApplicationDetailResponse])
async def get_applications_for_job(
    job_id: int,
    current_user: UserBase = Depends(get_current_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Check if the job exists and if the current user is its owner (client)
        cursor.execute("SELECT client_id FROM jobs WHERE id = %s", (job_id,))
        job_row = cursor.fetchone()

        if job_row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        job_client_id = job_row[0]

        if current_user.user_type != UserType.client or current_user.id != job_client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view applications for this job."
            )

        # 2. Fetch all applications for this job, joining with users and artisan_details
        cursor.execute(
            """
            SELECT
                ja.id, ja.job_id, ja.artisan_id, ja.bid_amount, ja.message, ja.status, ja.created_at,
                u.full_name, u.email, u.phone_number, u.location,
                ad.bio, ad.years_experience
            FROM job_applications ja
            JOIN users u ON ja.artisan_id = u.id
            LEFT JOIN artisan_details ad ON u.id = ad.user_id
            WHERE ja.job_id = %s
            ORDER BY ja.created_at DESC;
            """,
            (job_id,)
        )
        application_rows = cursor.fetchall()

        applications_list = []
        for row in application_rows:
            (app_id, job_id_db, artisan_id_db, bid_amount, message, status_str, created_at,
             artisan_full_name, artisan_email, artisan_phone, artisan_location,
             artisan_bio, artisan_years_experience) = row

            # Convert status string to Enum
            app_status_enum = JobApplicationStatus(status_str)

            # Create nested ArtisanApplicationDetails object
            artisan_details_obj = ArtisanApplicationDetails(
                id=artisan_id_db,
                full_name=artisan_full_name,
                email=artisan_email,
                phone_number=artisan_phone,
                location=artisan_location,
                bio=artisan_bio,
                years_experience=artisan_years_experience
            )

            applications_list.append(
                JobApplicationDetailResponse(
                    id=app_id,
                    job_id=job_id_db,
                    artisan_id=artisan_id_db,
                    bid_amount=bid_amount,
                    message=message,
                    status=app_status_enum,
                    created_at=created_at,
                    artisan=artisan_details_obj
                )
            )

        return applications_list

    except HTTPException:
        raise # Re-raise HTTP exceptions
    except Exception as e:
        print(f"Error fetching applications for job {job_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error fetching applications")
    finally:
        if conn:
            put_db_connection(conn)            

@router.patch("/applications/{application_id}", response_model=JobApplicationDetailResponse)
async def update_application_status(
    application_id: int,
    status_update: ApplicationStatusUpdate,
    current_user: UserBase = Depends(get_current_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Fetch the application and associated job details
        cursor.execute(
            """
            SELECT
                ja.id, ja.job_id, ja.artisan_id, ja.bid_amount, ja.message, ja.status, ja.created_at,
                j.client_id AS job_client_id, j.status AS job_current_status, j.title AS job_title, -- Added job_title
                u.full_name, u.email, u.phone_number, u.location,
                ad.bio, ad.years_experience
            FROM job_applications ja
            JOIN jobs j ON ja.job_id = j.id
            JOIN users u ON ja.artisan_id = u.id
            LEFT JOIN artisan_details ad ON u.id = ad.user_id
            WHERE ja.id = %s;
            """,
            (application_id,)
        )
        application_row = cursor.fetchone()

        if application_row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

        (app_id, job_id, artisan_id, bid_amount, message, current_app_status_str, app_created_at,
         job_client_id, job_current_status_str, job_title, # Extracted job_title
         artisan_full_name, artisan_email, artisan_phone, artisan_location,
         artisan_bio, artisan_years_experience) = application_row

        # 2. Authorization Check: Ensure current user is the job's client
        if current_user.user_type != UserType.client or current_user.id != job_client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this application's status."
            )

        # 3. Prevent status changes if job is already assigned/closed
        if job_current_status_str == JobStatus.assigned.value or \
           job_current_status_str == JobStatus.completed.value or \
           job_current_status_str == JobStatus.cancelled.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot change application status for a job that is already '{job_current_status_str}'."
            )

        # 4. Update Application Status
        new_app_status = status_update.status

        if new_app_status == JobApplicationStatus.accepted:
            # Check if job is already assigned by another application
            cursor.execute(
                "SELECT assigned_artisan_id FROM jobs WHERE id = %s",
                (job_id,)
            )
            existing_assigned_artisan = cursor.fetchone()[0]
            if existing_assigned_artisan is not None and existing_assigned_artisan != artisan_id:
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Job is already assigned to another artisan."
                )

            # Set this application to 'accepted'
            cursor.execute(
                "UPDATE job_applications SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (new_app_status.value, app_id)
            )

            # Update job status and assign artisan
            cursor.execute(
                "UPDATE jobs SET status = %s, assigned_artisan_id = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (JobStatus.assigned.value, artisan_id, job_id)
            )

            # Reject all other pending applications for this job
            cursor.execute(
                "UPDATE job_applications SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE job_id = %s AND id != %s AND status = %s",
                (JobApplicationStatus.rejected.value, job_id, app_id, JobApplicationStatus.pending.value)
            )

            # --- NEW NOTIFICATION CODE FOR ACCEPTED APPLICATION ---
            await create_notification(
                user_id=artisan_id,
                message=f"Your application for job '{job_title}' has been accepted!",
                notification_type=NotificationType.application_accepted,
                entity_id=job_id,
                conn=conn # Pass the existing connection for transaction
            )
            # --- END NEW NOTIFICATION CODE ---

        else: # If new status is rejected, withdrawn, etc.
            cursor.execute(
                "UPDATE job_applications SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (new_app_status.value, app_id)
            )
            # --- NEW NOTIFICATION CODE FOR REJECTED/WITHDRAWN APPLICATION ---
            # Notify the artisan only if it's explicitly rejected by client or withdrawn by artisan
            if new_app_status == JobApplicationStatus.rejected:
                await create_notification(
                    user_id=artisan_id,
                    message=f"Your application for job '{job_title}' has been rejected.",
                    notification_type=NotificationType.application_rejected,
                    entity_id=job_id,
                    conn=conn # Pass the existing connection for transaction
                )
            # You could add another notification_type for 'withdrawn' if the artisan themselves calls this endpoint to withdraw
            # For now, assuming rejected is the primary one from client.
            # --- END NEW NOTIFICATION CODE ---

        conn.commit()

        # 5. Prepare and return the updated JobApplicationDetailResponse
        artisan_details_obj = ArtisanApplicationDetails(
            id=artisan_id,
            full_name=artisan_full_name,
            email=artisan_email,
            phone_number=artisan_phone,
            location=artisan_location,
            bio=artisan_bio,
            years_experience=artisan_years_experience
        )

        return JobApplicationDetailResponse(
            id=app_id,
            job_id=job_id,
            artisan_id=artisan_id,
            bid_amount=bid_amount,
            message=message,
            status=new_app_status, # Return the new status
            created_at=app_created_at,
            artisan=artisan_details_obj
        )

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"Error updating application {application_id} status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update application status due to server error")
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

        # 1. Fetch the existing job to check ownership, existence, and CURRENT STATUS
        cursor.execute("SELECT client_id, status, assigned_artisan_id FROM jobs WHERE id = %s", (job_id,))
        job_details_row = cursor.fetchone()

        if job_details_row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        existing_client_id, current_job_status_str, assigned_artisan_id = job_details_row
        current_job_status = JobStatus(current_job_status_str) # Convert to Enum

        # 2. Authorization Check: Ensure current user is the job owner
        if current_user.id != existing_client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this job")

        # --- NEW STATUS TRANSITION LOGIC ---
        requested_status = job_data.status

        if requested_status != current_job_status: # Only apply logic if status is actually changing
            if current_job_status == JobStatus.completed or current_job_status == JobStatus.cancelled:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot change status of an already {current_job_status.value} job."
                )

            if requested_status == JobStatus.completed:
                if current_job_status != JobStatus.assigned:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Only an 'assigned' job can be marked 'completed'."
                    )
                if assigned_artisan_id is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Job must have an assigned artisan to be marked 'completed'."
                    )
                # No other logic needed for completion, status update handles it

            elif requested_status == JobStatus.cancelled:
                # Can cancel from 'open' or 'assigned'
                if current_job_status == JobStatus.assigned and assigned_artisan_id is not None:
                    # If cancelling an assigned job, de-assign the artisan
                    assigned_artisan_id = None # Will be set to NULL in DB update

                # Optionally, reject all pending applications if cancelling an 'open' job
                if current_job_status == JobStatus.open:
                    cursor.execute(
                        "UPDATE job_applications SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE job_id = %s AND status = %s",
                        (JobApplicationStatus.rejected.value, job_id, JobApplicationStatus.pending.value)
                    )
            elif requested_status == JobStatus.assigned:
                # Prevent setting to assigned directly, should happen via application acceptance
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Job status 'assigned' is set by accepting an application, not direct update."
                )
            elif requested_status == JobStatus.open:
                # Prevent setting back to open from assigned/completed/cancelled
                if current_job_status != JobStatus.open:
                     raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot revert job status to 'open' from current state."
                    )
        # --- END NEW STATUS TRANSITION LOGIC ---


        # 3. Validate required skills (same logic as create_job)
        found_skill_ids = []
        invalid_skills = []
        # ... (existing skill validation code, no changes here) ...
        if job_data.required_skills:
            for skill_name in job_data.required_skills:
                cursor.execute("SELECT id FROM skills WHERE name = %s", (skill_name,))
                skill_row = cursor.fetchone()
                if skill_row:
                    found_skill_ids.append(skill_row[0])
                else:
                    invalid_skills.append(skill_name)

        if invalid_skills:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The following required skills are not recognized: {', '.join(invalid_skills)}. Please choose from available skills."
            )

        # 4. Update the main jobs table
        cursor.execute(
            """
            UPDATE jobs
            SET title = %s, description = %s, location = %s, budget = %s,
                status = %s, assigned_artisan_id = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s RETURNING id, client_id, created_at
            """,
            (job_data.title, job_data.description, job_data.location,
             job_data.budget, requested_status.value, assigned_artisan_id, job_id) # Use requested_status and potentially updated assigned_artisan_id
        )
        updated_job_id, client_id, created_at = cursor.fetchone()

        # 5. Update job_required_skills linking table (delete existing, then re-insert new)
        # ... (existing skill update code, no changes here) ...
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
            status=requested_status, # Return the new status
            assigned_artisan_id=assigned_artisan_id, # Return the potentially updated assigned_artisan_id
            created_at=created_at
        )

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"Error updating job {job_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update job due to server error")
    finally:
        if conn:
            put_db_connection(conn)

@router.get("/applications/me", response_model=List[ArtisanApplicationListResponse])
async def get_my_applications(
    current_user: UserBase = Depends(get_current_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Authorization Check: Only Artisans can view their applications
        if current_user.user_type != UserType.artisan:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only artisans can view their own applications."
            )

        # 2. Fetch all applications submitted by this artisan,
        #    joining with jobs and clients (users)
        cursor.execute(
            """
            SELECT
                ja.id, ja.job_id, ja.bid_amount, ja.message, ja.status, ja.created_at,
                j.title, j.description, j.location, j.budget, j.status AS job_status, j.created_at AS job_created_at,
                c.id AS client_id, c.full_name AS client_full_name, c.location AS client_location, c.email AS client_email
            FROM job_applications ja
            JOIN jobs j ON ja.job_id = j.id
            JOIN users c ON j.client_id = c.id -- Join to get client details
            WHERE ja.artisan_id = %s
            ORDER BY ja.created_at DESC;
            """,
            (current_user.id,)
        )
        application_rows = cursor.fetchall()

        my_applications_list = []
        for row in application_rows:
            (app_id, job_id, bid_amount, message, app_status_str, app_created_at,
             job_title, job_description, job_location, job_budget, job_status_str, job_created_at,
             client_id, client_full_name, client_location, client_email) = row

            # Convert enums
            app_status_enum = JobApplicationStatus(app_status_str)
            job_status_enum = JobStatus(job_status_str)

            # Create nested ClientForApplicationResponse
            client_obj = ClientForApplicationResponse(
                id=client_id,
                full_name=client_full_name,
                location=client_location,
                email=client_email
            )

            # Create nested JobForApplicationResponse
            job_obj = JobForApplicationResponse(
                id=job_id,
                title=job_title,
                description=job_description,
                location=job_location,
                budget=job_budget,
                status=job_status_enum,
                created_at=job_created_at,
                client=client_obj
            )

            my_applications_list.append(
                ArtisanApplicationListResponse(
                    id=app_id,
                    job_id=job_id,
                    bid_amount=bid_amount,
                    message=message,
                    status=app_status_enum,
                    created_at=app_created_at,
                    job=job_obj
                )
            )

        return my_applications_list

    except HTTPException:
        raise # Re-raise HTTP exceptions
    except Exception as e:
        print(f"Error fetching applications for artisan {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error fetching applications")
    finally:
        if conn:
            put_db_connection(conn)        

@router.get("/assigned/me", response_model=List[JobResponse])
async def get_my_assigned_jobs(
    current_user: UserBase = Depends(get_current_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Authorization Check: Only Artisans can view their assigned jobs
        if current_user.user_type != UserType.artisan:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only artisans can view their assigned jobs."
            )

        # 2. Fetch all jobs where the current artisan is assigned
        #    We use ARRAY_AGG to get all required skills, similar to get_all_jobs
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
                j.assigned_artisan_id,
                ARRAY_AGG(s.name ORDER BY s.name) AS required_skills_array
            FROM jobs j
            LEFT JOIN job_required_skills jrs ON j.id = jrs.job_id
            LEFT JOIN skills s ON jrs.skill_id = s.id
            WHERE j.assigned_artisan_id = %s
            GROUP BY j.id, j.client_id, j.title, j.description, j.location, j.budget, j.status, j.created_at, j.assigned_artisan_id
            ORDER BY j.created_at DESC;
            """,
            (current_user.id,)
        )
        job_rows = cursor.fetchall()

        assigned_jobs_list = []
        for row in job_rows:
            (job_id, client_id, title, description, location, budget,
             status_str, created_at, assigned_artisan_id, required_skills_array) = row

            # Convert enums
            status_enum = JobStatus(status_str)

            # Handle skills array that might be {NULL} if no skills or empty
            parsed_skills = [s for s in (required_skills_array if required_skills_array else []) if s is not None]


            assigned_jobs_list.append(
                JobResponse(
                    id=job_id,
                    client_id=client_id,
                    title=title,
                    description=description,
                    location=location,
                    budget=budget,
                    status=status_enum,
                    created_at=created_at,
                    assigned_artisan_id=assigned_artisan_id,
                    required_skills=parsed_skills
                )
            )
        return assigned_jobs_list

    except HTTPException:
        raise # Re-raise HTTP exceptions
    except Exception as e:
        print(f"Error fetching assigned jobs for artisan {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error fetching assigned jobs")
    finally:
        if conn:
            put_db_connection(conn)

@router.put("/{job_id}/complete", response_model=JobResponse)
async def complete_job(
    job_id: int,
    current_user: UserBase = Depends(get_current_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Fetch job details (including required_skills and title for notification)
        # Assuming required_skills is stored as a list of strings (e.g., TEXT[]) in your DB
        cursor.execute(
            "SELECT client_id, status, assigned_artisan_id, title, required_skills FROM jobs WHERE id = %s",
            (job_id,)
        )
        job_details = cursor.fetchone()

        if not job_details:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

        client_id, current_status_str, assigned_artisan_id, job_title, required_skills_db = job_details

        # 2. Authorization: Only the job's client can mark it complete
        if current_user.user_type != UserType.client or current_user.id != client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to mark this job as complete."
            )

        # 3. Validation: Job must be in 'assigned' status
        if JobStatus(current_status_str) != JobStatus.assigned:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job must be 'assigned' to be marked as complete. Current status: '{current_status_str}'."
            )

        # 4. Validation: Job must have an assigned artisan
        if assigned_artisan_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job must have an assigned artisan before it can be marked complete."
            )

        # 5. Update job status to 'completed'
        cursor.execute(
            "UPDATE jobs SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING *;",
            (JobStatus.completed.value, job_id)
        )
        updated_job_row = cursor.fetchone()
        conn.commit()

        if not updated_job_row:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update job status.")

        # 6. Create notification for the assigned artisan
        await create_notification(
            user_id=assigned_artisan_id,
            message=f"Your job '{job_title}' has been marked as complete by the client.",
            notification_type=NotificationType.job_status_update,
            entity_id=job_id,
            conn=conn # Pass the connection for transactional consistency
        )

        # 7. Return the updated job details
        # Ensure correct indexing based on your RETURNING * order
        # Assuming RETURNING * gives columns in the order they are defined in the table:
        # id, title, description, client_id, status, location, budget, created_at, updated_at, required_skills, assigned_artisan_id
        return JobResponse(
            id=updated_job_row[0],
            title=updated_job_row[1],
            description=updated_job_row[2],
            client_id=updated_job_row[3],
            status=JobStatus(updated_job_row[4]),
            location=updated_job_row[5],
            budget=updated_job_row[6],
            created_at=updated_job_row[7],
            updated_at=updated_job_row[8], # Corrected typo here
            required_skills=updated_job_row[9] if updated_job_row[9] else [], # Directly use the list of strings
            assigned_artisan_id=updated_job_row[10]
        )

    except HTTPException:
        if conn: conn.rollback()
        raise
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error completing job {job_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error completing job.")
    finally:
        if conn:
            put_db_connection(conn)
          
