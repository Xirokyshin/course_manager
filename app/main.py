from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from .database import engine, Base, SessionLocal
from .routers import auth, courses, students
from .services.course_service import CourseService

# Створення таблиць у БД при запуску
Base.metadata.create_all(bind=engine)

# --- Scheduled Task (Bonus Point) ---
def scheduled_deadline_checker():
    # Оскільки це фонова задача, ми мусимо створити сесію вручну
    db = SessionLocal()
    try:
        # Викликаємо нашу розумну логіку
        CourseService.check_missed_deadlines(db)
    except Exception as e:
        print(f"Error in scheduler: {e}")
    finally:
        db.close()

scheduler = BackgroundScheduler()
# Для тесту можна поставити 10 або 30 секунд, щоб швидше побачити результат
scheduler.add_job(scheduled_deadline_checker, 'interval', seconds=60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan, title="Student Course Manager")

# --- Global Exception Handler (Bonus Point) ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "Global Error Handler Caught this", "details": str(exc)},
    )

# Підключення роутерів (ось тут ми підтягуємо код з інших файлів)
app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(students.router)

@app.get("/")
def root():
    return {"message": "Welcome to Course Management API"}