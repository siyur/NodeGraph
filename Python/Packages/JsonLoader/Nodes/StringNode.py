from Python.Core.NodeBase import NodeBase


class StringNode(NodeBase):
    def __init__(self, name, uid=None):
        super(StringNode, self).__init__(name, uid=None)

        self.parent_pin = self.createInputPin("In", 'AnyPin')

    @staticmethod
    def category():
        return 'Utils'

    @staticmethod
    def description():
        return 'a string node'

