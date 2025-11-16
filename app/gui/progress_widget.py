"""
Reusable progress widget for displaying processing status
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QProgressBar,
                            QLabel, QTextEdit, QPushButton, QHBoxLayout)
from PyQt6.QtCore import Qt
from datetime import datetime


class ProgressWidget(QWidget):
    """Reusable widget for showing progress and status"""

    def __init__(self, title="Processing", parent=None):
        super().__init__(parent)
        self.title = title
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI components"""
        layout = QVBoxLayout()

        # Title label
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(self.title_label)

        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # Progress details (current/total)
        self.details_label = QLabel("0 / 0")
        layout.addWidget(self.details_label)

        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(200)
        layout.addWidget(self.log_display)

        # Control buttons
        button_layout = QHBoxLayout()

        self.pause_button = QPushButton("Pause")
        self.pause_button.setEnabled(False)
        button_layout.addWidget(self.pause_button)

        self.clear_log_button = QPushButton("Clear Log")
        self.clear_log_button.clicked.connect(self.clear_log)
        button_layout.addWidget(self.clear_log_button)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def update_progress(self, current, total, message=""):
        """
        Update progress display

        Args:
            current: Current item number
            total: Total items
            message: Status message
        """
        try:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)

            percentage = int((current / total * 100)) if total > 0 else 0
            self.progress_bar.setFormat(f"{percentage}%")

            self.details_label.setText(f"{current} / {total}")

            if message:
                self.status_label.setText(message)
                self.add_log(message)
        except Exception as e:
            # Fail silently for UI updates
            print(f"Error updating progress: {e}")

    def add_log(self, message):
        """
        Add message to log display

        Args:
            message: Message to add
        """
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_display.append(f"[{timestamp}] {message}")

            # Auto-scroll to bottom
            scrollbar = self.log_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            # Fail silently for UI updates
            print(f"Error adding log message: {e}")

    def clear_log(self):
        """Clear the log display"""
        self.log_display.clear()

    def set_title(self, title):
        """Set the title"""
        self.title = title
        self.title_label.setText(title)

    def set_status(self, status):
        """Set the status message"""
        self.status_label.setText(status)

    def reset(self):
        """Reset the progress display"""
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(100)
        self.details_label.setText("0 / 0")
        self.status_label.setText("Ready")

    def set_processing(self, processing=True):
        """
        Set processing state

        Args:
            processing: True if processing, False if stopped
        """
        self.pause_button.setEnabled(processing)

        if processing:
            self.status_label.setText("Processing...")
        else:
            self.status_label.setText("Stopped")

    def set_complete(self, success_count, fail_count):
        """
        Set completion state

        Args:
            success_count: Number of successful operations
            fail_count: Number of failed operations
        """
        self.status_label.setText(
            f"Complete: {success_count} succeeded, {fail_count} failed"
        )
        self.add_log(f"✓ Processing complete: {success_count} succeeded, {fail_count} failed")

    def set_error(self, error_message):
        """
        Set error state

        Args:
            error_message: Error message to display
        """
        self.status_label.setText(f"Error: {error_message}")
        self.status_label.setStyleSheet("color: red;")
        self.add_log(f"✗ Error: {error_message}")
