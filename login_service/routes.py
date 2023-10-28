import contextlib
import itertools
import sqlite3

from fastapi import Depends, HTTPException, APIRouter, status
from login_service.database.schemas import Users,Userlogin
from Utility import utils

router = APIRouter()

database = "./var/primary/fuse/database.db"
database_reps = itertools.cycle(["./var/secondary/fuse/database.db", "./var/tertiary/fuse/database.db"])
ALLOWED_ROLES = {"student", "professor", "registrar"}

# Connect to the database
def get_db():
    with contextlib.closing(sqlite3.connect(database, check_same_thread=False)) as db:
        db.row_factory = sqlite3.Row
        yield db

def get_db_replicas():

    curr_db = next(database_reps)

    try:
        connection = sqlite3.connect(curr_db, check_same_thread=False)
    except:
        curr_db = next(database_reps)
        connection = sqlite3.connect(curr_db, check_same_thread=False)
        try:
            connection = sqlite3.connect(curr_db, check_same_thread=False)
        except:
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Databases Unavailable",
            }
        )

    print(curr_db)

    with contextlib.closing(connection) as db:
            db.row_factory = sqlite3.Row
            yield db

@router.post("/register")
def register_user(user_data : Users,db: sqlite3.Connection = Depends(get_db)):
   
     # Check if the roles are valid
    invalid_roles = set(user_data.roles) - ALLOWED_ROLES
    if invalid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid roles",
                "invalid_roles": list(invalid_roles),
                "message": "Roles must be 'student', 'professor', or 'registrar'.",
            },
        )




    roles_str = ",".join(user_data.roles)
    user_data.password =  utils.hash_password(user_data.password)

    try:
        db.execute(
            """
            INSERT INTO users (uid, name, password, roles) VALUES (?, ?, ?, ?)
            """, (
                user_data.uid,
                user_data.name,
                user_data.password,
                roles_str
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
def verify_user(login_data:Userlogin,db: sqlite3.Connection = Depends(get_db_replicas)):
    cursor = db.cursor()
    # Fetch student data from db
    cursor.execute(
        """
        SELECT * FROM users
        WHERE name = ?
        """, (login_data.username,)
    )

    # cursor.execute(
    #     """
    #     SELECT u.*, r.name AS role_name
    #     FROM users AS u
    #     INNER JOIN roles AS r ON u.role_id = r.role_id
    #     WHERE u.name = ?
    #     """, (login_data.username,)
    # )

    user_data = cursor.fetchone()

    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Username not found")
    
    flag = utils.verify_password(login_data.password , user_data['password'])

    

    if(flag):
            return utils.generate_claims(login_data.username,user_data['uid'],user_data['roles'].split(','))
    else:
        return{"status":"invalid login credentials "}