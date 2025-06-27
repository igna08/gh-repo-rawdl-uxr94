from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.classroom import ClassroomCreate, ClassroomRead, ClassroomUpdate
from app.services import classroom_service, school_service
from app.models.classroom import Classroom as ClassroomModel # For response_model

router = APIRouter()

@router.post(
    "/schools/{school_id}/classrooms/",
    response_model=ClassroomRead,
    status_code=status.HTTP_201_CREATED,
    tags=["classrooms"],
    summary="Create a new classroom for a specific school",
)
def create_classroom_for_school(
    classroom: ClassroomCreate,
    school_id: UUID = Path(..., description="The ID of the school to create the classroom in"),
    db: Session = Depends(get_db),
):
    # Verify school exists
    db_school = school_service.get_school(db, school_id=school_id)
    if not db_school:
        raise HTTPException(status_code=404, detail=f"School with id {school_id} not found")
    
    created_classroom = classroom_service.create_classroom(db=db, classroom=classroom, school_id=school_id)
    if created_classroom is None: # Should ideally be handled by specific exceptions in service
        raise HTTPException(status_code=400, detail="Could not create classroom, possibly due to school not found or code generation issues.")
    return created_classroom

@router.get(
    "/schools/{school_id}/classrooms/",
    response_model=List[ClassroomRead],
    tags=["classrooms"],
    summary="Get classrooms for a specific school",
)
def read_classrooms_for_school(
    school_id: UUID = Path(..., description="The ID of the school"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    # Verify school exists
    db_school = school_service.get_school(db, school_id=school_id)
    if not db_school:
        raise HTTPException(status_code=404, detail=f"School with id {school_id} not found")
    
    classrooms = classroom_service.get_classrooms_by_school(db, school_id=school_id, skip=skip, limit=limit)
    return classrooms

@router.get(
    "/classrooms/",
    response_model=List[ClassroomRead],
    tags=["classrooms (admin)"],
    summary="Get all classrooms (admin)",
)
def read_all_classrooms(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    classrooms = classroom_service.get_all_classrooms(db, skip=skip, limit=limit)
    return classrooms

@router.get(
    "/classrooms/{classroom_id}",
    response_model=ClassroomRead,
    tags=["classrooms"],
    summary="Get a specific classroom by ID",
)
def read_classroom(
    classroom_id: UUID = Path(..., description="The ID of the classroom"),
    db: Session = Depends(get_db),
):
    db_classroom = classroom_service.get_classroom(db, classroom_id=classroom_id)
    if db_classroom is None:
        raise HTTPException(status_code=404, detail=f"Classroom with id {classroom_id} not found")
    return db_classroom

@router.put(
    "/classrooms/{classroom_id}",
    response_model=ClassroomRead,
    tags=["classrooms"],
    summary="Update a classroom",
)
def update_existing_classroom(
    classroom_in: ClassroomUpdate,
    classroom_id: UUID = Path(..., description="The ID of the classroom to update"),
    db: Session = Depends(get_db),
):
    db_classroom = classroom_service.update_classroom(db, classroom_id=classroom_id, classroom_in=classroom_in)
    if db_classroom is None:
        raise HTTPException(status_code=404, detail=f"Classroom with id {classroom_id} not found for updating")
    return db_classroom

@router.delete(
    "/classrooms/{classroom_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["classrooms"],
    summary="Delete a classroom",
)
def delete_existing_classroom(
    classroom_id: UUID = Path(..., description="The ID of the classroom to delete"),
    db: Session = Depends(get_db),
):
    db_classroom = classroom_service.delete_classroom(db, classroom_id=classroom_id)
    if db_classroom is None: # Or if it was already deleted and service returns None
        raise HTTPException(status_code=404, detail=f"Classroom with id {classroom_id} not found for deletion")
    return None
