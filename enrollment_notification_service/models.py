from enum import Enum
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Optional, List


class SubscriptionRequest(BaseModel):
    student_id: str
    course_code: str
    email: Optional[EmailStr] = Field(default=None)
    webhook_url: Optional[HttpUrl] = Field(default=None)


class SubscriptionResponse(BaseModel):
    status: str
    course_code: str


class UnSubscribeRequest(BaseModel):
    student_id: str
    course_code: str


class ListSubscriptionRequest(BaseModel):
    student_id: str


class QueryStatus(str, Enum):
    KEY_NOT_FOUND = "not found"
    UNSUBSCRIBE_SUCCESS = "unsubscription succesfull"
    SUBSCRIPTION_SUCCESS = "subscription successfull"
    SUBSCRIPTION_FAILED = "failed to subscribe"
    LIST_SUBSCRIPTION_FAILED = "failed to list subscribe"


class SubscriptionCourse(BaseModel):
    course_code: str
    email: Optional[str] = None
    webhook_url: Optional[str] = None


class ListSubscriptionResponse(BaseModel):
    subscribed_courses: List[SubscriptionCourse] = []
