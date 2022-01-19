"""Base package
"""
PACKAGE_NAME = 'PyFlowBase'
from collections import OrderedDict

from Python.UI.UIInterfaces import IPackage

# Pins
from Python.Packages.PyFlowBase.Pins.AnyPin import AnyPin
from Python.Packages.PyFlowBase.Pins.BoolPin import BoolPin
from Python.Packages.PyFlowBase.Pins.ExecPin import ExecPin
from Python.Packages.PyFlowBase.Pins.FloatPin import FloatPin
from Python.Packages.PyFlowBase.Pins.IntPin import IntPin
from Python.Packages.PyFlowBase.Pins.StringPin import StringPin

# Function based nodes
from Python.Packages.PyFlowBase.FunctionLibraries.ArrayLib import ArrayLib
from Python.Packages.PyFlowBase.FunctionLibraries.BoolLib import BoolLib
from Python.Packages.PyFlowBase.FunctionLibraries.DefaultLib import DefaultLib
from Python.Packages.PyFlowBase.FunctionLibraries.FloatLib import FloatLib
from Python.Packages.PyFlowBase.FunctionLibraries.IntLib import IntLib
from Python.Packages.PyFlowBase.FunctionLibraries.MathLib import MathLib
from Python.Packages.PyFlowBase.FunctionLibraries.MathAbstractLib import MathAbstractLib
from Python.Packages.PyFlowBase.FunctionLibraries.RandomLib import RandomLib
from Python.Packages.PyFlowBase.FunctionLibraries.PathLib import PathLib

# Class based nodes
from Python.Packages.PyFlowBase.Nodes.branch import branch
from Python.Packages.PyFlowBase.Nodes.tick import tick
from Python.Packages.PyFlowBase.Nodes.charge import charge
from Python.Packages.PyFlowBase.Nodes.delay import delay
from Python.Packages.PyFlowBase.Nodes.deltaTime import deltaTime
from Python.Packages.PyFlowBase.Nodes.doN import doN
from Python.Packages.PyFlowBase.Nodes.doOnce import doOnce
from Python.Packages.PyFlowBase.Nodes.flipFlop import flipFlop
from Python.Packages.PyFlowBase.Nodes.forLoop import forLoop
from Python.Packages.PyFlowBase.Nodes.forLoopBegin import forLoopBegin
from Python.Packages.PyFlowBase.Nodes.loopEnd import loopEnd
from Python.Packages.PyFlowBase.Nodes.whileLoopBegin import whileLoopBegin
from Python.Packages.PyFlowBase.Nodes.forEachLoop import forEachLoop
from Python.Packages.PyFlowBase.Nodes.forLoopWithBreak import forLoopWithBreak
from Python.Packages.PyFlowBase.Nodes.retriggerableDelay import retriggerableDelay
from Python.Packages.PyFlowBase.Nodes.sequence import sequence
from Python.Packages.PyFlowBase.Nodes.switchOnString import switchOnString
from Python.Packages.PyFlowBase.Nodes.timer import timer
from Python.Packages.PyFlowBase.Nodes.whileLoop import whileLoop
from Python.Packages.PyFlowBase.Nodes.getVar import getVar
from Python.Packages.PyFlowBase.Nodes.setVar import setVar
from Python.Packages.PyFlowBase.Nodes.reroute import reroute
from Python.Packages.PyFlowBase.Nodes.rerouteExecs import rerouteExecs
from Python.Packages.PyFlowBase.Nodes.makeArray import makeArray
from Python.Packages.PyFlowBase.Nodes.makeList import makeList
from Python.Packages.PyFlowBase.Nodes.makeDict import makeDict
from Python.Packages.PyFlowBase.Nodes.makeAnyDict import makeAnyDict
from Python.Packages.PyFlowBase.Nodes.makeDictElement import makeDictElement
from Python.Packages.PyFlowBase.Nodes.dictKeys import dictKeys
from Python.Packages.PyFlowBase.Nodes.floatRamp import floatRamp
from Python.Packages.PyFlowBase.Nodes.colorRamp import colorRamp
from Python.Packages.PyFlowBase.Nodes.stringToArray import stringToArray
from Python.Packages.PyFlowBase.Nodes.cliexit import cliexit


