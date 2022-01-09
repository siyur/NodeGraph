import weakref
from PySide2 import QtCore, QtWidgets, QtGui
from Python.Core.Common import PinDirection

from PyFlow.UI.Canvas.Painters import PinPainter

UI_PINS_FACTORIES = {}


def getUIPinInstance(owning_node, raw_instance):
    package_name = raw_instance.package_name
    instance = None
    if package_name in UI_PINS_FACTORIES:
        return UI_PINS_FACTORIES[package_name](owning_node, raw_instance)
    else:
        return UIPinBase(owning_node, raw_instance)


def REGISTER_UI_PIN_FACTORY(package_name, factory):
    """
    Called in Python.__init__.INITIALIZE function

    :param package_name:
    :param factory: dictionary that map packag name to ui_pin_factory script
    """
    if package_name not in UI_PINS_FACTORIES:
        UI_PINS_FACTORIES[package_name] = factory


class UIPinBase(QtWidgets.QGraphicsItem):
    def __init__(self, owning_node, raw_pin, parent=None):
        super(UIPinBase, self).__init__(parent=parent)
        self.setGraphicsItem(self)
        self.setFlag(QtWidgets.QGraphicsWidget.ItemSendsGeometryChanges)
        self.setCacheMode(self.DeviceCoordinateCache)
        self.setAcceptHoverEvents(True)
        self.setZValue(1)
        self.setParentItem(owning_node)

        self.UiNode = weakref.ref(owning_node)
        self._raw_pin = raw_pin or None

        # GUI
        self._font = QtGui.QFont("Consolas")
        self._font.setPointSize(6)
        self.pinSize = 6
        self.hovered = False
        self.bLabelHidden = False
        if self._raw_pin is not None:
            self._pinColor = QtGui.QColor(*self._raw_pin.color())
        else:
            self._pinColor = QtCore.Qt.white
        self._label_color = QtCore.Qt.white

    @property
    def label_color(self):
        return self._label_color

    @label_color.setter
    def label_color(self, value):
        self._label_color = value

    def pinCenter(self):
        """Point relative to pin widget, where circle is drawn."""

        frame = QtCore.QRectF(QtCore.QPointF(0, 0), self.geometry().size())
        half_pin_size = self.pinSize / 2
        pin_x = self.pinSize
        pin_y = (frame.height() / 2)
        if not self.bLabelHidden:
            if self.direction == PinDirection.Output:
                pin_x = frame.width() - self.pinSize + half_pin_size
        result = QtCore.QPointF(pin_x, pin_y)
        if self.owningNode().collapsed:
            label_height = self.owningNode().label_height
            if self.direction == PinDirection.Input:
                result = self.mapFromItem(
                    self.owningNode(), QtCore.QPointF(0, label_height))
            if self.direction == PinDirection.Output:
                result = self.mapFromItem(self.owningNode(), QtCore.QPointF(
                    self.owningNode().sizeHint(None, None).width(), label_height))
        return result

    def paint(self, painter, option, widget):
        if self.isArray():
            PinPainter.asArrayPin(self, painter, option, widget)
        elif self.isDict():
            PinPainter.asDictPin(self, painter, option, widget)
        else:
            PinPainter.asValuePin(self, painter, option, widget)
