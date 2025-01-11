# src/controllers/user_controller.py
from flask import jsonify, request
from werkzeug.security import check_password_hash
from src.models.user_model import User
from flask_jwt_extended import (
    create_access_token,
    set_access_cookies,
    unset_jwt_cookies,
)
from datetime import timedelta


def login():
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"message": "Missing email or password"}), 400

    user = User.query.filter_by(email=data["email"]).first()

    # Validate password
    if not user or not check_password_hash(user.password, data["password"]):
        return jsonify({"message": "Invalid credentials"}), 401

    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(hours=1),
    )

    response = jsonify({"message": "Login successful", "access_token": access_token})

    set_access_cookies(response, access_token)

    return response, 200


def logout():
    response = jsonify({"message": "Logout successful"})

    unset_jwt_cookies(response)

    return response, 200
