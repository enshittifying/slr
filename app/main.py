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


if __name__ == "__main__":
    main()
