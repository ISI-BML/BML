from flask import Blueprint, jsonify, request, session

from myapp.services.auth_service import AuthError, authenticate_user, register_user

api_auth_bp = Blueprint("api_auth", __name__, url_prefix="/api/auth")


@api_auth_bp.post("/register")
def api_register():
    data = request.get_json(silent=True) or {}
    try:
        user = register_user(
            username=data.get("username", ""),
            email=data.get("email", ""),
            password=data.get("password", ""),
            role=data.get("role", "user"),
            company_key=data.get("company_key"),
        )
        return jsonify(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            }
        ), 201
    except AuthError as err:
        return jsonify({"error": err.message}), err.status_code


@api_auth_bp.post("/login")
def api_login():
    data = request.get_json(silent=True) or {}
    try:
        user = authenticate_user(
            username=data.get("username", ""),
            password=data.get("password", ""),
        )
        session.clear()
        session["user_id"] = user.id
        return jsonify(
            {
                "id": user.id,
                "username": user.username,
                "role": user.role,
            }
        ), 200
    except AuthError as err:
        return jsonify({"error": err.message}), err.status_code
