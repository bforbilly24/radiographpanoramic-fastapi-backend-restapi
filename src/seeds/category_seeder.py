# src/seeds/category_seeder.py
from src.models.category_model import Category
from src.extensions import db

def seed_categories():
    categories = ["Lesi Periapikal", "Resorpsi", "Karies", "Impaksi"]
    for category_name in categories:
        existing_category = Category.query.filter_by(name=category_name).first()
        if not existing_category:
            new_category = Category(name=category_name)
            db.session.add(new_category)
    db.session.commit()
    print("Categories seeded successfully.")
