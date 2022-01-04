from Python.Core.UINodeBase import UINodeBase


class UIIntNode(UINodeBase):
    def __init__(self, node):
        super(UIIntNode, self).__init__(node)

    def post_create(self, json_template=None):
        super(UIIntNode, self).post_create(json_template)