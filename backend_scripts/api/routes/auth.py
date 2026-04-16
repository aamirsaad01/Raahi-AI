"""Authentication + admin user management routes."""

from flask import Blueprint, request, jsonify
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.user.security import hash_password, verify_password
from api.user.validators import validate_signup_payload, validate_password_strength
from api.utils.db_helper import DatabaseHelper

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _sanitize_user(user: dict) -> dict:
    user = dict(user)
    user.pop("password", None)
    return user


def _is_admin_request(data: dict) -> tuple[bool, str]:
    token = str(data.get("admin_email", "")).strip().lower()
    if token != "admin@raahi.com":
        return False, "Admin privileges required"
    return True, ""


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register new user
    
    POST /api/auth/register
    
    Request Body:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "password123"
    }
    
    Response:
    {
        "success": true,
        "user_id": 1,
        "message": "User registered successfully"
    }
    """
    try:
        data = request.get_json() or {}
        validation_error = validate_signup_payload(data)
        if validation_error:
            return jsonify({"success": False, "error": validation_error}), 400

        db = DatabaseHelper()
        try:
            user_id = db.create_user_profile(
                name=str(data["name"]).strip(),
                email=str(data["email"]).strip().lower(),
                contact_number=str(data["contact_number"]).strip(),
                dob=str(data["dob"]).strip(),
                cnic=str(data["cnic"]).strip(),
                medical_conditions=str(data.get("medical_conditions", "")).strip(),
                password_hash=hash_password(str(data["password"])),
                is_admin=False,
            )
        finally:
            db.close()

        if not user_id:
            return jsonify({
                "success": False,
                "error": "Email or CNIC already exists",
            }), 400

        return jsonify({
            "success": True,
            "user_id": user_id,
            "message": "User registered successfully",
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user
    
    POST /api/auth/login
    
    Request Body:
    {
        "email": "john@example.com",
        "password": "password123"
    }
    
    Response:
    {
        "success": true,
        "user": {
            "user_id": 1,
            "name": "John Doe",
            "email": "john@example.com"
        },
        "message": "Login successful"
    }
    """
    try:
        data = request.get_json() or {}
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))
        if not email or not password:
            return jsonify({"success": False, "error": "Email and password are required"}), 400

        db = DatabaseHelper()
        try:
            user = db.get_user_by_email(email)
            if not user or not verify_password(password, str(user.get("password", ""))):
                return jsonify({"success": False, "error": "Invalid email or password"}), 401
            if user.get("is_active") is False:
                return jsonify({"success": False, "error": "Account is disabled"}), 403
            db.update_user_last_login(int(user["user_id"]))
            user = db.get_user_by_id(int(user["user_id"])) or user
        finally:
            db.close()

        return jsonify({
            "success": True,
            "user": _sanitize_user(user),
            "message": "Login successful",
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500


@auth_bp.route("/users", methods=["GET"])
def admin_list_users():
    """Admin: list users."""
    admin_email = str(request.args.get("admin_email", "")).strip().lower()
    if admin_email != "admin@raahi.com":
        return jsonify({"success": False, "error": "Admin privileges required"}), 403
    db = DatabaseHelper()
    try:
        users = [_sanitize_user(u) for u in db.get_all_users()]
    finally:
        db.close()
    return jsonify({"success": True, "users": users}), 200


@auth_bp.route("/users/<int:user_id>", methods=["PUT"])
def admin_update_user(user_id: int):
    """Admin: update a user profile/settings."""
    try:
        data = request.get_json() or {}
        ok, err = _is_admin_request(data)
        if not ok:
            return jsonify({"success": False, "error": err}), 403

        if "password" in data:
            pwd_err = validate_password_strength(str(data["password"]))
            if pwd_err:
                return jsonify({"success": False, "error": pwd_err}), 400

        update_data = {
            "name": data.get("name"),
            "email": str(data.get("email", "")).strip().lower() if data.get("email") else None,
            "contact_number": data.get("contact_number"),
            "dob": data.get("dob"),
            "cnic": data.get("cnic"),
            "medical_conditions": data.get("medical_conditions"),
            "is_admin": data.get("is_admin"),
            "is_active": data.get("is_active"),
        }
        update_data = {k: v for k, v in update_data.items() if v is not None}

        db = DatabaseHelper()
        try:
            updated = db.update_user_profile_by_admin(user_id, update_data)
            updated_password = False
            if "password" in data:
                updated_password = db.update_user_profile_by_admin(
                    user_id, {"password": hash_password(str(data["password"]))}
                )
            user = db.get_user_by_id(user_id)
        finally:
            db.close()
        if not (updated or updated_password) or not user:
            return jsonify({"success": False, "error": "User not found"}), 404
        return jsonify({"success": True, "user": _sanitize_user(user)}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500


@auth_bp.route("/users/<int:user_id>", methods=["DELETE"])
def admin_delete_user(user_id: int):
    """Admin: delete user and related rows."""
    try:
        data = request.get_json() or {}
        ok, err = _is_admin_request(data)
        if not ok:
            return jsonify({"success": False, "error": err}), 403

        db = DatabaseHelper()
        try:
            user = db.get_user_by_id(user_id)
            if not user:
                return jsonify({"success": False, "error": "User not found"}), 404
            if str(user.get("email", "")).lower() == "admin@raahi.com":
                return jsonify({"success": False, "error": "Cannot delete default admin"}), 400
            deleted = db.delete_user_and_related(user_id)
        finally:
            db.close()
        if not deleted:
            return jsonify({"success": False, "error": "Delete failed"}), 400
        return jsonify({"success": True, "message": "User and related data deleted"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500

