"""Attendance tracking routes."""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from ..models import db, AttendanceLog

attendance_bp = Blueprint("attendance", __name__)


@attendance_bp.route("/", methods=["GET"])
@login_required
def get_attendance():
    """Get attendance records for the current user."""
    logs = AttendanceLog.query.filter_by(user_id=current_user.id)\
        .order_by(AttendanceLog.event_date.desc()).all()

    return jsonify([log.to_dict() for log in logs])


@attendance_bp.route("/log", methods=["POST"])
@login_required
def log_attendance():
    """Log attendance for an event."""
    data = request.get_json()

    log = AttendanceLog(
        user_id=current_user.id,
        event_name=data["event_name"],
        event_date=datetime.fromisoformat(data["event_date"]),
        status=data["status"],
        logged_at=datetime.utcnow(),
    )

    db.session.add(log)
    db.session.commit()

    return jsonify(log.to_dict()), 201


@attendance_bp.route("/events/<event_name>", methods=["GET"])
@login_required
def get_event_attendance(event_name):
    """Get all attendance records for an event (admin only)."""
    if not current_user.is_senior_editor():
        return jsonify({"error": "Insufficient permissions"}), 403

    logs = AttendanceLog.query.filter_by(event_name=event_name).all()
    return jsonify([log.to_dict() for log in logs])
