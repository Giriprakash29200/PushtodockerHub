from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from passlib.context import CryptContext
import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- Bcrypt Setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# --- Schema ---
class StudentCreate(BaseModel):
    register_number: str       # student enters their own register number
    name: str
    department: str
    password: str


# --- DB Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Routes ---

@app.get("/students")
def get_students(db: Session = Depends(get_db)):
    students = db.query(models.Student).all()
    return students


@app.post("/students")
def add_student(student: StudentCreate, db: Session = Depends(get_db)):
    # Check if register number already exists
    existing = db.query(models.Student).filter(models.Student.register_number == student.register_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Register number already exists")

    new_student = models.Student(
        register_number=student.register_number,
        name=student.name,
        department=student.department,
        password=hash_password(student.password)
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return {"message": "Student registered successfully", "register_number": new_student.register_number}


@app.put("/students/{register_number}")
def update_student(register_number: str, student: StudentCreate, db: Session = Depends(get_db)):
    existing_student = db.query(models.Student).filter(models.Student.register_number == register_number).first()
    if not existing_student:
        raise HTTPException(status_code=404, detail="Student not found")
    existing_student.name = student.name
    existing_student.department = student.department
    existing_student.password = hash_password(student.password)
    db.commit()
    db.refresh(existing_student)
    return {"message": "Student updated successfully", "register_number": existing_student.register_number}


@app.delete("/students/{register_number}")
def delete_student(register_number: str, db: Session = Depends(get_db)):
    existing_student = db.query(models.Student).filter(models.Student.register_number == register_number).first()
    if not existing_student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(existing_student)
    db.commit()
    return {"message": "Student deleted successfully"}