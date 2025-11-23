# app/schemas.py
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional, Dict
from datetime import datetime

# --- Auth Schemas ---
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=50)

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Assignment Schemas ---
class AssignmentCreate(BaseModel):
    title: str
    type: str = Field(..., pattern="^(lab|exam)$") # Validator: only lab or exam
    max_score: int = Field(..., gt=0)
    deadline: datetime
    penalty_points: int = 0
    content: Dict[str, str]

class AssignmentResponse(AssignmentCreate):
    id: int
    course_id: int
    class Config:
        from_attributes = True

# --- Student Schemas ---
# 1. Створюємо спільну базу (тільки безпечні поля)
class StudentBase(BaseModel):
    full_name: str
    email: EmailStr


# 2. Схема для СТВОРЕННЯ (тут додаємо пароль)
class StudentCreate(StudentBase):
    password: str


# 3. Схема для ЛОГІНУ (тут тільки пошта і пароль)
class StudentLogin(BaseModel):
    email: str
    password: str


# 4. Схема для ВІДПОВІДІ (наслідує Base, а не Create -> тому без пароля!)
class StudentResponse(StudentBase):
    id: int

    class Config:
        from_attributes = True

# --- Course Schemas ---
class CourseCreate(BaseModel):
    title: str
    max_lab_points: int
    max_exam_points: int

    @field_validator('max_exam_points')
    def check_total(cls, v, values):
        # Simple validation example
        if v > 100:
            raise ValueError('Exam points cannot exceed 100')
        return v

class CourseResponse(CourseCreate):
    id: int
    assignments: List[AssignmentResponse] = []
    students: List[StudentResponse] = []
    class Config:
        from_attributes = True

# --- Grade Schemas ---
class GradeCreate(BaseModel):
    student_id: int
    assignment_id: int
    score: float
    submitted_at: Optional[datetime] = None

class SubmissionCreate(BaseModel):
    assignment_id: int
    answer_text: str  # Наприклад, посилання на GitHub або текст відповіді

class GradeResponse(GradeCreate):
    id: int
    submitted_at: datetime


    class Config:
        from_attributes = True
