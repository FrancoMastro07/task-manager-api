from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Task(BaseModel):
    id: int 
    name: str 
    done: bool 

class UpdateTask(BaseModel):
    id: int | None = None
    name: str | None = None
    done: bool | None = None 

tasks = []

@app.get("/")
def root():
    return {"app":"Task Manager API",
            "Version":"1.0"}
 
@app.post("/tasks", response_model=Task)
def add_task(task:Task):          #add task
    tasks.append(task)
    return task

@app.get("/tasks/{id}", response_model=Task)
def get_task(id:int) -> Task:            #get task
    if(id>=0 and id<len(tasks)):
        return tasks[id]
    else:
        raise HTTPException(status_code=404, detail="Task not found")

@app.get("/tasks", response_model=list[Task])
def get_tasks():          #get all tasks
    return tasks
    
@app.put("/tasks/{id}", response_model=Task)
def put_task(id:int, task:Task):      #change task completely
    if(id>=0 and id<len(tasks)):
        tasks[id] = task
        return task
    else:
        raise HTTPException(status_code=404, detail="Task not found")
    
@app.patch("/tasks/{id}", response_model=Task)
def change_task(id:int, task:UpdateTask):        #change task partially
    if(id>=0 and id<len(tasks)):
        if(task.id is not None):
            tasks[id].id = task.id
        if(task.name is not None):
            tasks[id].name = task.name
        if(task.done is not None):
            tasks[id].done = task.done    
        return tasks[id]
    else:
        raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/tasks/{id}", response_model=Task)
def delete_task(id:int):          #delete task
    if(id>=0 and id<len(tasks)):
        task = tasks.pop(id)
        return task
    else:
        raise HTTPException(status_code=404, detail="Task not found")