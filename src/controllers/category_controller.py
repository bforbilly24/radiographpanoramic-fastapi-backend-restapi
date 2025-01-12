# src/controllers/category_controller.py
from flask import jsonify, request
from src.models.category_model import Category
from src.extensions import db

def get_categories():
    try:
        categories = Category.query.all()
        result = [{"id": category.id, "name": category.name} for category in categories]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def add_category():
    try:
        data = request.json
        name = data.get("name")
        if not name:
            return jsonify({"error": "Category name is required"}), 400

        existing_category = Category.query.filter_by(name=name).first()
        if existing_category:
            return jsonify({"error": "Category already exists"}), 400

        new_category = Category(name=name)
        db.session.add(new_category)
        db.session.commit()
        return jsonify({"message": "Category added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
