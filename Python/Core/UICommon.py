import uuid
from nine import IS_PYTHON2, str
if IS_PYTHON2:
    from aenum import IntEnum
else:
    from enum import IntEnum
from Python import GET_PACKAGES
from Python.UI.Utils.stylesheet import Colors
from Python.Core.Common import SingletonDecorator


def fetchPackageNames(graphJson):
    """Parses serialized graph and returns all package names it uses

    :param graphJson: Serialized graph
    :type graphJson: dict
    :rtyoe: list(str)
    """
    packages = set()

    def worker(graphData):
        for node in graphData["nodes"]:
            packages.add(node["package"])

            for inpJson in node["inputs"]:
                packages.add(inpJson['package'])

            for outJson in node["inputs"]:
                packages.add(outJson['package'])

            if "graphData" in node:
                worker(node["graphData"])
    worker(graphJson)
    return packages


def validateGraphDataPackages(graphData, missedPackages=set()):
    """Checks if packages used in serialized data accessible

    Missed packages will be added to output set

    :param graphData: Serialized graph
    :type graphData: dict
    :param missedPackages: Package names that missed
    :type missedPackages: str
    :rtype: bool
    """
    existingPackages = GET_PACKAGES().keys()
    graphPackages = fetchPackageNames(graphData)
    for pkg in graphPackages:
        if pkg not in existingPackages:
            missedPackages.add(pkg)
    return len(missedPackages) == 0


class CanvasManipulationMode(IntEnum):
    NONE = 0
    SELECT = 1
    PAN = 2
    MOVE = 3
    ZOOM = 4
    COPY = 5


@SingletonDecorator
class NodeDefaults(object):
    """docstring for NodeDefaults."""

    def __init__(self):
        self.__contentMargins = 5
        self.__layoutsSpacing = 5
        self.__cornersRoundFactor = 6
        self.__svgIconKey = "svgIcon"
        self.__layer = 1000000

    @property
    def Z_LAYER(self):
        return self.__layer

    @property
    def SVG_ICON_KEY(self):
        return self.__svgIconKey

    @property
    def DEFAULT_NODE_HEAD_COLOR(self):
        return Colors.NodeNameRectGreen

    @property
    def CONTENT_MARGINS(self):
        return self.__contentMargins

    @property
    def LAYOUTS_SPACING(self):
        return self.__layoutsSpacing

    @property
    def CORNERS_ROUND_FACTOR(self):
        return self.__cornersRoundFactor


@SingletonDecorator
class SessionDescriptor(object):
    def __init__(self):
        self.software = ""


def findPinClassByType(dataType):
    for package_name, package in GET_PACKAGES().items():
        pins = package.GetPinClasses()
        if dataType in pins:
            return pins[dataType]
    return None
