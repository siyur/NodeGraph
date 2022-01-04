# don't worry about the "Unsolved reference error",
# the path to the package will be added when __init__ te Factory folder
from Python.Packages.JsonLoader.Pins import AnyPin

from Python.Packages.JsonLoader.Pins.UI import UIAnyPin

from Python.Core.UIPinBase import UIPinBase


def createUIPin(owning_node, raw_instance):
    if isinstance(raw_instance, AnyPin):
        return UIAnyPin(owning_node, raw_instance)
    else:
        return UIPinBase(owning_node, raw_instance)
