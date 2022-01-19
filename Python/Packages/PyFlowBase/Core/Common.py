from nine import IS_PYTHON2
if IS_PYTHON2:
    from aenum import IntEnum
else:
    from enum import IntEnum

DEFAULT_IN_EXEC_NAME = str('inExec')
DEFAULT_OUT_EXEC_NAME = str('outExec')
DEFAULT_WIDGET_VARIANT = str('DefaultWidget')
REF = str('Reference')


class Direction(IntEnum):
    """ Direction identifiers
    """

    Left = 0  #: Left
    Right = 1  #: Right
    Up = 2  #: Up
    Down = 3  #: Down