from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
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
    title = Column(String, unique=True, index=True)
    description = Column(String)
    max_lab_points = Column(Integer, default=40)
    max_exam_points = Column(Integer, default=60)

    # --- МАГІЯ ТУТ (cascade) ---
    # Якщо видаляємо курс -> видаляються всі студенти і всі завдання цього курсу
    students = relationship("Student", back_populates="course", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")


class Student(Base):
    """Entity representing a Student."""
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    course_id = Column(Integer, ForeignKey("courses.id"))

    course = relationship("Course", back_populates="students")

    # Якщо видаляємо студента -> видаляються всі його оцінки
    grades = relationship("Grade", back_populates="student", cascade="all, delete-orphan")


class Assignment(Base):
    """Entity for Labs and Exams."""
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    type = Column(String)
    max_score = Column(Integer)
    deadline = Column(DateTime)
    penalty_points = Column(Integer, default=0)
    content = Column(JSON)
    course_id = Column(Integer, ForeignKey("courses.id"))

    course = relationship("Course", back_populates="assignments")

    # Якщо видаляємо завдання -> видаляються всі оцінки за нього
    grades = relationship("Grade", back_populates="assignment", cascade="all, delete-orphan")


class Grade(Base):
    """Entity for Grades."""
    __tablename__ = "grades"
    id = Column(Integer, primary_key=True, index=True)
    score = Column(Float, nullable=True)
    # Правильний час за замовчуванням
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    student_answer = Column(String, nullable=True)

    student_id = Column(Integer, ForeignKey("students.id"))
    assignment_id = Column(Integer, ForeignKey("assignments.id"))

    student = relationship("Student", back_populates="grades")
    assignment = relationship("Assignment", back_populates="grades")