from PySide2 import QtCore,QtWidgets, QtGui


class InputTextField(QtWidgets.QGraphicsTextItem):
    editingFinished = QtCore.Signal(bool)
    startEditing = QtCore.Signal()

    def __init__(self, text, node, parent=None, singleLine=False, validator=None):
        super(InputTextField, self).__init__(text, parent)
        self.node = node
        self.setFlags(QtWidgets.QGraphicsWidget.ItemSendsGeometryChanges | QtWidgets.QGraphicsWidget.ItemIsSelectable)
        self.singleLine = singleLine
        self.setObjectName("Nothing")
        self.origMoveEvent = self.mouseMoveEvent
        self.mouseMoveEvent = self.node.mouseMoveEvent
        self.validator = validator
        self.textBeforeEditing = ""

    def keyPressEvent(self, event):
        currentKey = event.key()
        if self.validator is not None:
            keyButtonText = event.text()
            doc = QtGui.QTextDocument(self.document().toPlainText())
            selectedText = self.textCursor().selectedText()
            cursor = doc.find(selectedText)
            cursor.insertText(keyButtonText)
            futureText = doc.toPlainText()
            validatorState, chunk, pos = self.validator.validate(futureText, 0)
            if currentKey not in (QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete):
                if validatorState == QtGui.QValidator.Invalid:
                    return

        if currentKey == QtCore.Qt.Key_Escape:
            # user rejects action. Restore text before editing
            self.setPlainText(self.textBeforeEditing)
            self.clearFocus()
            super(InputTextField, self).keyPressEvent(event)
            return

        if self.singleLine:
            if currentKey in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
                if self.toPlainText() == "":
                    self.setPlainText(self.textBeforeEditing)
                    event.ignore()
                    self.editingFinished.emit(False)
                    self.clearFocus()
                else:
                    event.ignore()
                    # self.editingFinished.emit(True)
                    self.clearFocus()
            else:
                super(InputTextField, self).keyPressEvent(event)
        else:
            super(InputTextField, self).keyPressEvent(event)

    def mousePressEvent(self, event):
        if self.objectName() == "MouseLocked":
            super(InputTextField, self).mousePressEvent(event)
        else:
            self.node.mousePressEvent(event)
            self.clearFocus()

    def mouseReleaseEvent(self, event):
        if self.objectName() == "MouseLocked":
            super(InputTextField, self).mouseReleaseEvent(event)
        else:
            self.node.mouseReleaseEvent(event)
            self.clearFocus()

    def mouseDoubleClickEvent(self, event):
        super(InputTextField, self).mouseDoubleClickEvent(event)
        self.setFlag(QtWidgets.QGraphicsWidget.ItemIsFocusable, True)
        self.startEditing.emit()
        self.setFocus()

    def focusInEvent(self, event):
        self.node.canvasRef().disableSortcuts()
        self.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
        self.setObjectName("MouseLocked")
        self.textBeforeEditing = self.toPlainText()
        self.mouseMoveEvent = self.origMoveEvent
        super(InputTextField, self).focusInEvent(event)

    def focusOutEvent(self, event):
        self.node.canvasRef().enableSortcuts()
        cursor = self.textCursor()
        cursor.clearSelection()
        self.setTextCursor(cursor)
        super(InputTextField, self).focusOutEvent(event)
        self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.setFlag(QtWidgets.QGraphicsWidget.ItemIsFocusable, False)
        self.setObjectName("Nothing")
        if self.toPlainText() == "" and self.validator is not None:
            self.setPlainText(self.textBeforeEditing)
            self.editingFinished.emit(False)
        else:
            self.editingFinished.emit(True)
        self.mouseMoveEvent = self.node.mouseMoveEvent

    def setGeometry(self, rect):
        self.prepareGeometryChange()
        self.setPos(rect.topLeft())