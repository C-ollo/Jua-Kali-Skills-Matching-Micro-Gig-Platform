from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from ..schemas import RegisterUser, LoginUser, UserProfile, UserBase, ArtisanDetails # Import your Pydantic models
from ..database import get_db_connection, put_db_connection # Import DB utilities
from typing import List, Dict

router = APIRouter(
    prefix="/api/skills", # All routes in this router will start with /api/skills
    tags=["Skills"]       # For API documentation
)

@router.get("/", response_model=List[Dict[str, int | str]]) # Example response model for skills
async def get_all_skills(conn = Depends(get_db_connection)):
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT id, name FROM skills ORDER BY name")
        skills_data = cursor.fetchall()
        # Format the response as a list of dictionaries
        skills_list = [{"id": skill[0], "name": skill[1]} for skill in skills_data]
        return skills_list

    except Exception as e:
        print(f"Error fetching skills: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error fetching skills")
    finally:
        pass # FastAPI handles connection closing via Depends

