"""
Contains all static functions and values

"""
import re
import time
from nine import IS_PYTHON2, str
if IS_PYTHON2:
    from aenum import IntEnum, Flag, auto
else:
    from enum import IntEnum, Flag, auto

#---------------------- classes -----------------------

class PinSelectionGroup(IntEnum):
    """Used in :meth:`~Python.Core.NodeBase.NodeBase.getPinSG` for optimization purposes
    """

    Inputs = 0  #: Input pins
    Outputs = 1  #: Outputs pins
    BothSides = 2  #: Both sides pins


class PinOptions(Flag):
    """Used to determine how Pin behaves.

    Apply flags on pin instances.

    .. seealso:: :meth:`~PyFlow.Core.PinBase.PinBase.enableOptions` :meth:`~PyFlow.Core.PinBase.PinBase.disableOptions`
    """

    ArraySupported = auto()  #: Pin can hold array data structure
    DictSupported = auto()  #: Pin can hold dict data structure
    SupportsOnlyArrays = auto()  #: Pin will only support other pins with array data structure

    AllowMultipleConnections = auto()  #: This enables pin to allow more that one input connection. See :func:`~PyFlow.Core.Common.connectPins`

    ChangeTypeOnConnection = auto()  #: Used by :class:`~PyFlow.Packages.PyFlowBase.Pins.AnyPin.AnyPin` to determine if it can change its data type on new connection.
    RenamingEnabled = auto()  #: Determines if pin can be renamed
    Dynamic = auto()  #: Specifies if pin was created dynamically (during program runtime)
    AlwaysPushDirty = auto()  #: Pin will always be seen as dirty (computation needed)
    Storable = auto()  #: Determines if pin data can be stored when pin serialized
    AllowAny = auto()  #: Special flag that allow a pin to be :class:`~PyFlow.Packages.PyFlowBase.Pins.AnyPin.AnyPin`, which means non typed without been marked as error. By default a :py:class:`PyFlow.Packages.PyFlowBase.Pins.AnyPin.AnyPin` need to be initialized with some data type, other defined pin. This flag overrides that. Used in lists and non typed nodes
    DictElementSupported = auto()  #: Dicts are constructed with :class:`DictElement` objects. So dict pins will only allow other dicts until this flag enabled. Used in :class:`~PyFlow.Packages.PyFlowBase.Nodes.makeDict` node


class PinDirection(IntEnum):
    """Determines whether it is input pin or output
    """

    Input = 0  #: Left side pins
    Output = 1  #: Right side pins


class SingletonDecorator:
    """Decorator to make class unique, so each time called same object returned
    """
    allInstances = []

    @staticmethod
    def destroyAll():
        for instance in SingletonDecorator.allInstances:
            instance.destroy()

    def __init__(self, cls):
        self.cls = cls
        self.instance = None
        self.allInstances.append(self)

    def destroy(self):
        del self.instance
        self.instance = None

    def __call__(self, *args, **kwds):
        if self.instance is None:
            self.instance = self.cls(*args, **kwds)

        return self.instance

#---------------------- methods ----------------------


def lerp(start, end, alpha):
    """Performs a linear interpolation

    >>> start + alpha * (end - start)

    :param start: start the value to interpolate from
    :param end: end the value to interpolate to
    :param alpha: alpha how far to interpolate
    :returns: The result of the linear interpolation
    """
    return (start + alpha * (end - start))

def clamp(n, vmin, vmax):
    """Computes the value of the first specified argument clamped to a range defined by the second and third specified arguments

    :param n: input Value
    :param vmin: MiniMum Value
    :param vmax: Maximum Value
    :returns: The clamped value of n
    """
    return max(min(n, vmax), vmin)

def GetRangePct(MinValue, MaxValue, Value):
    """Calculates the percentage along a line from **MinValue** to **MaxValue** that value is.

    :param MinValue: Minimum Value
    :param MaxValue: Maximum Value
    :param Value: Input value
    :returns: The percentage (from 0.0 to 1.0) betwen the two values where input value is
    """
    return (Value - MinValue) / (MaxValue - MinValue)

def currentProcessorTime():
    if IS_PYTHON2:
        return time.clock()
    else:
        return time.process_time()

