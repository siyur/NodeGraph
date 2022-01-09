
import json
import uuid
try:
    from inspect import getfullargspec as getargspec
except:
    from inspect import getargspec

from PySide2 import QtCore, QtGui, QtWidgets

from Python import GET_PACKAGES
from Python import GET_PACKAGE_PATH

from Python.Core.Common import *
from Python.Core.UICommon import *
from Python.Core.NodeBase import NodeBase

from Python.UI.Utils.stylesheet import editableStyleSheet


class NodeBoxLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent, events=True):
        super(NodeBoxLineEdit, self).__init__(parent)
        self.setParent(parent)
        self._events = events
        self.parent = parent
        self.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.setObjectName("le_nodes")
        style = "border-radius: 2px;" +\
                "font-size: 14px;" +\
                "border-style: outset;" +\
                "border-width: 1px;"
        self.setStyleSheet(style)
        self.setPlaceholderText("enter node name..")


class NodeBoxTreeWidget(QtWidgets.QTreeWidget):
    showInfo = QtCore.Signal(object)
    hideInfo = QtCore.Signal()

    def __init__(self, parent, canvas, bNodeInfoEnabled=True, useDragAndDrop=True, bGripsEnabled=True):
        super(NodeBoxTreeWidget, self).__init__(parent)
        style = "border-radius: 2px;" +\
                "font-size: 14px;" +\
                "border-style: outset;" +\
                "border-width: 1px;"
        self.setStyleSheet(style)
        self.bGripsEnabled = bGripsEnabled
        self.canvas = canvas
        self.setParent(parent)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.setObjectName("tree_nodes")
        self.setSortingEnabled(True)
        self.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.setColumnCount(0)
        self.setHeaderHidden(True)
        self.bUseDragAndDrop = useDragAndDrop
        if useDragAndDrop:
            self.setDragEnabled(True)
            self.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)
        self.setAnimated(True)
        self.categoryPaths = {}
        self.bNodeInfoEnabled = bNodeInfoEnabled
        self.currentItemChanged.connect(self.onCurrentItemChanged)
        self.suggestionsEnabled = False

    def onCurrentItemChanged(self, current, previous):
        if current is not None:
            if self.bNodeInfoEnabled:
                if not current.bCategory:
                    if current.docString is not None:
                        self.showInfo.emit(current.docString)
                else:
                    self.hideInfo.emit()

    def _isCategoryExists(self, category_name, categories):
        bFound = False
        if category_name in categories:
            return True
        if not bFound:
            for c in categories:
                sepCatNames = c.split('|')
                if len(sepCatNames) == 1:
                    if category_name == c:
                        return True
                else:
                    for i in range(0, len(sepCatNames)):
                        c = '|'.join(sepCatNames)
                        if category_name == c:
                            return True
                        sepCatNames.pop()
        return False

    def insertNode(self, nodeCategoryPath, name, doc=None, libName=None, bPyNode=False, bCompoundNode=False):
        nodePath = nodeCategoryPath.split('|')
        categoryPath = ''
        # walk from tree top to bottom, creating folders if needed
        # also writing all paths in dict to avoid duplications
        for folderId in range(0, len(nodePath)):
            folderName = nodePath[folderId]
            if folderId == 0:
                categoryPath = folderName
                if categoryPath not in self.categoryPaths:
                    rootFolderItem = QtWidgets.QTreeWidgetItem(self)
                    rootFolderItem.bCategory = True
                    rootFolderItem.setFlags(QtCore.Qt.ItemIsEnabled)
                    rootFolderItem.setText(0, folderName)
                    rootFolderItem.setBackground(
                        folderId, editableStyleSheet().BgColorBright)
                    self.categoryPaths[categoryPath] = rootFolderItem
            else:
                parentCategoryPath = categoryPath
                categoryPath += '|{}'.format(folderName)
                if categoryPath not in self.categoryPaths:
                    childCategoryItem = QtWidgets.QTreeWidgetItem(self.categoryPaths[parentCategoryPath])
                    childCategoryItem.setFlags(QtCore.Qt.ItemIsEnabled)
                    childCategoryItem.bCategory = True
                    childCategoryItem.setText(0, folderName)
                    childCategoryItem.setBackground(0, editableStyleSheet().BgColorBright.lighter(150))
                    self.categoryPaths[categoryPath] = childCategoryItem
        # create node under constructed folder
        # TODO: Subclass QTreeWidgetItem to not create dynamic attributes. Below code is ugly
        nodeItem = QtWidgets.QTreeWidgetItem(self.categoryPaths[categoryPath])
        nodeItem.bCategory = False
        nodeItem.bPyNode = bPyNode
        nodeItem.bCompoundNode = bCompoundNode
        nodeItem.setText(0, name)
        nodeItem.libName = libName
        nodeItem.docString = doc
        return nodeItem

    def refresh(self, pattern='', pin_direction=None):
        self.clear()
        self.categoryPaths = {}

        dataType = None
        if self.canvas.pressedPin is not None:
            dataType = self.canvas.pressedPin.dataType

        for package_name, package in GET_PACKAGES().items():
            # class based nodes
            for node_class in package.GetNodeClasses().values():

                nodeCategoryPath = "{0}|{1}".format(package_name, node_class.category)

                # checkString = node_class.__name__ + nodeCategoryPath + ''.join(node_class.keywords())
                # if pattern.lower() not in checkString.lower():
                #     continue
                if dataType is None:
                    self.insertNode(nodeCategoryPath, node_class.__name__, node_class.description())
                else:
                    hints = node_class.pin_type_hints()
                    # if pressed pin is output pin
                    # filter by nodes input types
                    if pin_direction == PinDirection.Output and dataType in hints.input_types:
                        self.insertNode(nodeCategoryPath, node_class.__name__, node_class.description())

                    # if pressed pin is input pin
                    # filter by nodes output types
                    elif pin_direction == PinDirection.Input and dataType in hints.output_types:
                        self.insertNode(nodeCategoryPath, node_class.__name__, node_class.description())

            # expand all categories
            if dataType is not None:
                for categoryItem in self.categoryPaths.values():
                    categoryItem.setExpanded(True)
            self.sortItems(0, QtCore.Qt.AscendingOrder)

    def mousePressEvent(self, event):
        super(NodeBoxTreeWidget, self).mousePressEvent(event)
        item_clicked = self.currentItem()
        if not item_clicked:
            event.ignore()
            return
        # check if clicked item is a category
        if item_clicked.bCategory:
            event.ignore()
            return
        # find top level parent
        rootItem = item_clicked
        bPyNode = False
        bCompoundNode = False
        if not item_clicked.bCategory:
            bPyNode = rootItem.bPyNode
            bCompoundNode = rootItem.bCompoundNode
        while not rootItem.parent() is None:
            rootItem = rootItem.parent()
            if not rootItem.bCategory:
                bPyNode = rootItem.bPyNode
                bCompoundNode = rootItem.bCompoundNode
        packageName = rootItem.text(0)
        pressed_text = item_clicked.text(0)

        if pressed_text in self.categoryPaths.keys():
            event.ignore()
            return

        jsonTemplate = NodeBase.json_template()
        jsonTemplate['package'] = packageName
        jsonTemplate['type'] = pressed_text
        jsonTemplate['name'] = pressed_text
        jsonTemplate['uuid'] = str(uuid.uuid4())
        jsonTemplate['meta']['label'] = pressed_text
        jsonTemplate['bPyNode'] = bPyNode
        jsonTemplate['bCompoundNode'] = bCompoundNode

        if self.canvas.pressedPin is not None and self.bGripsEnabled:
            a = self.canvas.mapToScene(self.canvas.mouseReleasePos)
            jsonTemplate["x"] = a.x()
            jsonTemplate["y"] = a.y()
            node = self.canvas.createNode(jsonTemplate)
            if bPyNode or bCompoundNode:
                node.rebuild()
            self.canvas.hideNodeBox()
            pressedPin = self.canvas.pressedPin
            if pressedPin.direction == PinDirection.Input:
                for pin in node.ui_outputs.values():
                    wire = self.canvas.connectPinsInternal(pressedPin, pin)
                    if wire is not None:
                        break
            if pressedPin.direction == PinDirection.Output:
                for pin in node.ui_inputs.values():
                    wire = self.canvas.connectPinsInternal(pin, pressedPin)
                    if wire is not None:
                        break
        else:
            drag = QtGui.QDrag(self)
            mime_data = QtCore.QMimeData()

            pressed_text = json.dumps(jsonTemplate)
            mime_data.setText(pressed_text)
            drag.setMimeData(mime_data)
            drag.exec_()

    def update(self):
        for category in self.categoryPaths.values():
            if not category.parent():
                category.setBackground(
                    0, editableStyleSheet().BgColorBright)
            else:
                category.setBackground(
                    0, editableStyleSheet().BgColorBright.lighter(150))
        super(NodeBoxTreeWidget, self).update()


