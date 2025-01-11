# src/routes/auth_route.py
from flask import Blueprint
from src.controllers.user_controller import login, logout 
from flask_jwt_extended import jwt_required

auth_route = Blueprint("auth_route", __name__, url_prefix='/api/auth')

auth_route.route("/login", methods=["POST"])(login)

auth_route.route("/logout", methods=["POST"])(jwt_required()(logout))
