from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.school import SchoolCreate, SchoolRead, SchoolUpdate
from app.services import school_service
from app.models.school import School # Import School model for response_model typing

router = APIRouter(
    prefix="/schools",
    tags=["schools"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=SchoolRead, status_code=status.HTTP_201_CREATED)
def create_school(
    school: SchoolCreate, db: Session = Depends(get_db)
) -> School:
    return school_service.create_school(db=db, school=school)

@router.get("/", response_model=List[SchoolRead])
def read_schools(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> List[School]:
    schools = school_service.get_schools(db, skip=skip, limit=limit)
    return schools

@router.get("/{school_id}", response_model=SchoolRead)
def read_school(school_id: UUID, db: Session = Depends(get_db)) -> School:
    db_school = school_service.get_school(db, school_id=school_id)
    if db_school is None:
        raise HTTPException(status_code=404, detail="School not found")
    return db_school

@router.put("/{school_id}", response_model=SchoolRead)
def update_school(
    school_id: UUID, school_in: SchoolUpdate, db: Session = Depends(get_db)
) -> School:
    db_school = school_service.update_school(db, school_id=school_id, school_in=school_in)
    if db_school is None:
        raise HTTPException(status_code=404, detail="School not found")
    return db_school

@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_school(school_id: UUID, db: Session = Depends(get_db)) -> None:
    db_school = school_service.delete_school(db, school_id=school_id)
    if db_school is None:
        raise HTTPException(status_code=404, detail="School not found")
    return None
