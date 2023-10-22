from pydantic import BaseModel

class Users(BaseModel):
    uid: int
    name: str
    password: str
    role_id: str

class Roles(BaseModel):
    role_id: int
    name: str

class User_Roles(BaseModel):
    uid: int
    role_id: int

class Userlogin(BaseModel):
    username:str
    password:str
    