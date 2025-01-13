# src/seeds/run_seeders.py
import sys
import os
from sqlalchemy.orm import Session
from src.db.session import SessionLocal
from src.seeds.category_seeder import seed_categories
from src.seeds.user_seeder import seed_users


def run_seeders():
    db: Session = SessionLocal()
    try:
        # Seed categories
        seed_categories(db)
        # Seed users
        seed_users(db)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    run_seeders()
