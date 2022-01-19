
class NodeActionButtonInfo(object):
    """Used to populate node header with buttons representing node's actions from node's menu.

    See UINodeBase constructor and postCrate method.
    """

    def __init__(self, defaultSvgIcon, actionButtonClass=None):
        super(NodeActionButtonInfo, self).__init__()
        self._defaultSvgIcon = defaultSvgIcon
        self._actionButtonClass = actionButtonClass

    def actionButtonClass(self):
        return self._actionButtonClass

    def filePath(self):
        return self._defaultSvgIcon