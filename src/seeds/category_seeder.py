# src/seeds/category_seeder.py
from sqlalchemy.orm import Session
from src.models.category_model import Category

def seed_categories(db: Session):
    categories = ["Lesi Periapikal", "Resorpsi", "Karies", "Impaksi"]

    for category_name in categories:
        # Check if the category already exists
        existing_category = db.query(Category).filter(Category.name == category_name).first()
        if not existing_category:
            new_category = Category(name=category_name)
            db.add(new_category)

    db.commit()
    print("Categories seeded successfully.")
