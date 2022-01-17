import uuid
import weakref

from copy import copy
from blinker import Signal
from Python.Core.Interface import IPin
from Python.Core.Common import \
    PinDirection, \
    disconnectPins, \
    getConnectedPins, \
    PinOptions, \
    push


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
        self._data = None
        self._default_value = None
        self.dirty = True
        self.affects = set()
        self.affected_by = set()

        self.name = name
        self._group = ""
        self.direction = direction

        # gui class weak ref
        self.ui = None
        self.__ui_json_data = None

        # registration
        self.owning_node().pins.add(self)
        self.owning_node().pins_creation_order[self.uid] = self

        # This is for to be able to connect pins by location on node
        self.pin_index = 0
        if direction == PinDirection.Input:
            self.pin_index = len(self.owning_node().ordered_inputs)
        if direction == PinDirection.Output:
            self.pin_index = len(self.owning_node().ordered_outputs)

    @property
    def ui_json_data(self):
        try:
            dt = self.__ui_json_data.copy()
            return dt
        except Exception as e:
            return None

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

    @property
    def data_type(self):
        """Returns data type of this pin

        :rtype: str
        """
        return self.__class__.__name__

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
        :type err: Exception
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

    def current_data(self):
        """Returns current value of this pin, without any graph evaluation

        :rtype: object
        """
        if self._data is None:
            return self._default_value
        return self._data

    def hasConnections(self):
        """Return the number of connections this pin has

        :rtype: int
        """
        num_connections = 0
        if self.direction == PinDirection.Input:
            num_connections += len(self.affected_by)
        elif self.direction == PinDirection.Output:
            num_connections += len(self.affects)
        return num_connections > 0

    def aboutToConnect(self, other):
        """This method called right before two pins connected

        :param other: Pin which this pin is going to be connected with
        :type other: :class:`~PyFlow.Core.PinBase.PinBase`
        """
        pass
        # if other.structureType != self.structureType:
        #     if self.optionEnabled(PinOptions.ChangeTypeOnConnection) or self.structureType == StructureType.Multi:
        #         self.changeStructure(other._currStructure)
        #         self.onPinConnected.send(other)

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
        if self.uid in self.owning_node().pins_creation_order:
            self.owning_node().pins_creation_order.pop(self.uid)

    def set_data(self, data):
        """Sets value to pin

        :param data: Data to be set
        :type data: object
        """
        # if self.super is None:
        #     return
        try:
            self.setDirty()
            # if isinstance(data, DictElement) and not self.optionEnabled(PinOptions.DictElementSupported):
            #     data = data[1]
            # if not self.isArray() and not self.isDict():
            #     if isinstance(data, DictElement):
            #         self._data = DictElement(data[0], self.super.processData(data[1]))
            #     else:
            #         if isinstance(data, list):
            #             self._data = data
            #         else:
            #             self._data = self.super.processData(data)
            # elif self.isArray():
            #     if isinstance(data, list):
            #         if self.validateArray(data, self.super.processData):
            #             self._data = data
            #         else:
            #             raise Exception("Some Array Input is not valid Data")
            #     else:
            #         self._data = [self.super.processData(data)]
            # elif self.isDict():
            #     if isinstance(data, PFDict):
            #         self._data = PFDict(data.keyType, data.valueType)
            #         for key, value in data.items():
            #             self._data[key] = self.super.processData(value)
            #     elif isinstance(data, DictElement) and len(data) == 2:
            #         self._data.clear()
            #         self._data[data[0]] = self.super.processData(data[1])

            if self.direction == PinDirection.Output:
                for i in self.affects:
                    i.setData(self.current_data())

            elif self.direction == PinDirection.Input and self.owning_node().__class__.__name__ == "compound":
                for i in self.affects:
                    i.setData(self.current_data())

            if self.direction == PinDirection.Input or self.optionEnabled(PinOptions.AlwaysPushDirty):
                push(self)
            self.clear_error()
            self.dataBeenSet.send(self)
        except Exception as exc:
            self.set_error(exc)
            self.setDirty()
        if self._last_error is not None:
            self.owning_node().set_error(self._last_error)
        wrapper = self.owning_node().get_ui()
        if wrapper:
            wrapper.update()

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
            'dataType': self.data_type,
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

