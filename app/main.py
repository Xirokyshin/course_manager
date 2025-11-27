from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from .database import engine, Base, SessionLocal
from .routers import auth, courses, students
from .services.course_service import CourseService
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

# Creating all tables in database (One time operation)
Base.metadata.create_all(bind=engine)

# --- Scheduled Task ---
def scheduled_deadline_checker():
    # New database session for the scheduled task
    db = SessionLocal()
    try:
        CourseService.check_missed_deadlines(db)
    except Exception as e:
        print(f"Error in scheduler: {e}")
    finally:
        db.close()

scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_deadline_checker, 'interval', seconds=60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize cache
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")

    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan, title="Student Course Manager")

# --- Global Exception Handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "Global Error Handler Caught this", "details": str(exc)},
    )

# --- Include Routers ---
app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(students.router)

@app.get("/")
def start_point():
    return {"message": "Welcome to Course Management API"}