## Copyright 2015-2019 Ilgar Lunin, Pedro Cabrera

## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at

##     http://www.apache.org/licenses/LICENSE-2.0

## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.


"""Application class here
"""

import os
import sys
import json

import shutil
from string import ascii_letters
import random

from blinker import Signal
from Python.Core.PathsRegistry import PathsRegistry
from Python.Core.Common import\
    currentProcessorTime, \
    SingletonDecorator
from Python.Core.UICommon import \
    SessionDescriptor, \
    validateGraphDataPackages
from PySide2 import QtWidgets, QtCore, QtGui
from Python.UI.Widgets.BlueprintCanvas import BlueprintCanvasWidget
from Python.UI.Utils.stylesheet import editableStyleSheet
from Python.Core.GraphManager import GraphManagerSingleton
from Python.Input import InputAction, InputActionType
from Python.Input import InputManager
from Python import Version
from Python import INITIALIZE

from Python import GET_PACKAGES

EDITOR_TARGET_FPS = 60


def generateRandomString(numSymbolds=5):
    result = ""
    for i in range(numSymbolds):
        letter = random.choice(ascii_letters)
        result += letter
    return result


def getOrCreateMenu(menuBar, title):
    for child in menuBar.findChildren(QtWidgets.QMenu):
        if child.title() == title:
            return child
    menu = QtWidgets.QMenu(menuBar)
    menu.setObjectName(title)
    menu.setTitle(title)
    return menu


def winTitle():
    return "Node Graph v{0}".format(Version.currentVersion().__str__())


