from Python.Core.NodeBase import NodeBase


class ListNode(NodeBase):
    def __init__(self, name, uid=None):
        super(ListNode, self).__init__(name, uid=None)

        self.data = []

    @staticmethod
    def category():
        return 'Utils'

    @staticmethod
    def description():
        return 'a list node'

    def set_data(self, data):
        self.data = data
