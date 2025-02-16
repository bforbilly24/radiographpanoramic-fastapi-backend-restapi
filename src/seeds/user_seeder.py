# src/seeds/user_seeder.py
from sqlalchemy.orm import Session
from src.models.user_model import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hash the password for secure storage."""
    return pwd_context.hash(password)


def seed_users(db: Session):
    users = [
        {
            "name": "Super Admin",
            "email": "superadmin@mail.com",
            "role": "super_admin",
            "password": "kopi90",
        },
        {
            "name": "Admin",
            "email": "admin@mail.com",
            "role": "admin",
            "password": "kopi90",
        },
    ]

    for user_data in users:
        # Check if the user already exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing_user:
            hashed_password = get_password_hash(user_data["password"])
            new_user = User(
                name=user_data["name"],
                email=user_data["email"],
                role=user_data["role"],
                password=hashed_password,
            )
            db.add(new_user)
            print(f"{user_data['name']} added!")

    db.commit()
    print("Seeder completed: Users have been added.")
