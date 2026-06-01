from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Integer, String, Boolean, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_NAME = os.getenv("POSTGRES_DB")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

Base = declarative_base()

class TaskDB(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    done = Column(Boolean)

class CreateTask(BaseModel):
    name: str 
    done: bool = False

class Task(BaseModel):
    id: int
    name: str 
    done: bool  

    model_config = ConfigDict(from_attributes=True)

class UpdateTask(BaseModel):
    name: str | None = None
    done: bool | None = None


app = FastAPI()

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

@app.get("/")
def root():

    return {"app":"Task Manager API",
            "Version":"1.0"}
 
@app.post("/tasks", response_model=Task)
def add_task(t:CreateTask) -> Task:          #add task
    
    try:
        session = SessionLocal()
        task = TaskDB(name=t.name, done=t.done)
        session.add(task)
        session.commit()
        session.refresh(task)
        
        return task
    finally:
        session.close()

@app.get("/tasks/{id}", response_model=Task)
def get_task(id:int) -> Task:            #get task

    try:
        session = SessionLocal()
        task = session.get(TaskDB, id)

        if(task is None):
        
            raise HTTPException(status_code=404, detail="Task not found")
        else:
            return task
    finally:
        session.close()

@app.get("/tasks", response_model=list[Task])
def get_tasks() -> list[Task]:                                 #get all tasks

    try:
        session = SessionLocal()
        tasks = session.query(TaskDB).all()

        return tasks
    finally:
        session.close()

@app.put("/tasks/{id}", response_model=Task)
def put_task(id:int, t:CreateTask) -> Task:      #change task completely

    try:
        session = SessionLocal()
        task = session.get(TaskDB, id)
    
        if(task is None):
            
            raise HTTPException(status_code=404, detail="Task not found")
        
        task.name = t.name
        task.done = t.done
        session.commit()
        session.refresh(task)

        return task
    finally:
        session.close()
    
@app.patch("/tasks/{id}", response_model=Task)
def change_task(id:int, t:UpdateTask) -> Task:        #change task partially

    try:
        session = SessionLocal()
        task = session.get(TaskDB, id)
    
        if(task is None):
            
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
def delete_task(id:int) -> Task:          #delete task

    try:
        session = SessionLocal()
        task = session.get(TaskDB, id)

        if(task is None):
            
            raise HTTPException(status_code=404, detail="Task not found")
        delete_task = task
        session.delete(task)
        session.commit()
        
        return delete_task
    finally:
        session.close()