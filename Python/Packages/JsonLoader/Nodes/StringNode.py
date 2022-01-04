from Python.Core.NodeBase import NodeBase


class StringNode(NodeBase):
    def __init__(self, name, uid=None):
        super(StringNode, self).__init__(name, uid=None)

        self.data = ""

    @staticmethod
    def category():
        return 'Utils'

    @staticmethod
    def description():
        return 'a string node'

    def set_data(self, data):
        self.data = data
