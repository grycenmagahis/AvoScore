"""
Developed By: JumpShot Team
Written by: riscyseven
"""

from PyQt6 import QtWidgets, uic
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt

from window.editor import Editor
from window.startmenu import StartMenu
from window.settings import Settings
from window.about import About
from window.tabdialog import TabDialog
from fileio.projectfile import ProjectFile
from fileio.startfile import StartFile
from project import Project
from progsetting import ProgSetting

from gm_resources import resourcePath, GMessageBox # Importing my PyInstaller resource manager

VERSION = "1.0.3"

class MainWindow(QtWidgets.QMainWindow):
    """
    This class contains the main window of the application.
    Contains the main toolbar and diverts the program to the right functionality.
    """

    def __init__(self, parent=None):
        super().__init__(parent) # Call the inherited classes __init__ method
        
        ProgSetting().loadProperties("required/data.json")
        StartFile().load()
        self.project = None
        self.tabWidget = None
        self.editor = None
        self._initUI()
        self.dialogs = []


    def _initUI(self):
        path = resourcePath("src/window/ui/mainwindow.ui") # replaced complicated path logic with resourcePath()
        uic.loadUi(path, self) # Load the .ui file
        self.setWindowTitle("AvoScore")
        self.setWindowIcon(QIcon(resourcePath("src/resources/icon.ico"))) # Using a slightly modified version of my PyInstaller Resource system. Also seen on line 18. Basically uses working directory OR temp directory for absolute paths to files.
        
        # Set minimum window size
        self.setMinimumSize(900, 650)
        
        # Add Avolution logo to menu bar (centered)
        self._setupLogoInMenuBar()
        
        self.show() # Show the GUI

        # Setting up the toolbar with app branding
        self.toolBar.addWidget(QtWidgets.QPushButton(QIcon(resourcePath("src/resources/icon.ico")),
         f" AvoScore v{VERSION}"))
        self.toolBar.addSeparator()
        self.editModeButton = QtWidgets.QPushButton("Editor Mode")
        self.toolBar.addWidget(self.editModeButton)
        self.editModeButton.setEnabled(False)
        self.editModeButton.clicked.connect(self._editModeClicked)

        self.toolBar.addSeparator()

        self.popOutButton = QtWidgets.QPushButton("Pop Out Tab")
        self.toolBar.addWidget(self.popOutButton)
        self.popOutButton.setEnabled(False)
        self.popOutButton.clicked.connect(self._popOutClicked)

        self.actionSaveAs.triggered.connect(self._saveAsTriggered)
        self.actionOpen.triggered.connect(self._openTriggered)
        self.actionNew.triggered.connect(self._newTriggered)
        self.actionSave.triggered.connect(self._saveTriggered)
        self.actionProgSet.triggered.connect(self._settingsTriggered)
        self.actionProjSet.triggered.connect(self._projSettingsTriggered)
        self.actionAbout.triggered.connect(self._aboutTriggered)
        self.actionHome.triggered.connect(self._homeTriggered)
        self.actionClose.triggered.connect(self._closeProjectTriggered)

        self.actionSave.setEnabled(False)
        self.actionSaveAs.setEnabled(False)
        self.actionProjSet.setEnabled(False)
        self.actionClose.setEnabled(False)

        self.toolBar.setVisible(False)

        # Setup status bar
        self._setupStatusBar()

        self.startMenu = StartMenu(self._newTriggered, self._openTriggered)
        self.setCentralWidget(self.startMenu)
        self._windowChanged()
        self._updateStatusBar()

    def _setupLogoInMenuBar(self):
        """Add Avolution logo to the right side of the menu bar."""
        # Create a widget to hold the logo
        logoWidget = QtWidgets.QWidget()
        logoLayout = QtWidgets.QHBoxLayout(logoWidget)
        logoLayout.setContentsMargins(0, 0, 10, 0)
        
        # Add spacer to push logo to center/right
        logoLayout.addStretch()
        
        # Create logo label
        logoLabel = QtWidgets.QLabel()
        try:
            pixmap = QPixmap(resourcePath("src/resources/avolution_logo.png"))
            # Scale the logo to fit nicely in the menu bar (height ~24px)
            scaledPixmap = pixmap.scaledToHeight(24, Qt.TransformationMode.SmoothTransformation)
            logoLabel.setPixmap(scaledPixmap)
        except:
            logoLabel.setText("AVOLUTION")
            logoLabel.setStyleSheet("color: #C41E3A; font-weight: bold; font-size: 14px;")
        
        logoLayout.addWidget(logoLabel)
        
        # Add the logo widget to the menu bar
        self.menubar.setCornerWidget(logoWidget, Qt.Corner.TopRightCorner)

    def _setupStatusBar(self):
        """Setup the status bar with project count and version."""
        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Left side - project count
        self.projectCountLabel = QtWidgets.QLabel("0 projects")
        self.statusBar.addWidget(self.projectCountLabel)
        
        # Right side - version info
        self.versionLabel = QtWidgets.QLabel(f"AvoScore v{VERSION} - Open-source Livestream Scoring Utility")
        self.statusBar.addPermanentWidget(self.versionLabel)

    def _updateStatusBar(self, count=None):
        """Update the project count in the status bar."""
        if count is None:
            try:
                setting = ProgSetting()
                count = len(setting.getRecentlyOpened())
            except:
                count = 0
        self.projectCountLabel.setText(f"{count} project{'s' if count != 1 else ''}")


    def _newTriggered(self):
        self._removeAllDialog()
        self.editor = Editor()
        self.actionSave.setEnabled(True)
        self.actionSaveAs.setEnabled(True)
        self.actionClose.setEnabled(True)
        self.setCentralWidget(self.editor)

        if (self.tabWidget != None):
            self.tabWidget.deleteLater()
            self.tabWidget = None
            self.project = None
            self.toolBar.setVisible(False)
            self.editModeButton.setEnabled(False)
        self.actionProjSet.setEnabled(True)


    def _saveTriggered(self):
        if (self.editor != None):
            self.editor.saveAction()


    def _saveAsTriggered(self):
        if (self.editor != None):
            self.editor.saveAsAction()


    def _openTriggered(self, action, fileName=None):
        self._removeAllDialog()

        if (fileName == None or fileName == ""):
            self.fileName = QtWidgets.QFileDialog.getOpenFileName(self, "Open Project File", ".", "JSON File (*.json)")
        else:
            self.fileName = [fileName, "JSON File (*.json)"]

        self.actionSave.setEnabled(False)
        self.actionSaveAs.setEnabled(False)
        self.actionProjSet.setEnabled(False)

        if (self.fileName[0] != "" and self.fileName[1] == "JSON File (*.json)"):
            self.editor = None
            try:
                self.tabWidget = QtWidgets.QTabWidget()
                self.tabWidget.setMovable(True)
                self.project = Project()
                self.project.setFileName(self.fileName[0])
                ProjectFile(self.project).load()
                self.project.setFileName(self.fileName[0])

                for tabName, tab in self.project.getAllLO().items():
                    if (tab.getProperty()["Pop Out On Start"]):
                        self._createNewDialog(tab)
                    else:
                        self.tabWidget.addTab(tab, tabName)

                self.setCentralWidget(self.tabWidget)
                self.toolBar.setVisible(True)
                self.editModeButton.setEnabled(True)
                self.actionClose.setEnabled(True)
                self._enablePopOutButton()

                self.project.setDate()
                ProgSetting().addRecentlyOpened(self.project)

            except Exception as ex:
                GMessageBox("Project File Load Error",
                 f"This file may be corrupted or not a valid project file.\nPlease try again.\n{ex}",
                  "Info", self).exec()

                self.toolBar.setVisible(False)
                self.actionClose.setEnabled(False)
                try:
                    self.setCentralWidget(self.startMenu)
                except RuntimeError:
                    self.startMenu = StartMenu(self._newTriggered, self._openTriggered)
                    self.setCentralWidget(self.startMenu)


    def _settingsTriggered(self):
        settings = Settings(ProgSetting().getProperties(), self)
        if  (settings.exec() == settings.DialogCode.Accepted):
            self._windowChanged()
            ProgSetting().saveProperties("required/data.json")


    def _projSettingsTriggered(self):
        settings = Settings(self.editor.getProject().getProperty(), self)
        if (settings.exec() == settings.DialogCode.Accepted):
            self.editor.getProject().saveProperties()


    def _aboutTriggered(self):
        About(self).exec()


    def _homeTriggered(self):
        """Go back to the main menu / start screen."""
        self._closeProjectTriggered()


    def _closeProjectTriggered(self):
        """Close the current project and return to the start menu."""
        # Check if there's an editor with unsaved changes
        if self.editor is not None:
            if not self.editor.closingDialog():
                return  # User cancelled

        self._removeAllDialog()
        
        # Save the recently opened projects
        StartFile().save()
        
        # Clean up current state
        if self.tabWidget is not None:
            self.tabWidget.deleteLater()
            self.tabWidget = None
        
        self.project = None
        self.editor = None
        
        # Reset UI state
        self.toolBar.setVisible(False)
        self.editModeButton.setEnabled(False)
        self.popOutButton.setEnabled(False)
        self.actionSave.setEnabled(False)
        self.actionSaveAs.setEnabled(False)
        self.actionProjSet.setEnabled(False)
        self.actionClose.setEnabled(False)
        
        # Create fresh start menu with updated recent projects
        self.startMenu = StartMenu(self._newTriggered, self._openTriggered)
        self.setCentralWidget(self.startMenu)
        self._updateStatusBar()


    def _enablePopOutButton(self):
        if (self.tabWidget.count() > 0):
            self.popOutButton.setEnabled(True)
        else:
            self.popOutButton.setEnabled(False)


    def _editModeClicked(self):
        self._removeAllDialog()
        self.editor = Editor(self.project)
        self.tabWidget.deleteLater()
        self.tabWidget = None
        self.project = None
        self.toolBar.setVisible(False)
        self.editModeButton.setEnabled(False)
        self.actionSave.setEnabled(True)
        self.actionSaveAs.setEnabled(True)
        self.actionProjSet.setEnabled(True)
        self.setCentralWidget(self.editor)

    
    def _createNewDialog(self, tab):
        dialog = TabDialog(tab, self._popOutTabClosed, None)
        dialog.setWindowTitle(tab.objectName())
        dialog.show()
        self.dialogs.append(dialog)


    def _removeAllDialog(self):
        if (self.editor != None):
            self.editor.removeTabs()
        for dialog in self.dialogs:
            dialog.deleteLater()
        self.dialogs = []

    
    def _popOutClicked(self):
        tab = self.tabWidget.currentWidget()

        tab.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self._createNewDialog(tab)
        tab.setVisible(True)

        if (self.tabWidget.count() == 0):
            self.popOutButton.setEnabled(False)


    def _popOutTabClosed(self, tab):
        self.tabWidget.addTab(tab.getTab(), tab.getTab().objectName())
        self._enablePopOutButton()
        self.dialogs.remove(tab)


    def closeEvent(self, evt) -> None:
        StartFile().save()
        if (self.editor == None):
            self._removeAllDialog()
            return

        if (self.editor.closingDialog()):
            evt.accept()
            self._removeAllDialog()
        else:
            evt.ignore()


    def _windowChanged(self):
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, ProgSetting().getProperties()["Always On Top"])
        self.show()