## Copyright 2015-2019 Ilgar Lunin, Pedro Cabrera

## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at

##     http://www.apache.org/licenses/LICENSE-2.0

## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.


from Python.Packages.PyFlowBase.Nodes.switchOnString import switchOnString
from Python.Packages.PyFlowBase.Nodes.getVar import getVar
from Python.Packages.PyFlowBase.Nodes.setVar import setVar
from Python.Packages.PyFlowBase.Nodes.sequence import sequence
from Python.Packages.PyFlowBase.Nodes.pythonNode import pythonNode
from Python.Packages.PyFlowBase.Nodes.commentNode import commentNode
from Python.Packages.PyFlowBase.Nodes.stickyNote import stickyNote
from Python.Packages.PyFlowBase.Nodes.reroute import reroute
from Python.Packages.PyFlowBase.Nodes.rerouteExecs import rerouteExecs
from Python.Packages.PyFlowBase.Nodes.graphNodes import (
    graphInputs,
    graphOutputs
)
from Python.Packages.PyFlowBase.Nodes.floatRamp import floatRamp
from Python.Packages.PyFlowBase.Nodes.colorRamp import colorRamp

from Python.Packages.PyFlowBase.Nodes.compound import compound
from Python.Packages.PyFlowBase.Nodes.constant import constant
from Python.Packages.PyFlowBase.Nodes.convertTo import convertTo
from Python.Packages.PyFlowBase.Nodes.makeDict import makeDict
from Python.Packages.PyFlowBase.Nodes.makeAnyDict import makeAnyDict

from Python.Packages.PyFlowBase.Nodes.forLoopBegin import forLoopBegin
from Python.Packages.PyFlowBase.Nodes.whileLoopBegin import whileLoopBegin

from Python.Packages.PyFlowBase.Nodes.imageDisplay import imageDisplay
from Python.Packages.PyFlowBase.UI.UIImageDisplayNode import UIImageDisplayNode

from Python.Packages.PyFlowBase.UI.UISwitchOnStringNode import UISwitchOnString
from Python.Packages.PyFlowBase.UI.UIGetVarNode import UIGetVarNode
from Python.Packages.PyFlowBase.UI.UISetVarNode import UISetVarNode
from Python.Packages.PyFlowBase.UI.UISequenceNode import UISequenceNode
from Python.Packages.PyFlowBase.UI.UICommentNode import UICommentNode
from Python.Packages.PyFlowBase.UI.UIStickyNote import UIStickyNote
from Python.Packages.PyFlowBase.UI.UIRerouteNodeSmall import UIRerouteNodeSmall
from Python.Packages.PyFlowBase.UI.UIPythonNode import UIPythonNode
from Python.Packages.PyFlowBase.UI.UIGraphNodes import (
    UIGraphInputs,
    UIGraphOutputs
)
from Python.Packages.PyFlowBase.UI.UIFloatRamp import UIFloatRamp
from Python.Packages.PyFlowBase.UI.UIColorRamp import UIColorRamp

from Python.Packages.PyFlowBase.UI.UICompoundNode import UICompoundNode
from Python.Packages.PyFlowBase.UI.UIConstantNode import UIConstantNode
from Python.Packages.PyFlowBase.UI.UIConvertToNode import UIConvertToNode
from Python.Packages.PyFlowBase.UI.UIMakeDictNode import UIMakeDictNode
from Python.Packages.PyFlowBase.UI.UIForLoopBeginNode import UIForLoopBeginNode
from Python.Packages.PyFlowBase.UI.UIWhileLoopBeginNode import UIWhileLoopBeginNode

from Python.Core.UINodeBase import UINodeBase


def createUINode(raw_instance):
    if isinstance(raw_instance, getVar):
        return UIGetVarNode(raw_instance)
    if isinstance(raw_instance, setVar):
        return UISetVarNode(raw_instance)
    if isinstance(raw_instance, switchOnString):
        return UISwitchOnString(raw_instance)
    if isinstance(raw_instance, sequence):
        return UISequenceNode(raw_instance)
    if isinstance(raw_instance, commentNode):
        return UICommentNode(raw_instance)
    if isinstance(raw_instance, stickyNote):
        return UIStickyNote(raw_instance)
    if isinstance(raw_instance, reroute) or isinstance(raw_instance, rerouteExecs):
        return UIRerouteNodeSmall(raw_instance)
    if isinstance(raw_instance, graphInputs):
        return UIGraphInputs(raw_instance)
    if isinstance(raw_instance, graphOutputs):
        return UIGraphOutputs(raw_instance)
    if isinstance(raw_instance, compound):
        return UICompoundNode(raw_instance)
    if isinstance(raw_instance, pythonNode):
        return UIPythonNode(raw_instance)
    if isinstance(raw_instance, constant):
        return UIConstantNode(raw_instance)
    if isinstance(raw_instance, convertTo):
        return UIConvertToNode(raw_instance)
    if isinstance(raw_instance, makeDict):
        return UIMakeDictNode(raw_instance)
    if isinstance(raw_instance, makeAnyDict):
        return UIMakeDictNode(raw_instance)
    if isinstance(raw_instance, floatRamp):
        return UIFloatRamp(raw_instance)
    if isinstance(raw_instance, colorRamp):
        return UIColorRamp(raw_instance)
    if isinstance(raw_instance, imageDisplay):
        return UIImageDisplayNode(raw_instance)
    if isinstance(raw_instance,forLoopBegin):
        return UIForLoopBeginNode(raw_instance)
    if isinstance(raw_instance,whileLoopBegin):
        return UIWhileLoopBeginNode(raw_instance)
    return UINodeBase(raw_instance)
