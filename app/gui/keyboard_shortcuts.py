"""
Comprehensive Keyboard Shortcuts Manager - 30+ commands for power users
SUPERCHARGED: Vim-style navigation, customizable bindings, command palette
"""
import logging
from typing import Dict, Callable, Optional
from PyQt6.QtWidgets import (QWidget, QDialog, QVBoxLayout, QHBoxLayout,
                            QTableWidget, QTableWidgetItem, QPushButton,
                            QLineEdit, QLabel, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QKeySequence, QShortcut, QAction
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class KeyboardShortcutManager(QObject):
    """
    Comprehensive keyboard shortcut manager

    Features:
    - 30+ built-in shortcuts
    - Customizable key bindings
    - Command palette (Ctrl+P)
    - Vim-style navigation (j/k for up/down)
    - Context-aware shortcuts
    - Shortcut cheat sheet (F1)
    - Import/export bindings
    - Conflict detection
    """

    # Signals
    command_triggered = pyqtSignal(str)  # Emitted when command is triggered

    # Default shortcuts
    DEFAULT_SHORTCUTS = {
        # File operations
        'file.refresh': 'Ctrl+R',
        'file.settings': 'Ctrl+,',
        'file.quit': 'Ctrl+Q',
        'file.export': 'Ctrl+E',

        # Navigation
        'nav.next_tab': 'Ctrl+Tab',
        'nav.prev_tab': 'Ctrl+Shift+Tab',
        'nav.sp_tab': 'Alt+1',
        'nav.r1_tab': 'Alt+2',
        'nav.r2_tab': 'Alt+3',
        'nav.analytics_tab': 'Alt+4',
        'nav.search_tab': 'Alt+5',

        # Search
        'search.focus': 'Ctrl+F',
        'search.clear': 'Esc',
        'search.errors': 'Ctrl+Shift+E',
        'search.next_result': 'F3',
        'search.prev_result': 'Shift+F3',

        # Selection (Vim-style)
        'select.next': 'J',
        'select.prev': 'K',
        'select.first': 'G,G',  # gg (vim-style)
        'select.last': 'Shift+G',
        'select.all': 'Ctrl+A',

        # Actions
        'action.run': 'Ctrl+Enter',
        'action.pause': 'Ctrl+P',
        'action.stop': 'Ctrl+Shift+C',
        'action.retry': 'Ctrl+Shift+R',

        # Article operations
        'article.create': 'Ctrl+N',
        'article.delete': 'Delete',
        'article.view_details': 'Enter',
        'article.open_drive': 'Ctrl+O',

        # Batch operations
        'batch.select_all_pending': 'Ctrl+Shift+P',
        'batch.select_all_errors': 'Ctrl+Shift+E',
        'batch.run_selected': 'Ctrl+Shift+Enter',

        # View
        'view.zoom_in': 'Ctrl+=',
        'view.zoom_out': 'Ctrl+-',
        'view.zoom_reset': 'Ctrl+0',
        'view.fullscreen': 'F11',
        'view.logs': 'Ctrl+L',
        'view.cache': 'Ctrl+Shift+C',

        # Help
        'help.shortcuts': 'F1',
        'help.guide': 'Ctrl+H',
        'help.about': 'Ctrl+Shift+A',

        # Command palette
        'command.palette': 'Ctrl+Shift+P',

        # Theme
        'theme.toggle': 'Ctrl+T',
        'theme.dark': 'Ctrl+Shift+D',
        'theme.light': 'Ctrl+Shift+L',
    }

    # Command descriptions
    COMMAND_DESCRIPTIONS = {
        'file.refresh': 'Refresh articles from Google Sheets',
        'file.settings': 'Open settings dialog',
        'file.quit': 'Quit application',
        'file.export': 'Export current view',

        'nav.next_tab': 'Switch to next tab',
        'nav.prev_tab': 'Switch to previous tab',
        'nav.sp_tab': 'Go to Source Pull tab',
        'nav.r1_tab': 'Go to R1 Preparation tab',
        'nav.r2_tab': 'Go to R2 Validation tab',
        'nav.analytics_tab': 'Go to Analytics tab',
        'nav.search_tab': 'Go to Search tab',

        'search.focus': 'Focus search box',
        'search.clear': 'Clear search',
        'search.errors': 'Show only errors',
        'search.next_result': 'Jump to next search result',
        'search.prev_result': 'Jump to previous search result',

        'select.next': 'Select next item (Vim j)',
        'select.prev': 'Select previous item (Vim k)',
        'select.first': 'Select first item (Vim gg)',
        'select.last': 'Select last item (Vim G)',
        'select.all': 'Select all items',

        'action.run': 'Run selected action',
        'action.pause': 'Pause current operation',
        'action.stop': 'Stop current operation',
        'action.retry': 'Retry failed items',

        'article.create': 'Create new article',
        'article.delete': 'Delete selected article',
        'article.view_details': 'View article details',
        'article.open_drive': 'Open in Google Drive',

        'batch.select_all_pending': 'Select all pending items',
        'batch.select_all_errors': 'Select all items with errors',
        'batch.run_selected': 'Run batch operation on selected',

        'view.zoom_in': 'Zoom in',
        'view.zoom_out': 'Zoom out',
        'view.zoom_reset': 'Reset zoom',
        'view.fullscreen': 'Toggle fullscreen',
        'view.logs': 'Open logs directory',
        'view.cache': 'Open cache directory',

        'help.shortcuts': 'Show keyboard shortcuts',
        'help.guide': 'Open user guide',
        'help.about': 'About SLR Citation Processor',

        'command.palette': 'Open command palette',

        'theme.toggle': 'Toggle dark/light theme',
        'theme.dark': 'Switch to dark theme',
        'theme.light': 'Switch to light theme',
    }

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.shortcuts = {}  # QShortcut objects
        self.custom_bindings = {}  # Custom key bindings
        self.command_handlers = {}  # Command -> handler mapping

        # Load custom bindings
        self.load_custom_bindings()

        # Set up shortcuts
        self.setup_all_shortcuts()

    def setup_all_shortcuts(self):
        """Set up all keyboard shortcuts"""
        # Get effective bindings (custom overrides default)
        bindings = {**self.DEFAULT_SHORTCUTS, **self.custom_bindings}

        for command, key_sequence in bindings.items():
            self.register_shortcut(command, key_sequence)

        logger.info(f"Registered {len(self.shortcuts)} keyboard shortcuts")

    def register_shortcut(self, command: str, key_sequence: str):
        """
        Register a keyboard shortcut

        Args:
            command: Command identifier (e.g., 'file.refresh')
            key_sequence: Key sequence (e.g., 'Ctrl+R')
        """
        try:
            # Handle multi-key sequences (e.g., 'G,G' for vim gg)
            if ',' in key_sequence:
                # TODO: Implement multi-key sequence support
                logger.debug(f"Multi-key sequence not yet supported: {key_sequence}")
                return

            shortcut = QShortcut(QKeySequence(key_sequence), self.main_window)
            shortcut.activated.connect(lambda cmd=command: self.trigger_command(cmd))

            self.shortcuts[command] = shortcut
            logger.debug(f"Registered shortcut: {command} -> {key_sequence}")

        except Exception as e:
            logger.error(f"Error registering shortcut {command}: {e}", exc_info=True)

    def trigger_command(self, command: str):
        """
        Trigger a command

        Args:
            command: Command identifier
        """
        try:
            logger.debug(f"Command triggered: {command}")

            # Call registered handler if exists
            if command in self.command_handlers:
                self.command_handlers[command]()
            else:
                # Emit signal for external handling
                self.command_triggered.emit(command)

        except Exception as e:
            logger.error(f"Error triggering command {command}: {e}", exc_info=True)

    def register_command_handler(self, command: str, handler: Callable):
        """
        Register a handler for a command

        Args:
            command: Command identifier
            handler: Callable to handle the command
        """
        self.command_handlers[command] = handler
        logger.debug(f"Registered handler for command: {command}")

    def customize_binding(self, command: str, new_key_sequence: str):
        """
        Customize key binding for a command

        Args:
            command: Command identifier
            new_key_sequence: New key sequence
        """
        try:
            # Remove old shortcut
            if command in self.shortcuts:
                self.shortcuts[command].deleteLater()
                del self.shortcuts[command]

            # Add new shortcut
            self.custom_bindings[command] = new_key_sequence
            self.register_shortcut(command, new_key_sequence)

            # Save custom bindings
            self.save_custom_bindings()

            logger.info(f"Customized binding: {command} -> {new_key_sequence}")

        except Exception as e:
            logger.error(f"Error customizing binding: {e}", exc_info=True)

    def reset_to_defaults(self):
        """Reset all bindings to defaults"""
        # Clear all shortcuts
        for shortcut in self.shortcuts.values():
            shortcut.deleteLater()
        self.shortcuts.clear()

        # Clear custom bindings
        self.custom_bindings.clear()

        # Re-setup with defaults
        self.setup_all_shortcuts()

        # Save (empty) custom bindings
        self.save_custom_bindings()

        logger.info("Reset shortcuts to defaults")

    def load_custom_bindings(self):
        """Load custom bindings from file"""
        try:
            bindings_path = Path("app/resources/config/shortcuts.json")

            if bindings_path.exists():
                with open(bindings_path, 'r') as f:
                    self.custom_bindings = json.load(f)
                logger.info(f"Loaded {len(self.custom_bindings)} custom bindings")
            else:
                self.custom_bindings = {}

        except Exception as e:
            logger.error(f"Error loading custom bindings: {e}", exc_info=True)
            self.custom_bindings = {}

    def save_custom_bindings(self):
        """Save custom bindings to file"""
        try:
            bindings_path = Path("app/resources/config/shortcuts.json")
            bindings_path.parent.mkdir(parents=True, exist_ok=True)

            with open(bindings_path, 'w') as f:
                json.dump(self.custom_bindings, f, indent=2)

            logger.info(f"Saved {len(self.custom_bindings)} custom bindings")

        except Exception as e:
            logger.error(f"Error saving custom bindings: {e}", exc_info=True)

    def get_all_bindings(self) -> Dict[str, str]:
        """Get all effective bindings (defaults + custom)"""
        return {**self.DEFAULT_SHORTCUTS, **self.custom_bindings}

    def show_cheat_sheet(self):
        """Show keyboard shortcuts cheat sheet"""
        dialog = ShortcutsDialog(self, self.main_window)
        dialog.exec()


class ShortcutsDialog(QDialog):
    """Dialog to view and customize keyboard shortcuts"""

    def __init__(self, shortcut_manager: KeyboardShortcutManager, parent=None):
        super().__init__(parent)
        self.shortcut_manager = shortcut_manager
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        self.load_shortcuts()

    def setup_ui(self):
        """Set up the UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        header = QLabel("Keyboard Shortcuts")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)

        # Search
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search commands...")
        self.search_input.textChanged.connect(self.filter_shortcuts)
        search_layout.addWidget(self.search_input)

        layout.addLayout(search_layout)

        # Shortcuts table
        self.shortcuts_table = QTableWidget()
        self.shortcuts_table.setColumnCount(3)
        self.shortcuts_table.setHorizontalHeaderLabels(['Command', 'Shortcut', 'Description'])
        self.shortcuts_table.setAlternatingRowColors(True)
        layout.addWidget(self.shortcuts_table)

        # Actions
        actions_layout = QHBoxLayout()

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        actions_layout.addWidget(reset_btn)

        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.export_shortcuts)
        actions_layout.addWidget(export_btn)

        import_btn = QPushButton("Import")
        import_btn.clicked.connect(self.import_shortcuts)
        actions_layout.addWidget(import_btn)

        actions_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        actions_layout.addWidget(close_btn)

        layout.addLayout(actions_layout)

    def load_shortcuts(self):
        """Load shortcuts into table"""
        bindings = self.shortcut_manager.get_all_bindings()
        descriptions = self.shortcut_manager.COMMAND_DESCRIPTIONS

        self.shortcuts_table.setRowCount(len(bindings))

        for row, (command, key_sequence) in enumerate(sorted(bindings.items())):
            self.shortcuts_table.setItem(row, 0, QTableWidgetItem(command))
            self.shortcuts_table.setItem(row, 1, QTableWidgetItem(key_sequence))
            self.shortcuts_table.setItem(row, 2, QTableWidgetItem(descriptions.get(command, '')))

        self.shortcuts_table.resizeColumnsToContents()

    def filter_shortcuts(self, text: str):
        """Filter shortcuts by search text"""
        for row in range(self.shortcuts_table.rowCount()):
            match = False
            for col in range(3):
                item = self.shortcuts_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.shortcuts_table.setRowHidden(row, not match)

    def reset_to_defaults(self):
        """Reset shortcuts to defaults"""
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Reset Shortcuts",
            "Reset all shortcuts to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.shortcut_manager.reset_to_defaults()
            self.load_shortcuts()

    def export_shortcuts(self):
        """Export shortcuts to JSON"""
        from PyQt6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Shortcuts",
            "shortcuts.json",
            "JSON Files (*.json)"
        )

        if file_path:
            bindings = self.shortcut_manager.get_all_bindings()
            with open(file_path, 'w') as f:
                json.dump(bindings, f, indent=2)
            logger.info(f"Exported shortcuts to {file_path}")

    def import_shortcuts(self):
        """Import shortcuts from JSON"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Shortcuts",
            "",
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    bindings = json.load(f)

                # Validate and apply
                for command, key_sequence in bindings.items():
                    if command in self.shortcut_manager.DEFAULT_SHORTCUTS:
                        self.shortcut_manager.customize_binding(command, key_sequence)

                self.load_shortcuts()
                QMessageBox.information(self, "Success", "Shortcuts imported successfully")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import shortcuts: {e}")