def findGoodId(ids):
    """
    Finds good minimum unique int from iterable. Starting from 1

    :param ids: a collection of occupied ids
    :type ids: list|set|tuple
    :returns: Unique Id
    :rtype: int
    """
    if len(ids) == 0:
        return 1

    ids = sorted(set(ids))
    lastID = min(ids)

    if lastID > 1:
        return 1

    for ID in ids:
        diff = ID - lastID
        if diff > 1:
            return lastID + 1
            break
        lastID = ID
    else:
        return ID + 1

def pinAffects(lhs, rhs):
    """This function for establish dependencies bitween pins

    .. warning:: Used internally, users will hardly need this

    :param lhs: First pin to connect
    :type lhs: :py:class:`PyFlow.Core.PinBase.PinBase`
    :param rhs: Second Pin to connect
    :type rhs: :py:class:`PyFlow.Core.PinBase.PinBase`
    """
    assert(lhs is not rhs), "pin can not affect itself"
    lhs.affects.add(rhs)
    rhs.affected_by.add(lhs)


def connectPins(src, dst):
    """**Connects two pins**

    This are the rules how pins connect:

    * Input value pins can have one output connection if :py:class:`PyFlow.Core.Common.PinOptions.AllowMultipleConnections` flag is disabled
    * Output value pins can have any number of connections
    * Input execs can have any number of connections
    * Output execs can have only one connection

    :param src: left hand side pin
    :type src: :py:class:`PyFlow.Core.PinBase.PinBase`
    :param dst: right hand side pin
    :type dst: :py:class:`PyFlow.Core.PinBase.PinBase`
    :returns: True if connected Successfully
    :rtype: bool
    """
    if src.direction == PinDirection.Input:
        src, dst = dst, src

    if not canConnectPins(src, dst):
        return False

    # input value pins can have one output connection if `AllowMultipleConnections` flag is disabled
    # output value pins can have any number of connections
    if src.IsValuePin() and dst.IsValuePin():
        if dst.hasConnections():
            if not dst.optionEnabled(PinOptions.AllowMultipleConnections):
                dst.disconnectAll()

    # input execs can have any number of connections
    # output execs can have only one connection
    if src.isExec() and dst.isExec():
        if src.hasConnections():
            if not src.optionEnabled(PinOptions.AllowMultipleConnections):
                src.disconnectAll()

    if src.isExec() and dst.isExec():
        src.onExecute.connect(dst.call)

    dst.aboutToConnect(src)
    src.aboutToConnect(dst)

    pinAffects(src, dst)
    src.setDirty()

    dst.setData(src.current_data())

    dst.pin_connected(src)
    src.pin_connected(dst)
    push(dst)
    return True


def getConnectedPins(pin):
    """Find all connected Pins to input Pin

    :param pin: Pin to search connected pins
    :type pin: :py:class:`PyFlow.Core.PinBase.PinBase`
    :returns: Set of connected pins
    :rtype: set(:py:class:`PyFlow.Core.PinBase.PinBase`)
    """
    result = set()
    if pin.direction == PinDirection.Input:
        for lhsPin in pin.affected_by:
            result.add(lhsPin)
    if pin.direction == PinDirection.Output:
        for rhsPin in pin.affects:
            result.add(rhsPin)
    return result


def canConnectPins(src, dst):
    """**Very important fundamental function, it checks if connection between two pins is possible**

    :param src: Source pin to connect
    :type src: :py:class:`PyFlow.Core.PinBase.PinBase`
    :param dst: Destination pin to connect
    :type dst: :py:class:`PyFlow.Core.PinBase.PinBase`
    :returns: True if connection can be made, and False if connection is not possible
    :rtype: bool
    """
    if src is None or dst is None:
        return False

    if src.direction == dst.direction:
        return False

    if arePinsConnected(src, dst):
        return False

    if src.direction == PinDirection.Input:
        src, dst = dst, src

    if cycleCheck(src, dst):
        return False
    return True

def cycleCheck(src, dst):
    """Check for cycle connected nodes

    :param src: hand side pin
    :type src: :class:`PyFlow.Core.PinBase`
    :param dst: hand side pin
    :type dst: :class:`PyFlow.Core.PinBase`
    :returns: True if cycle deleted
    :rtype: bool
    """
    if src.direction == PinDirection.Input:
        src, dst = dst, src
    start = src
    if src in dst.affects:
        return True
    for i in dst.affects:
        if cycleCheck(start, i):
            return True
    return False

