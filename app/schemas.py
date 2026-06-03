from pydantic import BaseModel, ConfigDict

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

class UserCreate(BaseModel):
    username: str
    password: str
    email:str

class UserResponse(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)