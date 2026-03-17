"""
Developed By: JumpShot Team
Written by: riscyseven
"""

from PyQt6.QtWidgets import QWidget, QListWidgetItem, QTreeWidgetItem, QHeaderView
from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from gm_resources import resourcePath
from attr import StartMenuAttr
from progsetting import ProgSetting

class StartMenu(QWidget):
    def __init__(self, newCallBack, openCallBack, parent=None):
        super().__init__(parent) # Call the inherited classes __init__ method
        self.newCallBack = newCallBack
        self.openCallBack = openCallBack
        self.templateMap = {}
        self.recentProjects = []
        self._initUI()


    def _initUI(self):
        """
        Initializes the startmenu UI.

        :param: none
        :return: none
        """
        path = resourcePath("src/window/ui/startmenu.ui")
        uic.loadUi(path, self) # Load the .ui file
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


    def resizeEvent(self, evt):
        """
        Handle resize - columns auto-stretch via QHeaderView.
        """
        super().resizeEvent(evt)


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
            for proj in setting.getRecentlyOpened().values():
                item = QTreeWidgetItem()
                for i in range(5):
                    item.setTextAlignment(i, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

                tempProj = proj.getProperty()

                item.setText(0, tempProj["Name"])
                item.setText(1, tempProj["Author"])
                item.setText(2, tempProj["Version"])
                item.setText(3, tempProj["FN"])
                item.setText(4, tempProj["Date"])
                self.treeWidget.addTopLevelItem(item)
                self.recentProjects.append(tempProj)
        except:
            pass

    def _filterProjects(self, text: str):
        """
        Filters the recent projects based on search text.

        :param text: search query
        :return: none
        """
        searchText = text.lower().strip()
        
        # Filter tree widget items (skip the first "Open Existing File" item)
        for i in range(self.treeWidget.topLevelItemCount()):
            item = self.treeWidget.topLevelItem(i)
            if i == 0:  # Skip the "Open Existing File" header
                item.setHidden(False)
                continue
            
            # Check if search text matches any column
            matches = False
            for col in range(self.treeWidget.columnCount()):
                if searchText in item.text(col).lower():
                    matches = True
                    break
            
            item.setHidden(not matches if searchText else False)

    def refresh(self):
        """
        Refreshes the recent projects list.
        
        :param: none
        :return: none
        """
        # Clear existing items except the first "Open Existing File" header
        while self.treeWidget.topLevelItemCount() > 1:
            self.treeWidget.takeTopLevelItem(1)
        
        # Reload recent projects
        self._loadRecent()