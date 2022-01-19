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


from nine import str
from Python.UI.Tool.Tool import ShelfTool
from Python.Packages.PyFlowBase.Tools import RESOURCES_DIR
from Python.Packages.PyFlowBase.Core.Common import Direction

from PySide2 import QtGui
from PySide2.QtWidgets import QFileDialog


class AlignTopTool(ShelfTool):
    """docstring for AlignTopTool."""
    def __init__(self):
        super(AlignTopTool, self).__init__()

    @staticmethod
    def toolTip():
        return "Aligns selected nodes by top most node"

    @staticmethod
    def getIcon():
        return QtGui.QIcon(RESOURCES_DIR + "aligntop.png")

    @staticmethod
    def name():
        return str("AlignTopTool")

    def do(self):
        self.pyFlowInstance.getCanvas().alignSelectedNodes(Direction.Up)
