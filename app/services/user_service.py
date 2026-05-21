from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.models.users import Users

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRepository

    def get_active_user_by_phonenumber(self, phonenumber: str) -> Users:
        user = self.repository.get_user_by_phonenumber(self.db, phonenumber)
        if user and user.active:
            return user
        return None
