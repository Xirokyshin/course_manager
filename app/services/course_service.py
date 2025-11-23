from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..models import Course, Assignment, Student, Grade
from ..schemas import CourseCreate, AssignmentCreate, StudentCreate, GradeCreate, SubmissionCreate
from .email_service import send_email_notification
from datetime import datetime, timezone

# Simple in-memory cache (Bonus point)
course_cache = {}


class CourseService:

    @staticmethod
    def create_course(db: Session, course: CourseCreate):
        # Logic: Handle duplicated courses
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
        # Bonus: Cache implementation demonstration
        if course_id in course_cache:
            print("--- Returning from CACHE ---")
            return course_cache[course_id]

        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        course_cache[course_id] = course
        return course

    @staticmethod
    def add_assignment(db: Session, course_id: int, assignment: AssignmentCreate):
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # Logic: Check formula violation
        current_points = sum(a.max_score for a in course.assignments if a.type == assignment.type)
        limit = course.max_lab_points if assignment.type == 'lab' else course.max_exam_points

        if current_points + assignment.max_score > limit:
            raise HTTPException(status_code=400,
                                detail=f"Adding this {assignment.type} exceeds the point limit defined in formula.")

        db_assign = Assignment(**assignment.model_dump(), course_id=course_id)
        db.add(db_assign)
        db.commit()
        db.refresh(db_assign)

        # Invalidate cache since data changed
        if course_id in course_cache:
            del course_cache[course_id]

        return db_assign

    @staticmethod
    def submit_assignment(db: Session, submission: SubmissionCreate):
        # Перевірка, чи існує завдання
        assignment = db.query(Assignment).filter(Assignment.id == submission.assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # Перевірка на дублікат (чи вже здавав)
        existing_submission = db.query(Grade).filter(
            Grade.student_id == submission.student_id,
            Grade.assignment_id == submission.assignment_id
        ).first()

        if existing_submission:
            # Якщо вже здавав - оновлюємо час і відповідь (перездача)
            existing_submission.submitted_at = datetime.now(timezone.utc)
            existing_submission.student_answer = submission.answer_text
            db.commit()
            db.refresh(existing_submission)
            return existing_submission

        # Створення нового запису (здача)
        db_submission = Grade(
            student_id=submission.student_id,
            assignment_id=submission.assignment_id,
            student_answer=submission.answer_text,
            score=None,  # Оцінки поки немає
            submitted_at=datetime.now(timezone.utc)  # Фіксуємо РЕАЛЬНИЙ час здачі
        )
        db.add(db_submission)
        db.commit()
        db.refresh(db_submission)
        return db_submission

    @staticmethod
    def grade_student(db: Session, grade_data: GradeCreate):
        assignment = db.query(Assignment).filter(Assignment.id == grade_data.assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # Шукаємо роботу студента
        submission = db.query(Grade).filter(
            Grade.student_id == grade_data.student_id,
            Grade.assignment_id == grade_data.assignment_id
        ).first()

        # Якщо студент нічого не здавав, але викладач хоче поставити оцінку (наприклад, "2")
        # Ми створюємо запис примусово
        if not submission:
            submission = Grade(
                student_id=grade_data.student_id,
                assignment_id=grade_data.assignment_id,
                submitted_at=datetime.now(timezone.utc),  # Час здачі = зараз
                score=0
            )
            db.add(submission)

        # --- ЛОГІКА ОЦІНЮВАННЯ ---
        # Ми використовуємо час, коли СТУДЕНТ здав роботу (submission.submitted_at)
        # А не час, коли викладач ставить оцінку!

        submission_time = submission.submitted_at
        if submission_time.tzinfo is None:
            submission_time = submission_time.replace(tzinfo=timezone.utc)

        final_score = grade_data.score

        # Перевірка на максимум балів
        if final_score > assignment.max_score:
            raise HTTPException(status_code=400, detail="Score exceeds max points")

        # Штрафи (порівнюємо час здачі студента з дедлайном)
        if submission_time > assignment.deadline.replace(tzinfo=timezone.utc):
            final_score -= assignment.penalty_points
            if final_score < 0: final_score = 0

        # Оновлюємо оцінку в базі
        submission.score = final_score
        db.commit()
        db.refresh(submission)

        # Відправка пошти (код той самий, скорочено для прикладу)
        student = db.query(Student).filter(Student.id == grade_data.student_id).first()
        send_email_notification(student.email, f"Graded: {assignment.title}", f"Score: {final_score}")

        return submission

    @staticmethod
    def check_missed_deadlines(db: Session):
        print("--- [SCHEDULER] Starting check... ---")

        # 1. Знаходимо завдання, де дедлайн вже минув
        now = datetime.now(timezone.utc)
        expired_assignments = db.query(Assignment).filter(Assignment.deadline < now).all()

        for assignment in expired_assignments:
            # 2. Знаходимо всіх студентів цього курсу
            students = db.query(Student).filter(Student.course_id == assignment.course_id).all()

            for student in students:
                # 3. Перевіряємо, чи є оцінка/здача
                submission = db.query(Grade).filter(
                    Grade.student_id == student.id,
                    Grade.assignment_id == assignment.id
                ).first()

                # Якщо запису немає — значить студент пропустив дедлайн
                if not submission:
                    print(
                        f"--- [SCHEDULER] Student {student.id} missed assignment {assignment.id}. Setting score to 0. ---")

                    zero_grade = Grade(
                        student_id=student.id,
                        assignment_id=assignment.id,
                        score=0,  # Ставимо 0
                        student_answer="MISSED DEADLINE",
                        submitted_at=now
                    )
                    db.add(zero_grade)

        db.commit()