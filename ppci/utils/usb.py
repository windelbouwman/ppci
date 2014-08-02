from ctypes import Structure, POINTER, CDLL, CFUNCTYPE
from ctypes import c_uint16, c_uint8, c_int, c_uint, c_ssize_t, c_void_p
from ctypes import byref, create_string_buffer

# libusb wrapper:
libusb = CDLL('libusb-1.0.so')

# helper:
def buildfunc(name, argtypes, restype=c_int):
   f = getattr(libusb, name)
   f.argtypes = argtypes
   f.restype = restype
   globals()[name] = f
   return f
def enum(**enums):
   reverse = dict((value, key) for key, value in enums.items())
   enums['reverse_mapping'] = reverse
   return type('enum', (), enums)

# enums
libusb_class_code = enum(PER_INTERFACE=0, AUDIO=1, COMM=2, HID=3, \
         PHYSICAL=5, PRINTER=7, PTP=6, MASS_STORAGE=8, HUB=9, \
         DATA=10, SMART_CARD=0xb, CONTENT_SECURITY=0xd, VIDEO=0xe, \
         PERSONAL_HEALTHCARE=0xf, DIAGNOSTIC_DEVICE=0xdc, WIRELESS=0xe,\
         APPLICATION=0xfe, VENDOR_SPEC=0xff)
libusb_speed = enum(UNKNOWN=0, LOW=1, FULL=2, HIGH=3, SUPER=4)
libusb_error = enum(SUCCES=0, ERROR_IO=-1, ERROR_INVALID_PARAM=-2, \
         ERROR_ACCESS=-3, ERROR_NO_DEVICE=-4, ERROR_NOT_FOUND=-5, \
         ERROR_BUSY=-6, ERROR_TIMEOUT=-7, ERROR_OVERFLOW=-8, \
         ERROR_PIPE=-9, ERROR_INTERRUPTED=-10, ERROR_NO_MEM=-11, \
         ERROR_NOT_SUPPORTED=-12, ERROR_OTHER=-99)
libusb_transfer_status = enum(\
         COMPLETED=0, ERROR=1, TIMED_OUT=2, \
         CANCELLED=3, STALL=4, NO_DEVICE=5, OVERFLOW=6)

# types
c_int_p = POINTER(c_int)
class libusb_context(Structure):
   pass
libusb_context_p = POINTER(libusb_context)
libusb_context_p_p = POINTER(libusb_context_p)

class libusb_device(Structure):
   pass
libusb_device_p = POINTER(libusb_device)
libusb_device_p_p = POINTER(libusb_device_p)
libusb_device_p_p_p = POINTER(libusb_device_p_p)

class libusb_device_handle(Structure):
   pass
libusb_device_handle_p = POINTER(libusb_device_handle)
libusb_device_handle_p_p = POINTER(libusb_device_handle_p)

class libusb_device_descriptor(Structure):
   _fields_ = [
               ('bLength', c_uint8),
               ('bDescriptorType', c_uint8),
               ('bcdUSB', c_uint16),
               ('bDeviceClass', c_uint8),
               ('bDeviceSubClass', c_uint8),
               ('bDeviceProtocol', c_uint8),
               ('bMaxPacketSize0', c_uint8),
               ('idVendor', c_uint16),
               ('idProduct', c_uint16),
               ('bcdDevice', c_uint16),
               ('iManufacturer', c_uint8),
               ('iProduct', c_uint8),
               ('iSerialNumber', c_uint8),
               ('iNumConfigurations', c_uint8)
              ]
libusb_device_descriptor_p = POINTER(libusb_device_descriptor)

"""
class libusb_transfer(Structure):
   pass
libusb_transfer_p = POINTER(libusb_transfer)
libusb_transfer_cb_fn = CFUNCTYPE(None, libusb_transfer_p)
libusb_transfer._fields_ = [
      ('dev_handle', libusb_device_handle_p),
      ('flags', c_uint8),
      ('endpoint', c_uchar),
      ('type', c_uchar),
      ('timeout', c_uint),
      ('status', c_int), # enum libusb_transfer_status
      ('length', c_int),
      ('actual_length', c_int),
      ('callback', libusb_transfer_cb_fn),
      ('userdata', c_void_p),
      ('buffer', c_void_p),
      ('num_iso_packets', c_int),
      ('iso_packet_desc', libusb_iso_packet_descriptor)
   ]
"""
# functions
buildfunc('libusb_init', [libusb_context_p_p], c_int)

buildfunc('libusb_get_device_list', \
   [libusb_context_p, libusb_device_p_p_p], c_ssize_t)
buildfunc('libusb_free_device_list', [libusb_device_p_p, c_int], None)
buildfunc('libusb_get_bus_number', [libusb_device_p], c_uint8)
buildfunc('libusb_get_device_address', [libusb_device_p], c_uint8)
buildfunc('libusb_get_device_speed', [libusb_device_p])
buildfunc('libusb_unref_device', [libusb_device_p], None)
buildfunc('libusb_open', [libusb_device_p, libusb_device_handle_p_p])
buildfunc('libusb_close', [libusb_device_handle_p], None)
buildfunc('libusb_get_configuration',[libusb_device_handle_p,POINTER(c_int)])
buildfunc('libusb_set_configuration', [libusb_device_handle_p, c_int])
buildfunc('libusb_claim_interface', [libusb_device_handle_p, c_int])

buildfunc('libusb_get_device_descriptor',\
   [libusb_device_p, libusb_device_descriptor_p])

