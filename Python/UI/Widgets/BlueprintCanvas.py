import uuid
import json
import weakref
from functools import partial
from PySide2 import QtWidgets, QtCore, QtGui
from Python.UI.Canvas.CanvasBase import CanvasBase
from Python.UI.Utils.stylesheet import Colors
from Python.UI.Canvas.SelectionRect import SelectionRect
from Python.UI.Views.NodeBox import NodesBox
from Python.UI.Canvas.AutoPanController import AutoPanController

from Python.Core.UIPinBase import UIPinBase
from Python.Core.UINodeBase import UINodeBase, getUINodeInstance
from Python.Core.NodeBase import NodeBase
from Python.Core.PinBase import PinBase
from Python.Core.Common import \
    PinDirection, \
    PinSelectionGroup, \
    canConnectPins, \
    cycleCheck, \
    connectPins, \
    disconnectPins
from Python.Core.UICommon import CanvasManipulationMode
from Python.Core.UIConnection import UIConnection

from Python.Input import InputManager, InputAction, InputActionType
from Python import GET_PACKAGE_CHECKED


class BlueprintCanvas(CanvasBase):
    """
    UI canvas class
    """

    _realTimeLineInvalidColor = Colors.Red
    _realTimeLineNormalColor = Colors.White
    _realTimeLineValidColor = Colors.Green

    def __init__(self, graph_manager, app_instance=None):
        super(BlueprintCanvas, self).__init__()

        self.menu = QtWidgets.QMenu()
        self.populate_menu()

        self.graph_manager = graph_manager
        self.graph_manager.graphChanged.connect(self.on_graph_changed)
        self.app_instance = app_instance

        self.pressedPin = None
        self.releasedPin = None
        self.resizing = False

        self.autoPanController = AutoPanController()

        self.hoveredReroutes = []

        # realtime pin connection line
        self.realTimeLine = QtWidgets.QGraphicsPathItem(None, self.scene())
        self.realTimeLine.name = 'RealTimeLine'
        self.realTimeLineInvalidPen = QtGui.QPen(self._realTimeLineInvalidColor, 2.0, QtCore.Qt.SolidLine)
        self.realTimeLineNormalPen = QtGui.QPen(self._realTimeLineNormalColor, 2.0, QtCore.Qt.DashLine)
        self.realTimeLineValidPen = QtGui.QPen(self._realTimeLineValidColor, 2.0, QtCore.Qt.SolidLine)
        self.realTimeLine.setPen(self.realTimeLineNormalPen)

        # node box
        self.node_box = NodesBox(self.getApp(), self, bUseDragAndDrop=True)
        self.node_box.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        self._drawRealtimeLine = False
        self._UIConnections = {}
        self.reconnectingWires = set()

        self.currentPressedKey = None

        self.dropCallback = None
        self.tempnode = None

    @property
    def nodes(self):
        """returns all ui nodes dict including compounds
        """
        result = {}
        for raw_node in self.graph_manager.get_all_nodes():
            ui_node = raw_node.get_ui()
            if ui_node is None:
                print("{0} has not UI wrapper".format(raw_node.name))
            if raw_node.uid in result:
                raw_node.uid = uuid.uuid4()
            result[raw_node.uid] = ui_node
        return result

    @property
    def pins(self):
        """Returns UI pins dict {uuid: UIPinBase}
        """
        result = {}
        for node in self.graph_manager.get_all_nodes():
            for pin in node.pins:
                result[pin.uid] = pin.getWrapper()()
        return result

    @property
    def connections(self):
        return self._UIConnections

    def on_graph_changed(self, new_graph):
        for node in self.get_all_nodes():
            bVisible = node._rawNode.graph() == new_graph
            node.setVisible(bVisible)
            for pin in node.UIPins.values():
                for connection in pin.uiConnectionList:
                    if bVisible:
                        if not connection.isUnderCollapsedComment():
                            connection.setVisible(bVisible)
                    else:
                        connection.setVisible(bVisible)
        self.validateConnections(new_graph)

        for node in self.get_all_nodes():
            node.updateNodeShape()

    def set_selected_nodes_collapsed(self, collapsed=True):
        for node in self.selectedNodes():
            node.collapsed = collapsed

    def populate_menu(self):
        self.actionCollapseSelectedNodes = self.menu.addAction("Collapse selected nodes")
        self.actionCollapseSelectedNodes.triggered.connect(lambda: self.set_selected_nodes_collapsed(True))

        self.actionExpandSelectedNodes = self.menu.addAction("Expand selected nodes")
        self.actionExpandSelectedNodes.triggered.connect(lambda: self.set_selected_nodes_collapsed(False))

    def getApp(self):
        return self.app_instance

    def get_all_nodes(self):
        """returns all ui nodes list
        """
        return list(self.nodes.values())

    def selectedNodes(self):
        all_nodes = self.get_all_nodes()
        assert(None not in all_nodes), "Bad nodes!"
        return [i for i in all_nodes if i.isSelected()]

    def selectedConnections(self):
        return [i for i in self.connections.values() if i.isSelected()]

    def clearSelection(self):
        for node in self.selectedNodes():
            node.setSelected(False)

        for connection in self.selectedConnections():
            connection.setSelected(False)

    def showNodeBox(self, pinDirection=None):
        self.node_box.show()
        self.node_box.move(QtGui.QCursor.pos())
        self.node_box.treeWidget.refresh('', pinDirection)
        self.node_box.lineEdit.blockSignals(True)
        self.node_box.lineEdit.setText("")
        self.node_box.lineEdit.blockSignals(False)
        self.node_box.lineEdit.setFocus()

    def hideNodeBox(self):
        self.node_box.hide()
        self.node_box.lineEdit.clear()

    def shutDown(self, *args, **kwargs):
        self.scene().clear()
        self.hideNodeBox()
        for node in self.get_all_nodes():
            node.shutDown()

    def findPinNearPosition(self, scene_pos, tolerance=3):
        tolerance = tolerance * self.currentViewScale()
        rect = QtCore.QRect(QtCore.QPoint(scene_pos.x() - tolerance, scene_pos.y() - tolerance),
                            QtCore.QPoint(scene_pos.x() + tolerance, scene_pos.y() + tolerance))
        items = self.items(rect)
        pins = [i for i in items if isinstance(i, UIPinBase)]
        if len(pins) > 0:
            return pins[0]
        return None

    def node_from_instance(self, instance):
        if isinstance(instance, UINodeBase):
            return instance
        node = instance
        while (isinstance(node, QtWidgets.QGraphicsItem) or
               isinstance(node, QtWidgets.QGraphicsWidget) or
               isinstance(node, QtWidgets.QGraphicsProxyWidget)) and \
                node.parentItem():
            node = node.parentItem()
        if isinstance(node, UINodeBase):
            return node
        else:
            return None

    def _createNode(self, json_template):

        nodeInstance = getNodeInstance(json_template, self)
        assert(nodeInstance is not None), "Node instance is not found!"
        nodeInstance.setPos(json_template["x"], json_template["y"])
        # set pins data
        for inpJson in json_template['inputs']:
            pin = nodeInstance.getPinSG(inpJson['name'], PinSelectionGroup.Inputs)
            if pin:
                pin.uid = uuid.UUID(inpJson['uuid'])

        for outJson in json_template['outputs']:
            pin = nodeInstance.getPinSG(outJson['name'], PinSelectionGroup.Outputs)
            if pin:
                pin.uid = uuid.UUID(outJson['uuid'])

        return nodeInstance

    def createNode(self, json_template, **kwargs):
        node_instance = self._createNode(json_template)
        return node_instance

    def add_node(self, ui_node, jsonTemplate, parentGraph=None):
        """Adds node to a graph

        :param ui_node: Raw node wrapper
        :type ui_node: :class:`~PyFlow.UI.Canvas.UINodeBase.UINodeBase`
        """

        ui_node.canvasRef = weakref.ref(self)
        self.scene().addItem(ui_node)

        assert(jsonTemplate is not None)

        if ui_node._raw_node.graph is None:
            # if added from node box
            self.graph_manager.active_graph().add_node(ui_node._raw_node, jsonTemplate)
        else:
            # When copy paste compound node. we are actually pasting a tree of graphs
            # So we need to put each node under correct graph
            assert(parentGraph is not None), "Parent graph is invalid"
            parentGraph.add_node(ui_node._raw_node, jsonTemplate)
        ui_node.post_create(jsonTemplate)

    def updateReroutes(self, event, showPins=False):
        tolerance = 9 * self.currentViewScale()
        mouseRect = QtCore.QRect(QtCore.QPoint(event.pos().x() - tolerance, event.pos().y() - tolerance),
                                 QtCore.QPoint(event.pos().x() + tolerance, event.pos().y() + tolerance))
        hoverItems = self.items(mouseRect)
        self.hoveredReroutes += [node for node in hoverItems if isinstance(node, UINodeBase) and node.isReroute()]
        for node in self.hoveredReroutes:
            if showPins:
                if node in hoverItems:
                    node.showPins()
                else:
                    node.hidePins()
                    self.hoveredReroutes.remove(node)
            else:
                node.hidePins()
                self.hoveredReroutes.remove(node)

    def create_ui_connection_for_connected_pins(self, srcUiPin, dstUiPin):
        assert(srcUiPin is not None)
        assert(dstUiPin is not None)
        if srcUiPin.direction == PinDirection.Input:
            srcUiPin, dstUiPin = dstUiPin, srcUiPin
        uiConnection = UIConnection(srcUiPin, dstUiPin, self)
        self.scene().addItem(uiConnection)
        self.connections[uiConnection.uid] = uiConnection
        # restore wire data
        pinWrapperData = srcUiPin.ui_json_data
        if pinWrapperData is not None:
            if "wires" in pinWrapperData:
                wiresData = pinWrapperData["wires"]
                key = str(dstUiPin.pinIndex)
                if str(dstUiPin.pinIndex) in wiresData:
                    uiConnection.applyJsonData(wiresData[key])
        return uiConnection

    def connect_pins_internal(self, src, dst):
        result = connectPins(src._raw_pin, dst._raw_pin)
        if result:
            return self.create_ui_connection_for_connected_pins(src, dst)
        return None

    def connect_pins(self, src, dst):
        # Highest level connect pins function
        pass
        if src and dst:
            if canConnectPins(src._raw_pin, dst._raw_pin):
                wire = self.connect_pins_internal(src, dst)
        #         if wire is not None:
        #             EditorHistory().saveState("Connect pins", modify=True)

    def remove_item_by_name(self, name):
        for i in self.scene().items():
            if hasattr(i, 'name') and i.name == name:
                self.scene().removeItem(i)

    def removeConnection(self, connection):
        src = connection.source()._raw_pin
        dst = connection.destination()._raw_pin
        # this will remove raw pins from affection lists
        # will call pinDisconnected for raw pins
        disconnectPins(src, dst)

        # call disconnection events for ui pins
        connection.source().pin_disconnected(connection.destination())
        connection.destination().pin_disconnected(connection.source())
        self.connections.pop(connection.uid)
        connection.source().uiConnectionList.remove(connection)
        connection.destination().uiConnectionList.remove(connection)
        connection.prepareGeometryChange()
        self.scene().removeItem(connection)

    def mousePressEvent(self, event):
        # TODO: Move navigation part to base class
        self.pressed_item = self.itemAt(event.pos())
        node = self.node_from_instance(self.pressed_item)
        self.pressedPin = self.findPinNearPosition(event.pos())
        modifiers = event.modifiers()
        self.mousePressPose = event.pos()

        current_input_action = InputAction("temp", "temp", InputActionType.Mouse, event.button(), modifiers=modifiers)

        # hide nodebox
        if not isinstance(self.pressed_item, NodesBox) and self.node_box.isVisible():
            self.node_box.hide()
            self.node_box.lineEdit.clear()

        # pressed empty space
        if not self.pressed_item:
            # selection rect
            self.resizing = False
            if event.button() == QtCore.Qt.LeftButton and modifiers in [QtCore.Qt.NoModifier,
                                                                        QtCore.Qt.ShiftModifier,
                                                                        QtCore.Qt.ControlModifier,
                                                                        QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier]:
                self.manipulationMode = CanvasManipulationMode.SELECT
                self._selectionRect = SelectionRect(graph=self, mouseDownPos=self.mapToScene(event.pos()),
                                                    modifiers=modifiers)
                self._selectionRect.selectFullyIntersectedItems = True
                self._mouseDownSelection = [node for node in self.selectedNodes()]
                self._mouseDownConnectionsSelection = [node for node in self.selectedConnections()]
                if modifiers not in [QtCore.Qt.ShiftModifier, QtCore.Qt.ControlModifier]:
                    self.clearSelection()
                return
            else:
                if hasattr(self, "_selectionRect") and self._selectionRect is not None:
                    self._selectionRect.destroy()
                    self._selectionRect = None

        # canvas pan
        if current_input_action in InputManager()["Canvas.Pan"]:
            self.manipulationMode = CanvasManipulationMode.PAN
            self._lastPanPoint = self.mapToScene(event.pos())
            return

        # canvas zoom
        if current_input_action in InputManager()["Canvas.Zoom"]:
            self.manipulationMode = CanvasManipulationMode.ZOOM
            self._lastTransform = QtGui.QTransform(self.transform())
            self._lastSceneRect = self.sceneRect()
            self._lastSceneCenter = self._lastSceneRect.center()
            self._lastScenePos = self.mapToScene(event.pos())
            self._lastOffsetFromSceneCenter = self._lastScenePos - self._lastSceneCenter
            return

        # set connection
        if isinstance(self.pressed_item, UIConnection) and modifiers != QtCore.Qt.AltModifier:
            self.resizing = False
            if modifiers == QtCore.Qt.NoModifier and event.button() == QtCore.Qt.LeftButton:
                closestPin = self.findPinNearPosition(event.pos(), 20)
                if closestPin is not None:
                    if closestPin.direction == PinDirection.Input:
                        self.pressed_item.destinationPositionOverride = lambda: self.mapToScene(self.mousePos)
                    elif closestPin.direction == PinDirection.Output:
                        self.pressed_item.sourcePositionOverride = lambda: self.mapToScene(self.mousePos)
                    self.reconnectingWires.add(self.pressed_item)
                return

        if isinstance(self.pressed_item, UINodeBase):

            if isinstance(node, UINodeBase) and node.resizable:
                super(BlueprintCanvas, self).mousePressEvent(event)
                self.resizing = node.bResize
                node.setSelected(False)

            # drag chained nodes
            if current_input_action in InputManager()["Canvas.DragChainedNodes"]:
                if modifiers != QtCore.Qt.ShiftModifier:
                    self.clearSelection()
                node.setSelected(True)
                selectedNodes = self.selectedNodes()
                if len(selectedNodes) > 0:
                    for snode in selectedNodes:
                        for n in node.getChainedNodes():
                            n.setSelected(True)
                        snode.setSelected(True)
                self.manipulationMode = CanvasManipulationMode.MOVE
                return

            if modifiers in [QtCore.Qt.NoModifier, QtCore.Qt.AltModifier]:
                super(BlueprintCanvas, self).mousePressEvent(event)
            if modifiers == QtCore.Qt.ControlModifier and event.button() == QtCore.Qt.LeftButton:
                node.setSelected(not node.isSelected())
            if modifiers == QtCore.Qt.ShiftModifier:
                node.setSelected(True)

            if node.bResize:
                return

            if current_input_action in InputManager()["Canvas.DragNodes"]:
                self.manipulationMode = CanvasManipulationMode.MOVE
                if self.pressed_item.objectName() == "MouseLocked":
                    super(BlueprintCanvas, self).mousePressEvent(event)
                return

            # drag copy node
            if current_input_action in InputManager()["Canvas.DragCopyNodes"]:
                self.manipulationMode = CanvasManipulationMode.COPY
                return

            # resize node
            if node.resizable and node.should_resize(self.mapToScene(event.pos()))["resize"]:
                self.resizing = False
                if isinstance(node, UINodeBase) and node.resizable:
                    super(BlueprintCanvas, self).mousePressEvent(event)
                self.resizing = node.bResize
                node.setSelected(False)
                return

        # pressed on a pin
        if isinstance(self.pressed_item, UIPinBase):
            if event.button() == QtCore.Qt.LeftButton and modifiers == QtCore.Qt.NoModifier:
                self.pressed_item.topLevelItem().setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
                self.pressed_item.topLevelItem().setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, False)
                self._drawRealtimeLine = True
            elif event.button() == QtCore.Qt.LeftButton and modifiers == QtCore.Qt.ControlModifier:
                for wire in self.pressed_item.uiConnectionList:
                    if self.pressed_item.direction == PinDirection.Input:
                        wire.destinationPositionOverride = lambda: self.mapToScene(self.mousePos)
                    elif self.pressed_item.direction == PinDirection.Output:
                        wire.sourcePositionOverride = lambda: self.mapToScene(self.mousePos)
                    self.reconnectingWires.add(wire)
            if current_input_action in InputManager()["Canvas.DisconnectPin"]:
                self.removeEdgeCmd(self.pressed_item.connections)
                self._drawRealtimeLine = False

        self.resizing = False

    def mouseReleaseEvent(self, event):
        super(BlueprintCanvas, self).mouseReleaseEvent(event)

        modifiers = event.modifiers()

        # find possible actions after mouse release
        self.mouseReleasePos = event.pos()
        self.released_item = self.itemAt(event.pos())
        self.releasedPin = self.findPinNearPosition(event.pos())

        if len(self.reconnectingWires) > 0:
            if self.releasedPin is not None:
                for wire in self.reconnectingWires:
                    if wire.destinationPositionOverride is not None:
                        lhsPin = wire.source()
                        self.removeConnection(wire)
                        self.connect_pins_internal(lhsPin, self.releasedPin)
                    elif wire.sourcePositionOverride is not None:
                        rhsPin = wire.destination()
                        self.removeConnection(wire)
                        self.connect_pins_internal(self.releasedPin, rhsPin)
            else:
                for wire in self.reconnectingWires:
                    self.removeConnection(wire)

            for wire in self.reconnectingWires:
                wire.sourcePositionOverride = None
                wire.destinationPositionOverride = None
            self.reconnectingWires.clear()

        for n in self.get_all_nodes():
            # if not n.isCommentNode:
            n.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
            n.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)

        if self._drawRealtimeLine:
            self._drawRealtimeLine = False
            if self.realTimeLine in self.scene().items():
                self.remove_item_by_name('RealTimeLine')

        if self.manipulationMode == CanvasManipulationMode.SELECT:
            self._selectionRect.destroy()
            self._selectionRect = None

        if event.button() == QtCore.Qt.RightButton and modifiers == QtCore.Qt.NoModifier:
            # show nodebox only if drag is small and no items under cursor
            if self.pressed_item is None or (isinstance(self.pressed_item, UINodeBase)):
                if modifiers == QtCore.Qt.NoModifier:
                    dragDiff = self.mapToScene(self.mousePressPose) - self.mapToScene(event.pos())
                    if all([abs(i) < 0.4 for i in [dragDiff.x(), dragDiff.y()]]):
                        self.showNodeBox()
        elif event.button() == QtCore.Qt.RightButton and modifiers == QtCore.Qt.ControlModifier:
            self.menu.exec_(QtGui.QCursor.pos())
        elif event.button() == QtCore.Qt.LeftButton and self.releasedPin is None:
            if isinstance(self.pressed_item, UIPinBase) and not self.resizing and modifiers == QtCore.Qt.NoModifier:
                # suggest nodes that can be connected to pressed pin
                self.showNodeBox(self.pressed_item.direction)
        self.manipulationMode = CanvasManipulationMode.NONE
        if not self.resizing:
            p_itm = self.pressedPin
            r_itm = self.releasedPin
            do_connect = True
            for i in [p_itm, r_itm]:
                if not i:
                    do_connect = False
                    break
                if not isinstance(i, UIPinBase):
                    do_connect = False
                    break
            if p_itm and r_itm:
                if p_itm.__class__.__name__ == UIPinBase.__name__ and r_itm.__class__.__name__ == UIPinBase.__name__:
                    if cycleCheck(p_itm, r_itm):
                        # print('cycles are not allowed')
                        do_connect = False

            if do_connect:
                if p_itm is not r_itm:
                    self.connect_pins(p_itm, r_itm)

        # We don't want properties view go crazy
        # check if same node pressed and released left mouse button and not moved
        releasedNode = self.node_from_instance(self.released_item)
        pressedNode = self.node_from_instance(self.pressed_item)
        manhattanLengthTest = (self.mousePressPose - event.pos()).manhattanLength() <= 2
        if all([event.button() == QtCore.Qt.LeftButton, releasedNode is not None, pressedNode is not None, pressedNode == releasedNode, manhattanLengthTest]):
            pass
            # check if clicking on node action button
            # if self.released_item is not None:
            #     if isinstance(self.released_item.parentItem(), NodeActionButtonBase):
            #         return
            #     self.tryFillPropertiesView(pressedNode)
        self.resizing = False
        self.updateReroutes(event, False)

    def mouseMoveEvent(self, event):
        # TODO: Move navigation part to base class
        self.mousePos = event.pos()
        mouseDelta = QtCore.QPointF(self.mousePos) - self._lastMousePos
        modifiers = event.modifiers()
        itemUnderMouse = self.itemAt(event.pos())
        node = self.node_from_instance(itemUnderMouse)
        if itemUnderMouse and isinstance(node, UINodeBase) and node.resizable:
            resizeOpts = node.should_resize(self.mapToScene(event.pos()))
            if resizeOpts["resize"] or node.bResize:
                if resizeOpts["direction"] in [(1, 0), (-1, 0)]:
                    self.viewport().setCursor(QtCore.Qt.SizeHorCursor)
                elif resizeOpts["direction"] in [(0, 1), (0, -1)]:
                    self.viewport().setCursor(QtCore.Qt.SizeVerCursor)
                elif resizeOpts["direction"] in [(1, 1), (-1, -1)]:
                    self.viewport().setCursor(QtCore.Qt.SizeFDiagCursor)
                elif resizeOpts["direction"] in [(-1, 1), (1, -1)]:
                    self.viewport().setCursor(QtCore.Qt.SizeBDiagCursor)
            elif not self.resizing:
                self.viewport().setCursor(QtCore.Qt.ArrowCursor)
        elif itemUnderMouse is None and not self.resizing:
            self.viewport().setCursor(QtCore.Qt.ArrowCursor)

        if self._drawRealtimeLine:
            if isinstance(self.pressed_item, PinBase):
                if self.pressed_item.parentItem().isSelected():
                    self.pressed_item.parentItem().setSelected(False)
            if self.realTimeLine not in self.scene().items():
                self.scene().addItem(self.realTimeLine)

            self.updateReroutes(event, True)

            p1 = self.pressed_item.scenePos() + self.pressed_item.pinCenter()
            p2 = self.mapToScene(self.mousePos)

            mouseRect = QtCore.QRect(QtCore.QPoint(event.pos().x() - 5, event.pos().y() - 4),
                                     QtCore.QPoint(event.pos().x() + 5, event.pos().y() + 4))
            hoverItems = self.items(mouseRect)

            hoveredPins = [pin for pin in hoverItems if isinstance(pin, UIPinBase)]
            if len(hoveredPins) > 0:
                item = hoveredPins[0]
                if isinstance(item, UIPinBase) and isinstance(self.pressed_item, UIPinBase):
                    canBeConnected = canConnectPins(self.pressed_item._raw_pin, item._raw_pin)
                    self.realTimeLine.setPen(self.realTimeLineValidPen if canBeConnected else self.realTimeLineInvalidPen)
                    if canBeConnected:
                        p2 = item.scenePos() + item.pinCenter()
            else:
                self.realTimeLine.setPen(self.realTimeLineNormalPen)

            distance = p2.x() - p1.x()
            multiply = 3
            path = QtGui.QPainterPath()
            path.moveTo(p1)
            path.cubicTo(QtCore.QPoint(p1.x() + distance / multiply, p1.y()),
                         QtCore.QPoint(p2.x() - distance / 2, p2.y()), p2)
            self.realTimeLine.setPath(path)
            if modifiers == QtCore.Qt.AltModifier:
                self._drawRealtimeLine = False
                if self.realTimeLine in self.scene().items():
                    self.remove_item_by_name('RealTimeLine')
                rerouteNode = self.getRerouteNode(event.pos())
                self.clearSelection()
                rerouteNode.setSelected(True)
                for inp in rerouteNode.ui_inputs.values():
                    if canConnectPins(self.pressed_item._raw_pin, inp._raw_pin):
                        self.connect_pins(self.pressed_item, inp)
                        break
                for out in rerouteNode.ui_outputs.values():
                    if canConnectPins(self.pressed_item._raw_pin, out._raw_pin):
                        self.connect_pins(self.pressed_item, out)
                        break
                self.pressed_item = rerouteNode
                self.manipulationMode = CanvasManipulationMode.MOVE
        if self.manipulationMode == CanvasManipulationMode.SELECT:
            dragPoint = self.mapToScene(event.pos())
            self._selectionRect.setDragPoint(dragPoint, modifiers)
            # This logic allows users to use ctrl and shift with rectangle
            # select to add / remove nodes.

            nodes = self.get_all_nodes()

            if modifiers == QtCore.Qt.ControlModifier:
                # handle nodes
                for node in nodes:
                    if node in self._mouseDownSelection:
                        if node.isSelected() and self._selectionRect.collidesWithItem(node):
                            node.setSelected(False)
                        elif not node.isSelected() and not self._selectionRect.collidesWithItem(node):
                            node.setSelected(True)
                    else:
                        if not node.isSelected() and self._selectionRect.collidesWithItem(node):
                            node.setSelected(True)
                        elif node.isSelected() and not self._selectionRect.collidesWithItem(node):
                            if node not in self._mouseDownSelection:
                                node.setSelected(False)

                # handle connections
                for wire in self.connections.values():
                    if wire in self._mouseDownConnectionsSelection:
                        if wire.isSelected() and QtWidgets.QGraphicsWidget.collidesWithItem(self._selectionRect, wire):
                            wire.setSelected(False)
                        elif not wire.isSelected() and not QtWidgets.QGraphicsWidget.collidesWithItem(self._selectionRect, wire):
                            wire.setSelected(True)
                    else:
                        if not wire.isSelected() and QtWidgets.QGraphicsWidget.collidesWithItem(self._selectionRect, wire):
                            wire.setSelected(True)
                        elif wire.isSelected() and not QtWidgets.QGraphicsWidget.collidesWithItem(self._selectionRect, wire):
                            if wire not in self._mouseDownConnectionsSelection:
                                wire.setSelected(False)

            elif modifiers == QtCore.Qt.ShiftModifier:
                for node in nodes:
                    if not node.isSelected() and self._selectionRect.collidesWithItem(node):
                        node.setSelected(True)
                    elif node.isSelected() and not self._selectionRect.collidesWithItem(node):
                        if node not in self._mouseDownSelection:
                            node.setSelected(False)

                for wire in self.connections.values():
                    if not wire.isSelected() and QtWidgets.QGraphicsWidget.collidesWithItem(self._selectionRect, wire):
                        wire.setSelected(True)
                    elif wire.isSelected() and not QtWidgets.QGraphicsWidget.collidesWithItem(self._selectionRect, wire):
                        if wire not in self._mouseDownConnectionsSelection:
                            wire.setSelected(False)

            elif modifiers == QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier:
                for node in nodes:
                    if self._selectionRect.collidesWithItem(node):
                        node.setSelected(False)

                for wire in self.connections.values():
                    if QtWidgets.QGraphicsWidget.collidesWithItem(self._selectionRect, wire):
                        wire.setSelected(False)
            else:
                self.clearSelection()
                for node in nodes:
                    # if node not in [self.inputsItem,self.outputsItem]:
                    if not node.isSelected() and self._selectionRect.collidesWithItem(node):
                        node.setSelected(True)
                    elif node.isSelected() and not self._selectionRect.collidesWithItem(node):
                        node.setSelected(False)

                for wire in self.connections.values():
                    if not wire.isSelected() and QtWidgets.QGraphicsWidget.collidesWithItem(self._selectionRect, wire):
                        wire.setSelected(True)
                    elif wire.isSelected() and not QtWidgets.QGraphicsWidget.collidesWithItem(self._selectionRect, wire):
                        wire.setSelected(False)
        elif self.manipulationMode == CanvasManipulationMode.MOVE:
            # TODO: do not change object names. Rewrite with flag e.g. `bMovementLocked`
            if self.pressed_item.objectName() == "MouseLocked":
                super(BlueprintCanvas, self).mouseMoveEvent(event)
            else:
                newPos = self.mapToScene(event.pos())
                scaledDelta = mouseDelta / self.currentViewScale()

                selectedNodes = self.selectedNodes()
                # Apply the delta to each selected node
                for node in selectedNodes:
                    node.translate(scaledDelta.x(), scaledDelta.y())

                    if node.isReroute() and modifiers == QtCore.Qt.AltModifier:
                        mouseRect = QtCore.QRect(QtCore.QPoint(event.pos().x() - 1, event.pos().y() - 1),
                                                 QtCore.QPoint(event.pos().x() + 1, event.pos().y() + 1))
                        hoverItems = self.items(mouseRect)
                        newOuts = []
                        newIns = []
                        for item in hoverItems:
                            if isinstance(item, UIConnection):
                                if list(node.ui_inputs.values())[0].connections and list(node.ui_outputs.values())[0].connections:
                                    if item.source() == list(node.ui_inputs.values())[0].connections[0].source():
                                        newOuts.append([item.destination(), item.drawDestination])
                                    if item.destination() == list(node.ui_outputs.values())[0].connections[0].destination():
                                        newIns.append([item.source(), item.drawSource])
                        for out in newOuts:
                            self.connect_pins(list(node.ui_outputs.values())[0], out[0])
                        for inp in newIns:
                            self.connect_pins(inp[0], list(node.ui_inputs.values())[0])
        elif self.manipulationMode == CanvasManipulationMode.PAN:
            self.pan(mouseDelta)
        elif self.manipulationMode == CanvasManipulationMode.ZOOM:
            zoom_factor = 1.0
            if mouseDelta.x() > 0:
                zoom_factor = 1.0 + mouseDelta.x() / 100.0
            else:
                zoom_factor = 1.0 / (1.0 + abs(mouseDelta.x()) / 100.0)
            self.zoom(zoom_factor)
        elif self.manipulationMode == CanvasManipulationMode.COPY:
            delta = self.mousePos - self.mousePressPose
            if delta.manhattanLength() > 15:
                self.manipulationMode = CanvasManipulationMode.MOVE
                selectedNodes = self.selectedNodes()
                copiedNodes = self.copyNodes(toClipBoard=False)
                self.pasteNodes(move=False, data=copiedNodes)
                scaledDelta = delta / self.currentViewScale()
                for node in self.selectedNodes():
                    node.translate(scaledDelta.x(), scaledDelta.y())
        else:
            super(BlueprintCanvas, self).mouseMoveEvent(event)
        self.autoPanController.Tick(self.viewport().rect(), event.pos())
        self._lastMousePos = event.pos()

    def dragEnterEvent(self, event):
        super(BlueprintCanvas, self).dragEnterEvent(event)
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                url = urls[0]
                if url.isLocalFile():
                    filePath = url.toLocalFile()
                    if filePath.endswith(".pygraph"):
                        with open(filePath, 'r') as f:
                            data = json.load(f)
                            if "fileVersion" in data:
                                event.accept()
                                self.dropCallback = partial(self.getApp().loadFromFileChecked, filePath)
                                return
                    elif filePath.endswith(".compound"):
                        with open(filePath, 'r') as f:
                            data = json.load(f)

                            def spawnCompoundFromData(data):
                                mousePos = self.mapToScene(self.mousePos)
                                compound = self.spawnNode("compound", mousePos.x(), mousePos.y())
                                compound.assignData(data)
                            event.accept()
                            self.dropCallback = partial(spawnCompoundFromData, data)
                            return
                    elif filePath.endswith(".pynode"):
                        with open(filePath, 'r') as f:
                            data = f.read()

                            def spawnPyNodeFromData(data):
                                mousePos = self.mapToScene(self.mousePos)
                                compound = self.spawnNode("pythonNode", mousePos.x(), mousePos.y())
                                compound.tryApplyNodeData(data)
                            event.accept()
                            self.dropCallback = partial(spawnPyNodeFromData, data)
                            return
        elif event.mimeData().hasFormat('text/plain'):
            scenePos = self.mapToScene(event.pos())
            event.accept()
            mime = str(event.mimeData().text())
            jsonData = json.loads(mime)

            packageName = jsonData["package"]
            nodeType = jsonData["type"]
            libName = jsonData["lib"]
            name = nodeType

            node_template = NodeBase.json_template()
            node_template['package'] = packageName
            node_template['lib'] = libName
            node_template['type'] = nodeType
            node_template['name'] = name
            node_template['x'] = scenePos.x()
            node_template['y'] = scenePos.y()
            node_template['meta']['label'] = nodeType
            node_template['uuid'] = str(uuid.uuid4())
            try:
                self.tempnode.isTemp = False
                self.tempnode = None
            except Exception as e:
                pass
            self.tempnode = self._createNode(node_template)
            if jsonData["bPyNode"] or jsonData["bCompoundNode"]:
                self.tempnode.rebuild()
            if self.tempnode:
                self.tempnode.isTemp = True
            self.hoverItems = []

    def dragMoveEvent(self, event):
        self.mousePos = event.pos()
        scenePos = self.mapToScene(self.mousePos)
        if self.dropCallback is not None:
            event.accept()
        elif event.mimeData().hasFormat('text/plain'):
            event.setDropAction(QtCore.Qt.MoveAction)
            event.accept()
            if self.tempnode:
                self.tempnode.setPos((self.tempnode.w / -2) + scenePos.x(), scenePos.y())
                mouseRect = QtCore.QRect(QtCore.QPoint(scenePos.x() - 1, scenePos.y() - 1),
                                         QtCore.QPoint(scenePos.x() + 1, scenePos.y() + 1))
                hoverItems = self.scene().items(mouseRect)
                for item in hoverItems:
                    if isinstance(item, UIConnection):
                        valid = False
                        for inp in self.tempnode.ui_inputs.values():
                            if canConnectPins(item.source()._raw_pin, inp._raw_pin):
                                valid = True
                        for out in self.tempnode.ui_outputs.values():
                            if canConnectPins(out._raw_pin, item.destination()._raw_pin):
                                valid = True
                        if valid:
                            self.hoverItems.append(item)
                            item.drawThick()
                for item in self.hoverItems:
                    if item not in hoverItems:
                        self.hoverItems.remove(item)
                        if isinstance(item, UIConnection):
                            item.restoreThick()
                    else:
                        if isinstance(item, UIConnection):
                            item.drawThick()
        else:
            super(BlueprintCanvas, self).dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        super(BlueprintCanvas, self).dragLeaveEvent(event)
        self.dropCallback = None
        if self.tempnode:
            self.tempnode._rawNode.kill()
            self.tempnode = None

    def dropEvent(self, event):
        if self.dropCallback is not None:
            self.dropCallback()
            self.dropCallback = None
        scenePos = self.mapToScene(event.pos())
        x = scenePos.x()
        y = scenePos.y()

        if event.mimeData().hasFormat('text/plain'):
            jsonData = json.loads(event.mimeData().text())

            # try load mime data text as json
            # in case if it is a variable
            # if no keyboard modifires create context menu with two actions
            # for creating getter or setter
            # if control - create getter, if alt - create setter
            packageName = jsonData["package"]
            nodeType = jsonData["type"]
            libName = jsonData['lib']
            name = nodeType
            dropItem = self.node_from_instance(self.itemAt(scenePos.toPoint()))
            if not dropItem or isinstance(dropItem, UINodeBase) or isinstance(dropItem, UIPinBase) or isinstance(dropItem, UIConnection):
                node_template = NodeBase.json_template()
                node_template['package'] = packageName
                node_template['lib'] = libName
                node_template['type'] = nodeType
                node_template['name'] = name
                node_template['x'] = x
                node_template['y'] = y
                node_template['meta']['label'] = nodeType
                node_template['uuid'] = str(uuid.uuid4())
                if self.tempnode:
                    self.tempnode.isTemp = False
                    self.tempnode.update()
                    node = self.tempnode
                    self.tempnode = None
                    for it in self.items(scenePos.toPoint()):
                        if isinstance(it, UIPinBase):
                            dropItem = it
                            break
                        elif isinstance(it, UIConnection):
                            dropItem = it
                            break
                    node.eventDropOnCanvas()
                else:
                    node = self.createNode(node_template)

                nodeInputs = node.namePinInputsMap
                nodeOutputs = node.namePinOutputsMap

                if isinstance(dropItem, UIPinBase):
                    node.setPos(x - node.boundingRect().width(), y)
                    for inp in nodeInputs.values():
                        if canConnectPins(dropItem._raw_pin, inp._raw_pin):
                            if dropItem.isExec():
                                dropItem._raw_pin.disconnectAll()
                            self.connect_pins(dropItem, inp)
                            node.setPos(x + node.boundingRect().width(), y)
                            break
                    for out in nodeOutputs.values():
                        if canConnectPins(out._raw_pin, dropItem._raw_pin):
                            self.connect_pins(out, dropItem)
                            node.setPos(x - node.boundingRect().width(), y)
                            break
                elif isinstance(dropItem, UIConnection):
                    for inp in nodeInputs.values():
                        if canConnectPins(dropItem.source()._raw_pin, inp._raw_pin):
                            if dropItem.source().isExec():
                                dropItem.source()._raw_pin.disconnectAll()
                            self.connect_pins(dropItem.source(), inp)
                            break
                    for out in nodeOutputs.values():
                        if canConnectPins(out._raw_pin, dropItem.destination()._raw_pin):
                            self.connect_pins(out, dropItem.destination())
                            break
                elif not dropItem:
                    self.hideNodeBox()
        super(BlueprintCanvas, self).dropEvent(event)




