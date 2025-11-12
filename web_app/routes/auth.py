"""Authentication routes using Google OAuth 2.0."""

import json
import requests
from flask import Blueprint, redirect, request, url_for, session, current_app
from flask_login import login_user, logout_user, login_required
from oauthlib.oauth2 import WebApplicationClient

from ..models import db, User

auth_bp = Blueprint("auth", __name__)


def get_google_provider_cfg():
    """Get Google's OAuth 2.0 configuration."""
    return requests.get(current_app.config["GOOGLE_DISCOVERY_URL"]).json()


@auth_bp.route("/login")
def login():
    """Initiate Google OAuth login flow."""
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Create OAuth client
    client = WebApplicationClient(current_app.config["GOOGLE_CLIENT_ID"])

    # Prepare authorization request with domain hint
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=current_app.config["GOOGLE_REDIRECT_URI"],
        scope=["openid", "email", "profile"],
        hd=current_app.config["ALLOWED_DOMAIN"],  # Domain hint for stanford.edu
    )

    return redirect(request_uri)


@auth_bp.route("/callback")
def callback():
    """Handle OAuth callback from Google."""
    # Get authorization code from the callback
    code = request.args.get("code")

    # Get Google's token endpoint
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare token request
    client = WebApplicationClient(current_app.config["GOOGLE_CLIENT_ID"])
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )

    # Get tokens
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(
            current_app.config["GOOGLE_CLIENT_ID"],
            current_app.config["GOOGLE_CLIENT_SECRET"],
        ),
    )

    # Parse tokens
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Get user info
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # Verify email is from allowed domain
    user_info = userinfo_response.json()
    email = user_info.get("email")

    if not email:
        return "Email not provided by Google", 400

    # Verify domain
    domain = email.split("@")[-1]
    if domain != current_app.config["ALLOWED_DOMAIN"]:
        return f"Access denied. Email must be from {current_app.config['ALLOWED_DOMAIN']}", 403

    # Check if user exists in database
    user = User.query.filter_by(email=email).first()

    if not user:
        # Create new user if they don't exist
        user = User(
            email=email,
            full_name=user_info.get("name", ""),
            role="member_editor",  # Default role
        )
        db.session.add(user)
        db.session.commit()

    # Log the user in
    login_user(user)

    return redirect(url_for("dashboard.index"))


@auth_bp.route("/logout")
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    return redirect(url_for("dashboard.index"))


@auth_bp.route("/user")
@login_required
def get_current_user():
    """Get current user information."""
    from flask_login import current_user
    return current_user.to_dict()
