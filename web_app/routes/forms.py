"""Form management routes."""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from ..models import db, FormDefinition, FormSubmission

forms_bp = Blueprint("forms", __name__)


@forms_bp.route("/", methods=["GET"])
@login_required
def get_forms():
    """Get all form definitions."""
    forms = db.session.query(FormDefinition.form_name, FormDefinition.google_form_id)\
        .distinct().all()

    return jsonify([
        {"form_name": f.form_name, "google_form_id": f.google_form_id}
        for f in forms
    ])


@forms_bp.route("/<form_name>", methods=["GET"])
@login_required
def get_form_definition(form_name):
    """Get form definition by name."""
    definitions = FormDefinition.query.filter_by(form_name=form_name).all()
    return jsonify([d.to_dict() for d in definitions])


@forms_bp.route("/submissions", methods=["POST"])
def submit_form():
    """Handle form submission (webhook from Google Forms)."""
    data = request.get_json()

    submission = FormSubmission(
        form_id=data["form_id"],
        user_email=data["user_email"],
        responses=data["responses"],
        submitted_at=data.get("submitted_at"),
    )

    db.session.add(submission)
    db.session.commit()

    return jsonify(submission.to_dict()), 201


@forms_bp.route("/submissions/<form_id>", methods=["GET"])
@login_required
def get_form_submissions(form_id):
    """Get all submissions for a form."""
    if not current_user.is_senior_editor():
        return jsonify({"error": "Insufficient permissions"}), 403

    submissions = FormSubmission.query.filter_by(form_id=form_id).all()
    return jsonify([s.to_dict() for s in submissions])
