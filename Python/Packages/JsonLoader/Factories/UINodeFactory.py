# don't worry about the "Unsolved reference error",
# the path to the package will be added when __init__ te Factory folder
from Python.Packages.JsonLoader.Nodes.DictionaryNode import DictionaryNode
from Python.Packages.JsonLoader.Nodes.IntNode import IntNode
from Python.Packages.JsonLoader.Nodes.ListNode import ListNode
from Python.Packages.JsonLoader.Nodes.StringNode import StringNode

from Python.Packages.JsonLoader.Nodes.UI.UIDictionaryNode import UIDictionaryNode
from Python.Packages.JsonLoader.Nodes.UI.UIIntNode import UIIntNode
from Python.Packages.JsonLoader.Nodes.UI.UIListNode import UIListNode
from Python.Packages.JsonLoader.Nodes.UI.UIStringNode import UIStringNode

from Python.Core.UINodeBase import UINodeBase


def createUINode(raw_instance):
    if isinstance(raw_instance, DictionaryNode):
        return UIDictionaryNode(raw_instance)
    elif isinstance(raw_instance, IntNode):
        return UIIntNode(raw_instance)
    elif isinstance(raw_instance, ListNode):
        return UIListNode(raw_instance)
    elif isinstance(raw_instance, StringNode):
        return UIStringNode(raw_instance)
    else:
        return UINodeBase(raw_instance)