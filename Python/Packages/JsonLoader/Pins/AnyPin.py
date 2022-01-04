
from Python.Core.PinBase import PinBase


class AnyPin(PinBase):
    def __init__(self, name, owning_node, direction, **kwargs):
        """
        :param name: Pin name
        :type name: string
        :param owningNode: Owning Node
        :type owningNode: :py:class:`PyFlow.Core.NodeBase.NodeBase`
        :param direction: PinDirection , can be input or output
        :type direction: :py:class:`PyFlow.Core.Common.PinDirection`
        """
        super(AnyPin, self).__init__(name, owning_node, direction, **kwargs)
