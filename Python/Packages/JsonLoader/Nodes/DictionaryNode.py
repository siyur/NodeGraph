from collections import OrderedDict
from Python.Core.NodeBase import NodeBase


class DictionaryNode(NodeBase):
    def __init__(self, name, uid=None):
        super(DictionaryNode, self).__init__(name, uid=None)

        self.data = OrderedDict()

    @staticmethod
    def category():
        return 'Utils'

    @staticmethod
    def description():
        return 'a dictionary node'

    def set_data(self, data):
        self.data = data
