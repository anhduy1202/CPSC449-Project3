import contextlib
import sqlite3

from fastapi import Depends, HTTPException, APIRouter, status
from login_service.database.schemas import Users
from Utility import utils

router = APIRouter()

database = "mydatabase.db"

# Connect to the database
def get_db():
    with contextlib.closing(sqlite3.connect('login_service/database/mydatabase.db')) as db:
        db.row_factory = sqlite3.Row
        yield db


@router.post("/register")
def register_user(user_data : Users,db: sqlite3.Connection = Depends(get_db)):
    user_data.password =  utils.hash_password(user_data.password)
    try:
        db.execute(
            """
            INSERT INTO users (uid, name, password, role_id) VALUES (?, ?, ?, ?)
            """, (
                user_data.uid,
                user_data.name,
                user_data.password,
                user_data.role_id
            )
        )
        db.commit()
        return user_data
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)}
        )

@router.post("/login")
def verify_user(username:str , password:str,db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    # Fetch student data from db
    cursor.execute(
        """
        SELECT password FROM users
        WHERE name = ?
        """, (username,)
    )
    user_data = cursor.fetchone()

    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Username not found")

    flag = utils.verify_password(password , user_data[0])

    if(flag):
        return {"status":"you are sucessfully logged in"}
    else:
        return{"status":"invalid login credentials "}