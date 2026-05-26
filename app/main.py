from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI()


def connection():
    return sqlite3.connect("tasks.db")

def task_to_dict(task):
    return {"id":task[0],
                "name":task[1],
                "done":bool(task[2])}

conn = connection()
cursor = conn.cursor()
cursor.execute(''' CREATE TABLE IF NOT EXISTS tasks(
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT,
               done BOOLEAN
               )
''')
conn.commit()
conn.close()

class CreateTask(BaseModel):
    name: str 
    done: bool = False

class Task(BaseModel):
    id: int
    name: str 
    done: bool  

class UpdateTask(BaseModel):
    name: str | None = None
    done: bool | None = None


@app.get("/")
def root():

    return {"app":"Task Manager API",
            "Version":"1.0"}
 
@app.post("/tasks", response_model=Task)
def add_task(task:CreateTask) -> Task:          #add task

    conn = connection()
    cursor = conn.cursor()
    cursor.execute('''
            INSERT INTO tasks(name, done)
            VALUES(?, ?)''', (task.name, task.done))
    conn.commit()
    task_id = cursor.lastrowid
    
    conn.close()

    return  {
        "id": task_id,
        "name": task.name,
        "done": task.done
    }

@app.get("/tasks/{id}", response_model=Task)
def get_task(id:int) -> Task:            #get task

    conn = connection()
    cursor = conn.cursor()
    cursor.execute('''
           SELECT * FROM tasks WHERE id=?''', (id,))
    res = cursor.fetchone()
    conn.close()

    if(res is None):
    
        raise HTTPException(status_code=404, detail="Task not found")
    else:
        return task_to_dict(res)

@app.get("/tasks", response_model=list[Task])
def get_tasks() -> list[Task]:                                 #get all tasks

    conn = connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM tasks''')
    res = cursor.fetchall()
    conn.close()

    return [
        task_to_dict(task)
        for task in res
        ]

@app.put("/tasks/{id}", response_model=Task)
def put_task(id:int, task:CreateTask) -> Task:      #change task completely

    conn = connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM tasks WHERE id=?''', (id,))
    exists = cursor.fetchone()
    if(exists is None):
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    
    cursor.execute('''UPDATE tasks SET name=?, done=?
                   WHERE id=?''', (task.name, task.done, id))
    conn.commit()

    cursor.execute('''SELECT * FROM tasks WHERE id=?''', (id,))
    res = cursor.fetchone()
    conn.close()
    
    return task_to_dict(res)
    
@app.patch("/tasks/{id}", response_model=Task)
def change_task(id:int, task:UpdateTask) -> Task:        #change task partially

    conn = connection()
    cursor = conn.cursor()
    
    cursor.execute('''SELECT * FROM tasks WHERE id=?''', (id,))
    exists = cursor.fetchone()
    if(exists is None):
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    if(task.name is not None):
            cursor.execute('''UPDATE tasks SET name=? WHERE id=?''', (task.name, id))
    if(task.done is not None):
            cursor.execute('''UPDATE tasks SET done=? WHERE id=?''', (task.done, id))  

    conn.commit()
    cursor.execute('''SELECT * FROM tasks WHERE id=?''', (id,))
    res = cursor.fetchone()
    conn.close()
    
    return task_to_dict(res)

@app.delete("/tasks/{id}", response_model=Task)
def delete_task(id:int) -> Task:          #delete task

    conn = connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM tasks WHERE id=?''', (id,))
    res = cursor.fetchone()

    if(res is None):
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    
    cursor.execute('''
           DELETE FROM tasks WHERE id=?''',(id,))
    conn.commit()
    conn.close()
    
    return task_to_dict(res)