from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import CourseCreate, CourseResponse, AssignmentCreate
from ..models import User
from ..services.course_service import CourseService
from ..services.auth_service import get_current_user
from fastapi_cache.decorator import cache

router = APIRouter(prefix="/courses", tags=["Courses"])

@router.post("/", response_model=CourseResponse)
def create_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return CourseService.create_course(db, course)

@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Тільки викладач може видаляти
):
    return CourseService.delete_course(db, course_id)

@router.delete("/assignments/{assignment_id}")
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Тільки викладач
):
    return CourseService.delete_assignment(db, assignment_id)

@router.get("/{course_id}", response_model=CourseResponse)
@cache(expire=60)
async def read_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Просто повертаємо курс, без зайвих запитів
    return CourseService.get_course(db, course_id)

@router.post("/{course_id}/assignments/")
def add_assignment(
    course_id: int,
    assignment: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return CourseService.add_assignment(db, course_id, assignment)