#!/usr/bin/env python
"""Initialize the database with tables and optional seed data."""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_app import create_app
from web_app.models import db, User, SystemConfig
from datetime import datetime


def init_database(seed_data=False):
    """Initialize database tables and optionally seed with test data."""
    app = create_app()

    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✓ Database tables created successfully!")

        if seed_data:
            print("\nSeeding database with test data...")

            # Create a test admin user
            admin = User(
                email="admin@stanford.edu",
                full_name="Test Admin",
                role="admin",
            )
            db.session.add(admin)

            # Add system configuration
            SystemConfig.set_value(
                "google_calendar_id",
                os.getenv("GOOGLE_CALENDAR_ID", "test-calendar-id"),
                "ID of the shared Google Calendar",
            )

            SystemConfig.set_value(
                "google_drive_folder_id",
                os.getenv("GOOGLE_DRIVE_FOLDER_ID", "test-folder-id"),
                "ID of the Google Drive folder for PDFs",
            )

            db.session.commit()
            print("✓ Test data seeded successfully!")

        print("\n✅ Database initialization complete!")


if __name__ == "__main__":
    seed = "--seed" in sys.argv
    init_database(seed_data=seed)
