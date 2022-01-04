from collections import OrderedDict
from PySide2 import QtCore, QtWidgets, QtGui, QtSvg
from Python.Core.UICommon import NodeDefaults
from Python.UI.Utils.stylesheet import Colors
from Python.UI.Canvas.Painters import NodePainter
from Python.Core.Common import PinDirection
from Python.Core.UIPinBase import getUIPinInstance
from Python.Core.NodeNameWidget import NodeNameWidget

UI_NODES_FACTORIES = {}


def getUINodeInstance(raw_instance):
    package_name = raw_instance.package_name
    instance = None
    if package_name in UI_NODES_FACTORIES:
        return UI_NODES_FACTORIES[package_name](raw_instance)
    else:
        return UINodeBase(raw_instance)


def REGISTER_UI_NODE_FACTORY(package_name, factory):
    if package_name not in UI_NODES_FACTORIES:
        UI_NODES_FACTORIES[package_name] = factory


class UINodeBase(QtWidgets.QGraphicsWidget):
    draw_label = None

    def __init__(self, raw_node, color=Colors.NodeBackgrounds, head_color_override=None):
        super(UINodeBase, self).__init__()

        # Raw Node Definition
        self._raw_node = raw_node or None
        self._raw_node.set_ui(self)

        # Color and Size Options
        self.optPenSelectedType = QtCore.Qt.SolidLine
        self.color = color
        self._label_text_color = QtCore.Qt.white
        if self.draw_label is None:
            self.draw_label = True
        self.head_color_override = head_color_override
        self.head_color = NodeDefaults().DEFAULT_NODE_HEAD_COLOR
        self._w = 0
        self.h = 30
        self.minWidth = 50
        self.minHeight = self.h

        # Font Options
        self.nodeNameFont = QtGui.QFont("Consolas")
        self.nodeNameFont.setPointSize(6)

        # GUI Layout
        self.drawLayoutsDebug = False
        self.nodeLayout = QtWidgets.QGraphicsLinearLayout(QtCore.Qt.Vertical)
        self.nodeLayout.setContentsMargins(NodeDefaults().CONTENT_MARGINS,
                                           NodeDefaults().CONTENT_MARGINS,
                                           NodeDefaults().CONTENT_MARGINS,
                                           NodeDefaults().CONTENT_MARGINS)
        self.nodeLayout.setSpacing(NodeDefaults().LAYOUTS_SPACING)

        self.headerLayout = QtWidgets.QGraphicsLinearLayout(QtCore.Qt.Horizontal)

        self.nodeNameWidget = NodeNameWidget(self)
        if self.draw_label:
            self.headerLayout.addItem(self.nodeNameWidget)
        self.nodeNameWidget.setPos(0, 1)

        self.headerLayout.setContentsMargins(0, 0, 0, 0)
        self.headerLayout.setSpacing(3)

        self.headerLayout.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.headerLayout.setMaximumHeight(self.label_height)

        self.exposedActionButtonsLayout = QtWidgets.QGraphicsLinearLayout(QtCore.Qt.Horizontal)
        self.exposedActionButtonsLayout.setContentsMargins(0, 0, 0, 0)
        self.exposedActionButtonsLayout.setSpacing(2)
        self.exposedActionButtonsLayout.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        self.headerLayout.addItem(self.exposedActionButtonsLayout)
        self.headerLayout.setAlignment(self.exposedActionButtonsLayout, QtCore.Qt.AlignRight)

        self.customLayout = QtWidgets.QGraphicsLinearLayout(QtCore.Qt.Vertical)
        self.customLayout.setContentsMargins(0, 0, 0, 0)
        self.customLayout.setSpacing(NodeDefaults().LAYOUTS_SPACING)
        self.customLayout.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        self.hasCustomLayout = False

        self.pinsLayout = QtWidgets.QGraphicsLinearLayout(QtCore.Qt.Horizontal)
        self.pinsLayout.setContentsMargins(0, 0, 0, 0)
        self.pinsLayout.setSpacing(NodeDefaults().LAYOUTS_SPACING)
        self.pinsLayout.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)

        self.inputsLayout = QtWidgets.QGraphicsLinearLayout(QtCore.Qt.Vertical)
        self.inputsLayout.setContentsMargins(0, 0, 0, 0)
        self.inputsLayout.setSpacing(NodeDefaults().LAYOUTS_SPACING)
        self.inputsLayout.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)

        self.outputsLayout = QtWidgets.QGraphicsLinearLayout(QtCore.Qt.Vertical)
        self.outputsLayout.setContentsMargins(0, 0, 0, 0)
        self.outputsLayout.setSpacing(NodeDefaults().LAYOUTS_SPACING)
        self.outputsLayout.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)

        self.pinsLayout.addItem(self.inputsLayout)
        self.pinsLayout.addItem(self.outputsLayout)
        self.pinsLayout.setAlignment(self.inputsLayout, QtCore.Qt.AlignLeft)
        self.pinsLayout.setAlignment(self.outputsLayout, QtCore.Qt.AlignRight)
        self.pinsLayout.setPreferredWidth(self.nodeLayout.preferredWidth())

        self.nodeLayout.addItem(self.headerLayout)
        # self.nodeLayout.addItem(self.customLayout)
        self.nodeLayout.addItem(self.pinsLayout)

        self.setLayout(self.nodeLayout)

        self.svgIcon = QtSvg.QGraphicsSvgItem(self)
        self.svgIcon.setPos(-6, -6)

        self.canvasRef = None
        self._menu = QtWidgets.QMenu()

        # Resizing Options
        self.initialRectWidth = self.minWidth
        self.initialRectHeight = self.minHeight
        self._collapsed = False
        self.resizable = False
        self.bResize = False
        self.resizeDirection = (0, 0)
        self.resizeStrips = [0, 0, 0, 0,  # Left, Top, Right, Bottom
                             0, 0, 0, 0]  # BottomRight, BottomLeft, TopLeft, TopRight
        self.roundness = NodeDefaults().CORNERS_ROUND_FACTOR

        # Hiding/Moving By Group/collapse/By Pin
        self.mousePressPos = QtCore.QPointF()

        # collapse action
        self._groups = {"input": {}, "output": {}}

    @property
    def uid(self):
        return self._raw_node._uid

    @uid.setter
    def uid(self, value):
        self._raw_node._uid = value

    @property
    def name(self):
        return self._raw_node.name

    @name.setter
    def name(self, value):
        self._raw_node.setName(value)

    @property
    def groups(self):
        return self._groups

    @property
    def collapsed(self):
        return self._collapsed

    @collapsed.setter
    def collapsed(self, is_collapsed):
        if is_collapsed != self._collapsed:
            self._collapsed = is_collapsed
            self.aboutToCollapse(self._collapsed)
            for i in range(0, self.inputsLayout.count()):
                inp = self.inputsLayout.itemAt(i)
                inp.setVisible(not is_collapsed)
            for o in range(0, self.outputsLayout.count()):
                out = self.outputsLayout.itemAt(o)
                out.setVisible(not is_collapsed)
            for cust in range(0, self.customLayout.count()):
                out = self.customLayout.itemAt(cust)
                out.setVisible(not is_collapsed)
            self.update_node_shape()

    @property
    def label_text_color(self):
        return self._label_text_color

    @label_text_color.setter
    def label_text_color(self, value):
        self._label_text_color = value
        self.nodeNameWidget.setTextColor(self._label_text_color)

    @property
    def w(self):
        return self._w

    @w.setter
    def w(self, value):
        self._w = value

    @property
    def label_height(self):
        return self.nodeNameWidget.sizeHint(None, None).height()

    @property
    def label_width(self):
        header_width = self.nodeNameWidget.sizeHint(None, None).width()
        header_width += self.buttonsWidth()
        return max(header_width, self.minWidth)

    @property
    def namePinOutputsMap(self):
        result = OrderedDict()
        for raw_pin in self._raw_node.pins:
            if raw_pin.direction == PinDirection.Output:
                wrapper = raw_pin.getWrapper()
                if wrapper is not None:
                    result[raw_pin.name] = wrapper()
        return result

    @property
    def namePinInputsMap(self):
        result = OrderedDict()
        for raw_pin in self._raw_node.pins:
            if raw_pin.direction == PinDirection.Input:
                result[raw_pin.name] = raw_pin.getWrapper()()
        return result

    def description(self):
        return self._raw_node.description()

    def update_node_header_color(self):
        if self.head_color_override is None:
            self.head_color = NodeDefaults().DEFAULT_NODE_HEAD_COLOR
        else:
            self.head_color = self.head_color_override

    def setHeaderHtml(self, html):
        self.nodeNameWidget.setHtml(html)

    def _create_UI_pin_wrapper(self, raw_pin, index=-1, group=None, linkedPin=None):
        ui = raw_pin.get_ui()
        if ui is not None:
            return ui()

        p = getUIPinInstance(self, raw_pin)
        p.call = raw_pin.call

        name = raw_pin.name
        lblName = name
        if raw_pin.direction == PinDirection.Input:
            insertionIndex = -1
            self.inputsLayout.insertItem(insertionIndex, p)
            self.inputsLayout.setAlignment(p, QtCore.Qt.AlignLeft)
            self.inputsLayout.invalidate()

        elif raw_pin.direction == PinDirection.Output:
            insertionIndex = -1
            self.outputsLayout.insertItem(insertionIndex, p)
            self.outputsLayout.setAlignment(p, QtCore.Qt.AlignRight)
            self.outputsLayout.invalidate()

        p.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.update()
        self.update_node_shape()
        p.syncDynamic()
        p.syncRenamable()
        if self.collapsed:
            p.hide()
        return p

    def getNodeWidth(self):
        width = self.getPinsWidth() + self.pinsLayout.spacing() * 2
        if self.resizable:
            width = max(self._rect.width(), width)
        width = max(width, self.label_width)
        return width

    def finalize_rename(self, accepted=False):
        """Called by :class:`~PyFlow.UI.Canvas.UINodeBase.NodeName`

        If user pressed :kbd:`escape` name before editing will be restored. If User pressed :kbd:`enter` or removed focus
        rename action will be accepted and node will be renamed and name will be checked for uniqueness.

        :param accepted: Wheter user accepted editing or not
        :type accepted: :class:`bool`
        """
        if accepted:
            name = self.nodeNameWidget.getPlainText()
            if self.isNameValidationEnabled():
                name = name.replace(" ", "")
            new_name = self.canvasRef().graphManager.get_uniq_node_name(name)
            self.name = new_name
            self.setHeaderHtml(new_name)

    def update_node_shape(self):
        self.prepareGeometryChange()
        self.invalidateNodeLayouts()
        self.updateGeometry()
        self.update()
        if self.canvasRef is not None:
            self.canvasRef().update()
        self.nodeNameWidget.updateGeometry()
        self.nodeNameWidget.update()
        self.pinsLayout.setPreferredWidth(self.getNodeWidth() - self.nodeLayout.spacing())
        self.headerLayout.setPreferredWidth(self.getNodeWidth() - self.nodeLayout.spacing())
        self.customLayout.setPreferredWidth(self.getNodeWidth() - self.nodeLayout.spacing())

    def invalidateNodeLayouts(self):
        self.inputsLayout.invalidate()
        self.outputsLayout.invalidate()
        self.pinsLayout.invalidate()
        self.headerLayout.invalidate()
        self.exposedActionButtonsLayout.invalidate()
        self.nodeLayout.invalidate()
        self.customLayout.invalidate()

    def post_create(self, json_template=None):
        self.update_node_header_color()

        # create ui pin wrappers
        for i in self._raw_node.getOrderedPins():
            self._create_UI_pin_wrapper(i)

        self.update_node_shape()
        self.setPos(self._raw_node.x, self._raw_node.y)

        if self._raw_node.graph is None:
            print("graph doesn't exist for node: %s" % self._raw_node.name)
        assert(self._raw_node.graph() is not None), "NODE GRAPH IS NONE"
        if self.canvasRef is not None:
            if self.canvasRef().graphManager.active_graph() != self._raw_node.graph():
                self.hide()

        if not self.draw_label:
            self.nodeNameWidget.hide()

        self.createActionButtons()

        if json_template is not None and json_template["wrapper"] is not None:
            if "exposeInputsToCompound" in json_template["wrapper"]:
                self.setExposePropertiesToCompound(json_template["wrapper"]["exposeInputsToCompound"])
            if "collapsed" in json_template["wrapper"]:
                self.collapsed = json_template["wrapper"]["collapsed"]
            if "groups" in json_template["ui"]:
                try:
                    for group_name, expanded in json_template["ui"]["groups"]["input"].items():
                        self.groups["input"][group_name].setExpanded(expanded)
                    for group_name, expanded in json_template["ui"]["groups"]["output"].items():
                        self.groups["output"][group_name].setExpanded(expanded)
                except:
                    pass

        description = self.description()
        if description:
            self.setToolTip("%s\nComputingTime: %s"%(str(self.description()),self._raw_node._computingTime))
        else:
            self.setToolTip("\nComputingTime: %s"%self._raw_node._computingTime)

    def paint(self, painter, option, widget):
        NodePainter.default(self, painter, option, widget)
        if self.drawLayoutsDebug:
            painter.setPen(QtGui.QPen(QtCore.Qt.green, 0.75))
            painter.drawRect(self.headerLayout.geometry())
            painter.setPen(QtGui.QPen(QtCore.Qt.black, 0.75))
            painter.drawRect(self.nodeNameWidget.geometry())
            painter.drawRect(self.exposedActionButtonsLayout.geometry())
            painter.setPen(QtGui.QPen(QtCore.Qt.red, 0.75))
            painter.drawRect(self.pinsLayout.geometry())
            painter.setPen(QtGui.QPen(QtCore.Qt.green, 0.75))
            painter.drawRect(self.inputsLayout.geometry())
            painter.drawRect(self.outputsLayout.geometry())
            painter.setPen(QtGui.QPen(QtCore.Qt.blue, 0.75))
            painter.drawRect(self.customLayout.geometry())

    def resetResizeStrips(self):
        for i in range(len(self.resizeStrips)):
            self.resizeStrips[i] = 0

    def should_resize(self, cursor_pos):
        result = {"resize": False, "direction": self.resizeDirection}
        if self.resizeStrips[0] == 1:   # left
            result["resize"] = True
            result["direction"] = (-1, 0)
        if self.resizeStrips[1] == 1:   # top
            result["resize"] = True
            result["direction"] = (0, -1)
        if self.resizeStrips[2] == 1:   # right
            result["resize"] = True
            result["direction"] = (1, 0)
        if self.resizeStrips[3] == 1:   # bottom
            result["resize"] = True
            result["direction"] = (0, 1)
        if self.resizeStrips[4] == 1:   # bottom right
            result["resize"] = True
            result["direction"] = (1, 1)
        if self.resizeStrips[5] == 1:   # bottom left
            result["resize"] = True
            result["direction"] = (-1, 1)
        if self.resizeStrips[6] == 1:   # top left
            result["resize"] = True
            result["direction"] = (-1, -1)
        if self.resizeStrips[7] == 1:   # top right
            result["resize"] = True
            result["direction"] = (1, -1)
        return result

    def mousePressEvent(self, event):
        self.update()
        self.mousePressPos = event.pos()
        super(UINodeBase, self).mousePressEvent(event)
        self.mousePressPos = event.scenePos()
        self.origPos = self.pos()
        self.initPos = self.pos()
        self.initialRect = self.boundingRect()
        if not self.collapsed and self.resizable:
            resizeOpts = self.should_resize(self.mapToScene(event.pos()))
            if resizeOpts["resize"]:
                self.resizeDirection = resizeOpts["direction"]
                self.initialRectWidth = self.initialRect.width()
                self.initialRectHeight = self.initialRect.height()
                self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
                self.bResize = True

    def mouseMoveEvent(self, event):
        super(UINodeBase, self).mouseMoveEvent(event)
        # resize
        if self.bResize:
            delta = event.scenePos() - self.mousePressPos
            if self.resizeDirection == (-1, 0):   # left
                posdelta = self.mapToScene(event.pos()) - self.origPos
                posdelta2 = self.mapToScene(event.pos()) - self.initPos
                newWidth = -posdelta2.x() + self.initialRectWidth
                if newWidth > self.minWidth:
                    self.translate(posdelta.x(), 0)
                    self.origPos = self.pos()
                    self._rect.setWidth(newWidth)
                    self.updateNodeShape()
            elif self.resizeDirection == (0, -1):    # top
                posdelta = self.mapToScene(event.pos()) - self.origPos
                posdelta2 = self.mapToScene(event.pos()) - self.initPos
                minHeight = -posdelta2.y() + self.initialRectHeight
                if minHeight > self.minHeight:
                    self.translate(0, posdelta.y())
                    self.origPos = self.pos()
                    self._rect.setHeight(minHeight)
                    self.updateNodeShape()
            elif self.resizeDirection == (1, 0):  # right
                newWidth = delta.x() + self.initialRectWidth
                if newWidth > self.minWidth:
                    self._rect.setWidth(newWidth)
                    self.w = newWidth
                    self.updateNodeShape()
            elif self.resizeDirection == (0, 1):    # bottom
                newHeight = delta.y() + self.initialRectHeight
                if newHeight > self.minHeight:
                    self._rect.setHeight(newHeight)
                    self.updateNodeShape()
            elif self.resizeDirection == (1, 1):    # bottom right
                newWidth = delta.x() + self.initialRectWidth
                newHeight = delta.y() + self.initialRectHeight
                if newWidth > self.minWidth:
                    self._rect.setWidth(newWidth)
                    self.w = newWidth
                    self.updateNodeShape()
                if newHeight > self.minHeight:
                    self._rect.setHeight(newHeight)
                    self.updateNodeShape()
            elif self.resizeDirection == (-1, 1):    # bottom left
                newHeight = delta.y() + self.initialRectHeight
                if newHeight > self.minHeight:
                    self._rect.setHeight(newHeight)
                posdelta = self.mapToScene(event.pos()) - self.origPos
                posdelta2 = self.mapToScene(event.pos()) - self.initPos
                newWidth = -posdelta2.x() + self.initialRectWidth
                if newWidth > self.minWidth:
                    self.translate(posdelta.x(), 0)
                    self.origPos = self.pos()
                    self._rect.setWidth(newWidth)
                self.updateNodeShape()
            elif self.resizeDirection == (-1, -1):    # top left
                posdelta = self.mapToScene(event.pos()) - self.origPos
                posdelta2 = self.mapToScene(event.pos()) - self.initPos
                minHeight = -posdelta2.y() + self.initialRectHeight
                if minHeight > self.minHeight:
                    self.translate(0, posdelta.y())
                    self.origPos = self.pos()
                    self._rect.setHeight(minHeight)
                newWidth = -posdelta2.x() + self.initialRectWidth
                if newWidth > self.minWidth:
                    self.translate(posdelta.x(), 0)
                    self.origPos = self.pos()
                    self._rect.setWidth(newWidth)
                self.updateNodeShape()
            elif self.resizeDirection == (1, -1):  # top right
                posdelta = self.mapToScene(event.pos()) - self.origPos
                posdelta2 = self.mapToScene(event.pos()) - self.initPos
                minHeight = -posdelta2.y() + self.initialRectHeight
                if minHeight > self.minHeight:
                    self.translate(0, posdelta.y())
                    self.origPos = self.pos()
                    self._rect.setHeight(minHeight)
                newWidth = delta.x() + self.initialRectWidth
                if newWidth > self.minWidth:
                    self._rect.setWidth(newWidth)
                    self.w = newWidth
                self.updateNodeShape()
            self.update()

    def mouseReleaseEvent(self, event):
        self.bResize = False
        self.resetResizeStrips()
        self.update()
        super(UINodeBase, self).mouseReleaseEvent(event)

    def shutDown(self):
        pass

    def eventDropOnCanvas(self):
        pass