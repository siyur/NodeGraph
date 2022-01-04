import uuid
import weakref
from collections import Counter
from Python.Core.Interface import ISerializable
from Python.UI.Widgets.BlueprintCanvas import getRawNodeInstance
from Python.Core.Common import \
    arePinsConnected, \
    connectPins


class GraphBase(ISerializable):
    """Data structure representing a nodes graph

    :var name: name of the graph
    :vartype name: string

    :var graphManager: reference to graph manager
    :vartype graphManager: :class:`~PyFlow.Core.GraphManager.GraphManager`

    :var categoryChanged: signal emitted after graph category was changed
    :vartype categoryChanged: :class:`~blinker.base.Signal`

    :var childGraphs: a set of child graphs
    :vartype childGraphs: :class:`set`

    :var nodes: nodes storage. Dictionary with :class:`uuid.UUID` as key and :class:`~PyFlow.Core.NodeBase.NodeBase` as value
    :vartype nodes: :class:`dict`

    :var uid: Unique identifier
    :vartype uid: :class:`uuid.UUID`

    .. py:method:: parentGraph
        :property:

        :getter: Returns a reference to parent graph or None if this graph is root

        :setter: Sets new graph as new parent for this graph

    .. py:method:: name
        :property:

        :getter: Returns graph name

        :setter: Sets new graph name and fires signal

    .. py:method:: category
        :property:

        :getter: Returns graph category

        :setter: Sets new graph category and fires signal

    .. py:method:: pins
        :property:

        :getter: Returns dictionary with :class:`uuid.UUID` as key and :class:`~PyFlow.Core.PinBase.PinBase` as value
        :rtype: dict

    """
    def __init__(self, name, manager, uid=None, *args, **kwargs):
        super(GraphBase, self).__init__(*args, **kwargs)
        self.graphManager = manager

        self.__name = name
        self._nodes = {} # map node uid to node instance
        self.uid = uuid.uuid4() if uid is None else uid

        manager.add(self)

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = str(value) or "new graph"

    def serialize(self, *args, **kwargs):
        """Returns serialized representation of this graph

        :rtype: dict
        """
        result = {
            self.name:
                {
                    'nodes': [n.serialize() for n in self._nodes.values()]
                }
        }
        return result

    def populateFromJson(self, jsonData):
        """Populates itself from serialized data

        :param jsonData: serialized graph
        :type jsonData: dict
        """
        self.clear()
        self.name = self.graphManager.getUniqGraphName(jsonData['name'])

        # restore nodes
        for nodeJson in jsonData['nodes']:
            # check if variable getter or setter and pass variable
            node_args = ()
            node_kwargs = {}
            if nodeJson['type'] in ('getVar', 'setVar'):
                node_kwargs['var'] = self._vars[uuid.UUID(nodeJson['varUid'])]
            nodeJson['owningGraphName'] = self.name
            node = getRawNodeInstance(nodeJson['type'], packageName=nodeJson['package'], libName=nodeJson['lib'], *node_args, **node_kwargs)
            self.add_node(node, nodeJson)

        # restore connection
        for nodeJson in jsonData['nodes']:
            for nodeOutputJson in nodeJson['outputs']:
                for link_data in nodeOutputJson['linkedTo']:
                    try:
                        lhs_node = self._nodes[uuid.UUID(link_data["lhsNodeUid"])]
                    except Exception as e:
                        lhs_node = self.find_node(link_data["lhsNodeName"])

                    try:
                        lhs_pin = lhs_node.ordered_outputs[link_data["outPinId"]]
                    except Exception as e:
                        print("lhs_pin not found {0}".format(str(link_data)))
                        continue

                    try:
                        rhs_node = self._nodes[uuid.UUID(link_data["rhsNodeUid"])]
                    except Exception as e:
                        rhs_node = self.find_node(link_data["rhsNodeName"])

                    try:
                        rhs_pin = rhs_node.ordered_inputs[link_data["inPinId"]]
                    except Exception as e:
                        continue

                    if not arePinsConnected(lhs_pin, rhs_pin):
                        connected = connectPins(lhs_pin, rhs_pin)
                        # assert(connected is True), "Failed to restore connection"
                        if not connected:
                            print("Failed to restore connection", lhs_pin, rhs_pin)
                            connectPins(lhs_pin, rhs_pin)

    def clear(self):
        """Clears content of this graph
        """
        # clear itself
        for node in list(self._nodes.values()):
            node.kill()
        self._nodes.clear()

    def get_nodes(self):
        """Returns this graph's nodes storage

        :rtype: dict(:class:`~PyFlow.Core.NodeBase.NodeBase`)
        """
        return self._nodes

    def find_node(self, name):
        """Tries to find node by name

        :param name: Node name
        :type name: str or None
        """
        for i in self._nodes.values():
            if i.name == name:
                return i
        return None

    def add_node(self, node, jsonTemplate=None):
        """Adds node to storage

        :param node: Node to add
        :type node: NodeBase
        :param jsonTemplate: serialized representation of node. This used when graph deserialized to do custom stuff after node will be added.
        :type jsonTemplate: dict
        :rtype: bool
        """

        assert(node is not None), "failed to add node, None is passed"
        if node.uid in self._nodes:
            return False

        # node.graph = weakref.ref(self)
        node.graph = self
        if jsonTemplate is not None:
            jsonTemplate['name'] = self.graphManager.get_uniq_node_name(jsonTemplate['name'])
        else:
            node.setName(self.graphManager.getUniqNodeName(node.name))

        self._nodes[node.uid] = node
        node.post_create(jsonTemplate)
        return True