from Python.Packages.PyFlowBase.Nodes.consoleOutput import consoleOutput
from Python.Packages.PyFlowBase.Nodes.address import address
from Python.Packages.PyFlowBase.Nodes.graphNodes import graphInputs, graphOutputs
from Python.Packages.PyFlowBase.Nodes.pythonNode import pythonNode
from Python.Packages.PyFlowBase.Nodes.compound import compound
from Python.Packages.PyFlowBase.Nodes.constant import constant
from Python.Packages.PyFlowBase.Nodes.convertTo import convertTo
from Python.Packages.PyFlowBase.Nodes.imageDisplay import imageDisplay


from Python.Packages.PyFlowBase.Nodes.commentNode import commentNode
from Python.Packages.PyFlowBase.Nodes.stickyNote import stickyNote

from Python.Packages.PyFlowBase.Tools.ScreenshotTool import ScreenshotTool
from Python.Packages.PyFlowBase.Tools.NodeBoxTool import NodeBoxTool
from Python.Packages.PyFlowBase.Tools.SearchResultsTool import SearchResultsTool
from Python.Packages.PyFlowBase.Tools.AlignLeftTool import AlignLeftTool
from Python.Packages.PyFlowBase.Tools.AlignRightTool import AlignRightTool
from Python.Packages.PyFlowBase.Tools.AlignTopTool import AlignTopTool
from Python.Packages.PyFlowBase.Tools.AlignBottomTool import AlignBottomTool
from Python.Packages.PyFlowBase.Tools.HistoryTool import HistoryTool
from Python.Packages.PyFlowBase.Tools.PropertiesTool import PropertiesTool
from Python.Packages.PyFlowBase.Tools.VariablesTool import VariablesTool
from Python.Packages.PyFlowBase.Tools.CompileTool import CompileTool
from Python.Packages.PyFlowBase.Tools.LoggerTool import LoggerTool

from Python.Packages.PyFlowBase.Exporters.PythonScriptExporter import PythonScriptExporter

# Factories
from Python.Packages.PyFlowBase.Factories.UIPinFactory import createUIPin
from Python.Packages.PyFlowBase.Factories.PinInputWidgetFactory import getInputWidget
from Python.Packages.PyFlowBase.Factories.UINodeFactory import createUINode

# Prefs widgets
from Python.Packages.PyFlowBase.PrefsWidgets.General import GeneralPreferences
from Python.Packages.PyFlowBase.PrefsWidgets.InputPrefs import InputPreferences
from Python.Packages.PyFlowBase.PrefsWidgets.ThemePrefs import ThemePreferences


_FOO_LIBS = {
    ArrayLib.__name__: ArrayLib(PACKAGE_NAME),
    BoolLib.__name__: BoolLib(PACKAGE_NAME),
    DefaultLib.__name__: DefaultLib(PACKAGE_NAME),
    FloatLib.__name__: FloatLib(PACKAGE_NAME),
    IntLib.__name__: IntLib(PACKAGE_NAME),
    MathLib.__name__: MathLib(PACKAGE_NAME),
    MathAbstractLib.__name__: MathAbstractLib(PACKAGE_NAME),
    RandomLib.__name__: RandomLib(PACKAGE_NAME),
    PathLib.__name__: PathLib(PACKAGE_NAME),
}


