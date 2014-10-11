
# Global device list to which devices are registered.
devices = {}


def registerDevice(chipId):
    """ Decorator to register a device """
    def wrapper(dev):
        devices[chipId] = dev
        return dev
    return wrapper

# Global interface dictionary.
interfaces = {}


def registerInterface(vid_pid):
    def wrapper(iface):
        interfaces[vid_pid] = iface
        return iface
    return wrapper


class Device:
    """
      Base class for a device possibly connected via an interface.
    """
    def __init__(self, iface):
        # Store the interface through which this device is connected:
        assert isinstance(iface, Interface)
        self.iface = iface


class Interface:
    """
      Generic interface class. Connected via Usb to a JTAG interface.
      Possibly is connected with a certain chip.
    """
    pass
