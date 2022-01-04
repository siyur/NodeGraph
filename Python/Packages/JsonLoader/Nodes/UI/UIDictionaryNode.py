from Python.Core.UINodeBase import UINodeBase


class UIDictionaryNode(UINodeBase):
    def __init__(self, node):
        super(UIDictionaryNode, self).__init__(node)
        # Resizing Options
        self.resizable = True

    def post_create(self, json_template=None):
        super(UIDictionaryNode, self).post_create(json_template)