def arePinsConnected(src, dst):
    """Checks if two pins are connected

    .. note:: Pins can be passed in any order if **src** pin is :py:class:`PyFlow.Core.Common.PinDirection`, they will be swapped

    :param src: left hand side pin
    :type src: :py:class:`PyFlow.Core.PinBase`
    :param dst: right hand side pin
    :type dst: :py:class:`PyFlow.Core.PinBase`
    :returns: True if Pins are connected
    :rtype: bool
    """
    if src.direction == dst.direction:
        return False
    if src.owning_node() == dst.owning_node():
        return False
    if src.direction == PinDirection.Input:
        src, dst = dst, src
    if dst in src.affects and src in dst.affected_by:
        return True
    return False

def connectPins(src, dst):
    """**Connects two pins**

    This are the rules how pins connect:

    * Input value pins can have one output connection if :py:class:`PyFlow.Core.Common.PinOptions.AllowMultipleConnections` flag is disabled
    * Output value pins can have any number of connections
    * Input execs can have any number of connections
    * Output execs can have only one connection

    :param src: left hand side pin
    :type src: :py:class:`PyFlow.Core.PinBase.PinBase`
    :param dst: right hand side pin
    :type dst: :py:class:`PyFlow.Core.PinBase.PinBase`
    :returns: True if connected Successfully
    :rtype: bool
    """
    if src.direction == PinDirection.Input:
        src, dst = dst, src

    if not canConnectPins(src, dst):
        return False

    dst.aboutToConnect(src)
    src.aboutToConnect(dst)

    # establish dependencies bitween pins
    pinAffects(src, dst)

    dst.set_data(src.current_data())

    dst.pin_connected(src)
    src.pin_connected(dst)
    return True

def disconnectPins(src, dst):
    """Disconnects two pins

    :param src: left hand side pin
    :type src: :py:class:`~Python.Core.PinBase.PinBase`
    :param dst: right hand side pin
    :type dst: :py:class:`~Python.Core.PinBase.PinBase`
    :returns: True if disconnection success
    :rtype: bool
    """
    if arePinsConnected(src, dst):
        if src.direction == PinDirection.Input:
            src, dst = dst, src
        src.affects.remove(dst)
        dst.affected_by.remove(src)
        src.pin_disconnected(dst)
        dst.pin_disconnected(src)
        return True
    return False


def push(start_from):
    """Marks dirty all ports from start to the right

    this part of graph will be recomputed every tick

    :param start_from: pin from which recursion begins
    :type start_from: :py:class:`~PyFlow.Core.PinBase.PinBase`
    """
    if not len(start_from.affects) == 0:
        start_from.setDirty()
        for i in start_from.affects:
            i.setDirty()
            push(i)


def extractDigitsFromEndOfString(string):
    """Get digits at end of a string

    Example:

    >>> nums = extractDigitsFromEndOfString("h3ello154")
    >>> print(nums, type(nums))
    >>> 154 <class 'int'>

    :param string: Input numbered string
    :type string: str
    :returns: Numbers in the final of the string
    :rtype: int
    """
    result = re.search('(\d+)$', string)
    if result is not None:
        return int(result.group(0))

def removeDigitsFromEndOfString(string):
    """Delete the numbers at the end of a string

    Similar to :func:`~PyFlow.Core.Common.extractDigitsFromEndOfString`, but removes digits in the end.

    :param string: Input string
    :type string: string
    :returns: Modified string
    :rtype: string
    """
    return re.sub(r'\d+$', '', string)


def getUniqNameFromList(existingNames, name):
    """Create unique name

    Iterates over **existingNames** and extracts the end digits to find a new unique id

    :param existingNames: List of strings where to search for existing indexes
    :type existingNames: list
    :param name: Name to obtain a unique version from
    :type name: str
    :returns: New name non overlapin with any in existingNames
    :rtype: str
    """
    if name not in existingNames:
        return name
    ids = set()
    for existingName in existingNames:
        digits = extractDigitsFromEndOfString(existingName)
        if digits is not None:
            ids.add(digits)
    idx = findGoodId(ids)
    name_no_digits = removeDigitsFromEndOfString(name)
    return name_no_digits + str(idx)
