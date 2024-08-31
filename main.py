from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import JSON, Column, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid



DATABASE_URL = "sqlite:///./kfak.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)

class Reader(Base):
    __tablename__ = "readers"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

class Author(Base):
    __tablename__ = "authors"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

class LoginRequest(BaseModel):
    email: str
    password: str

class Book(Base):
    __tablename__ = 'books'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    price = Column(Float)
    description = Column(String)
    picture_filename = Column(String, index=True)


class Demand(Base):
    __tablename__ = "demands"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    picture_url = Column(String, index=True)

class BuyRequest(Base):
    __tablename__ = "buy_requests"
    id = Column(Integer, primary_key=True, index=True)
    book_id_list = Column(JSON, index=True)
    reader_id = Column(String, index=True)

class BuyRequestCreate(BaseModel):
    book_id_list: list
    reader_id: str

class BookCreate(BaseModel):
    title: str
    author: str
    description: str
    price: float


class DemandCreate(BaseModel):
    title: str
    author: str
    description: str
    price: float
    picture_url: str

class ReaderSignup(BaseModel):
    name: str
    email: str
    password: str

class ReaderSignin(BaseModel):
    email: str
    password: str

class AuthorSignup(BaseModel):
    name: str
    email: str
    password: str

class AuthorSignin(BaseModel):
    email: str
    password: str

Base.metadata.create_all(bind=engine)

# Define the admin credentials
ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "12345678"

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/signup")
def signup(username: str = Form(...), email: str = Form(...), password: str = Form(...), role: str = Form(...), db: Session = Depends(SessionLocal)):
    db_user = get_user(db, username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(password)
    new_user = User(username=username, email=email, hashed_password=hashed_password, role=role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": f"User {new_user.username} with role {new_user.role} created successfully"}

@app.post("/login")
def login(request: LoginRequest):
    if request.email == ADMIN_EMAIL and request.password == ADMIN_PASSWORD:
        return {"message": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


# Reader Endpoints
@app.post("/reader-signup")
def reader_signup(reader: ReaderSignup, db: Session = Depends(get_db)):
    db_reader = db.query(Reader).filter(Reader.email == reader.email).first()
    if db_reader:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_reader = Reader(id=str(uuid.uuid4()), name=reader.name, email=reader.email, password=reader.password)
    db.add(new_reader)
    db.commit()
    return {"message": "Signup successful"}

@app.post("/reader-signin")
def reader_signin(reader: ReaderSignin, db: Session = Depends(get_db)):
    db_reader = db.query(Reader).filter(Reader.email == reader.email, Reader.password == reader.password).first()
    if not db_reader:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {"message": "Login successful", "name": db_reader.name, "id": db_reader.id}

# Author Endpoints
@app.post("/author-signup")
def author_signup(author: AuthorSignup, db: Session = Depends(get_db)):
    db_author = db.query(Author).filter(Author.email == author.email).first()
    if db_author:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_author = Author(id=str(uuid.uuid4()), name=author.name, email=author.email, password=author.password)
    db.add(new_author)
    db.commit()
    return {"message": "Signup successful"}

@app.post("/author-signin")
def author_signin(author: AuthorSignin, db: Session = Depends(get_db)):
    db_author = db.query(Author).filter(Author.email == author.email, Author.password == author.password).first()
    if not db_author:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {"message": "Login successful" , "name": db_author.name , "id" : db_author.id}

@app.get("/readers")
def get_readers(db: Session = Depends(get_db)):
    readers = db.query(Reader).all()
    return readers

@app.get("/authors")
def get_authors(db: Session = Depends(get_db)):
    authors = db.query(Author).all()
    return authors

@app.get("/api/books")
def get_books(db: Session = Depends(get_db)):
    return db.query(Book).all()

app.mount("/images", StaticFiles(directory="images"), name="images")




@app.post("/api/add-book")
async def add_book(
    title: str = Form(...),
    author: str = Form(...),
    price: float = Form(...),
    description: str = Form(...),
    picture: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    picture_location = f"images/{picture.filename}"
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(picture_location), exist_ok=True)
    
    with open(picture_location, "wb") as image_file:
        image_file.write(await picture.read())
    
    # Add the book to the database
    db_book = Book(
        title=title,
        author=author,
        price=price,
        description=description,
        picture_filename=picture.filename
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.get("/api/demands")
def get_demands(db: Session = Depends(get_db)):
    return db.query(Demand).all()

@app.post("/api/add-demand")
def add_demand(demand: DemandCreate, db: Session = Depends(get_db)):
    db_demand = Demand(
        title=demand.title,
        author=demand.author,
        description=demand.description,
        price=demand.price,
        picture_url=demand.picture_url
    )
    db.add(db_demand)
    db.commit()
    db.refresh(db_demand)
    return db_demand


@app.post("/api/approve-book-add")
def approve_book_add(id: int, db: Session = Depends(get_db)):
    demand = db.query(Demand).filter(Demand.id == id).first()
    if demand:
        book = Book(title=demand.book, author=demand.author, description="", price=0.0)
        db.add(book)
        db.delete(demand)
        db.commit()
        return {"status": "approved"}
    raise HTTPException(status_code=404, detail="Demand not found")

@app.post("/api/reject-book-add")
def reject_book_add(id: int, db: Session = Depends(get_db)):
    demand = db.query(Demand).filter(Demand.id == id).first()
    if demand:
        db.delete(demand)
        db.commit()
        return {"status": "rejected"}
    raise HTTPException(status_code=404, detail="Demand not found")

class DeleteBookRequest(BaseModel):
    id: int

@app.post("/api/delete-book")
def delete_book(request: DeleteBookRequest, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == request.id).first()
    if book:
        db.delete(book)
        db.commit()
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Book not found")


@app.post("/api/buy-book")
def buy_book(request: BuyRequestCreate, db: Session = Depends(get_db)):
    db_request = BuyRequest(book_id_list=request.book_id_list, reader_id=request.reader_id)
    db.add(db_request)
    db.commit()
    return {"status": "success"}

@app.get("/api/sells")
def get_sells(db: Session = Depends(get_db)):
    return db.query(BuyRequest).all()

@app.get("/api/get-reader/{id}")
def get_reader(id: str, db: Session = Depends(get_db)):
    reader = db.query(Reader).filter(Reader.id == id).first()
    if reader:
        return reader
    raise HTTPException(status_code=404, detail="Reader not found")


@app.get("/")
def read_root():
    return {"Hello": "World"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)