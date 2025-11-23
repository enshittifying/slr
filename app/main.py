"""
SLR Citation Processor - Desktop Application Entry Point
"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Add parent and current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from gui.main_window import MainWindow
from utils.logging import setup_logging
from utils.config import ConfigManager

def main():
    """Main entry point"""
    try:
        # Set up logging
        logger = setup_logging()
        logger.info("Starting SLR Citation Processor")

        # Load configuration
        config = ConfigManager()

        # Enable high DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("SLR Citation Processor")
        app.setOrganizationName("Stanford Law Review")

        # Create and show main window
        window = MainWindow(config)
        window.show()

        logger.info("Application started successfully")

        # Run event loop
        sys.exit(app.exec())

    except Exception as e:
        # Log the error if logger is available
        try:
            import logging
            logging.error(f"Fatal error starting application: {e}", exc_info=True)
        except:
            print(f"Fatal error starting application: {e}", file=sys.stderr)

        # Show error dialog to user
        try:
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Application Error")
            msg.setText("Failed to start SLR Citation Processor")
            msg.setInformativeText(str(e))
            msg.setDetailedText(f"{type(e).__name__}: {str(e)}")
            msg.exec()
        except:
            pass

        sys.exit(1)


if __name__ == "__main__":
    main()
