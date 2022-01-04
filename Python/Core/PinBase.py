import uuid
import weakref

from Python.Core.Interface import IPin
from Python.Core.Common import \
    PinDirection, \
    disconnectPins

class PinBase(IPin):
    """
    **Base class for pins**

    This is the base class that stores the data in the graph.
    This class is intended to be subclassed for each new registered data type you want to create.
    """

    def __init__(self, name, owning_node, direction):
        _packageName = ""

        # Access to the node
        self._uid = uuid.uuid4()
        self.owning_node = weakref.ref(owning_node)
        self.affects = set()
        self.affected_by = set()

        self.name = name
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
    def package_name(self):
        return self._packageName

    @property
    def uid(self):
        return self._uid

    @uid.setter
    def uid(self, value):
        if not value == self._uid:
            self._uid = value

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

    def getName(self):
        return self.name

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
