from fastapi import APIRouter, Depends, HTTPException, FastAPI
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .lib_db import SessionLocal
from . import models

class BookCreate(BaseModel):
    bookname: str
    author: str

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def get_books(db: Session = Depends(get_db)):
    books = db.query(models.Books).all()
    return books


@app.post("/")
def add_books(book: BookCreate, db: Session = Depends(get_db)):
    new_book = models.Books(bookname=book.bookname, author=book.author)
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return {"message": "Book Added Successfully!", "data": new_book}


@app.put("/")
def update_books(id: int, book: BookCreate, db: Session = Depends(get_db)):
    existing_book = db.query(models.Books).filter(models.Books.id == id).first()
    if not existing_book:
        raise HTTPException(status_code=404, detail="Book not found")
    existing_book.bookname = book.bookname
    existing_book.author = book.author
    db.commit()
    db.refresh(existing_book)
    return {"message": "Book updated successfully", "data": existing_book}


@app.delete("/")
def delete_books(id: int, db: Session = Depends(get_db)):
    book = db.query(models.Books).filter(models.Books.id == id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
    return {"message": "Book deleted successfully"}