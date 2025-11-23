from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    """Entity for Authorization requirement."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    email = Column(String, unique=True, index=True)


class Course(Base):
    """Entity representing a Course."""
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, index=True)  # Handle duplicates requirement
    description = Column(String)
    max_lab_points = Column(Integer, default=40)  # Example: 4 labs * 10
    max_exam_points = Column(Integer, default=60)

    students = relationship("Student", back_populates="course")
    assignments = relationship("Assignment", back_populates="course")


class Student(Base):
    """Entity representing a Student."""
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String)
    course_id = Column(Integer, ForeignKey("courses.id"))

    course = relationship("Course", back_populates="students")
    grades = relationship("Grade", back_populates="student")


class Assignment(Base):
    """Entity for Labs and Exams."""
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    type = Column(String)  # 'lab' or 'exam'
    max_score = Column(Integer)
    deadline = Column(DateTime)
    penalty_points = Column(Integer, default=0)
    content = Column(JSON)  # Task description or variants
    course_id = Column(Integer, ForeignKey("courses.id"))

    course = relationship("Course", back_populates="assignments")
    grades = relationship("Grade", back_populates="assignment")


class Grade(Base):
    __tablename__ = "grades"
    id = Column(Integer, primary_key=True, index=True)
    score = Column(Float, nullable=True)  # <-- Дозволяємо NULL (оцінки ще немає)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    # Нове поле для тексту студента
    student_answer = Column(String, nullable=True)

    student_id = Column(Integer, ForeignKey("students.id"))
    assignment_id = Column(Integer, ForeignKey("assignments.id"))

    student = relationship("Student", back_populates="grades")
    assignment = relationship("Assignment", back_populates="grades")  # тут була помилка в назві relationship, але це не критично