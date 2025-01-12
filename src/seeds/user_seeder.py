# src/seeds/user_seeder.py
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.app import create_app, db
from src.models.user_model import User
from werkzeug.security import generate_password_hash

app = create_app()

def seed_users():
    with app.app_context():
        if not User.query.filter_by(email="superadmin@mail.com").first():
            super_admin = User(
                name="Super Admin",
                email="superadmin@mail.com",
                role="super_admin",
                password=generate_password_hash("kopi90") 
            )
            db.session.add(super_admin)
            print("Super Admin added!")

        if not User.query.filter_by(email="admin@mail.com").first():
            admin = User(
                name="Admin",
                email="admin@mail.com",
                role="admin",
                password=generate_password_hash("kopi90") 
            )
            db.session.add(admin)
            print("Admin added!")

        db.session.commit()
        print("Seeder completed: Users have been added.")

if __name__ == "__main__":
    seed_users()
