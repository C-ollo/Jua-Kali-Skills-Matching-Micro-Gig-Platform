# backend/schemas.py

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime
# --- Models for Request Bodies ---

class UserType(str, Enum):
    client = "client"
    artisan = "artisan"
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

class JobStatus(str, Enum):
    open = "open"
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class JobBase(BaseModel):
    title: str
    description: str
    location: str # Or a more complex Location model later
    budget: float
    required_skills: List[str] = [] # Skills needed for the job
    status: JobStatus = JobStatus.open # Default status when created

class JobCreate(JobBase):
    # All fields from JobBase are inherited.
    # Add any fields specific only to creation if needed, otherwise this can be empty.
    pass

class JobResponse(JobBase):
    id: int
    client_id: int # The ID of the user (client) who posted the job
    created_at: datetime # When the job was posted

    class Config:
        from_attributes = True # Changed from orm_mode=True for Pydantic V2    

class JobApplicationStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    withdrawn = "withdrawn" # Optional: if an artisan withdraws application

class JobApplicationBase(BaseModel):
    # job_id: int
    bid_amount: Optional[float] = None # Optional: Artisan can bid a price
    message: Optional[str] = None     # Optional: Message to the client

class JobApplicationCreate(JobApplicationBase):
    pass # All fields from JobApplicationBase are used for creation

class JobApplicationResponse(JobApplicationBase):
    id: int
    artisan_id: int # The ID of the artisan who applied
    status: JobApplicationStatus = JobApplicationStatus.pending
    created_at: datetime

    class Config:
        from_attributes = True # Pydantic V2      


class ArtisanApplicationDetails(BaseModel):
    id: int
    full_name: str
    email: str
    phone_number: str
    location: str
    bio: Optional[str] = None # Include bio for quick artisan summary
    years_experience: Optional[int] = None # Include experience

class JobApplicationDetailResponse(BaseModel):
    id: int
    job_id: int
    artisan_id: int
    bid_amount: Optional[float] = None
    message: Optional[str] = None
    status: JobApplicationStatus
    created_at: datetime
    # Add artisan details for the client to view
    artisan: ArtisanApplicationDetails # Nested Pydantic model

    class Config:
        from_attributes = True          