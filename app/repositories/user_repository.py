from sqlalchemy.orm import Session
from app.models.users import Users

class UserRepository:
    @staticmethod
    def get_user_by_phonenumber(db: Session, phonenumber: str) -> Users:
        return db.query(Users).filter(Users.phonenumber == phonenumber).first()
