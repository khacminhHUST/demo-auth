import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserListItem(BaseModel):
    id: uuid.UUID
    full_name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True
