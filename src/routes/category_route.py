# src/routes/category_route.py
from flask import Blueprint
from flask_jwt_extended import jwt_required
from src.controllers.category_controller import get_categories, add_category

category_route = Blueprint("category_route", __name__, url_prefix='/api/categories')

@category_route.route("/", methods=["GET"])
@jwt_required()
def get_all_categories():
    return get_categories()

@category_route.route("/", methods=["POST"])
@jwt_required()
def create_category():
    return add_category()
