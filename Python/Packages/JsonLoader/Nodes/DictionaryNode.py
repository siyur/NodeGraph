from collections import OrderedDict
from Python.Core.NodeBase import NodeBase, NodePinsSuggestionsHelper


class DictionaryNode(NodeBase):
    def __init__(self, name, uid=None):
        super(DictionaryNode, self).__init__(name, uid=None)

        self.parent_pin = self.createInputPin("In", 'AnyPin')

        self.child_item = self.createOutputPin("Out test", 'AnyPin')


    @staticmethod
    def category():
        return 'Utils'

    @staticmethod
    def description():
        return 'a dictionary node'

    @staticmethod
    def pin_type_hints():
        helper = NodePinsSuggestionsHelper()
        helper.add_input_data_type('AnyPin')
        helper.add_output_data_type('AnyPin')
        return helper

    def set_data(self, data):
        self.data = data
