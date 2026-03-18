"""
Custom Project Card Widget for Start Menu

Displays recent projects as interactive cards with sport-specific images.
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QMenu, QMessageBox
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QPoint

from gm_resources import GMessageBox

class ProjectCard(QFrame):
    """A custom card widget displaying a project with image, title, sport tag, description and date."""

    CARD_WIDTH = 300
    CARD_MIN_HEIGHT = 116
    CARD_MAX_HEIGHT = 136
    
    def __init__(self, projectData, parent=None, onOpen=None, onDeleteFile=None):
        super().__init__(parent)
        self.projectData = projectData
        self.onOpen = onOpen
        self.onDeleteFile = onDeleteFile
        self.setProperty("class", "ProjectCard")
        # Make sure stylesheet backgrounds actually paint for this widget.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(self.CARD_WIDTH, self.CARD_MIN_HEIGHT)
        self.setMaximumSize(self.CARD_WIDTH, self.CARD_MAX_HEIGHT)
        
        self._initUI()
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click on card."""
        if self.onOpen:
            self.onOpen(self._field("FN", ""))
        super().mouseDoubleClickEvent(event)
    
    def _initUI(self):
        """Initialize the card UI layout."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Content section with padding
        contentFrame = QFrame()
        contentFrame.setProperty("class", "ProjectCardContent")
        contentFrame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        contentLayout = QVBoxLayout()
        contentLayout.setContentsMargins(12, 8, 12, 8)
        contentLayout.setSpacing(4)
        
        # Header row: title + three-dots menu
        headerLayout = QHBoxLayout()
        headerLayout.setContentsMargins(0, 0, 0, 0)
        headerLayout.setSpacing(8)

        titleLabel = QLabel(self._field("Name", "Untitled"))
        titleLabel.setProperty("class", "CardTitle")
        titleFont = QFont()
        titleFont.setPointSize(14)
        titleFont.setBold(True)
        titleLabel.setFont(titleFont)
        titleLabel.setWordWrap(True)
        headerLayout.addWidget(titleLabel, 1)

        menuButton = QPushButton("...")
        menuButton.setCursor(Qt.CursorShape.PointingHandCursor)
        menuButton.setToolTip("Options")
        menuButton.setFixedWidth(28)
        menuButton.setFlat(True)
        menuButton.setStyleSheet("QPushButton{padding:0; border:none;}")
        headerLayout.addWidget(menuButton, 0, Qt.AlignmentFlag.AlignTop)

        menu = QMenu(menuButton)
        actionOpen = menu.addAction("Open")
        actionDelete = menu.addAction("Delete")
        menuButton.clicked.connect(lambda: menu.exec(menuButton.mapToGlobal(QPoint(0, menuButton.height()))))

        actionOpen.triggered.connect(self._openFromMenu)
        actionDelete.triggered.connect(self._deleteProjectFile)

        contentLayout.addLayout(headerLayout)
        
        # Sport tag and metadata on same row
        metaLayout = QHBoxLayout()
        metaLayout.setContentsMargins(0, 0, 0, 0)
        metaLayout.setSpacing(8)
        
        # Sport tag
        sport = self._getSportTag()
        sportKey = sport.replace(" ", "")
        sportLabel = QLabel(sport)
        # Only apply a specific sport style if the theme defines it; otherwise SportTag alone.
        if sportKey in ("Basketball", "Hockey", "Soccer"):
            sportLabel.setProperty("class", f"SportTag SportTag{sportKey}")
        else:
            sportLabel.setProperty("class", "SportTag")
        sportFont = QFont()
        sportFont.setPointSize(10)
        sportFont.setBold(True)
        sportLabel.setFont(sportFont)
        metaLayout.addWidget(sportLabel)
        metaLayout.addStretch()
        
        contentLayout.addLayout(metaLayout)
        
        # Description
        desc = str(self._field("Description", "")).strip()
        if desc:
            descLabel = QLabel(desc)
            descLabel.setProperty("class", "CardDescription")
            descFont = QFont()
            descFont.setPointSize(10)
            descLabel.setFont(descFont)
            descLabel.setWordWrap(True)
            descLabel.setMaximumHeight(36)
            contentLayout.addWidget(descLabel)
        
        # Date
        dateLabel = QLabel(f"Modified {self._field('Date', 'N/A')}")
        dateLabel.setProperty("class", "CardDate")
        dateFont = QFont()
        dateFont.setPointSize(9)
        dateLabel.setFont(dateFont)
        contentLayout.addWidget(dateLabel)
        
        contentFrame.setLayout(contentLayout)
        layout.addWidget(contentFrame)
        
        self.setLayout(layout)


    def _openFromMenu(self):
        if self.onOpen:
            self.onOpen(self._field("FN", ""))


    def _deleteProjectFile(self):
        fileName = str(self._field("FN", ""))
        if not fileName:
            GMessageBox("Delete Project", "No file path found for this project.", "Info", self).exec()
            return

        ask = GMessageBox(
            "Delete Project File",
            f"This will permanently delete:\n{fileName}\n\nContinue?",
            "AskYesNo",
            self,
        )

        if ask.exec() != QMessageBox.StandardButton.Yes:
            return

        try:
            import os
            if os.path.exists(fileName):
                os.remove(fileName)
            else:
                GMessageBox("Delete Project", "File does not exist on disk.", "Info", self).exec()
        except Exception as ex:
            GMessageBox("Delete Project", f"Failed to delete file.\n\n{ex}", "Info", self).exec()
            return

        # Remove from recent list after successful delete attempt
        if self.onDeleteFile:
            self.onDeleteFile(fileName)


    def _getSportTag(self) -> str:
        tag = str(self._field("Sport", "")).strip()
        if tag:
            return tag
        return self._extractSport()
    
    def _extractSport(self):
        """Extract sport type from project name or use default."""
        name = str(self._field("Name", "")).lower()
        
        # Simple heuristic to detect sport from project name
        if "basketball" in name:
            return "Basketball"
        elif "hockey" in name:
            return "Hockey"
        elif "soccer" in name or "football" in name:
            return "Soccer"
        elif "baseball" in name:
            return "Baseball"
        
        # Default fallback
        return "General"


    def _field(self, key: str, default=""):
        """Return a field from projectData (supports dict and Property)."""
        if self.projectData is None:
            return default

        if isinstance(self.projectData, dict):
            return self.projectData.get(key, default)

        # Project.getProperty returns a Property object that implements __getitem__
        try:
            value = self.projectData[key]
            return default if value is None else value
        except Exception:
            return default
