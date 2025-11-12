"""System configuration model."""

from sqlalchemy import PrimaryKeyConstraint
from .base import db


class SystemConfig(db.Model):
    """
    System Configuration model for storing key-value settings.
    """

    __tablename__ = "system_config"

    key = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, nullable=False)

    __table_args__ = (PrimaryKeyConstraint("key", name="pk_system_config"),)

    def __repr__(self):
        return f"<SystemConfig {self.key}={self.value}>"

    def to_dict(self):
        """Convert config to dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_value(cls, key: str, default=None):
        """Get a configuration value by key."""
        config = cls.query.filter_by(key=key).first()
        return config.value if config else default

    @classmethod
    def set_value(cls, key: str, value: str, description: str = None):
        """Set or update a configuration value."""
        from datetime import datetime

        config = cls.query.filter_by(key=key).first()
        if config:
            config.value = value
            config.updated_at = datetime.utcnow()
            if description:
                config.description = description
        else:
            config = cls(
                key=key,
                value=value,
                description=description,
                updated_at=datetime.utcnow(),
            )
            db.session.add(config)
        db.session.commit()
        return config
