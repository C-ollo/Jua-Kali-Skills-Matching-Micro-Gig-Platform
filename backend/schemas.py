# backend/schemas.py

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

# --- Models for Request Bodies ---

class RegisterUser(BaseModel):
    full_name: str = Field(..., min_length=1)
    email: EmailStr # Pydantic's EmailStr provides basic email validation
    phone_number: str = Field(..., min_length=10) # Basic validation for phone number
    password: str = Field(..., min_length=6) # Enforce min length for password
    user_type: str = Field(..., pattern="^(client|artisan)$") # Only 'client' or 'artisan'
    location: Optional[str] = None # Optional for client, but required for artisan by backend logic
    bio: Optional[str] = None
    years_experience: Optional[int] = Field(None, ge=0) # Non-negative integer
    skills: Optional[List[str]] = None # List of strings for skills

    # This method is for Pydantic v1. For v2, use model_validator(mode='after')
    # Here we'll make sure artisan-specific fields are provided if user_type is 'artisan'
    # For simplicity, you'll enforce this more robustly in the route logic itself
    # as Pydantic doesn't easily handle conditional "required" across fields directly in BaseModel without custom validators.

class LoginUser(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)

# --- Models for Response Bodies ---
# These define what your API will return

class UserBase(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone_number: str
    user_type: str
    location: Optional[str] = None

    class Config:
        from_attributes = True # Changed from orm_mode = True in Pydantic v2

class ArtisanDetails(BaseModel):
    bio: Optional[str] = None
    years_experience: Optional[int] = None
    average_rating: Optional[float] = None
    total_reviews: Optional[int] = None
    is_available: Optional[bool] = True

    class Config:
        from_attributes = True

class UserProfile(UserBase):
    # Inherits fields from UserBase
    artisan_details: Optional[ArtisanDetails] = None
    skills: Optional[List[str]] = None