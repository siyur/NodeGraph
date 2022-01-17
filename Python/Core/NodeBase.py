import uuid

from blinker import Signal

from collections import OrderedDict
from Python import CreateRawPin
from Python.Core.Interface import INode
from Python.Core.Common import \
    PinSelectionGroup,\
    PinDirection, \
    getUniqNameFromList, \
    PinOptions


class NodePinsSuggestionsHelper(object):
    """Describes node's pins types and structs for inputs and outputs
    separately. Used by nodebox to suggest good nodes.
    """
    def __init__(self):
        super(NodePinsSuggestionsHelper, self).__init__()
        self.template = {'types': {'inputs': [], 'outputs': []},
                         'structs': {'inputs': [], 'outputs': []}}
        self.input_types = set()
        self.output_types = set()

    def add_input_data_type(self, data_type):
        self.input_types.add(data_type)

    def add_output_data_type(self, data_type):
        self.output_types.add(data_type)


class NodeBase(INode):
    _package_name = ""

    def __init__(self, name, uid=None):
        super(NodeBase, self).__init__()
        self.killed = Signal()
        self.tick = Signal(float)
        self.setDirty = Signal()

        self.dirty = True
        self._uid = uuid.uuid4() if uid is None else uid
        self.graph = None
        self.name = name
        self.pins_creation_order = OrderedDict()
        self._pins = set()
        self.x = 0.0
        self.y = 0.0

        self._last_error = None
        self.errorOccured = Signal(object)
        self.errorCleared = Signal()

        # Flags
        self._flags = PinOptions.Storable
        self._origFlags = self._flags

        # gui class weak ref
        self.ui = None
        self.__ui_json_data = None

    @property
    def package_name(self):
        return self._package_name

    @property
    def pins(self):
        return self._pins

    @property
    def uid(self):
        return self._uid

    @uid.setter
    def uid(self, value):
        if self.graph is not None:
            self.graph().get_nodes()[value] = self.graph().get_nodes().pop(self._uid)
        self._uid = value

    @property
    def inputs(self):
        """Returns all input pins. Dictionary generated every time property called, so cache it when possible.
        """
        result = OrderedDict()
        for pin in self.pins:
            if pin.direction == PinDirection.Input:
                result[pin.uid] = pin
        return result

    @property
    def ordered_inputs(self):
        result = {}
        sorted_inputs = sorted(self.inputs.values(), key=lambda x: x.pin_index)
        for inp in sorted_inputs:
            result[inp.pin_index] = inp
        return result

    @property
    def outputs(self):
        """Returns all output pins. Dictionary generated every time property called, so cache it when possible.
        """
        result = OrderedDict()
        for pin in self.pins:
            if pin.direction == PinDirection.Output:
                result[pin.uid] = pin
        return result

    @property
    def ordered_outputs(self):
        result = {}
        sorted_outputs = sorted(self.outputs.values(), key=lambda x: x.pin_index)
        for out in sorted_outputs:
            result[out.pin_index] = out
        return result

    @staticmethod
    def json_template():
        template = {'package': None,
                    'lib': None,
                    'type': None,
                    'owningGraphName': None,
                    'name': None,
                    'uuid': None,
                    'inputs': [],
                    'outputs': [],
                    'meta': {'var': {}},
                    'ui': {}
                    }
        return template

    @staticmethod
    def pin_type_hints():
        return NodePinsSuggestionsHelper()

    @staticmethod
    def description():
        return "Default node description"

    def is_valid(self):
        return self._last_error is None

    def get_last_error_message(self):
        return self._last_error

    def clear_error(self):
        self._last_error = None
        self.errorCleared.send()

    def set_error(self, err):
        self._last_error = str(err)
        self.errorOccured.send(self._last_error)

    def checkForErrors(self):
        failed_pins = {}
        for pin in self._pins:
            if pin._last_error is not None:
                failed_pins[pin.name] = pin._last_error
        if len(failed_pins):
            self._last_error = "Error on Pins:%s" % str(failed_pins)
        else:
            self.clear_error()
        ui = self.get_ui()
        if ui:
            ui.update()

    def get_ordered_pins(self):
        return self.pins_creation_order.values()

    def serialize(self):
        template = NodeBase.json_template()

        template['package'] = self.package_name
        template['type'] = __class__.__name__
        template['name'] = self.name
        template['owningGraphName'] = self.graph().name
        template['uuid'] = str(self.uid)
        template['inputs'] = [i.serialize() for i in self.inputs.values()]
        template['outputs'] = [o.serialize() for o in self.outputs.values()]
        template['meta']['label'] = self.name
        template['x'] = self.x
        template['y'] = self.y

        # if running with ui get ui wrapper data to save
        ui_wrapper = self.get_ui()
        if ui_wrapper:
            template['ui'] = ui_wrapper.serialization_hook()
        return template

    def get_ui(self):
        """Returns reference to gui if it exists

        :rtype: gui class instance or None
        """
        return self.ui

    def set_ui(self, ui_wrapper):
        """Sets gui

        :param ui_wrapper: gui class
        :type ui_wrapper: Whatever gui class
        """
        self.ui = ui_wrapper

    def set_position(self, x, y):
        """Sets node coordinate on canvas

        Used to correctly restore gui wrapper class

        :param x: X coordinate
        :type x: float
        :param y: Y coordinate
        :type y: float
        """
        self.x = x
        self.y = y

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = str(name)

    def get_uniq_pin_name(self, name):
        """Returns unique name for pin

        :param name: Target pin name
        :type name: str
        :rtype: str
        """
        pin_names = [i.name for i in list(list(self.inputs.values())) + list(list(self.outputs.values()))]
        return getUniqNameFromList(pin_names, name)

    def createInputPin(self, pinName, dataType, foo=None, constraint=None, group=""):
        """Creates input pin

        :param pinName: Pin name
        :type pinName: str
        :param dataType: Pin data type
        :type dataType: str
        :param foo: Pin callback. used for exec pins
        :type foo: function
        :param constraint: Pin constraint. Should be any hashable type. We use str
        :type constraint: object
        :param structConstraint: Pin struct constraint. Also should be hashable type
        :type structConstraint: object
        :param group: Pin group. Used only by ui wrapper
        :type group: str
        """
        pinName = self.get_uniq_pin_name(pinName)
        p = CreateRawPin(pinName, self, dataType, PinDirection.Input)
        p.group = group


        if foo:
            p.onExecute.connect(foo, weak=False)

        p.markedAsDirty.connect(self.setDirty.send)
        return p

    def createOutputPin(self, pinName, dataType, constraint=None, group=""):
        """Creates output pin

        :param pinName: Pin name
        :type pinName: str
        :param dataType: Pin data type
        :type dataType: str
        :param constraint: Pin constraint. Should be any hashable type. We use str
        :type constraint: object
        :param structConstraint: Pin struct constraint. Also should be hashable type
        :type structConstraint: object
        :param supportedPinDataTypes: List of allowed pin data types to be connected. Used by AnyPin
        :type supportedPinDataTypes: list(str)
        :param group: Pin group. Used only by ui wrapper
        :type group: str
        """
        pinName = self.get_uniq_pin_name(pinName)
        p = CreateRawPin(pinName, self, dataType, PinDirection.Output)
        p.group = group

        if constraint is not None:
            p.updateConstraint(constraint)
        return p

    def post_create(self, json_template=None):
        """Called after node was added to graph

        :param json_template: Serialized data of spawned node
        :type json_template: dict or None
        """
        if json_template is not None:
            self.uid = uuid.UUID(json_template['uuid'])
            self.set_name(json_template['name'])
            self.x = json_template['x']
            self.y = json_template['y']

            self.__ui_json_data = None

            # set pins data
            sorted_inputs = sorted(json_template['inputs'], key=lambda pin_dict: pin_dict["pinIndex"])
            for inp_Json in sorted_inputs:
                pin = self.get_pin_sg(str(inp_Json['name']), PinSelectionGroup.Inputs)
                pin.deserialize(inp_Json)

            sorted_outputs = sorted(json_template['outputs'], key=lambda pin_dict: pin_dict["pinIndex"])
            for out_Json in sorted_outputs:
                pin = self.get_pin_sg(str(out_Json['name']), PinSelectionGroup.Outputs)
                pin.deserialize(out_Json)

            # store data for wrapper
            if 'ui' in json_template:
                self.__ui_json_data = json_template['ui']

        self.checkForErrors()

    def kill(self, *args, **kwargs):

        if self.uid not in self.graph().get_nodes():
            return

        # self.killed.send()

        for pin in self.inputs.values():
            pin.kill()
        for pin in self.outputs.values():
            pin.kill()
        self.graph().get_nodes().pop(self.uid)

    def get_pin_sg(self, name, pins_selection_group=PinSelectionGroup.BothSides):
        """Tries to find pin by name and selection group

        :param name: Pin name to search
        :type name: str
        :param pins_selection_group: Side to search
        :type pins_selection_group: :class:`~PyFlow.Core.Common.PinSelectionGroup`
        :rtype: :class:`~PyFlow.Core.PinBase.PinBase` or None
        """
        inputs = self.inputs
        outputs = self.outputs
        if pins_selection_group == PinSelectionGroup.BothSides:
            for p in list(inputs.values()) + list(outputs.values()):
                if p.name == name:
                    return p
        elif pins_selection_group == PinSelectionGroup.Inputs:
            for p in list(inputs.values()):
                if p.name == name:
                    return p
        else:
            for p in list(outputs.values()):
                if p.name == name:
                    return p

    def checkForErrors(self):
        pass