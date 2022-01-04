"""
Base package
"""

PACKAGE_NAME = 'JsonLoader'

from Python.UI.UIInterfaces import IPackage

# Pins
from Python.Packages.JsonLoader.Pins.AnyPin import AnyPin
# Class based nodes
from Python.Packages.JsonLoader.Nodes.DictionaryNode import DictionaryNode
from Python.Packages.JsonLoader.Nodes.IntNode import IntNode
from Python.Packages.JsonLoader.Nodes.ListNode import ListNode
from Python.Packages.JsonLoader.Nodes.StringNode import StringNode
# Factories
from Python.Packages.JsonLoader.Factories.UIPinFactory import createUIPin
from Python.Packages.JsonLoader.Factories.UINodeFactory import createUINode

_PINS = {
    AnyPin.__name__: AnyPin,
}

_NODES = {
    DictionaryNode.__name__: DictionaryNode,
    IntNode.__name__: IntNode,
    ListNode.__name__: ListNode,
    StringNode.__name__: StringNode,
}


class JsonLoader(IPackage):
    """Base pyflow package
    """
    def __init__(self):
        super(JsonLoader, self).__init__()

    @staticmethod
    def GetNodeClasses():
        return _NODES

    @staticmethod
    def GetPinClasses():
        return _PINS

    @staticmethod
    def UIPinsFactory():
        return createUIPin

    @staticmethod
    def UINodesFactory():
        return createUINode