from Python.Core.NodeBase import NodeBase


class IntNode(NodeBase):
    def __init__(self, name, uid=None):
        super(IntNode, self).__init__(name, uid=None)

        self.data = 0

    @staticmethod
    def category():
        return 'Utils'

    @staticmethod
    def description():
        return 'an integer node'

    def set_data(self, data):
        self.data = data
