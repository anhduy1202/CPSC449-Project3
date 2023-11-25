import contextlib
import enrollment_service.query_helper as qh
import redis

from fastapi import Depends, HTTPException, APIRouter, Header, status
import boto3
from enrollment_service.database.schemas import Class

router = APIRouter()
dropped = []

FREEZE = False
MAX_WAITLIST = 3
database = "enrollment_service/database/database.db"
dynamodb_client = boto3.client('dynamodb', endpoint_url='http://localhost:5500')
table_name = 'TitanOnlineEnrollment'
r = redis.Redis()


#==========================================students==================================================


# DONE: GET available classes for a student
@router.get("/students/{student_id}/classes", tags=['Student']) 
def get_available_classes(student_id: str):
    # Check if student exists in the database
    student_data = qh.query_student(dynamodb_client, student_id)
    if not student_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No student found")
    class_data = qh.query_available_classes(dynamodb_client, student_id)
    if not class_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No classes found")
    # If watlist full, don't show full classes with open waitlists
    filtered_class_data = []
    for item in class_data:
        waitlist_key = f'waitlist:{item["id"]}'
        waitlist_length = r.llen(waitlist_key)
        # If student is in the waitlist, don't show the class
        id = f"s#{student_id}".encode('utf-8')
        if id in r.lrange(waitlist_key, 0, -1):
            continue
        # Add the item to filtered_data only if the waitlist is not full
        if waitlist_length < MAX_WAITLIST or r.exists(waitlist_key) == 0:
            filtered_class_data.append(item)

    return {"Classes" : filtered_class_data}


# DONE: GET currently enrolled classes for a student
@router.get("/students/{student_id}/enrolled", tags=['Student'])
def view_enrolled_classes(student_id: str):
    # Check if student exists in the database
    student_data = qh.query_student(dynamodb_client, student_id)
    if not student_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No student found")
    class_data = qh.query_enrolled_classes(dynamodb_client, student_id)
    if not class_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No classes found")

    return {"Enrolled": class_data}

# DONE
# Enrolls a student into an available class,
# or will automatically put the student on an open waitlist for a full class
@router.post("/students/{student_id}/classes/{class_id}/enroll", tags=['Student'], summary="Enroll in a class")
def enroll_student_in_class(student_id: str, class_id: str):
    # Check if the student exists in the database
    student_data = qh.query_student(dynamodb_client, student_id)
    if not student_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No student found")

    # Check if the class exists in the database
    class_data = qh.query_class(dynamodb_client, class_id)
    if not class_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No class found")

    # Check if student is already enrolled in the class
    enrolled_class = qh.query_enrolled_classes(dynamodb_client, student_id)
    if enrolled_class:
        class_ids = [item['id'] for item in enrolled_class]
        if class_id in class_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student is already enrolled in this class")
    
    # Check if class is frozen
    if class_data['Frozen']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enrollment is frozen")
    
    # Check if the class is full
    if class_data['currentEnroll'] >= class_data['maxEnroll']:
        print("Class is full")
        # Waitlist handling
        waitlist_key = f"waitlist:{class_id}"
        # check if waitlist exists, add to wailist Redis with key waitlist:class_id, value s#student_id
        if not r.exists(waitlist_key):
            r.rpush(waitlist_key, f"s#{student_id}")
            return {"message": "Student added to waitlist"}
        else:
            # check if student is already on waitlist
            id = f"s#{student_id}".encode('utf-8')
            if id in r.lrange(waitlist_key, 0, -1):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student is already on waitlist")
            # check if adding student to waitlist will exceed max waitlist
            if r.llen(waitlist_key) < MAX_WAITLIST:
                r.rpush(waitlist_key, f"s#{student_id}")
                return {"message": "Student added to waitlist"}
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to add student to waitlist due to already having max number of waitlists")

    # Add student to enrolled class in the database

    enrolled_class = qh.update_enrolled_class(dynamodb_client, student_id, class_id)
    if not enrolled_class:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to enroll student in class")
    
    # Increment enrollment number in the database
    new_enrollment = class_data['currentEnroll'] + 1
    update_finished = qh.update_current_enroll(dynamodb_client, class_id, new_enrollment)
    if not update_finished:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update class enrollment")
    
    # Fetch the updated class data from the databas
    updated_class_data = qh.query_class(dynamodb_client, class_id)

    return updated_class_data["Detail"]

