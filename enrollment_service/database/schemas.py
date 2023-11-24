from pydantic import BaseModel
from typing import List

class Department(BaseModel):
    id: int
    name: str

class Instructor(BaseModel):
    id: int
    name: str

class Class(BaseModel):
    Name: str
    Department: str
    CourseCode: str
    SectionNumber: str
    maxEnroll: int
    InstructorId: str


class Student(BaseModel):
    id: str
    name: str
    dropped_classes: List[Class] = [] 

class Enrollment(BaseModel):
    placement: int
    class_id: int
    student_id: int

class Dropped(BaseModel):
    class_id: int
    student_id: int