_NODES = {
    branch.__name__: branch,
    charge.__name__: charge,
    delay.__name__: delay,
    deltaTime.__name__: deltaTime,
    doN.__name__: doN,
    doOnce.__name__: doOnce,
    flipFlop.__name__: flipFlop,
    forLoop.__name__: forLoop,
    forLoopBegin.__name__: forLoopBegin,
    loopEnd.__name__: loopEnd,
    forLoopWithBreak.__name__: forLoopWithBreak,
    retriggerableDelay.__name__: retriggerableDelay,
    sequence.__name__: sequence,
    switchOnString.__name__: switchOnString,
    timer.__name__: timer,
    whileLoop.__name__: whileLoop,
    whileLoopBegin.__name__: whileLoopBegin,
    commentNode.__name__: commentNode,
    stickyNote.__name__: stickyNote,
    getVar.__name__: getVar,
    setVar.__name__: setVar,
    reroute.__name__: reroute,
    rerouteExecs.__name__: rerouteExecs,
    graphInputs.__name__: graphInputs,
    graphOutputs.__name__: graphOutputs,
    compound.__name__: compound,
    pythonNode.__name__: pythonNode,
    makeArray.__name__: makeArray,
    makeList.__name__: makeList,
    makeDict.__name__: makeDict,
    makeAnyDict.__name__: makeAnyDict,
    makeDictElement.__name__: makeDictElement,
    consoleOutput.__name__: consoleOutput,
    forEachLoop.__name__: forEachLoop,
    address.__name__: address,
    constant.__name__: constant,
    tick.__name__: tick,
    convertTo.__name__: convertTo,
    dictKeys.__name__: dictKeys,
    floatRamp.__name__: floatRamp,
    colorRamp.__name__: colorRamp,
    stringToArray.__name__: stringToArray,
    imageDisplay.__name__: imageDisplay,
    cliexit.__name__: cliexit
}

_PINS = {
    AnyPin.__name__: AnyPin,
    BoolPin.__name__: BoolPin,
    ExecPin.__name__: ExecPin,
    FloatPin.__name__: FloatPin,
    IntPin.__name__: IntPin,
    StringPin.__name__: StringPin,
}

# Toolbar will be created in following order
_TOOLS = OrderedDict()
_TOOLS[CompileTool.__name__] = CompileTool
_TOOLS[ScreenshotTool.__name__] = ScreenshotTool
_TOOLS[AlignLeftTool.__name__] = AlignLeftTool
_TOOLS[AlignRightTool.__name__] = AlignRightTool
_TOOLS[AlignTopTool.__name__] = AlignTopTool
_TOOLS[AlignBottomTool.__name__] = AlignBottomTool
_TOOLS[HistoryTool.__name__] = HistoryTool
_TOOLS[PropertiesTool.__name__] = PropertiesTool
_TOOLS[VariablesTool.__name__] = VariablesTool
_TOOLS[NodeBoxTool.__name__] = NodeBoxTool
_TOOLS[SearchResultsTool.__name__] = SearchResultsTool
_TOOLS[LoggerTool.__name__] = LoggerTool

_EXPORTERS = OrderedDict()
_EXPORTERS[PythonScriptExporter.__name__] = PythonScriptExporter


_PREFS_WIDGETS = OrderedDict()
_PREFS_WIDGETS["General"] = GeneralPreferences
_PREFS_WIDGETS["Input"] = InputPreferences
_PREFS_WIDGETS["Theme"] = ThemePreferences


class PyFlowBase(IPackage):
    """Base pyflow package
    """
    def __init__(self):
        super(PyFlowBase, self).__init__()

    @staticmethod
    def GetExporters():
        return _EXPORTERS

    @staticmethod
    def GetFunctionLibraries():
        return _FOO_LIBS

    @staticmethod
    def GetNodeClasses():
        return _NODES

    @staticmethod
    def GetPinClasses():
        return _PINS

    @staticmethod
    def GetToolClasses():
        return _TOOLS

    @staticmethod
    def UIPinsFactory():
        return createUIPin

    @staticmethod
    def UINodesFactory():
        return createUINode

    @staticmethod
    def PinsInputWidgetFactory():
        return getInputWidget

    @staticmethod
    def PrefsWidgets():
        return _PREFS_WIDGETS
