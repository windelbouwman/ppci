from . import usb

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

def createInterfaces():
   """ Create a list of detected interfaces """
   ctx = usb.UsbContext()

   # Retrieve all usb devices:
   devs = ctx.DeviceList
   keys = interfaces.keys()

   # Filter function to filter only registered interfaces:
   def filt(usbiface):
      return (usbiface.VendorId, usbiface.ProductId) in keys
   def buildInterface(usbiface):
      key = (usbiface.VendorId, usbiface.ProductId)
      iface = interfaces[key]
      return iface(usbiface)
   return [buildInterface(uif) for uif in filter(filt, devs)]

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
   def createDevice(self):
      """ Try to get the device connected to this interface """
      if self.ChipId in devices:
         return devices[self.ChipId](self)
      raise STLinkException('No device found!')

class STLinkException(Exception):
   """ Exception used for interfaces and devices """
   pass

