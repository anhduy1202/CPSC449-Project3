from pydantic import BaseModel
from typing import List

class Department(BaseModel):
    id: int
    name: str

class Instructor(BaseModel):
    id: int
    name: str

class Class(BaseModel):
    id: int
    name: str
    course_code: str
    section_number: int
    current_enroll: int
    max_enroll: int
    department_id: int
    instructor_id: int

class Student(BaseModel):
    id: int
    name: str
    dropped_classes: List[Class] = [] 

class Enrollment(BaseModel):
    placement: int
    class_id: int
    student_id: int

class Dropped(BaseModel):
    class_id: int
    student_id: int