import weakref
from PySide2 import QtCore, QtWidgets, QtGui
from Python.Core.Common import PinDirection

from Python.UI.Canvas.Painters import PinPainter

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


class UIPinBase(QtWidgets.QGraphicsWidget):
    """UI pin wrapper.
    """

    # Event called when pin is connected
    OnPinConnected = QtCore.Signal(object)
    # Event called when pin is disconnected
    OnPinDisconnected = QtCore.Signal(object)

    def __init__(self, owning_node, raw_pin, parent=None):
        super(UIPinBase, self).__init__(parent=parent)
        self.setGraphicsItem(self)
        self.setFlag(QtWidgets.QGraphicsWidget.ItemSendsGeometryChanges)
        self.setCacheMode(self.DeviceCoordinateCache)
        self.setAcceptHoverEvents(True)
        self.setZValue(1)
        self.setParentItem(owning_node)

        self.ui_node = weakref.ref(owning_node)
        self._raw_pin = raw_pin or None

        if self._raw_pin is not None:
            self._display_name = self._raw_pin.name
            self._raw_pin.set_ui(self)
            self._raw_pin.killed.connect(self.kill)

        # GUI
        self._font = QtGui.QFont("Consolas")
        self._font.setPointSize(6)
        self.pinSize = 6
        self.hovered = False
        self.bLabelHidden = False
        if self._raw_pin is not None:
            self._pin_color = QtGui.QColor(*self._raw_pin.color())
        else:
            self._pin_color = QtCore.Qt.white
        self._label_color = QtCore.Qt.white

        self.uiConnectionList = []

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)

    @property
    def ui_json_data(self):
        return self._raw_pin.ui_json_data

    @property
    def owning_node(self):
        return self.ui_node

    @property
    def direction(self):
        return self._raw_pin.direction

    @property
    def label_color(self):
        return self._label_color

    @label_color.setter
    def label_color(self, value):
        self._label_color = value

    def color(self):
        return self._pin_color

    @property
    def data_type(self):
        return self._raw_pin.data_type

    def display_name(self):
        return self._display_name

    def set_display_name(self, display_name):
        if display_name != self._display_name:
            self._display_name = display_name
            self.displayNameChanged.emit(self._display_name)
            self.prepareGeometryChange()
            self.updateGeometry()
            self.update()

    def setDirty(self):
        self._raw_pin.setDirty()

    @property
    def _data(self):
        return self._raw_pin._data

    @_data.setter
    def _data(self, value):
        self._raw_pin._data = value

    @property
    def affects(self):
        return self._raw_pin.affects

    #=================overriding parent method===============

    def sizeHint(self, which, constraint):
        height = QtGui.QFontMetrics(self._font).height()
        width = self.pinSize * 2
        if not self.bLabelHidden:
            width += QtGui.QFontMetrics(self._font).width(self.display_name())
        return QtCore.QSizeF(width, height)

    #=========================

    def set_data(self, value):
        self._raw_pin.set_data(value)
        self.dataBeenSet.emit(value)

    def get_data(self):
        return self._raw_pin.getData()

    def pin_connected(self, other):
        self.OnPinConnected.emit(other)
        self.update()

    def pin_disconnected(self, other):
        self.OnPinDisconnected.emit(other)
        self.update()

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
        if self.owning_node().collapsed:
            label_height = self.owning_node().label_height
            if self.direction == PinDirection.Input:
                result = self.mapFromItem(
                    self.owning_node(), QtCore.QPointF(0, label_height))
            if self.direction == PinDirection.Output:
                result = self.mapFromItem(self.owning_node(), QtCore.QPointF(
                    self.owning_node().sizeHint(None, None).width(), label_height))
        return result

    def kill(self, *args, **kwargs):
        """this will be called after raw pin is deleted
        """
        scene = self.scene()
        if scene is None:
            del self
            return

        if self._raw_pin.direction == PinDirection.Input:
            self.owning_node().inputsLayout.removeItem(self)
        else:
            self.owning_node().outputsLayout.removeItem(self)

        self.OnPinDeleted.emit(self)
        try:
            scene = self.scene()
            if scene is None:
                del self
                return
            scene.removeItem(self)
            self.owning_node().updateNodeShape()
        except:
            pass

    def paint(self, painter, option, widget):
        PinPainter.asValuePin(self, painter, option, widget)
        # if self.isArray():
        #     PinPainter.asArrayPin(self, painter, option, widget)
        # elif self.isDict():
        #     PinPainter.asDictPin(self, painter, option, widget)
        # else:
        #     PinPainter.asValuePin(self, painter, option, widget)