# DONE
# Have a student drop a class they're enrolled in
@router.delete("/students/{student_id}/classes/{class_id}", tags=['Student'], summary="Drop a class")
def drop_student_from_class(student_id: str, class_id: str):
    # Check if the student exists in the database
    student_data = qh.query_student(dynamodb_client, student_id)
    if not student_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No student found")
    # Check if the class exists in the database
    class_data = qh.query_class(dynamodb_client, class_id)
    if not class_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No class found")
    # Check if student is enrolled in the class
    enrolled_class = qh.query_enrolled_classes(dynamodb_client, student_id)
    if not enrolled_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student is not enrolled in this class")
    class_ids = [item['id'] for item in enrolled_class]
    if class_id not in class_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student is not enrolled in this class")
    # Drop student from class
    drop_finished = qh.drop_student_from_class(dynamodb_client, student_id, class_id)
    if not drop_finished:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to drop student from class")
    # Decrement enrollment number in the database
    new_enrollment = class_data['currentEnroll'] - 1
    update_finished = qh.update_current_enroll(dynamodb_client, class_id, new_enrollment)
    if not update_finished:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update class enrollment")
    # check if waitlist exists for class
    # check if freeze is on
    if not class_data['Frozen']:
        if r.exists(f"waitlist:{class_id}"):
            # first student on waitlist is automatically enrolled
            waitlist_data = r.lrange(f"waitlist:{class_id}", 0, 0)
            waitlist_data = [item.decode('utf-8')[2:] for item in waitlist_data]
            # Enroll student in class
            enrolled_class = qh.update_enrolled_class(dynamodb_client, waitlist_data[0], class_id)
            if not enrolled_class:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to enroll student in class")
            # Increment enrollment number in the database
            new_enrollment = class_data['currentEnroll'] + 1
            update_finished = qh.update_current_enroll(dynamodb_client, class_id, new_enrollment)
            if not update_finished:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update class enrollment")
            # Remove student from waitlist
            r.lrem(f"waitlist:{class_id}", 0, f"s#{waitlist_data[0]}")
            # Fetch the updated class data from the databas
            updated_class_data = qh.query_class(dynamodb_client, class_id)
            return {"message": "Student dropped from class and first student on waitlist enrolled", "Class": updated_class_data["Detail"]}
    return {"message": "Student dropped from class"}
    

#==========================================wait list========================================== 


