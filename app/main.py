from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.schemas import CreateTask, Task, UpdateTask, UserCreate, UserResponse
from typing import Annotated
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta, UTC
import os

DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_NAME = os.getenv("POSTGRES_DB")
TOKEN_KEY = os.getenv("TOKEN_KEY")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

Base = declarative_base()

class TaskDB(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    done = Column(Boolean)
    user_id = Column(Integer, ForeignKey("users.id"))

class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
pwd_context = CryptContext(schemes=["bcrypt"],
                            deprecated="auto")

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

def encode_token(payload: dict) -> str:
    token = jwt.encode(payload, TOKEN_KEY, algorithm="HS256")
    return token

def decode_token(token: Annotated[str, Depends(oauth2_scheme)]) -> UserDB:
    try:
        session = SessionLocal()
        data = jwt.decode(token, TOKEN_KEY, algorithms=["HS256"])
        user = session.query(UserDB).filter(UserDB.username == data["username"]).first()
        if(user is None):
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    finally:
        session.close()

def hash_password(psw: str) -> str:
    return pwd_context.hash(psw)

def verify_password(psw:str, hashed_psw:str) -> bool:
    return pwd_context.verify(psw, hashed_psw)
    

@app.get("/")
def root():

    return {"app":"Task Manager API",
            "Version":"1.0"}
 
@app.post("/tasks", response_model=Task)
def add_task(t:CreateTask, current_user: Annotated[UserDB, Depends(decode_token)]) -> Task:          #add task
    
    try:
        session = SessionLocal()
        task = TaskDB(name=t.name, done=t.done, user_id=current_user.id)
        session.add(task)
        session.commit()
        session.refresh(task)
        
        return task
    finally:
        session.close()

@app.get("/tasks/{id}", response_model=Task)
def get_task(id:int, current_user: Annotated[UserDB, Depends(decode_token)]) -> Task:            #get task

    try:
        session = SessionLocal()
        task = session.get(TaskDB, id)

        if(task is None or task.user_id!=current_user.id):
        
            raise HTTPException(status_code=404, detail="Task not found")
        else:
            return task
    finally:
        session.close()

@app.get("/tasks", response_model=list[Task])
def get_tasks(current_user: Annotated[UserDB, Depends(decode_token)]) -> list[Task]:                                 #get all tasks

    try:
        session = SessionLocal()
        tasks = session.query(TaskDB).filter(TaskDB.user_id==current_user.id).all()

        return tasks
    finally:
        session.close()

@app.put("/tasks/{id}", response_model=Task)
def put_task(id:int, t:CreateTask, current_user: Annotated[UserDB, Depends(decode_token)]) -> Task:      #change task completely

    try:
        session = SessionLocal()
        task = session.get(TaskDB, id)
    
        if(task is None or task.user_id!=current_user.id):
            
            raise HTTPException(status_code=404, detail="Task not found")
        
        task.name = t.name
        task.done = t.done
        session.commit()
        session.refresh(task)

        return task
    finally:
        session.close()
    
@app.patch("/tasks/{id}", response_model=Task)
def change_task(id:int, t:UpdateTask, current_user: Annotated[UserDB, Depends(decode_token)]) -> Task:        #change task partially

    try:
        session = SessionLocal()
        task = session.get(TaskDB, id)
    
        if(task is None or task.user_id!=current_user.id):
            
            raise HTTPException(status_code=404, detail="Task not found")

        if(t.name is not None):
                task.name = t.name
        if(t.done is not None):
                task.done = t.done  

        session.commit()
        session.refresh(task)
        
        return task
    finally:
        session.close()

@app.delete("/tasks/{id}", response_model=Task)
def delete_task(id:int, current_user: Annotated[UserDB, Depends(decode_token)]) -> Task:          #delete task

    try:
        session = SessionLocal()
        task = session.get(TaskDB, id)

        if(task is None or task.user_id!=current_user.id):
            
            raise HTTPException(status_code=404, detail="Task not found")
        delete_task = task
        session.delete(task)
        session.commit()
        
        return delete_task
    finally:
        session.close()


@app.post("/register", response_model=UserResponse)
def register(user: UserCreate):
    try:
        session = SessionLocal()

        user_repeated = session.query(UserDB).filter(UserDB.username==user.username).first()
        if(user_repeated is not None):
            raise HTTPException(status_code=400, detail="User already created")
        
        email_repeated = session.query(UserDB).filter(UserDB.email==user.email).first()
        if(email_repeated is not None):
            raise HTTPException(status_code=400, detail="Email already exists")
        
        new_user = UserDB(username=user.username, email=user.email, hashed_password=hash_password(user.password))
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        return new_user
    finally:

        session.close()

@app.post("/token")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    try:

        session = SessionLocal()
        user = session.query(UserDB).filter(UserDB.username == form_data.username).first()

        if(user is None or not verify_password(form_data.password, user.hashed_password)):
            raise HTTPException(status_code=401, detail="Incorrect username or password")

        payload = {"username":user.username, "email":user.email, "exp":datetime.now(UTC) + timedelta(hours=1)}

        token = encode_token(payload)
        return {"access_token":token, "token_type":"bearer"}
    finally:
        session.close()

@app.get("/users/profile", response_model=UserResponse)
def profile(user:Annotated[UserDB, Depends(decode_token)]):
    return user