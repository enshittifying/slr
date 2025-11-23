"""API routes for external integrations and AJAX calls."""

from flask import Blueprint, jsonify
from flask_login import login_required, current_user

api_bp = Blueprint("api", __name__)


@api_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "slr-workflow-api"}), 200


@api_bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    """Get current user information."""
    return jsonify(current_user.to_dict()), 200


@api_bp.route("/stats", methods=["GET"])
@login_required
def get_user_stats():
    """Get statistics for the current user."""
    from ..models import Assignment

    assignments = Assignment.query.filter_by(user_id=current_user.id).all()

    stats = {
        "total_tasks": len(assignments),
        "not_started": sum(1 for a in assignments if a.status == "not_started"),
        "in_progress": sum(1 for a in assignments if a.status == "in_progress"),
        "completed": sum(1 for a in assignments if a.status == "completed"),
    }

    return jsonify(stats), 200
