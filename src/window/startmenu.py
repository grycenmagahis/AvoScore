"""Main menu / start screen.

Displays recent projects in a card grid with sport images.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QListWidgetItem,
    QTreeWidgetItem,
    QHeaderView,
    QGridLayout,
    QSizePolicy,
)
from PyQt6 import uic
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

from gm_resources import resourcePath
from attr import StartMenuAttr
from progsetting import ProgSetting
from window.projectcard import ProjectCard, NewProjectCard
from fileio.startfile import StartFile

class StartMenu(QWidget):
    def __init__(self, newCallBack, openCallBack, parent=None):
        super().__init__(parent) # Call the inherited classes __init__ method
        self.newCallBack = newCallBack
        self.openCallBack = openCallBack
        self.templateMap = {}
        self.recentProjects = []
        self._cardWidgets = []
        self._cardGrid = None
        self._cardsContainer = None
        self._gridColumns = 0
        self._initUI()


    def _initUI(self):
        """
        Initializes the startmenu UI.

        :param: none
        :return: none
        """
        path = resourcePath("src/window/ui/startmenu.ui")
        uic.loadUi(path, self) # Load the .ui file

        # Style hooks (Qt stylesheet uses the dynamic "class" property)
        self.setProperty("class", "StartMenu")
        try:
            self.searchFrame.setProperty("class", "HeaderBar")
        except Exception:
            pass
        self.searchBar.setProperty("class", "SearchBar")
        self.scrollArea.setProperty("class", "CardsContainer")
        self.scrollArea.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # Hide legacy widgets to match the requested card-style start screen.
        # (New/Open actions remain available in the main window menu.)
        try:
            self.newProjectLabel.setVisible(False)
            self.listWidget.setVisible(False)
            self.treeWidget.setVisible(False)
        except Exception:
            pass

        # Card grid container (inserted where the old tree widget lived)
        self._cardsContainer = QWidget(self.scrollAreaContents)
        self._cardsContainer.setProperty("class", "CardsContainer")
        self._cardsContainer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._cardGrid = QGridLayout(self._cardsContainer)
        self._cardGrid.setContentsMargins(0, 0, 0, 0)
        self._cardGrid.setHorizontalSpacing(16)
        self._cardGrid.setVerticalSpacing(16)
        self._cardGrid.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # Insert cards container after the "Recent Projects" label.
        # If the UI changes, fall back to appending at the bottom.
        inserted = False
        try:
            idx = self.scrollLayout.indexOf(self.recentLabel)
            if idx != -1:
                self.scrollLayout.insertWidget(idx + 1, self._cardsContainer)
                inserted = True
        except Exception:
            inserted = False
        if not inserted:
            self.scrollLayout.addWidget(self._cardsContainer)

        self.treeWidget.setProperty("class", "StartTreeWidget")
        self.treeWidget.header().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # All columns stretch to fill the full width
        header = self.treeWidget.header()
        header.setStretchLastSection(False)
        for i in range(5):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        
        self.listWidget.itemDoubleClicked.connect(self._newTemplateClicked)
        self.treeWidget.itemDoubleClicked.connect(self._openTemplateClicked)
        
        # Connect search bar
        self.searchBar.textChanged.connect(self._filterProjects)
        
        self._loadStartFile()
        self.treeWidget.topLevelItem(0).setTextAlignment(0, Qt.AlignmentFlag.AlignLeft)

        # Initial layout of cards
        self._rebuildCards()
        QTimer.singleShot(0, self._reflowCards)


    def _loadStartFile(self):
        """
        Loads the start file into the start menu

        :param: none
        :return: none
        """
        self.templateList = StartMenuAttr.templateList
        self._loadTemplates()
        self._loadRecent()


    def _newTemplateClicked(self, item: QListWidgetItem):
        if (item.text() == "New Project"):
            self.newCallBack()
        else:
            self.openCallBack(None, StartMenuAttr.templateList[item.text()][StartMenuAttr.FILE])


    def _openTemplateClicked(self, item: QTreeWidgetItem):
        self.openCallBack(None, item.text(3))


    def _loadTemplates(self):
        """
        Loads the templates into the start menu

        :param templates: dictionary of templates
        :return: none
        """
        for value in self.templateList.values():
            try:
                self.listWidget.addItem(QListWidgetItem(QIcon(resourcePath(value[StartMenuAttr.ICON])),
                 value[StartMenuAttr.NAME]))
            except FileNotFoundError:
                try:
                    self.listWidget.addItem(QListWidgetItem(QIcon(value[StartMenuAttr.ICON]),
                     value[StartMenuAttr.NAME]))
                except FileNotFoundError:
                    self.listWidget.addItem(QListWidgetItem(value[StartMenuAttr.NAME]))


    def _loadRecent(self) -> None:
        """
        Loads the recent projects into the start menu

        :param recent: dictionary of recent projects
        :return: none
        """

        try:
            setting = ProgSetting()
            self.recentProjects = []

            # Preserve the existing tree population (even though it's hidden) to avoid
            # breaking any other code that might still rely on it.
            for proj in setting.getRecentlyOpened().values():
                tempProj = proj.getProperty()
                self.recentProjects.append(tempProj)

                try:
                    item = QTreeWidgetItem()
                    for i in range(5):
                        item.setTextAlignment(i, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    item.setText(0, str(self._projField(tempProj, "Name", "")))
                    item.setText(1, str(self._projField(tempProj, "Author", "")))
                    item.setText(2, str(self._projField(tempProj, "Version", "")))
                    item.setText(3, str(self._projField(tempProj, "FN", "")))
                    item.setText(4, str(self._projField(tempProj, "Date", "")))
                    self.treeWidget.addTopLevelItem(item)
                except Exception:
                    pass
        except Exception:
            self.recentProjects = []

        self._rebuildCards()


    def _clearCardGrid(self):
        if self._cardGrid is None:
            return

        while self._cardGrid.count():
            item = self._cardGrid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)


    def _calcColumns(self) -> int:
        # Target card width aligned with ProjectCard min/max sizing.
        targetCardWidth = getattr(ProjectCard, "CARD_WIDTH", 340)
        gap = 16

        viewportWidth = 0
        try:
            viewportWidth = self.scrollArea.viewport().contentsRect().width()
        except Exception:
            viewportWidth = 0
        if viewportWidth <= 0:
            viewportWidth = self.width()

        usable = max(1, int(viewportWidth))
        cols = max(1, usable // (targetCardWidth + gap))
        return int(cols)


    def _reflowCards(self):
        if self._cardGrid is None:
            return

        cols = self._calcColumns()
        if cols == self._gridColumns and self._cardGrid.count() == len(self._cardWidgets):
            return
        self._gridColumns = cols

        self._clearCardGrid()

        # Ensure trailing space goes to the right, keeping cards left-aligned.
        # Reset any previous stretches.
        for i in range(max(self._gridColumns, 1) + 2):
            try:
                self._cardGrid.setColumnStretch(i, 0)
            except Exception:
                pass
        try:
            self._cardGrid.setColumnStretch(cols, 1)
        except Exception:
            pass

        for i, card in enumerate(self._cardWidgets):
            row = i // cols
            col = i % cols
            self._cardGrid.addWidget(card, row, col)


    def _rebuildCards(self, projects=None):
        if projects is None:
            projects = self.recentProjects

        # Clear old cards
        for card in self._cardWidgets:
            card.setParent(None)
        self._cardWidgets = []
        self._clearCardGrid()

        # Recreate cards
        newCard = NewProjectCard(parent=self._cardsContainer, onNew=self.newCallBack)
        self._cardWidgets.append(newCard)
        for proj in projects:
            card = ProjectCard(
                proj,
                parent=self._cardsContainer,
                onOpen=lambda fn: self.openCallBack(None, fn),
                onDeleteFile=self._removeRecent,
            )
            self._cardWidgets.append(card)

        self._reflowCards()

    def _filterProjects(self, text: str):
        """
        Filters the recent projects based on search text.

        :param text: search query
        :return: none
        """
        searchText = text.lower().strip()

        if not searchText:
            self._rebuildCards(self.recentProjects)
            return

        filtered = []
        for proj in self.recentProjects:
            hay = " ".join(
                [
                    str(self._projField(proj, "Name", "")),
                    str(self._projField(proj, "Author", "")),
                    str(self._projField(proj, "Version", "")),
                    str(self._projField(proj, "Date", "")),
                    str(self._projField(proj, "Sport", "")),
                    str(self._projField(proj, "Description", "")),
                ]
            ).lower()
            if searchText in hay:
                filtered.append(proj)

        self._rebuildCards(filtered)

    def refresh(self):
        """
        Refreshes the recent projects list.
        
        :param: none
        :return: none
        """
        # Clear existing items except the first "Open Existing File" header
        while self.treeWidget.topLevelItemCount() > 1:
            self.treeWidget.takeTopLevelItem(1)

        # Reload recent projects and rebuild cards
        self._loadRecent()


    def _removeRecent(self, fileName: str):
        """Remove a recent project entry and refresh the cards."""
        if not fileName:
            return
        try:
            setting = ProgSetting()
            if fileName in setting.getRecentlyOpened():
                setting.removeRecentlyOpened(fileName)
            StartFile().save()
        except Exception:
            pass

        self.refresh()

        # Update main window status bar count if available
        try:
            win = self.window()
            if hasattr(win, "_updateStatusBar"):
                win._updateStatusBar()
        except Exception:
            pass


    def _projField(self, proj, key: str, default=""):
        """Read a field from either dict-like or Property-like project data."""
        if proj is None:
            return default

        if isinstance(proj, dict):
            return proj.get(key, default)

        # Property implements __getitem__ (e.g. proj["Name"])
        try:
            value = proj[key]
            return default if value is None else value
        except Exception:
            return default


    def resizeEvent(self, evt):
        super().resizeEvent(evt)
        self._reflowCards()


    def showEvent(self, evt):
        super().showEvent(evt)
        QTimer.singleShot(0, self._reflowCards)