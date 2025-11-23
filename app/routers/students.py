from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import GradeCreate, StudentCreate, StudentResponse, GradeResponse, SubmissionCreate
from ..models import User, Student
from ..services.course_service import CourseService
from ..services.auth_service import get_current_user

router = APIRouter(tags=["Students & Grades"])

@router.post("/students/", response_model=StudentResponse)
def create_student(
    student: StudentCreate,
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Додавання студента до курсу
    db_student = Student(**student.model_dump(), course_id=course_id)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

@router.post("/grades/", response_model=GradeResponse)
def grade_student(
    grade: GradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return CourseService.grade_student(db, grade)

@router.post("/submit/")
def submit_assignment(
    submission: SubmissionCreate,
    db: Session = Depends(get_db)
    # Тут ми не вимагаємо current_user, імітуючи, що це робить студент.
    # В реальності тут була б авторизація студента.
):
    return CourseService.submit_assignment(db, submission)