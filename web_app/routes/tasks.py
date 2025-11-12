"""Task management routes."""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from ..models import db, Task, Assignment

tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.route("/", methods=["GET"])
@login_required
def get_tasks():
    """Get all tasks assigned to the current user."""
    assignments = Assignment.query.filter_by(user_id=current_user.id).all()
    return jsonify([assignment.to_dict() for assignment in assignments])


@tasks_bp.route("/<task_id>", methods=["GET"])
@login_required
def get_task(task_id):
    """Get a specific task by ID."""
    task = Task.query.get_or_404(task_id)
    return jsonify(task.to_dict())


@tasks_bp.route("/", methods=["POST"])
@login_required
def create_task():
    """Create a new task (admin/senior editor only)."""
    if not current_user.is_senior_editor():
        return jsonify({"error": "Insufficient permissions"}), 403

    data = request.get_json()

    task = Task(
        title=data["title"],
        description=data.get("description"),
        due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
        linked_form_id=data.get("linked_form_id"),
    )

    db.session.add(task)
    db.session.commit()

    return jsonify(task.to_dict()), 201


@tasks_bp.route("/<task_id>/assign", methods=["POST"])
@login_required
def assign_task(task_id):
    """Assign a task to users."""
    if not current_user.is_senior_editor():
        return jsonify({"error": "Insufficient permissions"}), 403

    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    user_ids = data.get("user_ids", [])

    for user_id in user_ids:
        # Check if assignment already exists
        existing = Assignment.query.filter_by(
            task_id=task_id, user_id=user_id
        ).first()

        if not existing:
            assignment = Assignment(task_id=task_id, user_id=user_id)
            db.session.add(assignment)

    db.session.commit()
    return jsonify({"message": "Task assigned successfully"}), 200


@tasks_bp.route("/assignments/<assignment_id>/status", methods=["PATCH"])
@login_required
def update_assignment_status(assignment_id):
    """Update the status of a task assignment."""
    assignment = Assignment.query.get_or_404(assignment_id)

    # Verify user owns this assignment
    if assignment.user_id != current_user.id and not current_user.is_senior_editor():
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json()
    new_status = data.get("status")

    if new_status not in ("not_started", "in_progress", "completed"):
        return jsonify({"error": "Invalid status"}), 400

    assignment.status = new_status
    if new_status == "completed":
        assignment.mark_completed()

    db.session.commit()

    return jsonify(assignment.to_dict()), 200
