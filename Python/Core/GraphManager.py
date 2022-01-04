from blinker import Signal
from Python.Core.GraphBase import GraphBase
from Python.Core.Common import \
    getUniqNameFromList, \
    SingletonDecorator
import Python.Version as Version

DEFAULT_GRAPH_NAME = str('root')


class GraphManager(object):
    """Data structure that holds graph tree

    This class switches active graph. Can insert or remove graphs to tree,
    can search nodes and variables across all graphs. Also this class responsible
    for giving unique names.
    """
    def __init__(self):
        super(GraphManager, self).__init__()
        self.terminationRequested = False  #: used by cli only
        self.graphChanged = Signal(object)
        self._graphs = {}
        self._active_graph = None
        self._active_graph = GraphBase(DEFAULT_GRAPH_NAME, self)

    def serialize(self):
        """Serializes itself to json.

        All child graphs will be serialized.

        :rtype: dict
        """
        saved = {}
        for graph in self._graphs.values():
            saved.update(graph.serialize())
        saved["fileVersion"] = str(Version.currentVersion())
        return saved

    def add(self, graph):
        """Adds graph to storage and ensures that graph name is unique

        :param graph: Graph to add
        :type graph: :class:`~Python.Core.GraphBase.GraphBase`
        """
        graph.name = self.get_uniq_graph_name(graph.name)
        self._graphs[graph.uid] = graph

    def clear(self, *args, **kwargs):
        """Wipes everything.
        """
        self._graphs.clear()
        self._graphs = {}
        del self._active_graph
        # create an empty new graph
        self._active_graph = GraphBase(DEFAULT_GRAPH_NAME, self)
        self.select_graph(self._active_graph)

    def select_graph(self, graph):
        """Sets supplied graph as active and fires event

        :param graph: Target graph
        :type graph: :class:`~PyFlow.Core.GraphBase.GraphBase`
        """
        for newGraph in self.get_all_graphs():
            if newGraph.name == graph.name:
                if newGraph.name != self.active_graph().name:
                    oldGraph = self.active_graph()
                    self._active_graph = newGraph
                    self.graphChanged.send(self.active_graph())
                    break

    def active_graph(self):
        """Returns active graph

        :rtype: :class:`~Python.Core.GraphBase.GraphBase`
        """
        return self._active_graph

    def get_all_graphs(self):
        """Returns all graphs

        :rtype: list(:class:`~Python.Core.GraphBase.GraphBase`)
        """
        return [g for g in self._graphs.values()]

    def get_uniq_graph_name(self, name):
        """Returns unique graph name

        :param name: Source name
        :type name: str
        :rtype: str
        """
        existing_names = [g.name for g in self.get_all_graphs()]
        return getUniqNameFromList(existing_names, name)

    def get_uniq_node_name(self, name):
        """Returns unique node name

        :param name: Source name
        :type name: str
        :rtype: str
        """
        existingNames = [n.name for n in self.get_all_nodes()]
        return getUniqNameFromList(existingNames, name)

    def get_all_nodes(self, class_name_filters=[]):
        """Returns all nodes across all graphs

        :param class_name_filters: If class name filters specified, only those node classes will be considered
        :type class_name_filters: list(str)
        :rtype: list(:class:`~PyFlow.Core.NodeBase.NodeBase`)
        """
        all_nodes = []
        for graph in self.get_all_graphs():
            if len(class_name_filters) == 0:
                all_nodes.extend(list(graph.get_nodes().values()))
            else:
                all_nodes.extend(
                    [node for node in graph.get_nodes().values() if node.__class__.__name__ in class_name_filters]
                )
        return all_nodes


@SingletonDecorator
class GraphManagerSingleton(object):
    """Singleton class that holds graph manager instance inside. Used by app as main graph manager
    """
    def __init__(self):
        self.man = GraphManager()

    def get(self):
        """Returns graph manager instance

        :rtype: :class:`~PyFlow.Core.GraphManager.GraphManager`
        """
        return self.man
