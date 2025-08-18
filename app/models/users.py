from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date

class User(BaseModel):
    uid: Optional[str] = None
    firstName: Optional[str] = Field(None, description="First name of the user")
    lastName: Optional[str] = Field(None, description="Last name of the user")
    email: EmailStr
    password: Optional[str] = Field(None, description="User password")
    dob: Optional[date] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, description="Gender")
    photoURL: Optional[str] = None
    isGoogleUser: bool = False

    def validate_required_fields(self):
        if not self.isGoogleUser:
            missing = [
                field for field in ["firstName", "lastName", "password", "dob", "gender"]
                if getattr(self, field) in (None, "")
            ]
            if missing:
                raise ValueError(f"Missing required fields for non-Google user: {', '.join(missing)}")