class BlueprintCanvasWidget(QtWidgets.QWidget):
    """
    docstring for BlueprintCanvasWidget.
    """
    def __init__(self, graph_manager, app_instance, parent=None):
        super(BlueprintCanvasWidget, self).__init__(parent)

        self.manager = graph_manager

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setSpacing(1)
        self.mainLayout.setContentsMargins(1, 1, 1, 1)
        self.setContentsMargins(1, 1, 1, 1)
        self.mainLayout.setObjectName("canvasWidgetMainLayout")
        self.pathLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addLayout(self.pathLayout)
        self.compoundPropertiesWidget = QtWidgets.QWidget()
        self.compoundPropertiesWidget.setContentsMargins(1, 1, 1, 1)
        self.compoundPropertiesWidget.setObjectName("compoundPropertiesWidget")
        self.compoundPropertiesLayout = QtWidgets.QHBoxLayout(self.compoundPropertiesWidget)
        self.compoundPropertiesLayout.setSpacing(1)
        self.compoundPropertiesLayout.setContentsMargins(1, 1, 1, 1)
        self.mainLayout.addWidget(self.compoundPropertiesWidget)

        self.canvas = BlueprintCanvas(graph_manager, app_instance)
        self.mainLayout.addWidget(self.canvas)

    def shutDown(self):
        self.canvas.shutDown()


