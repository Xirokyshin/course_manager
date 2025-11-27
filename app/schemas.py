from pydantic import BaseModel, EmailStr, Field, model_validator
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
class StudentBase(BaseModel):
    full_name: str
    email: EmailStr


class StudentCreate(StudentBase):
    password: str


class StudentLogin(BaseModel):
    email: str
    password: str


class StudentResponse(StudentBase):
    id: int

    class Config:
        from_attributes = True

# --- Course Schemas ---
class CourseCreate(BaseModel):
    title: str
    max_lab_points: int
    max_exam_points: int

    @model_validator(mode='after')
    def check_total_score_is_100(self):
        total = self.max_lab_points + self.max_exam_points

        if total != 100:
            raise ValueError(
                f'Total course points must be exactly 100. Currently: {self.max_lab_points} (Labs) + {self.max_exam_points} (Exam) = {total}')

        return self

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
    answer_text: str  # not final type

class GradeResponse(GradeCreate):
    id: int
    submitted_at: datetime

    class Config:
        from_attributes = True
