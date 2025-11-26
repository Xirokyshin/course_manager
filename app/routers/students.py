from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import GradeCreate, StudentCreate, StudentResponse, GradeResponse, SubmissionCreate, StudentLogin, Token
from ..models import User, Student
from ..services.course_service import CourseService
from ..services.auth_service import get_current_user, get_password_hash, verify_password, create_access_token, get_current_student

router = APIRouter(tags=["Students & Grades"])


@router.post("/students/", response_model=StudentResponse)
def create_student(
        student: StudentCreate,
        course_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)  # Тільки викладач може створювати
):
    # Перевірка на дублікат email
    if db.query(Student).filter(Student.email == student.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pwd = get_password_hash(student.password)

    db_student = Student(
        full_name=student.full_name,
        email=student.email,
        hashed_password=hashed_pwd,
        course_id=course_id
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


@router.post("/students/login", response_model=Token)
def login_student(login_data: StudentLogin, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == login_data.email).first()
    if not student or not verify_password(login_data.password, student.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    # Створюємо токен, де sub = email студента
    access_token = create_access_token(data={"sub": student.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.delete("/students/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Захист: тільки викладач
):
    # Тут ми викликаємо сервіс (доведеться імпортувати CourseService в цей файл, якщо ще немає)
    return CourseService.delete_student(db, student_id)

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

@router.post("/submit/")
def submit_assignment(
    submission: SubmissionCreate,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student) # <--- ТЕПЕР ТУТ ЗАХИСТ
):
    # Ми передаємо ID студента, який ми дізналися з токена
    return CourseService.submit_assignment(db, submission, student_id=current_student.id)
@router.post("/grades/", response_model=GradeResponse)
def grade_student(
    grade: GradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return CourseService.grade_student(db, grade)