# DONE: Get wait list position for a student in a class
@router.get("/students/{student_id}/waitlist/{class_id}", tags=['Waitlist'], summary="Get waitlist position for a student in a class")
def view_waiting_list(student_id: str, class_id: str):
    # check if student exists in the database
    student_data = qh.query_student(dynamodb_client, student_id)
    if not student_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No student found")
    # check if class exists in the database
    class_data = qh.query_class(dynamodb_client, class_id)
    if not class_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No class found")
    waitlist_key = f"waitlist:{class_id}"
    if not r.exists(waitlist_key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No waitlist found")
    waitlist_data = r.lrange(waitlist_key, 0, -1)
    if not waitlist_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No waitlist found")
    # Check if student is on waitlist
    id = f"s#{student_id}".encode('utf-8')
    if id not in waitlist_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student is not on waitlist")
    # Get student's position on waitlist
    position = waitlist_data.index(id) + 1
    return {"Waitlist Position": position}

# DONE: remove a student from a waiting list
@router.delete("/students/{student_id}/waitlist/{class_id}", tags=['Waitlist'], summary="Remove a student from a waiting list")
def remove_from_waitlist(student_id: str, class_id: str):
    # check if student exists in the database
    student_data = qh.query_student(dynamodb_client, student_id)
    if not student_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No student found")
    # check if class exists in the database
    class_data = qh.query_class(dynamodb_client, class_id)
    if not class_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No class found")
    waitlist_key = f"waitlist:{class_id}"
    if not r.exists(waitlist_key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No waitlist found")
    waitlist_data = r.lrange(waitlist_key, 0, -1)
    if not waitlist_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No waitlist found")
    # Check if student is on waitlist
    id = f"s#{student_id}".encode('utf-8')
    if id not in waitlist_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student is not on waitlist")
    # Remove student from waitlist
    r.lrem(waitlist_key, 0, id)
    return {"message": "Student removed from the waiting list"}

# DONE: Get waitlist for a class
@router.get("/classes/{class_id}/waitlist",tags=['Waitlist'], summary="Get waitlist for a class")
def view_current_waitlist(class_id: str):
    # Check if class exist
    class_data = qh.query_class(dynamodb_client, class_id)
    if not class_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No class found")
    waitlist_key = f"waitlist:{class_id}"
    if not r.exists(waitlist_key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No waitlist found")
    waitlist_data = r.lrange(waitlist_key, 0, -1)
    if not waitlist_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No waitlist found")
    waitlist_data = [item.decode('utf-8') for item in waitlist_data]
    # Get student info from waitlist_data
    waitlist_data = qh.batch_query_student(dynamodb_client, waitlist_data)
    return {"Waitlist": waitlist_data}


#==========================================Instructor==================================================


# DONE: view current enrollment for class
@router.get("/instructors/{instructor_id}/classes/{class_id}/enrollment", tags=['Instructor'], summary="Get current enrollment for class")
def get_instructor_enrollment(instructor_id: str, class_id: str):
    # check if instructor exists in the database
    instructor_data = qh.query_instructor(dynamodb_client, instructor_id)
    if not instructor_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No instructor found")
    # check if class exists in the database
    class_data = qh.query_class(dynamodb_client, class_id)
    if not class_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No class found")
    # check if instructor is assigned to class
    class_instructor = qh.query_class_instructor(dynamodb_client, instructor_id, class_id)
    if not class_instructor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instructor is not assigned to this class")
    # get enrollment data
    enrollment_data = qh.query_enrolled_students(dynamodb_client, class_id)
    if not enrollment_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No enrollment found")
    return {"Enrollment": enrollment_data}

# DONE: view students who have dropped the class
@router.get("/instructors/{instructor_id}/classes/{class_id}/drop", tags=['Instructor'], summary="Get students who dropped the class")
def get_instructor_dropped(instructor_id: str, class_id: str):
    # check if instructor exists in the database
    instructor_data = qh.query_instructor(dynamodb_client, instructor_id)
    if not instructor_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No instructor found")
    # check if class exists in the database
    class_data = qh.query_class(dynamodb_client, class_id)
    if not class_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No class found")
    # check if instructor is assigned to class
    class_instructor = qh.query_class_instructor(dynamodb_client, instructor_id, class_id)
    if not class_instructor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instructor is not assigned to this class")
    # get dropped data
    dropped_data = qh.query_dropped_students(dynamodb_client, class_id)
    if not dropped_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No dropped found")
    
    return {"Dropped": dropped_data}

# DONE: Instructor administratively drop students
@router.post("/instructors/{instructor_id}/classes/{class_id}/students/{student_id}/drop", tags=['Instructor'], summary="Instructor administratively drop students")
def instructor_drop_class(instructor_id: str, class_id: str, student_id: str):
    # check if instructor exists in the database
    instructor_data = qh.query_instructor(dynamodb_client, instructor_id)
    if not instructor_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No instructor found")
    # check if class exists in the database
    class_data = qh.query_class(dynamodb_client, class_id)
    if not class_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No class found")
    # check if instructor is assigned to class
    class_instructor = qh.query_class_instructor(dynamodb_client, instructor_id, class_id)
    if not class_instructor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instructor is not assigned to this class")
    # check if student exists in the database
    student_data = qh.query_student(dynamodb_client, student_id)
    if not student_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No student found")
    # check if student is enrolled in the class
    enrolled_class = qh.query_enrolled_classes(dynamodb_client, student_id)
    if not enrolled_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student is not enrolled in this class")
    class_ids = [item['id'] for item in enrolled_class]
    if class_id not in class_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student is not enrolled in this class")
    # Drop student from class
    drop_finished = qh.drop_student_from_class(dynamodb_client, student_id, class_id)
    if not drop_finished:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to drop student from class")
    # Decrement enrollment number in the database
    new_enrollment = class_data['currentEnroll'] - 1
    update_finished = qh.update_current_enroll(dynamodb_client, class_id, new_enrollment)
    if not update_finished:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update class enrollment")
    # check if waitlist exists for class
    # check if freeze is on
    if not class_data['Frozen']:
        if r.exists(f"waitlist:{class_id}"):
            # first student on waitlist is automatically enrolled
            waitlist_data = r.lrange(f"waitlist:{class_id}", 0, 0)
            waitlist_data = [item.decode('utf-8')[2:] for item in waitlist_data]
            # Enroll student in class
            enrolled_class = qh.update_enrolled_class(dynamodb_client, waitlist_data[0], class_id)
            if not enrolled_class:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to enroll student in class")
            # Increment enrollment number in the database
            new_enrollment = class_data['currentEnroll'] + 1
            update_finished = qh.update_current_enroll(dynamodb_client, class_id, new_enrollment)
            if not update_finished:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update class enrollment")
            # Remove student from waitlist
            r.lrem(f"waitlist:{class_id}", 0, f"s#{waitlist_data[0]}")
            # Fetch the updated class data from the databas
            updated_class_data = qh.query_class(dynamodb_client, class_id)
            return {"message": "Student dropped from class and first student on waitlist enrolled", "Class": updated_class_data["Detail"]}
    return {"message": "Student dropped from class"}


#==========================================registrar==================================================


# DONE: Create a new class
@router.post("/registrar/classes/", tags=['Registrar'])
def create_class(class_data: Class):
    # Check instructor exists in the database
    instructor_data = qh.query_instructor(dynamodb_client, class_data.InstructorId)
    if not instructor_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No instructor found")
    class_created = qh.create_class(dynamodb_client, class_data)
    if not class_created:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create class")
    return {"message": "Class created successfully"}

# DONE: Remove a class
@router.delete("/registrar/classes/{class_id}", tags=['Registrar'])
def remove_class(class_id: str):
    # Check if class exists in the database
    class_data = qh.query_class(dynamodb_client, class_id)
    if not class_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No class found")
    removed_class = qh.delete_class(dynamodb_client, class_id)
    if not removed_class:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to remove class")
    return {"message": "Class removed successfully"}

# DONE: Change the assigned instructor for a class
@router.put("/registrar/classes/{class_id}/instructors/{instructor_id}", tags=['Registrar'])
def change_instructor(class_id: str, instructor_id: str):
    # Check if class exists in the database
    class_data = qh.query_class(dynamodb_client, class_id)
    if not class_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No class found")
    # Check if instructor exists in the database
    instructor_data = qh.query_instructor(dynamodb_client, instructor_id)
    if not instructor_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No instructor found")
    # Change the assigned instructor for the class
    instructor_changed = qh.change_instructor(dynamodb_client, class_id, instructor_id)
    if not instructor_changed:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to change instructor")
    # return success message
    return {"message": "Instructor changed"}


# DONE: Freeze enrollment for classes
@router.put("/registrar/classes/{class_id}/freeze", tags=['Registrar'])
def freeze_automatic_enrollment(class_id: str):
    # Check if class exists in the database
    class_data = qh.query_class(dynamodb_client, class_id)
    if not class_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No class found")
    # Check if class is already frozen
    if class_data['Frozen']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Class is already frozen")
    # Freeze the class
    freeze_finished = qh.freeze_enrollment(dynamodb_client, class_id)
    if not freeze_finished:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to freeze enrollment")
    # return success message
    return {"message": "Enrollment frozen"}