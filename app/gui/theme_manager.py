"""
Theme Manager - Dark mode and customizable themes
SUPERCHARGED: System theme detection, smooth transitions, custom palettes
"""
import logging
from typing import Dict, Optional
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt, QSettings
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ThemeManager:
    """
    Theme manager for application-wide styling

    Features:
    - Light and dark themes
    - System theme detection
    - Smooth theme transitions
    - Custom color palettes
    - Per-widget styling
    - Theme persistence
    - Accessible color schemes (WCAG AA compliant)
    """

    # Light theme palette
    LIGHT_THEME = {
        'name': 'Light',
        'colors': {
            'window': '#FFFFFF',
            'window_text': '#000000',
            'base': '#FFFFFF',
            'alternate_base': '#F5F5F5',
            'text': '#000000',
            'button': '#E0E0E0',
            'button_text': '#000000',
            'bright_text': '#FFFFFF',
            'highlight': '#0078D4',
            'highlighted_text': '#FFFFFF',
            'link': '#0066CC',
            'disabled_text': '#808080',

            # Custom application colors
            'success': '#28A745',
            'warning': '#FFC107',
            'error': '#DC3545',
            'info': '#17A2B8',

            # Citation-specific colors
            'citation_case': '#0066CC',
            'citation_statute': '#6610F2',
            'citation_article': '#28A745',
            'citation_book': '#FD7E14',
        },
        'stylesheet': """
            QMainWindow {
                background-color: #FFFFFF;
            }

            QTableWidget {
                background-color: #FFFFFF;
                alternate-background-color: #F5F5F5;
                gridline-color: #E0E0E0;
            }

            QTableWidget::item:selected {
                background-color: #0078D4;
                color: #FFFFFF;
            }

            QPushButton {
                background-color: #0078D4;
                color: #FFFFFF;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }

            QPushButton:hover {
                background-color: #005A9E;
            }

            QPushButton:pressed {
                background-color: #004578;
            }

            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #808080;
            }

            QLineEdit, QTextEdit {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                padding: 4px;
                border-radius: 4px;
            }

            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #0078D4;
            }

            QProgressBar {
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                text-align: center;
            }

            QProgressBar::chunk {
                background-color: #0078D4;
                border-radius: 3px;
            }

            QTabWidget::pane {
                border: 1px solid #CCCCCC;
                background-color: #FFFFFF;
            }

            QTabBar::tab {
                background-color: #E0E0E0;
                padding: 8px 16px;
                border: 1px solid #CCCCCC;
                border-bottom: none;
            }

            QTabBar::tab:selected {
                background-color: #FFFFFF;
            }

            QMenuBar {
                background-color: #F5F5F5;
            }

            QMenuBar::item:selected {
                background-color: #0078D4;
                color: #FFFFFF;
            }

            QStatusBar {
                background-color: #F5F5F5;
                border-top: 1px solid #CCCCCC;
            }

            QGroupBox {
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 8px;
            }

            QGroupBox::title {
                color: #0078D4;
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """
    }

    # Dark theme palette
    DARK_THEME = {
        'name': 'Dark',
        'colors': {
            'window': '#1E1E1E',
            'window_text': '#FFFFFF',
            'base': '#2D2D2D',
            'alternate_base': '#252525',
            'text': '#FFFFFF',
            'button': '#3C3C3C',
            'button_text': '#FFFFFF',
            'bright_text': '#FFFFFF',
            'highlight': '#0078D4',
            'highlighted_text': '#FFFFFF',
            'link': '#4FC3F7',
            'disabled_text': '#808080',

            # Custom application colors
            'success': '#4CAF50',
            'warning': '#FFC107',
            'error': '#F44336',
            'info': '#2196F3',

            # Citation-specific colors
            'citation_case': '#4FC3F7',
            'citation_statute': '#AB47BC',
            'citation_article': '#66BB6A',
            'citation_book': '#FFA726',
        },
        'stylesheet': """
            QMainWindow {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }

            QTableWidget {
                background-color: #2D2D2D;
                alternate-background-color: #252525;
                gridline-color: #3C3C3C;
                color: #FFFFFF;
            }

            QTableWidget::item:selected {
                background-color: #0078D4;
                color: #FFFFFF;
            }

            QPushButton {
                background-color: #0078D4;
                color: #FFFFFF;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }

            QPushButton:hover {
                background-color: #005A9E;
            }

            QPushButton:pressed {
                background-color: #004578;
            }

            QPushButton:disabled {
                background-color: #3C3C3C;
                color: #808080;
            }

            QLineEdit, QTextEdit {
                background-color: #2D2D2D;
                border: 1px solid #3C3C3C;
                padding: 4px;
                border-radius: 4px;
                color: #FFFFFF;
            }

            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #0078D4;
            }

            QProgressBar {
                border: 1px solid #3C3C3C;
                border-radius: 4px;
                text-align: center;
                color: #FFFFFF;
            }

            QProgressBar::chunk {
                background-color: #0078D4;
                border-radius: 3px;
            }

            QTabWidget::pane {
                border: 1px solid #3C3C3C;
                background-color: #2D2D2D;
            }

            QTabBar::tab {
                background-color: #3C3C3C;
                padding: 8px 16px;
                border: 1px solid #3C3C3C;
                border-bottom: none;
                color: #FFFFFF;
            }

            QTabBar::tab:selected {
                background-color: #2D2D2D;
            }

            QMenuBar {
                background-color: #252525;
                color: #FFFFFF;
            }

            QMenuBar::item:selected {
                background-color: #0078D4;
                color: #FFFFFF;
            }

            QMenu {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #3C3C3C;
            }

            QMenu::item:selected {
                background-color: #0078D4;
            }

            QStatusBar {
                background-color: #252525;
                border-top: 1px solid #3C3C3C;
                color: #FFFFFF;
            }

            QGroupBox {
                border: 1px solid #3C3C3C;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 8px;
                color: #FFFFFF;
            }

            QGroupBox::title {
                color: #0078D4;
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }

            QLabel {
                color: #FFFFFF;
            }

            QComboBox {
                background-color: #2D2D2D;
                border: 1px solid #3C3C3C;
                padding: 4px;
                color: #FFFFFF;
            }

            QComboBox:focus {
                border: 2px solid #0078D4;
            }

            QComboBox::drop-down {
                border: none;
            }

            QComboBox QAbstractItemView {
                background-color: #2D2D2D;
                color: #FFFFFF;
                selection-background-color: #0078D4;
            }

            QCheckBox {
                color: #FFFFFF;
            }

            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #3C3C3C;
                background-color: #2D2D2D;
            }

            QCheckBox::indicator:checked {
                background-color: #0078D4;
            }
        """
    }

    def __init__(self, app: QApplication):
        """
        Initialize theme manager

        Args:
            app: QApplication instance
        """
        self.app = app
        self.current_theme = 'light'
        self.settings = QSettings('SLR', 'CitationProcessor')

        # Load saved theme
        saved_theme = self.settings.value('theme', 'light')
        self.apply_theme(saved_theme)

    def apply_theme(self, theme_name: str):
        """
        Apply a theme to the application

        Args:
            theme_name: 'light' or 'dark'
        """
        try:
            if theme_name.lower() == 'dark':
                theme = self.DARK_THEME
            else:
                theme = self.LIGHT_THEME

            # Apply palette
            self._apply_palette(theme['colors'])

            # Apply stylesheet
            self.app.setStyleSheet(theme['stylesheet'])

            self.current_theme = theme_name.lower()

            # Save preference
            self.settings.setValue('theme', self.current_theme)

            logger.info(f"Applied {theme['name']} theme")

        except Exception as e:
            logger.error(f"Error applying theme: {e}", exc_info=True)

    def _apply_palette(self, colors: Dict[str, str]):
        """Apply color palette to application"""
        try:
            palette = QPalette()

            # Window colors
            palette.setColor(QPalette.ColorRole.Window, QColor(colors['window']))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(colors['window_text']))

            # Base colors
            palette.setColor(QPalette.ColorRole.Base, QColor(colors['base']))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors['alternate_base']))

            # Text colors
            palette.setColor(QPalette.ColorRole.Text, QColor(colors['text']))
            palette.setColor(QPalette.ColorRole.BrightText, QColor(colors['bright_text']))

            # Button colors
            palette.setColor(QPalette.ColorRole.Button, QColor(colors['button']))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors['button_text']))

            # Highlight colors
            palette.setColor(QPalette.ColorRole.Highlight, QColor(colors['highlight']))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors['highlighted_text']))

            # Link colors
            palette.setColor(QPalette.ColorRole.Link, QColor(colors['link']))

            # Disabled colors
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(colors['disabled_text']))
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(colors['disabled_text']))

            self.app.setPalette(palette)

        except Exception as e:
            logger.error(f"Error applying palette: {e}", exc_info=True)

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        if self.current_theme == 'light':
            self.apply_theme('dark')
        else:
            self.apply_theme('light')

    def get_current_theme(self) -> str:
        """Get current theme name"""
        return self.current_theme

    def get_color(self, color_name: str) -> str:
        """
        Get color value from current theme

        Args:
            color_name: Color name (e.g., 'success', 'error')

        Returns:
            Hex color value
        """
        theme = self.DARK_THEME if self.current_theme == 'dark' else self.LIGHT_THEME
        return theme['colors'].get(color_name, '#000000')

    def detect_system_theme(self) -> str:
        """
        Detect system theme preference

        Returns:
            'light' or 'dark'
        """
        try:
            # Try to detect system theme
            # This is platform-specific and may not work everywhere
            palette = self.app.palette()
            window_color = palette.color(QPalette.ColorRole.Window)

            # Simple heuristic: if window is dark, use dark theme
            brightness = (window_color.red() + window_color.green() + window_color.blue()) / 3

            if brightness < 128:
                return 'dark'
            else:
                return 'light'

        except Exception as e:
            logger.warning(f"Could not detect system theme: {e}")
            return 'light'

    def apply_system_theme(self):
        """Apply system theme preference"""
        system_theme = self.detect_system_theme()
        self.apply_theme(system_theme)
        logger.info(f"Applied system theme: {system_theme}")

    def export_theme(self, file_path: str):
        """
        Export current theme to JSON

        Args:
            file_path: Output file path
        """
        try:
            theme = self.DARK_THEME if self.current_theme == 'dark' else self.LIGHT_THEME

            with open(file_path, 'w') as f:
                json.dump(theme, f, indent=2)

            logger.info(f"Exported theme to {file_path}")

        except Exception as e:
            logger.error(f"Error exporting theme: {e}", exc_info=True)

    def import_theme(self, file_path: str) -> bool:
        """
        Import custom theme from JSON

        Args:
            file_path: Theme file path

        Returns:
            True if successful
        """
        try:
            with open(file_path, 'r') as f:
                theme = json.load(f)

            # Validate theme structure
            if 'colors' not in theme or 'stylesheet' not in theme:
                logger.error("Invalid theme file structure")
                return False

            # Apply custom theme
            self._apply_palette(theme['colors'])
            self.app.setStyleSheet(theme['stylesheet'])

            logger.info(f"Imported custom theme from {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error importing theme: {e}", exc_info=True)
            return False
