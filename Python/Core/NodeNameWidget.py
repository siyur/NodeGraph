from PySide2 import QtCore,QtWidgets, QtGui
from Python.Core.InputTextField import InputTextField


class NodeNameValidator(QtGui.QRegExpValidator):
    """docstring for NodeNameValidator."""
    def __init__(self, parent=None):
        super(NodeNameValidator, self).__init__(QtCore.QRegExp('^[a-zA-Z][a-zA-Z0-9_]*$'), parent)


class NodeNameWidget(QtWidgets.QGraphicsWidget):
    """docstring for NodeName"""

    def __init__(self, parent=None):
        super(NodeNameWidget, self).__init__(parent)
        self.setAcceptHoverEvents(True)
        self.setFlag(QtWidgets.QGraphicsWidget.ItemSendsGeometryChanges)
        self.setCacheMode(QtWidgets.QGraphicsItem.DeviceCoordinateCache)
        self.labelItem = InputTextField(self.parentItem().name, parent, self, singleLine=True, validator=NodeNameValidator())
        self.labelItem.setDefaultTextColor(self.parentItem().label_text_color)
        self.labelItem.setAcceptHoverEvents(True)
        self.labelItem.document().contentsChanged.connect(self.parentItem().update_node_shape)
        self.labelItem.editingFinished.connect(self.parentItem().finalize_rename)

        self.labelItem.hoverMoveEvent = self.hoverMoveEvent
        self._font = QtGui.QFont("Consolas")
        self._font.setPointSize(6)
        self.labelItem.setFont(self._font)
        self.setGraphicsItem(self.labelItem)
        self.hovered = False
        self.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)

    def getFont(self):
        return self.labelItem.font()

    def getPlainText(self):
        return self.labelItem.toPlainText()

    def getHtml(self):
        return self.labelItem.toHtml()

    def setHtml(self, html):
        self.prepareGeometryChange()
        self.labelItem.setHtml(html)
        self._font.setPointSize(6)
        self.labelItem.setFont(self._font)
        self.updateGeometry()
        self.update()

    def setTextColor(self, color):
        self.labelItem.setDefaultTextColor(color)

    def mouseDoubleClickEvent(self, event):
        super(NodeNameWidget, self).mouseDoubleClickEvent(event)

    def isRenamable(self):
        return self.parentItem().isRenamable()

    def hoverEnterEvent(self, event):
        super(NodeNameWidget, self).hoverEnterEvent(event)
        self.hovered = True
        self.update()

    def hoverMoveEvent(self, event):
        self.parentItem().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        super(NodeNameWidget, self).hoverLeaveEvent(event)
        self.hovered = False
        self.update()

    def sizeHint(self, which, constraint):
        w = QtGui.QFontMetrics(self.getFont()).width(self.getPlainText())
        h = self.labelItem.boundingRect().height() + 5
        return QtCore.QSizeF(w, h)

    def setGeometry(self, rect):
        self.prepareGeometryChange()
        super(QtWidgets.QGraphicsWidget, self).setGeometry(rect)
        self.setPos(rect.topLeft())
        self.labelItem.setGeometry(rect)