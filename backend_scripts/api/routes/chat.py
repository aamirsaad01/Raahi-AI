"""Chat API routes."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from api.chat.service import ChatService

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


@chat_bp.route("/send", methods=["POST"])
def send_message():
    data = request.get_json() or {}
    try:
        user_id = int(data.get("user_id", 0))
    except (TypeError, ValueError):
        user_id = 0
    message = str(data.get("message", "")).strip()
    if user_id <= 0 or not message:
        return jsonify({"success": False, "error": "user_id and message are required"}), 400

    session_id = data.get("session_id")
    itinerary_id = data.get("itinerary_id")
    try:
        session_id = int(session_id) if session_id is not None else None
    except (TypeError, ValueError):
        session_id = None
    try:
        itinerary_id = int(itinerary_id) if itinerary_id is not None else None
    except (TypeError, ValueError):
        itinerary_id = None

    service = ChatService()
    try:
        result = service.send_message(
            user_id=user_id,
            message=message,
            session_id=session_id,
            itinerary_id=itinerary_id,
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        service.close()


@chat_bp.route("/sessions", methods=["GET"])
def list_sessions():
    try:
        user_id = int(request.args.get("user_id", "0"))
    except (TypeError, ValueError):
        user_id = 0
    if user_id <= 0:
        return jsonify({"success": False, "error": "user_id is required"}), 400
    service = ChatService()
    try:
        sessions = service.list_sessions(user_id)
        return jsonify({"success": True, "sessions": sessions}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        service.close()


@chat_bp.route("/sessions/<int:session_id>/messages", methods=["GET"])
def list_messages(session_id: int):
    try:
        user_id = int(request.args.get("user_id", "0"))
    except (TypeError, ValueError):
        user_id = 0
    if user_id <= 0:
        return jsonify({"success": False, "error": "user_id is required"}), 400
    service = ChatService()
    try:
        msgs = service.list_messages(user_id=user_id, session_id=session_id)
        return jsonify({"success": True, "messages": msgs}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        service.close()

