"""
Settings dialog for application configuration
"""
from PyQt6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QPushButton,
                            QComboBox, QFileDialog, QVBoxLayout, QHBoxLayout,
                            QLabel, QDialogButtonBox, QMessageBox)
from PyQt6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """Settings configuration dialog"""

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Set up the UI components"""
        layout = QVBoxLayout()

        # Form layout for settings
        form_layout = QFormLayout()

        # Google Sheets settings
        form_layout.addRow(QLabel("<b>Google Sheets</b>"))

        self.sheet_id_input = QLineEdit()
        self.sheet_id_input.setPlaceholderText("Google Sheets ID from URL")
        form_layout.addRow("Master Sheet ID:", self.sheet_id_input)

        # Google Drive settings
        form_layout.addRow(QLabel("<b>Google Drive</b>"))

        self.drive_folder_input = QLineEdit()
        self.drive_folder_input.setPlaceholderText("Google Drive Folder ID")
        form_layout.addRow("Drive Folder ID:", self.drive_folder_input)

        # LLM settings
        form_layout.addRow(QLabel("<b>LLM Configuration</b>"))

        self.llm_provider = QComboBox()
        self.llm_provider.addItems(["openai", "anthropic"])
        self.llm_provider.currentTextChanged.connect(self.on_provider_changed)
        form_layout.addRow("LLM Provider:", self.llm_provider)

        self.llm_model = QComboBox()
        form_layout.addRow("Model:", self.llm_model)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("API Key")
        form_layout.addRow("API Key:", self.api_key_input)

        # Service Account settings
        form_layout.addRow(QLabel("<b>Authentication</b>"))

        sa_layout = QHBoxLayout()
        self.sa_path_label = QLabel("Not configured")
        self.sa_browse_btn = QPushButton("Browse...")
        self.sa_browse_btn.clicked.connect(self.browse_service_account)
        sa_layout.addWidget(self.sa_path_label)
        sa_layout.addWidget(self.sa_browse_btn)
        form_layout.addRow("Service Account:", sa_layout)

        # Processing settings
        form_layout.addRow(QLabel("<b>Processing</b>"))

        self.max_concurrent_input = QLineEdit()
        self.max_concurrent_input.setPlaceholderText("5")
        form_layout.addRow("Max Concurrent Downloads:", self.max_concurrent_input)

        self.retry_attempts_input = QLineEdit()
        self.retry_attempts_input.setPlaceholderText("3")
        form_layout.addRow("Retry Attempts:", self.retry_attempts_input)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.RestoreDefaults
        )
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(
            self.restore_defaults
        )

        layout.addWidget(button_box)

        self.setLayout(layout)

    def on_provider_changed(self, provider):
        """Update model options when provider changes"""
        self.llm_model.clear()

        if provider == "openai":
            self.llm_model.addItems([
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo"
            ])
        elif provider == "anthropic":
            self.llm_model.addItems([
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229",
                "claude-3-haiku-20240307"
            ])

    def load_settings(self):
        """Load current settings from config"""
        # Google settings
        self.sheet_id_input.setText(self.config.get("google.spreadsheet_id", ""))
        self.drive_folder_input.setText(self.config.get("google.drive_folder_id", ""))

        # LLM settings
        provider = self.config.get("llm.provider", "openai")
        index = self.llm_provider.findText(provider)
        if index >= 0:
            self.llm_provider.setCurrentIndex(index)

        self.on_provider_changed(provider)

        model = self.config.get("llm.model", "")
        if model:
            index = self.llm_model.findText(model)
            if index >= 0:
                self.llm_model.setCurrentIndex(index)

        self.api_key_input.setText(self.config.get("llm.api_key", ""))

        # Service account
        sa_path = self.config.get("paths.credentials", "")
        if sa_path:
            self.sa_path_label.setText(sa_path)

        # Processing
        self.max_concurrent_input.setText(
            str(self.config.get("processing.max_concurrent_downloads", 5))
        )
        self.retry_attempts_input.setText(
            str(self.config.get("processing.retry_attempts", 3))
        )

    def save_settings(self):
        """Save settings to config"""
        try:
            # Validate required fields
            if not self.sheet_id_input.text():
                QMessageBox.warning(self, "Validation Error",
                                  "Master Sheet ID is required")
                return

            if not self.drive_folder_input.text():
                QMessageBox.warning(self, "Validation Error",
                                  "Drive Folder ID is required")
                return

            if not self.api_key_input.text():
                QMessageBox.warning(self, "Validation Error",
                                  "API Key is required")
                return

            # Update config
            updates = {
                "google": {
                    "spreadsheet_id": self.sheet_id_input.text(),
                    "drive_folder_id": self.drive_folder_input.text()
                },
                "llm": {
                    "provider": self.llm_provider.currentText(),
                    "model": self.llm_model.currentText(),
                    "api_key": self.api_key_input.text()
                },
                "processing": {
                    "max_concurrent_downloads": int(self.max_concurrent_input.text() or 5),
                    "retry_attempts": int(self.retry_attempts_input.text() or 3)
                }
            }

            self.config.update(updates)
            self.config.save_config()

            logger.info("Settings saved successfully")
            QMessageBox.information(self, "Success", "Settings saved successfully!")

            self.accept()

        except Exception as e:
            logger.error(f"Error saving settings: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

    def browse_service_account(self):
        """Browse for service account JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Service Account JSON",
            "",
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                # Set up encrypted credentials
                from app.utils.auth import ServiceAccountAuth
                output_path = self.config.get("paths.credentials")

                message = ServiceAccountAuth.setup_encrypted_credentials(
                    file_path,
                    output_path
                )

                self.sa_path_label.setText(output_path)
                QMessageBox.information(self, "Success", message)

                logger.info(f"Service account configured: {output_path}")

            except Exception as e:
                logger.error(f"Error setting up service account: {e}", exc_info=True)
                QMessageBox.critical(self, "Error",
                                   f"Failed to set up service account: {str(e)}")

    def restore_defaults(self):
        """Restore default settings"""
        reply = QMessageBox.question(
            self,
            "Restore Defaults",
            "Are you sure you want to restore default settings?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.config.reset_to_defaults()
            self.load_settings()
            logger.info("Settings restored to defaults")
            QMessageBox.information(self, "Success", "Settings restored to defaults")
