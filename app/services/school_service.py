from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.school import School
from app.schemas.school import SchoolCreate, SchoolUpdate

def create_school(db: Session, school: SchoolCreate) -> School:
    school_data = school.model_dump()
    if "logo_url" in school_data and school_data["logo_url"] is not None:
        school_data["logo_url"] = str(school_data["logo_url"])
    db_school = School(**school_data)
    db.add(db_school)
    db.commit()
    db.refresh(db_school)
    return db_school


def get_school(db: Session, school_id: UUID) -> School | None:
    return db.query(School).filter(School.id == school_id, School.deleted_at == None).first()

def get_schools(db: Session, skip: int = 0, limit: int = 100) -> list[School]:
    return db.query(School).filter(School.deleted_at == None).offset(skip).limit(limit).all()

def update_school(db: Session, school_id: UUID, school_in: SchoolUpdate) -> School | None:
    db_school = get_school(db, school_id)
    if db_school:
        update_data = school_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_school, key, value)
        db.commit()
        db.refresh(db_school)
    return db_school

def delete_school(db: Session, school_id: UUID) -> School | None:
    db_school = get_school(db, school_id)
    if db_school:
        db_school.deleted_at = datetime.utcnow()
        db.commit()
        db.refresh(db_school)
    return db_school
