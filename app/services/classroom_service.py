from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.classroom import Classroom
from app.schemas.classroom import ClassroomCreate, ClassroomUpdate
from app.services.school_service import get_school # To check if school exists

def create_classroom(db: Session, classroom: ClassroomCreate, school_id: UUID) -> Classroom | None:
    # Check if school exists
    db_school = get_school(db, school_id)
    if not db_school:
        return None # Or raise HTTPException
    
    # Generate a unique code for the classroom within the school
    # This is a simplified example; a more robust solution might be needed
    # to guarantee uniqueness under high concurrency.
    existing_codes = {
        c.code for c in 
        db.query(Classroom.code).filter(Classroom.school_id == school_id, Classroom.deleted_at == None).all()
    }
    
    base_code = classroom.name.replace(" ", "").upper()[:4]
    new_code = base_code
    counter = 1
    while new_code in existing_codes:
        new_code = f"{base_code}{counter}"
        counter += 1
        if counter > 1000: # Avoid infinite loop, set a practical limit
            raise Exception("Could not generate a unique classroom code.")


    db_classroom = Classroom(
        **classroom.model_dump(), 
        school_id=school_id,
        code=new_code # Add the generated code
    )
    db.add(db_classroom)
    db.commit()
    db.refresh(db_classroom)
    return db_classroom

def get_classroom(db: Session, classroom_id: UUID) -> Classroom | None:
    return db.query(Classroom).filter(Classroom.id == classroom_id, Classroom.deleted_at == None).first()

def get_classrooms_by_school(db: Session, school_id: UUID, skip: int = 0, limit: int = 100) -> list[Classroom]:
    return db.query(Classroom).filter(Classroom.school_id == school_id, Classroom.deleted_at == None).offset(skip).limit(limit).all()

def get_all_classrooms(db: Session, skip: int = 0, limit: int = 100) -> list[Classroom]:
    return db.query(Classroom).filter(Classroom.deleted_at == None).offset(skip).limit(limit).all()

def update_classroom(db: Session, classroom_id: UUID, classroom_in: ClassroomUpdate) -> Classroom | None:
    db_classroom = get_classroom(db, classroom_id)
    if db_classroom:
        update_data = classroom_in.model_dump(exclude_unset=True)
        
        # If name is being updated, consider if code should be regenerated or handled
        # For now, we are not changing the code upon name update.
        # If 'code' was part of ClassroomUpdate, it would need careful handling for uniqueness.

        for key, value in update_data.items():
            setattr(db_classroom, key, value)
        
        db_classroom.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_classroom)
    return db_classroom

def delete_classroom(db: Session, classroom_id: UUID) -> Classroom | None:
    db_classroom = get_classroom(db, classroom_id)
    if db_classroom:
        db_classroom.deleted_at = datetime.utcnow()
        db.commit()
        db.refresh(db_classroom)
    return db_classroom