class NodeBoxSizeGrip(QtWidgets.QSizeGrip):
    """docstring for NodeBoxSizeGrip."""
    def __init__(self, parent=None):
        super(NodeBoxSizeGrip, self).__init__(parent)

    def sizeHint(self):
        return QtCore.QSize(13, 13)

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = event.rect()
        painter.setBrush(QtGui.QColor(80, 80, 80, 255))
        painter.drawRoundedRect(rect, 3, 3)
        painter.drawPixmap(rect, QtGui.QPixmap(":resize_diagonal.png"))
        painter.end()


class NodesBox(QtWidgets.QFrame):
    """doc string for NodesBox"""

    def __init__(self, parent, canvas, bNodeInfoEnabled=True, bGripsEnabled=True, bUseDragAndDrop=False):
        super(NodesBox, self).__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Raised)
        self.bDragging = False
        self.lastCursorPos = QtCore.QPoint(0, 0)
        self.offset = QtCore.QPoint(0, 0)
        self.setMouseTracking(True)
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setObjectName("mainLayout")
        self.mainLayout.setSpacing(1)
        self.mainLayout.setContentsMargins(1, 1, 1, 1)
        self.splitter = QtWidgets.QSplitter()
        self.splitter.setObjectName("nodeBoxSplitter")
        self.mainLayout.addWidget(self.splitter)
        self.bGripsEnabled = bGripsEnabled
        if self.bGripsEnabled:
            self.sizeGrip = NodeBoxSizeGrip(self)
            self.sizeGrip.setObjectName("nodeBoxSizeGrip")
            self.sizeGripLayout = QtWidgets.QHBoxLayout()
            self.sizeGripLayout.setObjectName("sizeGripLayout")
            self.sizeGripLayout.setSpacing(1)
            self.sizeGripLayout.setContentsMargins(1, 1, 1, 1)
            spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
            self.sizeGripLayout.addItem(spacerItem)
            self.sizeGripLayout.addWidget(self.sizeGrip)
            self.mainLayout.addLayout(self.sizeGripLayout)

        self.nodeTreeWidget = QtWidgets.QWidget()
        self.nodeTreeWidget.setObjectName("nodeTreeWidget")
        self.nodeTreeWidget.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.nodeTreeWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setSpacing(1)
        self.verticalLayout.setContentsMargins(1, 1, 1, 1)
        self.splitter.addWidget(self.nodeTreeWidget)
        self.lineEdit = NodeBoxLineEdit(self)
        self.lineEdit.setObjectName("lineEdit")
        self.verticalLayout.addWidget(self.lineEdit)
        self.lineEdit.textChanged.connect(self.leTextChanged)
        self.nodeInfoWidget = QtWidgets.QTextBrowser()
        self.nodeInfoWidget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.nodeInfoWidget.setObjectName("nodeBoxInfoBrowser")
        self.nodeInfoWidget.setOpenExternalLinks(True)
        self.splitter.addWidget(self.nodeInfoWidget)
        self.splitter.addWidget(self.nodeInfoWidget)
        self.nodeInfoWidget.setVisible(bNodeInfoEnabled)

        self.treeWidget = NodeBoxTreeWidget(self, canvas, bNodeInfoEnabled, bUseDragAndDrop, bGripsEnabled)
        self.treeWidget.setObjectName("nodeBoxTreeWidget")
        self.treeWidget.headerItem().setText(0, "1")
        self.verticalLayout.addWidget(self.treeWidget)
        self.treeWidget.refresh()

        self.treeWidget.showInfo.connect(self.onShowInfo)
        self.treeWidget.hideInfo.connect(self.onHideInfo)

    def hideEvent(self, event):
        self.bDragging = False

    def showEvent(self, event):
        self.nodeInfoWidget.setHtml("")
        self.bDragging = False

    def onShowInfo(self, restructuredText):
        self.nodeInfoWidget.show()
        self.nodeInfoWidget.setHtml(rst2html(restructuredText))

    def onHideInfo(self):
        self.nodeInfoWidget.setHtml("")

    def sizeHint(self):
        return QtCore.QSize(500, 300)

    def expandCategory(self):
        for i in self.treeWidget.categoryPaths:
            self.treeWidget.setItemExpanded(
                self.treeWidget.categoryPaths[i], True)

    def leTextChanged(self):
        if self.lineEdit.text() == '':
            self.lineEdit.setPlaceholderText("enter node name..")
            self.treeWidget.refresh()
            return
        self.treeWidget.refresh(self.lineEdit.text())
        self.expandCategory()

    def mousePressEvent(self, event):
        super(NodesBox, self).mousePressEvent(event)
        if self.bGripsEnabled:
            if event.pos().y() >= self.geometry().height() - 30:
                self.bDragging = True
                self.lastCursorPos = QtGui.QCursor.pos()

    def mouseMoveEvent(self, event):
        super(NodesBox, self).mouseMoveEvent(event)
        if self.bGripsEnabled:
            if self.bDragging:
                delta = QtGui.QCursor.pos() - self.lastCursorPos
                currentPos = self.pos()
                self.move(currentPos + delta)
                self.lastCursorPos = QtGui.QCursor.pos()

    def mouseReleaseEvent(self, event):
        super(NodesBox, self).mouseReleaseEvent(event)
        self.bDragging = False
