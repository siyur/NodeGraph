import uuid
import weakref

from copy import copy
from blinker import Signal
from Python.Core.Interface import IPin
from Python.Core.Common import \
    PinDirection, \
    disconnectPins, \
    getConnectedPins


class PinBase(IPin):
    """
    **Base class for pins**

    This is the base class that stores the data in the graph.
    This class is intended to be subclassed for each new registered data type you want to create.
    """

    _packageName = ""

    def __init__(self, name, owning_node, direction):
        super(PinBase, self).__init__()
        # signals
        self.serialization_hook = Signal()
        self.onPinConnected = Signal(object)
        self.onPinDisconnected = Signal(object)
        self.nameChanged = Signal(str)
        self.killed = Signal()
        self.onExecute = Signal(object)
        self.markedAsDirty = Signal()

        self.errorOccured = Signal(object)
        self.errorCleared = Signal()
        self._last_error = None

        # Access to the node
        self.owning_node = weakref.ref(owning_node)

        self._uid = uuid.uuid4()
        self.dirty = True
        self.affects = set()
        self.affected_by = set()

        self.name = name
        self._group = ""
        self.direction = direction

        # gui class weak ref
        self.ui = None
        self.__ui_Json_data = None

        # This is for to be able to connect pins by location on node
        self.pin_index = 0
        if direction == PinDirection.Input:
            self.pin_index = len(self.owning_node().ordered_inputs)
        if direction == PinDirection.Output:
            self.pin_index = len(self.owning_node().ordered_outputs)

    @property
    def group(self):
        """Pin group

        This is just a tag which can be used in ui level

        :rtype: str
        """
        return self._group

    @group.setter
    def group(self, value):
        self._group = str(value)

    @property
    def package_name(self):
        return self._packageName

    @property
    def uid(self):
        return self._uid

    @uid.setter
    def uid(self, value):
        if not value == self._uid:
            self._uid = value

    @property
    def linked_to(self):
        """store connection from pins

        from left hand side to right hand side

        .. code-block:: python

            {
                "lhsNodeName": "", "outPinId": 0,
                "rhsNodeName": "", "inPinId": 0
            }

        where pin id is order in which pin was added to node

        :returns: Serialized connections
        :rtype: list(dict)
        """
        result = list()
        if self.direction == PinDirection.Output:
            for i in getConnectedPins(self):
                connection = {"lhsNodeName": "", "outPinId": 0, "rhsNodeName": "", "inPinId": 0}
                connection["lhsNodeName"] = self.owning_node().getName()
                connection["lhsNodeUid"] = str(self.owning_node().uid)
                connection["outPinId"] = self.pin_index
                connection["rhsNodeName"] = i.owning_node().getName()
                connection["rhsNodeUid"] = str(i.owning_node().uid)
                connection["inPinId"] = i.pinIndex
                result.append(connection)

        if self.direction == PinDirection.Input:
            for i in getConnectedPins(self):
                connection = {"lhsNodeName": "", "outPinId": 0, "rhsNodeName": "", "inPinId": 0}
                connection["lhsNodeName"] = i.owning_node().getName()
                connection["lhsNodeUid"] = str(i.owning_node().uid)
                connection["outPinId"] = i.pinIndex
                connection["rhsNodeName"] = self.owning_node().getName()
                connection["rhsNodeUid"] = str(self.owning_node().uid)
                connection["inPinId"] = self.pin_index
                result.append(connection)
        return result

    def setName(self, name):
        """Sets pin name and fires events

        :param name: New pin name
        :type name: str
        :returns: Whether renaming performed or not
        :rtype: bool
        """
        if name == self.name:
            return False
        self.name = self.owning_node().get_uniq_pin_name(name)
        return True

    def get_name(self):
        return self.name

    def get_full_name(self):
        """Returns full pin name, including node name

        :rtype: str
        """
        return self.owning_node().name + '_' + self.name

    def set_ui(self, ui_wrapper):
        """Sets ui wrapper instance

        :param ui_wrapper: Whatever ui class that represents this pin
        """
        if self.ui is None:
            self.ui = weakref.ref(ui_wrapper)

    def get_ui(self):
        """Returns ui wrapper instance
        """
        return self.ui

    def clear_error(self):
        """Clears any last error on this pin and fires event
        """
        if self._last_error is not None:
            self._last_error = None
            self.errorCleared.send()

    def set_error(self, err):
        """Marks this pin as invalid by setting error message to it. Also fires event

        :param err: Error message
        :type err: str
        """
        self._last_error = str(err)
        self.errorOccured.send(self._last_error)

    def setDirty(self):
        """Sets dirty flag to True
        """
        self.dirty = True
        for i in self.affects:
            i.dirty = True
        self.markedAsDirty.send()

    def pin_connected(self, other):
        """
        triggered when pin is connected
        :param other: the other pin that this pin connects to
        """
        return

    def pin_disconnected(self, other):
        """
        triggered when pin is disconnected
        :param other: the other pin that this pin disconnects from
        """
        pass

    def disconnect_all(self):
        if self.direction == PinDirection.Input:
            for o in list(self.affected_by):
                disconnectPins(self, o)
            self.affected_by.clear()

        if self.direction == PinDirection.Output:
            for i in list(self.affects):
                disconnectPins(self, i)
            self.affects.clear()

    # PinBase methods
    def kill(self, *args, **kwargs):
        """Deletes this pin
        """
        self.disconnect_all()
        if self in self.owning_node().pins:
            self.owning_node().pins.remove(self)
        if self.uid in self.owning_node().pinsCreationOrder:
            self.owning_node().pinsCreationOrder.pop(self.uid)

    def call(self, *args, **kwargs):
        if self.owning_node().is_valid():
            self.onExecute.send(*args, **kwargs)

    def serialize(self):
        """Serializes itself to json

        :rtype: dict
        """
        data = {
            'name': self.name,
            'package': self.package_name,
            'fullName': self.get_full_name(),
            'dataType': self.__class__.__name__,
            'direction': int(self.direction),
            'uuid': str(self.uid),
            'linked_to': list(self.linked_to),
            'pin_index': self.pin_index,

        }

        # Wrapper class can subscribe to this signal and return
        # UI specific data which will be considered on serialization
        # Blinker returns a tuple (receiver, return val)
        wrapper_data = self.serialization_hook.send(self)
        if wrapper_data is not None:
            if len(wrapper_data) > 0:
                # We take return value from one wrapper
                data['ui'] = wrapper_data[0][1]
        return data