## App itself
class App(QtWidgets.QMainWindow):

    appInstance = None

    newFileExecuted = Signal(bool)
    fileBeenLoaded = Signal()

    def __init__(self, parent=None):
        super(App, self).__init__(parent=parent)
        self._modified = False
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.currentSoftware = ""
        self.setWindowTitle(winTitle())
        self.setContentsMargins(1, 1, 1, 1)
        self.graphManager = GraphManagerSingleton()
        self.canvasWidget = BlueprintCanvasWidget(self.graphManager.get(), self)
        self.canvasWidget.setObjectName("canvasWidget")
        self.setCentralWidget(self.canvasWidget)
        self.setTabPosition(QtCore.Qt.AllDockWidgetAreas, QtWidgets.QTabWidget.North)
        self.setDockOptions(QtWidgets.QMainWindow.AnimatedDocks | QtWidgets.QMainWindow.AllowNestedDocks)

        self.menuBar = QtWidgets.QMenuBar(self)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 863, 21))
        self.menuBar.setObjectName("menuBar")
        self.setMenuBar(self.menuBar)
        self.toolBar = QtWidgets.QToolBar(self)
        self.toolBar.setObjectName("toolBar")
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)

        self.setWindowIcon(QtGui.QIcon(":/LogoBpApp.png"))
        self.currentTempDir = ""

        self.setMouseTracking(True)

        self._lastClock = 0.0
        self.fps = EDITOR_TARGET_FPS
        self._currentFileName = ''
        self.currentFileName = None

    def historyStatePushed(self, state):
        if state.modifiesData():
            self.modified = True
            self.updateLabel()

    @property
    def modified(self):
        return self._modified

    @modified.setter
    def modified(self, value):
        self._modified = value
        self.updateLabel()

    def updateLabel(self):
        label = "Untitled"
        if self.currentFileName is not None:
            if os.path.isfile(self.currentFileName):
                label = os.path.basename(self.currentFileName)
        if self.modified:
            label += "*"
        self.setWindowTitle("{0} - {1}".format(winTitle(), label))

    def getMenuBar(self):
        return self.menuBar

    def populateMenu(self):
        fileMenu = self.menuBar.addMenu("File")
        newFileAction = fileMenu.addAction("New file")
        newFileAction.setIcon(QtGui.QIcon(":/new_file_icon.png"))
        newFileAction.triggered.connect(self.newFile)

        loadAction = fileMenu.addAction("Load")
        loadAction.setIcon(QtGui.QIcon(":/folder_open_icon.png"))
        loadAction.triggered.connect(self.load)

        saveAction = fileMenu.addAction("Save")
        saveAction.setIcon(QtGui.QIcon(":/save_icon.png"))
        saveAction.triggered.connect(self.save)

        saveAsAction = fileMenu.addAction("Save as")
        saveAsAction.setIcon(QtGui.QIcon(":/save_as_icon.png"))
        saveAsAction.triggered.connect(lambda: self.save(True))

    def getToolbar(self):
        return self.toolBar

    def getCanvas(self):
        return self.canvasWidget.canvas

    def keyPressEvent(self, event):
        modifiers = event.modifiers()
        currentInputAction = InputAction(name="temp", actionType=InputActionType.Keyboard, key=event.key(), modifiers=modifiers)

        actionSaveVariants = InputManager()["App.Save"]
        actionNewFileVariants = InputManager()["App.NewFile"]
        actionLoadVariants = InputManager()["App.Load"]
        actionSaveAsVariants = InputManager()["App.SaveAs"]

        if currentInputAction in actionNewFileVariants:
            shouldSave = self.shouldSave()
            if shouldSave == QtWidgets.QMessageBox.Yes:
                self.save()
            elif shouldSave == QtWidgets.QMessageBox.Discard:
                return

            self.newFile()
            self.currentFileName = None
            self.modified = False
            self.updateLabel()
        if currentInputAction in actionSaveVariants:
            self.save()
        if currentInputAction in actionLoadVariants:
            shouldSave = self.shouldSave()
            if shouldSave == QtWidgets.QMessageBox.Yes:
                self.save()
            elif shouldSave == QtWidgets.QMessageBox.Discard:
                return
            self.load()
        if currentInputAction in actionSaveAsVariants:
            self.save(True)

    def loadFromFileChecked(self, filePath):
        shouldSave = self.shouldSave()
        if shouldSave == QtWidgets.QMessageBox.Yes:
            self.save()
        elif shouldSave == QtWidgets.QMessageBox.Discard:
            return
        self.loadFromFile(filePath)
        self.modified = False
        self.updateLabel()

    def loadFromData(self, data, clearHistory=False):

        # check first if all packages we are trying to load are legal
        missedPackages = set()
        if not validateGraphDataPackages(data, missedPackages):
            msg = "This graph can not be loaded. Following packages not found:\n\n"
            index = 1
            for missedPackageName in missedPackages:
                msg += "{0}. {1}\n".format(index, missedPackageName)
                index += 1
            QtWidgets.QMessageBox.critical(self, "Missing dependencies", msg)
            return

        self.newFile(keepRoot=False)
        # load raw data
        self.graphManager.get().deserialize(data)
        self.fileBeenLoaded.emit()
        self.graphManager.get().selectGraphByName(data["activeGraph"])
        self.updateLabel()
        PathsRegistry().rebuild()

    @property
    def currentFileName(self):
        return self._currentFileName

    @currentFileName.setter
    def currentFileName(self, value):
        self._currentFileName = value
        self.updateLabel()

    def loadFromFile(self, filePath):
        with open(filePath, 'r') as f:
            data = json.load(f)
            self.loadFromData(data, clearHistory=True)
            self.currentFileName = filePath

    def load(self):
        name_filter = "Graph files (*.pygraph)"
        save_path = QtWidgets.QFileDialog.getOpenFileName(filter=name_filter)
        if type(save_path) in [tuple, list]:
            fpath = save_path[0]
        else:
            fpath = save_path
        if not fpath == '':
            self.loadFromFile(fpath)

    def save(self, save_as=False):
        if save_as:
            name_filter = "Graph files (*.pygraph)"
            save_path = QtWidgets.QFileDialog.getSaveFileName(filter=name_filter)
            if type(save_path) in [tuple, list]:
                pth = save_path[0]
            else:
                pth = save_path
            if not pth == '':
                self.currentFileName = pth
            else:
                self.currentFileName = None
        else:
            if self.currentFileName is None:
                name_filter = "Graph files (*.pygraph)"
                save_path = QtWidgets.QFileDialog.getSaveFileName(filter=name_filter)
                if type(save_path) in [tuple, list]:
                    pth = save_path[0]
                else:
                    pth = save_path
                if not pth == '':
                    self.currentFileName = pth
                else:
                    self.currentFileName = None

        if not self.currentFileName:
            return False

        if not self.currentFileName.endswith(".pygraph"):
            self.currentFileName += ".pygraph"

        if not self.currentFileName == '':
            with open(self.currentFileName, 'w') as f:
                saveData = self.graphManager.get().serialize()
                json.dump(saveData, f, indent=4)
            print(str("// saved: '{0}'".format(self.currentFileName)))
            self.modified = False
            self.updateLabel()
            return True

    def newFile(self, keepRoot=True):

        # broadcast
        self.graphManager.get().clear(keepRoot=keepRoot)
        self.newFileExecuted.emit(keepRoot)

    def createPopupMenu(self):
        pass

    def shouldSave(self):
        if self.modified:
            btn = QtWidgets.QMessageBox.warning(self, "Confirm?", "Unsaved data will be lost. Save?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Discard)
            if btn == QtWidgets.QMessageBox.No:
                return QtWidgets.QMessageBox.No
            else:
                return btn
        return QtWidgets.QMessageBox.No

    def closeEvent(self, event):

        should_save = self.shouldSave()
        if should_save == QtWidgets.QMessageBox.Yes:
            if not self.save():
                event.ignore()
                return
        elif should_save == QtWidgets.QMessageBox.Discard:
            event.ignore()
            return

        self.canvasWidget.shutDown()

        # remove temp directory if exists
        if os.path.exists(self.currentTempDir):
            shutil.rmtree(self.currentTempDir)

        SingletonDecorator.destroyAll()

        App.appInstance = None

        QtWidgets.QMainWindow.closeEvent(self, event)

    @staticmethod
    def instance(parent=None, software=""):
        assert(software != ""), "Invalid arguments. Please pass you software name as second argument!"

        instance = App(parent)
        instance.currentSoftware = software
        SessionDescriptor().software = instance.currentSoftware

        if software == "standalone":
            editableStyleSheet(instance)

        try:
            extra_package_paths = []
            # TODO: implement extra package paths
            INITIALIZE(additionalPackageLocations=extra_package_paths, software=software)
        except Exception as e:
            print(e)
            QtWidgets.QMessageBox.critical(None, "Fatal error", str(e))
            return

        # populate tools
        canvas = instance.getCanvas()
        toolbar = instance.getToolbar()

        # populate menus
        instance.populateMenu()

        App.appInstance = instance

        return instance
