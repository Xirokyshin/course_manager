from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..models import Course, Assignment, Student, Grade
from ..schemas import CourseCreate, AssignmentCreate, GradeCreate, SubmissionCreate
from .email_service import send_email_notification
from datetime import datetime, timezone


class CourseService:

    @staticmethod
    def create_course(db: Session, course: CourseCreate):
        existing = db.query(Course).filter(Course.title == course.title).first()
        if existing:
            raise HTTPException(status_code=400, detail="Course with this title already exists")

        db_course = Course(**course.model_dump())
        db.add(db_course)
        db.commit()
        db.refresh(db_course)
        return db_course

    @staticmethod
    def get_course(db: Session, course_id: int):
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return course

    @staticmethod
    def add_assignment(db: Session, course_id: int, assignment: AssignmentCreate):
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # Check formula violation
        current_points = sum(a.max_score for a in course.assignments if a.type == assignment.type)
        limit = course.max_lab_points if assignment.type == 'lab' else course.max_exam_points

        if current_points + assignment.max_score > limit:
            raise HTTPException(status_code=400,
                                detail=f"Adding this {assignment.type} exceeds the point limit defined in formula.")

        db_assign = Assignment(**assignment.model_dump(), course_id=course_id)
        db.add(db_assign)
        db.commit()
        db.refresh(db_assign)

        return db_assign

    # --- ВИПРАВЛЕНИЙ МЕТОД SUBMIT ---
    @staticmethod
    def submit_assignment(db: Session, submission: SubmissionCreate, student_id: int):
        # 1. Перевірка існування завдання
        assignment = db.query(Assignment).filter(Assignment.id == submission.assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # --- ДОДАЄМО ПЕРЕВІРКУ СТУДЕНТА (ЗАХИСТ) ---
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        # -------------------------------------------

        # 2. Перевірка на дублікат (оновлення)
        existing_submission = db.query(Grade).filter(
            Grade.student_id == student_id,
            Grade.assignment_id == submission.assignment_id
        ).first()

        if existing_submission:
            existing_submission.submitted_at = datetime.now(timezone.utc)
            existing_submission.student_answer = submission.answer_text
            db.commit()
            db.refresh(existing_submission)
            return existing_submission

        # 3. Створення нового запису
        db_submission = Grade(
            student_id=student_id,
            assignment_id=submission.assignment_id,
            student_answer=submission.answer_text,
            score=None,
            submitted_at=datetime.now(timezone.utc)
        )
        db.add(db_submission)
        db.commit()
        db.refresh(db_submission)
        return db_submission

    # --- ВИПРАВЛЕНИЙ МЕТОД GRADE ---
    @staticmethod
    def grade_student(db: Session, grade_data: GradeCreate):
        # 1. Перевірка завдання
        assignment = db.query(Assignment).filter(Assignment.id == grade_data.assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # --- ДОДАЛИ ЦЮ ПЕРЕВІРКУ ---
        # 2. Перевірка студента (щоб не було помилки 500)
        student = db.query(Student).filter(Student.id == grade_data.student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        # ---------------------------

        # 3. Шукаємо роботу студента (здачу)
        submission = db.query(Grade).filter(
            Grade.student_id == grade_data.student_id,
            Grade.assignment_id == grade_data.assignment_id
        ).first()

        # Якщо студент не здавав, створюємо пустий запис
        if not submission:
            submission = Grade(
                student_id=grade_data.student_id,
                assignment_id=grade_data.assignment_id,
                submitted_at=datetime.now(timezone.utc),
                score=0
            )
            db.add(submission)

        # 4. Перевірка на максимум балів
        if grade_data.score > assignment.max_score:
            raise HTTPException(
                status_code=400,
                detail=f"Score ({grade_data.score}) cannot exceed max points ({assignment.max_score})."
            )

        # 5. Логіка часу та штрафів
        submission_time = submission.submitted_at
        if submission_time.tzinfo is None:
            submission_time = submission_time.replace(tzinfo=timezone.utc)

        final_score = grade_data.score

        if submission_time > assignment.deadline.replace(tzinfo=timezone.utc):
            final_score -= assignment.penalty_points
            if final_score < 0: final_score = 0

        # 6. Збереження
        submission.score = final_score
        db.commit()
        db.refresh(submission)

        # 7. Відправка пошти
        # (Тут ми вже використовуємо змінну student, яку знайшли на початку)
        email_subject = f"Grade for: {assignment.title}"
        email_body = (
            f"Hello {student.full_name},\n\n"
            f"You have been graded for the assignment: '{assignment.title}'.\n"
            f"Your score: {final_score} points.\n"
            f"Max possible score was: {assignment.max_score}\n\n"
            f"Best regards,\nCourse Manager System"
        )
        send_email_notification(student.email, email_subject, email_body)

        return submission

    @staticmethod
    def delete_course(db: Session, course_id: int):
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        db.delete(course)
        db.commit()

        return {"msg": "Course deleted"}

    @staticmethod
    def delete_assignment(db: Session, assignment_id: int):
        # 1. Шукаємо завдання
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # 2. ОЧИЩЕННЯ: Видаляємо всі оцінки/здачі за це завдання
        # Якщо цього не зробити, база даних може заборонити видалення
        db.query(Grade).filter(Grade.assignment_id == assignment_id).delete()

        # 3. Видаляємо саме завдання
        db.delete(assignment)
        db.commit()

        return {"msg": "Assignment and associated grades deleted"}

    @staticmethod
    def delete_student(db: Session, student_id: int):
        # 1. Шукаємо студента
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        # 2. Видаляємо студента
        # Завдяки cascade="all, delete-orphan" в моделі Student,
        # всі його оцінки (grades) видаляться АВТОМАТИЧНО.
        db.delete(student)
        db.commit()

        return {"msg": "Student and associated grades deleted"}

    @staticmethod
    def check_missed_deadlines(db: Session):
        print("--- [SCHEDULER] Starting check... ---")

        now = datetime.now(timezone.utc)
        expired_assignments = db.query(Assignment).filter(Assignment.deadline < now).all()

        for assignment in expired_assignments:
            students = db.query(Student).filter(Student.course_id == assignment.course_id).all()

            for student in students:
                submission = db.query(Grade).filter(
                    Grade.student_id == student.id,
                    Grade.assignment_id == assignment.id
                ).first()

                if not submission:
                    print(
                        f"--- [SCHEDULER] Student {student.id} missed assignment {assignment.id}. Setting score to 0. ---")

                    zero_grade = Grade(
                        student_id=student.id,
                        assignment_id=assignment.id,
                        score=0,
                        student_answer="MISSED DEADLINE",
                        submitted_at=now
                    )
                    db.add(zero_grade)

        db.commit()