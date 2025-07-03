# backend/routers/notification.py

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from psycopg2.extras import RealDictCursor

from backend.database import get_db_connection, put_db_connection
from backend.routers.auth import get_current_user
from backend.schemas import (
    UserBase,
    NotificationResponse,
    NotificationUpdate,
    NotificationType # Import the Enum
)

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)

# Helper function to create a notification (will be called from other routers)
async def create_notification(
    user_id: int,
    message: str,
    notification_type: NotificationType,
    entity_id: Optional[int] = None,
    conn=None # Allow passing existing connection for transactional consistency
):
    _conn = conn if conn else get_db_connection()
    try:
        cursor = _conn.cursor()
        cursor.execute(
            """
            INSERT INTO notifications (user_id, message, notification_type, entity_id)
            VALUES (%s, %s, %s, %s);
            """,
            (user_id, message, notification_type.value, entity_id) # Use .value for Enum
        )
        # If a new connection was opened, commit it. If part of a larger transaction, don't commit here.
        if not conn:
            _conn.commit()
        print(f"Notification created for user {user_id}: {message}") # For debugging
    except Exception as e:
        print(f"Failed to create notification for user {user_id}: {e}")
        if not conn:
            _conn.rollback() # Rollback if this specific notification insert failed
        # Don't re-raise, as notification creation shouldn't block main operation
    finally:
        if not conn and _conn: # Only close if this function opened it
            put_db_connection(_conn)

@router.get("/me", response_model=List[NotificationResponse])
async def get_my_notifications(
    current_user: UserBase = Depends(get_current_user),
    read_status: Optional[bool] = Query(None, description="Filter by read status (true for read, false for unread)"),
    limit: int = Query(20, ge=1, le=100, description="Limit the number of notifications"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor) # Use RealDictCursor for easier mapping

        query_base = "SELECT id, user_id, message, notification_type, entity_id, is_read, created_at FROM notifications WHERE user_id = %s"
        query_params = [current_user.id]
        where_clauses = []

        if read_status is not None:
            where_clauses.append("is_read = %s")
            query_params.append(read_status)

        full_query = query_base
        if where_clauses:
            full_query += " AND " + " AND ".join(where_clauses)
        full_query += " ORDER BY created_at DESC LIMIT %s OFFSET %s;"
        query_params.extend([limit, offset])

        cursor.execute(full_query, query_params)
        notifications = cursor.fetchall()

        return [NotificationResponse(**n) for n in notifications]

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching notifications for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error fetching notifications.")
    finally:
        if conn:
            put_db_connection(conn)

@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: int,
    read_status: NotificationUpdate, # Use the NotificationUpdate schema
    current_user: UserBase = Depends(get_current_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 1. Check if notification exists and belongs to the current user
        cursor.execute("SELECT user_id FROM notifications WHERE id = %s", (notification_id,))
        notification_owner_row = cursor.fetchone()

        if not notification_owner_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

        if notification_owner_row['user_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to modify this notification."
            )

        # 2. Update the read status
        cursor.execute(
            "UPDATE notifications SET is_read = %s, created_at = created_at WHERE id = %s RETURNING *;", # created_at = created_at to trigger updated_at if implemented
            (read_status.is_read, notification_id)
        )
        updated_notification = cursor.fetchone()
        conn.commit()

        return NotificationResponse(**updated_notification)

    except HTTPException:
        if conn: conn.rollback()
        raise
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error updating notification {notification_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error updating notification.")
    finally:
        if conn:
            put_db_connection(conn)

@router.put("/me/read_all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_as_read(
    current_user: UserBase = Depends(get_current_user)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE notifications SET is_read = TRUE WHERE user_id = %s AND is_read = FALSE;",
            (current_user.id,)
        )
        conn.commit()
        return # 204 No Content
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error marking all notifications as read for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error.")
    finally:
        if conn:
            put_db_connection(conn)