from sqlalchemy.orm import Session
from uuid import UUID
from app.models.user import User, UserCreate, UserUpdate

# This model will be created later
# from models.user import User 
def get_user_by_email(db: Session, email: str):
        print(f"Getting user by email: {email}") # Placeholder
        return db.query(User).filter(User.email == email).first()
# Placeholder for password hashing utility
def get_password_hash(password: str) -> str:
    return f"hashed_{password}"
def get_user_by_id(db: Session, user_id: UUID):

        return db.query(User).filter(User.id == user_id).first()
class UserService:
    def create_user(self, db: Session, user_in: UserCreate):
        # hashed_password = get_password_hash(user_in.password)
        # db_user = User(email=user_in.email, full_name=user_in.full_name, hashed_password=hashed_password)
        # db.add(db_user)
        # db.commit()
        # db.refresh(db_user)
        # return db_user
        print(f"User created: {user_in.email}") # Placeholder
        return {"message": "User created placeholder"}


    def get_user(self, db: Session, user_id: UUID):
        # return db.query(User).filter(User.id == user_id).first()
        print(f"Getting user by ID: {user_id}") # Placeholder
        return {"message": "Get user by ID placeholder"}




    def get_users(self, db: Session, skip: int = 0, limit: int = 100):
        # return db.query(User).offset(skip).limit(limit).all()
        print(f"Getting users with skip: {skip}, limit: {limit}") # Placeholder
        return [{"message": "Get users placeholder"}]

    def update_user(self, db: Session, user_id: UUID, user_in: UserUpdate):
        # db_user = self.get_user(db, user_id)
        # if not db_user:
        #     return None
        # update_data = user_in.dict(exclude_unset=True)
        # if "password" in update_data:
        #     update_data["hashed_password"] = get_password_hash(update_data["password"])
        #     del update_data["password"]
        # for field, value in update_data.items():
        #     setattr(db_user, field, value)
        # db.commit()
        # db.refresh(db_user)
        # return db_user
        print(f"Updating user: {user_id}") # Placeholder
        return {"message": "User updated placeholder"}

    def delete_user(self, db: Session, user_id: UUID):
        # db_user = self.get_user(db, user_id)
        # if not db_user:
        #     return None
        # db.delete(db_user)
        # db.commit()
        # return db_user
        print(f"Deleting user: {user_id}") # Placeholder
        return {"message": "User deleted placeholder"}

user_service = UserService()

