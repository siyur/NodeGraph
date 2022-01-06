
class ISerializable(object):
    """
    Interface for serialization and deserialization
    """
    def __init__(self):
        super(ISerializable, self).__init__()

    def serialize(self, *args, **Kwargs):
        """Implements how item will be serialized

        :raises NotImplementedError: If not implemented
        """
        raise NotImplementedError('serialize method of ISerializable is not implemented')

    def deserialize(self, jsonData):
        """Implements how item will be deserialized

        :raises NotImplementedError: If not implemented
        """
        raise NotImplementedError('deserialize method of ISerializable is not implemented')


class IItemBase(ISerializable):
    """Base class for pins and nodes

    .. py:method:: uid
        :property:

        :getter: Unique identifier accessor

                :raises: :class:`NotImplementedError`

        :setter: Unique identifier setter

                :raises: :class:`NotImplementedError`
    """

    def __init__(self):
        super(IItemBase, self).__init__()

    def get_ui(self):
        """Returns reference to gui if it exists

        :rtype: gui class instance or None
        """
        return None

    def set_ui(self, ui_wrapper):
        """Sets gui

        :param ui_wrapper: gui class
        :type ui_wrapper: Whatever gui class
        """
        pass

    @property
    def uid(self):
        raise NotImplementedError('uid property of IItemBase should be implemented')

    @uid.setter
    def uid(self, value):
        raise NotImplementedError('uid setter of IItemBase should be implemented')

    @uid.deleter
    def uid(self):
        raise NotImplementedError('uid property of IItemBase can not be deleted')

    def get_name(self):
        """Returns item's name

        :rtype: str

        :raises NotImplementedError: If not implemented
        """
        raise NotImplementedError('getName method of IItemBase is not implemented')

    def set_name(self, name):
        """Sets item name

        :param name: Target name
        :type name: str
        :raises NotImplementedError: If not implemented
        """
        raise NotImplementedError('setName method of IItemBase is not implemented')

    def kill(self):
        """Removes item

        :raises NotImplementedError: If not implemented
        """
        raise NotImplementedError('kill method of IItemBase is not implemented')

    def path(self):
        """Returns path to item

        :raises NotImplementedError: If not implemented
        """
        raise NotImplementedError('path method of IItemBase is not implemented')


class IPin(IItemBase):
    """Pin interface
    """

    def __init__(self):
        super(IPin, self).__init__()


class INode(IItemBase):

    def __init__(self):
        super(INode, self).__init__()