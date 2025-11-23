"""
Main application window
"""
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QStatusBar,
                            QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from pathlib import Path
import logging

from .sp_manager import SPManagerWidget
from .r1_manager import R1ManagerWidget
from .r2_manager import R2ManagerWidget
from .settings_dialog import SettingsDialog

from app.core.orchestrator import PipelineOrchestrator
from app.data.sheets_client import SheetsClient
from app.data.drive_client import DriveClient
from app.data.llm_client import create_llm_client
from app.utils.auth import ServiceAccountAuth

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.orchestrator = None
        self.setup_ui()
        self.initialize_services()

    def setup_ui(self):
        """Set up the UI components"""
        self.setWindowTitle("SLR Citation Processor")
        self.setMinimumSize(1200, 800)

        # Create menu bar
        self.create_menu_bar()

        # Create tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Status bar
        self.statusBar().showMessage("Ready")

        # Load stylesheet
        self.load_stylesheet()

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        refresh_action = QAction("&Refresh Articles", self)
        refresh_action.setShortcut("Ctrl+R")
        refresh_action.triggered.connect(self.refresh_articles)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        settings_action = QAction("&Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        logs_action = QAction("View &Logs", self)
        logs_action.triggered.connect(self.view_logs)
        view_menu.addAction(logs_action)

        cache_action = QAction("View &Cache", self)
        cache_action.triggered.connect(self.view_cache)
        view_menu.addAction(cache_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        user_guide_action = QAction("&User Guide", self)
        user_guide_action.setShortcut("F1")
        user_guide_action.triggered.connect(self.open_user_guide)
        help_menu.addAction(user_guide_action)

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def load_stylesheet(self):
        """Load Qt stylesheet"""
        try:
            style_path = Path(__file__).parent / "styles.qss"
            if style_path.exists():
                with open(style_path, 'r') as f:
                    self.setStyleSheet(f.read())
                logger.info("Loaded stylesheet")
        except Exception as e:
            logger.warning(f"Failed to load stylesheet: {e}")

    def initialize_services(self):
        """Initialize Google Sheets, Drive, and orchestrator"""
        try:
            self.statusBar().showMessage("Initializing services...")

            # Get credentials
            creds_path = self.config.get("paths.credentials")
            if not creds_path or not Path(creds_path).exists():
                QMessageBox.warning(
                    self,
                    "Setup Required",
                    "Service account not configured. Please configure in Settings."
                )
                self.open_settings()
                return

            # Initialize authentication
            auth = ServiceAccountAuth(creds_path)
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            credentials = auth.get_credentials(scopes)

            # Initialize Google Sheets client
            spreadsheet_id = self.config.get("google.spreadsheet_id")
            if not spreadsheet_id:
                raise ValueError("Google Sheets ID not configured")

            sheets_client = SheetsClient(credentials, spreadsheet_id)

            # Initialize Google Drive client
            drive_folder_id = self.config.get("google.drive_folder_id")
            if not drive_folder_id:
                raise ValueError("Google Drive folder ID not configured")

            drive_client = DriveClient(credentials, drive_folder_id)

            # Initialize LLM client
            llm_provider = self.config.get("llm.provider", "openai")
            llm_api_key = self.config.get("llm.api_key")
            llm_model = self.config.get("llm.model")

            if not llm_api_key:
                raise ValueError("LLM API key not configured")

            llm_client = create_llm_client(llm_provider, llm_api_key, llm_model)

            # Initialize orchestrator
            self.orchestrator = PipelineOrchestrator(
                sheets_client,
                drive_client,
                llm_client
            )

            # Create and add tabs
            self.tabs.addTab(SPManagerWidget(self.orchestrator), "Source Pull")
            self.tabs.addTab(R1ManagerWidget(self.orchestrator), "R1 Preparation")
            self.tabs.addTab(R2ManagerWidget(self.orchestrator), "R2 Validation")

            self.statusBar().showMessage("Services initialized successfully")
            logger.info("Services initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing services: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"Failed to initialize services: {str(e)}\n\n"
                "Please check your settings."
            )
            self.statusBar().showMessage("Initialization failed")

    def refresh_articles(self):
        """Refresh articles in all tabs"""
        try:
            self.statusBar().showMessage("Refreshing articles...")

            # Refresh each tab
            for i in range(self.tabs.count()):
                widget = self.tabs.widget(i)
                if hasattr(widget, 'load_articles'):
                    widget.load_articles()

            self.statusBar().showMessage("Articles refreshed")
            logger.info("Articles refreshed")

        except Exception as e:
            logger.error(f"Error refreshing articles: {e}", exc_info=True)
            QMessageBox.critical(self, "Error",
                               f"Failed to refresh articles: {str(e)}")

    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            # Settings were saved, reinitialize services
            reply = QMessageBox.question(
                self,
                "Restart Required",
                "Settings saved. Restart application to apply changes?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Reinitialize
                self.tabs.clear()
                self.initialize_services()

    def view_logs(self):
        """Open logs directory"""
        import subprocess
        import platform

        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(logs_dir)])
            elif platform.system() == "Windows":
                subprocess.run(["explorer", str(logs_dir)])
            else:  # Linux
                subprocess.run(["xdg-open", str(logs_dir)])

            logger.info("Opened logs directory")

        except Exception as e:
            logger.error(f"Error opening logs directory: {e}", exc_info=True)
            QMessageBox.information(self, "Logs Location",
                                  f"Logs directory: {logs_dir.absolute()}")

    def view_cache(self):
        """Open cache directory"""
        import subprocess
        import platform

        cache_dir = Path("cache")
        cache_dir.mkdir(exist_ok=True)

        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(cache_dir)])
            elif platform.system() == "Windows":
                subprocess.run(["explorer", str(cache_dir)])
            else:  # Linux
                subprocess.run(["xdg-open", str(cache_dir)])

            logger.info("Opened cache directory")

        except Exception as e:
            logger.error(f"Error opening cache directory: {e}", exc_info=True)
            QMessageBox.information(self, "Cache Location",
                                  f"Cache directory: {cache_dir.absolute()}")

    def open_user_guide(self):
        """Open user guide"""
        QMessageBox.information(
            self,
            "User Guide",
            "SLR Citation Processor - User Guide\n\n"
            "1. Configure settings (File → Settings)\n"
            "2. Run Source Pull (SP tab)\n"
            "3. Run R1 Preparation (R1 tab)\n"
            "4. Run R2 Validation (R2 tab)\n\n"
            "For detailed documentation, see README.md"
        )

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About SLR Citation Processor",
            "SLR Citation Processor v1.0\n\n"
            "Desktop application for Stanford Law Review citation processing.\n\n"
            "© 2024 Stanford Law Review\n\n"
            "Built with PyQt6, SLRinator, and Claude AI"
        )

    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            logger.info("Application closing")
            event.accept()
        else:
            event.ignore()
