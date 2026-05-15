"""Authentication + admin user management routes."""

from flask import Blueprint, request, jsonify
import sys
import os
from datetime import datetime
from email.utils import parsedate_to_datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.user.security import hash_password, verify_password
import psycopg2

from api.user.validators import (
    CNIC_RE,
    EMAIL_RE,
    PHONE_RE,
    validate_password_strength,
    validate_signup_payload,
    _age_years,
)
from api.utils.db_helper import DatabaseHelper

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _sanitize_user(user: dict) -> dict:
    user = dict(user)
    user.pop("password", None)
    return user


def _parse_dob_for_profile(dob_raw: str):
    """Accept YYYY-MM-DD, ISO datetimes, or RFC1123-style dates from clients/DB."""
    dob = str(dob_raw).strip()
    if not dob:
        raise ValueError("empty")
    try:
        return datetime.strptime(dob, "%Y-%m-%d").date()
    except ValueError:
        pass
    if len(dob) >= 10 and dob[4] == "-" and dob[7] == "-":
        try:
            return datetime.strptime(dob[:10], "%Y-%m-%d").date()
        except ValueError:
            pass
    try:
        return parsedate_to_datetime(dob).date()
    except (TypeError, ValueError, OverflowError) as e:
        raise ValueError("unrecognized dob format") from e


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


@auth_bp.route("/profile", methods=["PUT", "POST"])
def update_own_profile():
    """Update the signed-in user's profile (requires current password)."""
    try:
        data = request.get_json() or {}
        email = str(data.get("email", "")).strip().lower()
        current_password = str(data.get("current_password", ""))
        if not email or not current_password:
            return jsonify(
                {"success": False, "error": "Email and current password are required"}
            ), 400

        db = DatabaseHelper()
        try:
            user = db.get_user_by_email(email)
            if not user or not verify_password(
                current_password, str(user.get("password", ""))
            ):
                return jsonify({"success": False, "error": "Invalid email or password"}), 401

            uid = int(user["user_id"])
            patches: dict = {}

            if "name" in data and data["name"] is not None:
                name = str(data["name"]).strip()
                if len(name) < 2 or len(name) > 100:
                    return jsonify(
                        {"success": False, "error": "Name must be 2–100 characters"}
                    ), 400
                patches["name"] = name

            if "contact_number" in data and data["contact_number"] is not None:
                contact = str(data["contact_number"]).strip()
                if not PHONE_RE.match(contact):
                    return jsonify(
                        {
                            "success": False,
                            "error": "Contact number must be 10–15 digits (optional + prefix)",
                        }
                    ), 400
                patches["contact_number"] = contact

            if "dob" in data and data["dob"] is not None:
                dob = str(data["dob"]).strip()
                try:
                    dob_date = _parse_dob_for_profile(dob)
                except ValueError:
                    return jsonify(
                        {
                            "success": False,
                            "error": "DOB must be a valid date (use YYYY-MM-DD)",
                        }
                    ), 400
                if _age_years(dob_date) < 13:
                    return jsonify(
                        {"success": False, "error": "User must be at least 13 years old"}
                    ), 400
                patches["dob"] = dob_date.strftime("%Y-%m-%d")

            if "cnic" in data and data["cnic"] is not None:
                cnic = str(data["cnic"]).strip()
                if not CNIC_RE.match(cnic):
                    return jsonify(
                        {
                            "success": False,
                            "error": "CNIC must match 12345-1234567-1 format",
                        }
                    ), 400
                patches["cnic"] = cnic

            if "medical_conditions" in data:
                med = str(data.get("medical_conditions", "")).strip()
                if len(med) > 500:
                    return jsonify(
                        {"success": False, "error": "Medical conditions max 500 characters"}
                    ), 400
                patches["medical_conditions"] = med

            new_email = str(data.get("new_email", "")).strip().lower()
            if new_email:
                if new_email != email:
                    if not EMAIL_RE.match(new_email):
                        return jsonify(
                            {"success": False, "error": "Invalid new email format"}
                        ), 400
                    other = db.get_user_by_email(new_email)
                    if other and int(other["user_id"]) != uid:
                        return jsonify(
                            {"success": False, "error": "That email is already in use"}
                        ), 400
                    patches["email"] = new_email

            new_password = str(data.get("new_password", "")).strip()
            if new_password:
                pwd_err = validate_password_strength(new_password)
                if pwd_err:
                    return jsonify({"success": False, "error": pwd_err}), 400
                patches["password"] = hash_password(new_password)

            if not patches:
                fresh = db.get_user_by_id(uid)
                return jsonify(
                    {"success": True, "user": _sanitize_user(fresh or user)}
                ), 200

            try:
                updated = db.update_user_profile_by_admin(uid, patches)
            except psycopg2.errors.UniqueViolation:
                return jsonify(
                    {"success": False, "error": "Email or CNIC already exists"}
                ), 400

            fresh = db.get_user_by_id(uid)
            if not updated or not fresh:
                return jsonify({"success": False, "error": "Update failed"}), 400

            return jsonify({"success": True, "user": _sanitize_user(fresh)}), 200
        finally:
            db.close()
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