# synchronous functions:
buildfunc('libusb_bulk_transfer', [libusb_device_handle_p, c_uint8, \
   c_void_p, c_int, c_int_p, c_uint])

# pythonic API:

class UsbError(Exception):
   def __init__(self, msg, errorcode):
      if errorcode in libusb_error.reverse_mapping:
         errorcode = libusb_error.reverse_mapping[errorcode]
      msg = msg + 'Error code: {0}'.format(errorcode)
      super().__init__(msg)

class UsbContext(object):
   """ A usb context in case of multiple use """
   def __init__(self):
      self.context_p = libusb_context_p()
      r = libusb_init(byref(self.context_p))
      if r != 0:
         raise UsbError('libusb_init error!', r)
   def getDeviceList(self):
      devlist = libusb_device_p_p()
      count = libusb_get_device_list(self.context_p, byref(devlist))
      if count < 0:
         raise UsbError('Error getting device list', count)
      l = [UsbDevice(self, device_p.contents) for device_p in devlist[0:count]]
      libusb_free_device_list(devlist, 0)
      return l
   DeviceList = property(getDeviceList)

class UsbDevice:
   """ A detected usb device """
   def __init__(self, context, device_p):
      self.context = context
      self.dev_p = device_p
   def __del__(self):
      libusb_unref_device(self.dev_p)
   def getBusNumber(self):
      return libusb_get_bus_number(self.dev_p)
   BusNumber = property(getBusNumber)
   def getDeviceAddress(self):
      return libusb_get_device_address(self.dev_p)
   DeviceAddress = property(getDeviceAddress)
   def getSpeed(self):
      s = libusb_get_device_speed(self.dev_p)
      if s in libusb_speed.reverse_mapping:
         s = libusb_speed.reverse_mapping[s]
      return s
   Speed = property(getSpeed)
   def getDescriptor(self):
      descriptor = libusb_device_descriptor()
      r = libusb_get_device_descriptor(self.dev_p, byref(descriptor))
      if r != 0:
         raise UsbError('Error getting descriptor', r)
      return descriptor
   Descriptor = property(getDescriptor)
   VendorId = property(lambda self: self.Descriptor.idVendor)
   ProductId = property(lambda self: self.Descriptor.idProduct)
   NumConfigurations = property(lambda self: self.Descriptor.bNumConfigurations)
   def open(self):
      """ Opens this device and returns a handle """
      handle_p = libusb_device_handle_p()
      r = libusb_open(self.dev_p, byref(handle_p))
      if r != 0:
         raise UsbError('error opening device', r)
      return UsbDeviceHandle(self, handle_p)
   def __repr__(self):
      r2 = 'Usb device: bus {0} address {1} {2:04X}:{3:04X} speed {4}' \
         .format( \
         self.BusNumber, self.DeviceAddress, self.VendorId, \
         self.ProductId, self.Speed)
      return r2

USB_ENDPOINT_DIR_MASK = 0x80
USB_ENDPOINT_IN = 0x80
USB_ENDPOINT_OUT = 0x0

class UsbDeviceHandle:
   """ Handle to a detected usb device """
   def __init__(self, device, handle_p):
      self.device = device
      self.handle_p = handle_p
   def __del__(self):
      self.close()
   def close(self):
      if self.handle_p:
         libusb_close(self.handle_p)
         self.handle_p = None
   def getConfiguration(self):
      config = c_int()
      r = libusb_get_configuration(self.handle_p, byref(config))
      if r != 0: raise UsbError('Error getting configuration', r)
      return config.value
   def setConfiguration(self, config):
      r = libusb_set_configuration(self.handle_p, config)
      if r != 0: raise UsbError('Error setting configuration', r)
   Configuration = property(getConfiguration, setConfiguration)
   def claimInterface(self, interface_number):
      r = libusb_claim_interface(self.handle_p, interface_number)
      if r != 0: raise UsbError('Error claiming interface', r)
   def bulkWrite(self, endpoint, data, timeout=0):
      """ Synchronous bulk write """
      assert type(data) is bytes
      # assure the endpoint indicates the correct:
      endpoint = (endpoint & (~USB_ENDPOINT_DIR_MASK)) | USB_ENDPOINT_OUT
      buf = create_string_buffer(data)
      transferred = c_int()
      r = libusb_bulk_transfer(self.handle_p, endpoint, buf, len(data), \
         byref(transferred), timeout)
      if r != 0:
         raise UsbError('Bulk write failed', r)
      if transferred.value != len(data):
         raise UsbError('Not all {0} transferred {1}'.format(len(data), \
            transferred.value))
   def bulkRead(self, endpoint, numbytes, timeout=0):
      """ Synchronous bulk read """
      # assure the endpoint indicates the correct:
      endpoint = (endpoint & (~USB_ENDPOINT_DIR_MASK)) | USB_ENDPOINT_IN
      buf = create_string_buffer(numbytes)
      transferred = c_int()
      r = libusb_bulk_transfer(self.handle_p, endpoint, buf, numbytes, \
         byref(transferred), timeout)
      if r != 0:
         raise UsbError('Bulk read failed', r)
      if transferred.value != numbytes:
         raise UsbError('Not all {0} transferred {1}'.format(numbytes, \
            transferred.value))
      data = buf.raw[0:numbytes]
      return data

class UsbTransfer:
   def __init__(self):
      libusb_alloc_transfer(0)
