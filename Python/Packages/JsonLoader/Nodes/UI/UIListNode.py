from Python.Core.UINodeBase import UINodeBase


class UIListNode(UINodeBase):
    def __init__(self, node):
        super(UIListNode, self).__init__(node)

    def post_create(self, json_template=None):
        super(UIListNode, self).post_create(json_template)