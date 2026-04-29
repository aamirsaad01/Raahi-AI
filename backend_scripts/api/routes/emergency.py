"""Emergency contact routes."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from api.utils.db_helper import DatabaseHelper

emergency_bp = Blueprint("emergency", __name__, url_prefix="/api/emergency")


def _validate_phone(phone: str) -> bool:
    p = phone.strip().replace(" ", "")
    if p.startswith("+"):
        p = p[1:]
    return p.isdigit() and 10 <= len(p) <= 15


@emergency_bp.route("/contacts", methods=["POST"])
def create_emergency_contact():
    data = request.get_json() or {}
    required = ["itinerary_id", "contact_name", "relationship", "phone_number"]
    for f in required:
        if f not in data or str(data.get(f, "")).strip() == "":
            return jsonify({"success": False, "error": f"Missing required field: {f}"}), 400

    try:
        itinerary_id = int(data["itinerary_id"])
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "itinerary_id must be an integer"}), 400

    contact_name = str(data["contact_name"]).strip()
    relationship = str(data["relationship"]).strip()
    phone_number = str(data["phone_number"]).strip()

    if len(contact_name) < 2:
        return jsonify({"success": False, "error": "Contact name is too short"}), 400
    if len(relationship) < 2:
        return jsonify({"success": False, "error": "Relationship is too short"}), 400
    if not _validate_phone(phone_number):
        return jsonify({"success": False, "error": "Invalid phone number format"}), 400

    db = DatabaseHelper()
    try:
        it = db.get_itinerary(itinerary_id)
        if not it:
            return jsonify({"success": False, "error": "Itinerary not found"}), 404
        cid = db.save_itinerary_emergency_contact(
            itinerary_id=itinerary_id,
            contact_name=contact_name,
            relationship=relationship,
            phone_number=phone_number,
        )
    finally:
        db.close()

    return jsonify({"success": True, "contact_id": cid}), 201


@emergency_bp.route("/contacts", methods=["GET"])
def get_contacts_for_latest_itinerary():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "user_id is required"}), 400
    try:
        uid = int(user_id)
    except ValueError:
        return jsonify({"success": False, "error": "user_id must be integer"}), 400

    db = DatabaseHelper()
    try:
        itinerary = db.get_latest_itinerary_for_user(uid)
        if not itinerary:
            return jsonify(
                {
                    "success": True,
                    "itinerary_id": None,
                    "destination": None,
                    "contacts": [],
                }
            ), 200

        itinerary_id = int(itinerary["itinerary_id"])
        contacts = db.get_emergency_contacts_for_itinerary(itinerary_id)
        return jsonify(
            {
                "success": True,
                "itinerary_id": itinerary_id,
                "destination": itinerary.get("destination"),
                "contacts": contacts,
            }
        ), 200
    finally:
        db.close()


@emergency_bp.route("/linked-contact", methods=["GET"])
def get_linked_contact():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "user_id is required"}), 400
    try:
        uid = int(user_id)
    except ValueError:
        return jsonify({"success": False, "error": "user_id must be integer"}), 400

    db = DatabaseHelper()
    try:
        itinerary = db.get_latest_itinerary_for_user(uid)
        if not itinerary:
            return jsonify({"success": True, "contact": None, "itinerary_id": None}), 200
        contact = db.get_latest_emergency_contact_for_itinerary(int(itinerary["itinerary_id"]))
        return jsonify(
            {
                "success": True,
                "itinerary_id": int(itinerary["itinerary_id"]),
                "destination": itinerary.get("destination"),
                "contact": contact,
            }
        ), 200
    finally:
        db.close()

