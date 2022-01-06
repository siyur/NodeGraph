import os
import pkgutil
from PySide2 import QtWidgets

__all__ = [
    "INITIALIZE",
    "GET_PACKAGES",
    "GET_PACKAGE_CHECKED",
    "GET_PACKAGE_PATH",
    "CreateRawPin",
]

__PACKAGES = {}
__PACKAGE_PATHS = {}

DEFAULT_PACKAGE_DIR = os.path.join(os.path.normpath(os.path.dirname(__file__)), "Packages")


def GET_PACKAGES():
    return __PACKAGES


def GET_PACKAGE_PATH(package_name):
    if package_name in __PACKAGE_PATHS:
        return __PACKAGE_PATHS[package_name]


def GET_PACKAGE_CHECKED(package_name):
    assert package_name in __PACKAGES
    return __PACKAGES[package_name]


def findPinClassByType(dataType):
    for package_name, package in GET_PACKAGES().items():
        pins = package.GetPinClasses()
        if dataType in pins:
            return pins[dataType]
    return None


def CreateRawPin(name, owning_node, dataType, direction, **kwds):
    pinClass = findPinClassByType(dataType)
    if pinClass is None:
        return None
    inst = pinClass(name, owning_node, direction, **kwds)
    return inst


def INITIALIZE(additionalPackageLocations=[], software=""):
    '''
    Necessary setup actions to Initialize the node graph app

    :param additionalPackageLocations:
    :param software:
    :return:
    '''
    from Python.Core.UINodeBase import REGISTER_UI_NODE_FACTORY
    from Python.Core.UIPinBase import REGISTER_UI_PIN_FACTORY
    from Python.ConfigManager import ConfigManager
    ConfigManager()

    # init __PACKAGES
    for importer, modname, ispkg in pkgutil.iter_modules([DEFAULT_PACKAGE_DIR]):
        try:
            if ispkg:
                mod = importer.find_module(modname).load_module(modname)
                package = getattr(mod, modname)()
                __PACKAGES[modname] = package
                __PACKAGE_PATHS[modname] = os.path.normpath(mod.__path__[0])
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, str("Fatal error"), "Error On Module %s :\n%s" % (modname, str(e)))
            continue

    registered_internal_pin_data_types = set()

    for name, package in __PACKAGES.items():
        packageName = package.__class__.__name__
        for node in package.GetNodeClasses().values():
            node._packageName = packageName

        uiPinsFactory = package.UIPinsFactory()
        if uiPinsFactory is not None:
            REGISTER_UI_PIN_FACTORY(packageName, uiPinsFactory)

        uiNodesFactory = package.UINodesFactory()
        if uiNodesFactory is not None:
            REGISTER_UI_NODE_FACTORY(packageName, uiNodesFactory)
