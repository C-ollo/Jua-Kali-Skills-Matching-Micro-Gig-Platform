# backend/routers/review.py

from typing import List, Optional
from backend.routers.notification import create_notification
from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extras import RealDictCursor, execute_values

from backend.database import get_db_connection, put_db_connection
from backend.routers.auth import get_current_user
from backend.schemas import *

router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"]
)

@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    current_user: UserBase = Depends(get_current_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Authorization: Only clients can create reviews
        if current_user.user_type != UserType.client:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only clients can leave reviews."
            )

        # 2. Get job details and check validity
        # Added job_title to the select statement for the notification message
        cursor.execute(
            "SELECT client_id, assigned_artisan_id, status, title FROM jobs WHERE id = %s",
            (review_data.job_id,)
        )
        job_info_row = cursor.fetchone()

        if not job_info_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

        job_client_id, assigned_artisan_id, job_status_str, job_title = job_info_row

        # Check if the current client is the one who posted the job
        if job_client_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only review jobs you posted."
            )

        # Check if the job has been assigned
        if assigned_artisan_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This job has not been assigned to an artisan yet."
            )

        # Check if job status is 'completed'
        if JobStatus(job_status_str) != JobStatus.completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only completed jobs can be reviewed."
            )

        # Check if a review already exists for this job
        cursor.execute("SELECT id FROM job_reviews WHERE job_id = %s", (review_data.job_id,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This job has already been reviewed."
            )

        # 3. Insert the new review
        cursor.execute(
            """
            INSERT INTO job_reviews (job_id, client_id, artisan_id, rating, comment)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, job_id, client_id, artisan_id, rating, comment, created_at, updated_at;
            """,
            (review_data.job_id, current_user.id, assigned_artisan_id, review_data.rating, review_data.comment)
        )
        new_review_row = cursor.fetchone()
        if not new_review_row:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create review.")

        # 4. Update artisan's average_rating and total_reviews
        # Fetch all ratings for this artisan to recalculate
        cursor.execute(
            "SELECT rating FROM job_reviews WHERE artisan_id = %s",
            (assigned_artisan_id,)
        )
        all_ratings = [row[0] for row in cursor.fetchall()]

        new_total_reviews = len(all_ratings)
        new_average_rating = sum(all_ratings) / new_total_reviews if new_total_reviews > 0 else 0.0

        cursor.execute(
            """
            INSERT INTO artisan_details (user_id, average_rating, total_reviews)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                average_rating = EXCLUDED.average_rating,
                total_reviews = EXCLUDED.total_reviews,
                updated_at = CURRENT_TIMESTAMP;
            """,
            (assigned_artisan_id, round(new_average_rating, 2), new_total_reviews)
        )

        conn.commit() # Commit the review and artisan details update

        # --- NEW NOTIFICATION CODE FOR NEW REVIEW ---
        # Notify the artisan that they received a new review
        await create_notification(
            user_id=assigned_artisan_id,
            message=f"You received a new {review_data.rating}-star review for job '{job_title}'.",
            notification_type=NotificationType.new_review,
            entity_id=review_data.job_id, # Link to job
            conn=conn # Pass the existing connection for transactional consistency
        )
        # --- END NEW NOTIFICATION CODE ---

        # 5. Map the new review row to ReviewResponse
        (id, job_id, client_id, artisan_id, rating, comment, created_at, updated_at) = new_review_row
        return ReviewResponse(
            id=id, job_id=job_id, client_id=client_id, artisan_id=artisan_id,
            rating=rating, comment=comment, created_at=created_at, updated_at=updated_at
        )

    except HTTPException:
        if conn: conn.rollback()
        raise
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error creating review: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error creating review.")
    finally:
        if conn:
            put_db_connection(conn)