def getRawNodeInstance(nodeClassName, packageName=None, libName=None, **kwargs):
    from Python.Core.NodeBase import NodeBase
    package = GET_PACKAGE_CHECKED(packageName)
    # try find function first
    if libName is not None:
        for key, lib in package.GetFunctionLibraries().items():
            foos = lib.getFunctions()
            if libName == key and nodeClassName in foos:
                return NodeBase.initializeFromFunction(foos[nodeClassName])

    # try find node class
    nodes = package.GetNodeClasses()
    if nodeClassName in nodes:
        return nodes[nodeClassName](nodeClassName, **kwargs)

    return None


def getNodeInstance(jsonTemplate, canvas, parentGraph=None):
    nodeClassName = jsonTemplate['type']
    nodeName = jsonTemplate['name']
    packageName = jsonTemplate['package']
    if 'lib' in jsonTemplate:
        libName = jsonTemplate['lib']
    else:
        libName = None

    kwargs = {}

    # if get var or set var, construct additional keyword arguments
    if jsonTemplate['type'] in ('getVar', 'setVar'):
        kwargs['var'] = canvas.graphManager.findVariableByUid(uuid.UUID(jsonTemplate['varUid']))

    raw_instance = getRawNodeInstance(nodeClassName, packageName=packageName, libName=libName, **kwargs)
    if not raw_instance:
        return None
    raw_instance.uid = uuid.UUID(jsonTemplate['uuid'])
    assert(raw_instance is not None), "Node {0} not found in package {1}".format(nodeClassName, packageName)
    instance = getUINodeInstance(raw_instance)
    if instance:
        canvas.add_node(instance, jsonTemplate, parentGraph=parentGraph)
    return instance
