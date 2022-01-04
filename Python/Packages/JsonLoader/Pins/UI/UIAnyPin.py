from Python.Core.UIPinBase import UIPinBase


class UIAnyPin(UIPinBase):
    def __init__(self, owning_node, raw_pin):
        """UI wrapper for :class:`PyFlow.Packages.PyFlowBase.Pins.AnyPin`

        :param owningNode: Owning node
        :type owningNode: :class:`PyFlow.UI.Canvas.NodeBase`
        :param raw_pin: PinBase reference
        :type raw_pin: :class:`PyFlow.Packages.PyFlowBase.Pins.AnyPin`
        """
        super(UIAnyPin, self).__init__(owning_node, raw_pin)
