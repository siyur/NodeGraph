from PySide2 import QtWidgets

UI_PINS_FACTORIES = {}


def getUIPinInstance(owning_node, raw_instance):
    package_name = raw_instance.package_name
    instance = None
    if package_name in UI_PINS_FACTORIES:
        return UI_PINS_FACTORIES[package_name](owning_node, raw_instance)
    else:
        return UIPinBase(owning_node, raw_instance)


def REGISTER_UI_PIN_FACTORY(package_name, factory):
    """
    Called in Python.__init__.INITIALIZE function

    :param package_name:
    :param factory: dictionary that map packag name to ui_pin_factory script
    """
    if package_name not in UI_PINS_FACTORIES:
        UI_PINS_FACTORIES[package_name] = factory


class UIPinBase(QtWidgets.QGraphicsItem):
    def __init__(self, pin, parent=None):
        super(UIPinBase, self).__init__(parent=parent)
        self._pin = pin or None
