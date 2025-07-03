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
    average_rating: Optional[float] = None # Ensure this is present
    total_reviews: Optional[int] = None    # Ensure this is present
    is_available: Optional[bool] = True

    class Config:
        from_attributes = True

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
    assigned_artisan_id: Optional[int] = None

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

class ApplicationStatusUpdate(BaseModel):
    status: JobApplicationStatus # Only allow updating the status


class ClientForApplicationResponse(BaseModel):
    id: int
    full_name: str
    location: str
    email: str # Include email for communication

class JobForApplicationResponse(BaseModel):
    id: int
    title: str
    description: str
    location: str
    budget: float
    status: JobStatus # The job's current status
    created_at: datetime
    client: ClientForApplicationResponse # Nested Client details

    class Config:
        from_attributes = True

class ArtisanApplicationListResponse(BaseModel):
    id: int # Application ID
    job_id: int
    bid_amount: Optional[float] = None
    message: Optional[str] = None
    status: JobApplicationStatus # Application status (pending, accepted, rejected)
    created_at: datetime
    job: JobForApplicationResponse # Nested Job details

    class Config:
        from_attributes = True

        
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None # Ensure EmailStr is imported from pydantic
    phone_number: Optional[str] = None
    location: Optional[str] = None
    # Password not updated here, usually a separate endpoint

class ArtisanDetailsUpdate(BaseModel):
    bio: Optional[str] = None
    years_experience: Optional[int] = None
    skills: Optional[List[str]] = None # List of skill names to update 

class JobsListResponse(BaseModel):
    jobs: List[JobResponse]
    total_count: int
    page: int
    size: int

    class Config:
        from_attributes = True

class ArtisansListResponse(BaseModel):
    artisans: List[UserProfile] # List of full artisan profiles
    total_count: int
    page: int
    size: int

    class Config:
        from_attributes = True

class ReviewCreate(BaseModel):
    job_id: int = Field(..., description="The ID of the job being reviewed")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = Field(None, max_length=500, description="Optional text comment for the review")

class ReviewResponse(BaseModel):
    id: int
    job_id: int
    client_id: int
    artisan_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime # Ensure this is present

    class Config:
        from_attributes = True  

class NotificationType(str, Enum):
    job_status_update = "job_status_update"
    new_application = "new_application"
    application_accepted = "application_accepted"
    application_rejected = "application_rejected"
    new_review = "new_review"
    # Add more as needed, e.g., new_job_match, message, etc.

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    message: str
    notification_type: NotificationType
    entity_id: Optional[int] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationUpdate(BaseModel):
    is_read: bool           