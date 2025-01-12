# src/app.py
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.configs.database import Config
from src.extensions import db, migrate

jwt = JWTManager()

@jwt.unauthorized_loader
def unauthorized_error(callback):
    return (
        jsonify(
            {
                "message": "Not Authorized. Please provide a valid JWT token in the Authorization header."
            }
        ),
        401,
    )


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  

    CORS(app)

    db.init_app(app)
    migrate.init_app(app, db)

    jwt.init_app(app)


    app.config["UPLOAD_FOLDER"] = "uploads/original"
    app.config["PREDICTED_FOLDER"] = "uploads/predicted"

    from src.routes.radiograph_route import radiograph_route
    from src.routes.auth_route import auth_route
    from src.routes.category_route import category_route

    app.register_blueprint(radiograph_route)  
    app.register_blueprint(auth_route)        
    app.register_blueprint(category_route)     

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
