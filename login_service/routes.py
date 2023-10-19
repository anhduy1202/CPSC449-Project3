import contextlib
import sqlite3

from fastapi import Depends, HTTPException, APIRouter, status
from login_service.database.schemas import Users

router = APIRouter()

database = "mydatabase.db"

# Connect to the database
def get_db():
    with contextlib.closing(sqlite3.connect('login_service/database/mydatabase.db')) as db:
        db.row_factory = sqlite3.Row
        yield db


@router.post("/register")
def register_user(user_data : Users,db: sqlite3.Connection = Depends(get_db)):
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

