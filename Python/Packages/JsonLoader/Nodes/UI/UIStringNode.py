from Python.Core.UINodeBase import UINodeBase


class UIStringNode(UINodeBase):
    def __init__(self, node):
        super(UIStringNode, self).__init__(node)

    def post_create(self, json_template=None):
        super(UIStringNode, self).post_create(json_template)