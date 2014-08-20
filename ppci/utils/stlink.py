import struct, time
from .usb import UsbContext, UsbDevice
from .devices import Interface, STLinkException, registerInterface
from . import adi

"""
   More or less copied from:
     https://github.com/texane/stlink
   Tracing from:
     https://github.com/obe1line/stlink-trace

"""
ST_VID, STLINK2_PID = 0x0483, 0x3748

def checkDevice(device):
   return device.VendorId == ST_VID and device.ProductId == STLINK2_PID

DFU_MODE, MASS_MODE, DEBUG_MODE = 0, 1, 2

CORE_RUNNING = 0x80
CORE_HALTED = 0x81

# Commands:
GET_VERSION = 0xf1
DEBUG_COMMAND = 0xf2
DFU_COMMAND = 0xf3
GET_CURRENT_MODE = 0xf5

# dfu commands:
DFU_EXIT = 0x7

# debug commands:
DEBUG_ENTER = 0x20
DEBUG_EXIT = 0x21
DEBUG_ENTER_SWD = 0xa3
DEBUG_GETSTATUS = 0x01
DEBUG_FORCEDEBUG = 0x02
DEBUG_RESETSYS = 0x03
DEBUG_READALLREGS = 0x04
DEBUG_READREG = 0x5
DEBUG_WRITEREG = 0x6
DEBUG_READMEM_32BIT = 0x7
DEBUG_WRITEMEM_32BIT = 0x8
DEBUG_RUNCORE = 0x9
DEBUG_STEPCORE = 0xa

JTAG_WRITEDEBUG_32BIT = 0x35
JTAG_READDEBUG_32BIT = 0x36
TRACE_GET_BYTE_COUNT = 0x42

# cortex M3
CM3_REG_CPUID = 0xE000ED00

@registerInterface((ST_VID, STLINK2_PID))
class STLink2(Interface):
   """ STlink2 interface implementation. """
   def __init__(self, stlink2=None):
      self.devHandle = None
      if not stlink2:
         context = UsbContext()
         stlink2s = list(filter(checkDevice, context.DeviceList))
         if not stlink2s:
            raise STLinkException('Could not find an ST link 2 interface')
         if len(stlink2s) > 1:
            print('More then one stlink2 found, picking first one')
         stlink2 = stlink2s[0]
      assert isinstance(stlink2, UsbDevice) # Nifty type checking
      assert checkDevice(stlink2)
      self.stlink2 = stlink2
   def __del__(self):
      if self.IsOpen:
         if self.CurrentMode == DEBUG_MODE:
            self.exitDebugMode()
         self.close()

   def __str__(self):
      if self.IsOpen:
         return 'STlink2 device version {0}'.format(self.Version)
      else:
         return 'STlink2 device'

   def open(self):
      if self.IsOpen:
         return
      self.devHandle = self.stlink2.open()
      if self.devHandle.Configuration != 1:
         self.devHandle.Configuration = 1
      self.devHandle.claimInterface(0)

      # First initialization:
      if self.CurrentMode == DFU_MODE:
         self.exitDfuMode()
      if self.CurrentMode != DEBUG_MODE:
         self.enterSwdMode()
      #self.reset()

   def close(self):
      if self.IsOpen:
         self.devHandle.close()
         self.devHandle = None
   @property
   def IsOpen(self):
      return self.devHandle != None

   # modes:
   def getCurrentMode(self):
      cmd = bytearray(16)
      cmd[0] = GET_CURRENT_MODE
      reply = self.send_recv(cmd, 2) # Expect 2 bytes back
      return reply[0]
   CurrentMode = property(getCurrentMode)
   @property

   def CurrentModeString(self):
      modes = {DFU_MODE: 'dfu', MASS_MODE: 'massmode', DEBUG_MODE:'debug'}
      return modes[self.CurrentMode]
   def exitDfuMode(self):
      cmd = bytearray(16)
      cmd[0:2] = DFU_COMMAND, DFU_EXIT
      self.send_recv(cmd)
   def enterSwdMode(self):
      cmd = bytearray(16)
      cmd[0:3] = DEBUG_COMMAND, DEBUG_ENTER, DEBUG_ENTER_SWD
      self.send_recv(cmd)
   def exitDebugMode(self):
      cmd = bytearray(16)
      cmd[0:2] = DEBUG_COMMAND, DEBUG_EXIT
      self.send_recv(cmd)
      
   def getVersion(self):
      cmd = bytearray(16)
      cmd[0] = GET_VERSION
      data = self.send_recv(cmd, 6) # Expect 6 bytes back
      # Parse 6 bytes into various versions:
      b0, b1, b2, b3, b4, b5 = data
      stlink_v = b0 >> 4
      jtag_v = ((b0 & 0xf) << 2) | (b1 >> 6)
      swim_v = b1 & 0x3f
      vid = (b3 << 8) | b2
      pid = (b5 << 8) | b4
      return 'stlink={0} jtag={1} swim={2} vid:pid={3:04X}:{4:04X}'.format(\
         stlink_v, jtag_v, swim_v, vid, pid)
   Version = property(getVersion)
   
   @property
   def ChipId(self):
      return self.read_debug32(0xE0042000)
   @property
   def CpuId(self):
      u32 = self.read_debug32(CM3_REG_CPUID)
      implementer_id = (u32 >> 24) & 0x7f
      variant = (u32 >> 20) & 0xf
      part = (u32 >> 4) & 0xfff
      revision = u32 & 0xf
      return implementer_id, variant, part, revision
   def getStatus(self):
      cmd = bytearray(16)
      cmd[0:2] = DEBUG_COMMAND, DEBUG_GETSTATUS
      reply = self.send_recv(cmd, 2)
      return reply[0]
   Status = property(getStatus)
   @property
   def StatusString(self):
      s = self.Status
      statii = {CORE_RUNNING: 'CORE RUNNING', CORE_HALTED: 'CORE HALTED'}
      if s in statii:
         return statii[s]
      return 'Unknown status'

   def reset(self):
      cmd = bytearray(16)
      cmd[0:2] = DEBUG_COMMAND, DEBUG_RESETSYS
      self.send_recv(cmd, 2)

   # debug commands:
   def step(self):
        cmd = bytearray(16)
        cmd[0:2] = DEBUG_COMMAND, DEBUG_STEPCORE
        self.send_recv(cmd, 2)

   def run(self):
        cmd = bytearray(16)
        cmd[0:2] = DEBUG_COMMAND, DEBUG_RUNCORE
        self.send_recv(cmd, 2)

   def halt(self):
        cmd = bytearray(16)
        cmd[0:2] = DEBUG_COMMAND, DEBUG_FORCEDEBUG
        self.send_recv(cmd, 2)
   
   # Tracing:
   def traceEnable(self):
        """ Configure stlink to send trace data """
        self.write_debug32(0xE000EDF0, 0xA05F0003)

        # Enable TRCENA:
        self.write_debug32(0xE000EDFC, 0x01000000)

        # ?? Enable write??
        self.write_debug32(0xE0002000, 0x2)

        # TODO: send other commands

        # DBGMCU_CR:
        self.write_debug32(0xE0042004, 0x27)  # Enable trace in async mode

        # TPIU config:
        uc_freq = 16
        st_freq = 2
        divisor = int(uc_freq / st_freq) - 1
        self.write_debug32(0xE0040004, 0x00000001)  # current port size register --> 1 == port size = 1
        self.write_debug32(0xE0040010, divisor)  # random clock divider??
        self.write_debug32(0xE00400F0, 0x2)  # selected pin protocol (2 == NRZ)
        self.write_debug32(0xE0040304, 0x100)  # continuous formatting

        # ITM config:
        self.write_debug32(0xE0000FB0, 0xC5ACCE55)  # Unlock write access to ITM
        self.write_debug32(0xE0000F80, 0x00010005)  # ITM Enable, sync enable, ATB=1
        self.write_debug32(0xE0000E00, 0xFFFFFFFF)  # Enable all trace ports in ITM
        self.write_debug32(0xE0000E40, 0x0000000F)  # Set privilege mask for all 32 ports.

   def writePort0(self, v32):
      self.write_debug32(0xE0000000, v32)

   def getTraceByteCount(self):
      cmd = bytearray(16)
      cmd[0:2] = DEBUG_COMMAND, 0x42
      reply = self.send_recv(cmd, 2)
      return struct.unpack('<H', reply[0:2])[0]

   def readTraceData(self):
      bsize = self.getTraceByteCount()
      if bsize > 0:
         td = self.recv_ep3(bsize)
         print(td)
      else:
         print('no trace data')

   # Helper 1 functions:
   def write_debug32(self, address, value):
      cmd = bytearray(16)
      cmd[0:2] = DEBUG_COMMAND, JTAG_WRITEDEBUG_32BIT
      cmd[2:10] = struct.pack('<II', address, value)
      r = self.send_recv(cmd, 2)
   def read_debug32(self, address):
      cmd = bytearray(16)
      cmd[0:2] = DEBUG_COMMAND, JTAG_READDEBUG_32BIT
      cmd[2:6] = struct.pack('<I', address) # pack into u32 little endian
      reply = self.send_recv(cmd, 8)
      return struct.unpack('<I', reply[4:8])[0]
   def write_reg(self, reg, value):
      cmd = bytearray(16)
      cmd[0:3] = DEBUG_COMMAND, DEBUG_WRITEREG, reg
      cmd[3:7] = struct.pack('<I', value)
      r = self.send_recv(cmd, 2)
   def read_reg(self, reg):
      cmd = bytearray(16)
      cmd[0:3] = DEBUG_COMMAND, DEBUG_READREG, reg
      reply = self.send_recv(cmd, 4)
      return struct.unpack('<I', reply)[0]
   def read_all_regs(self):
      cmd = bytearray(16)
      cmd[0:2] = DEBUG_COMMAND, DEBUG_READALLREGS
      reply = self.send_recv(cmd, 84)
      fmt = '<' + 'I' * 21 # unpack 21 register values
      return list(struct.unpack(fmt, reply))
   def write_mem32(self, address, content):
      assert len(content) % 4 == 0
      cmd = bytearray(16)
      cmd[0:2] = DEBUG_COMMAND, DEBUG_WRITEMEM_32BIT
      cmd[2:8] = struct.pack('<IH', address, len(content))
      self.send_recv(cmd)
      self.send_recv(content)
   def read_mem32(self, address, length):
      assert length % 4 == 0
      cmd = bytearray(16)
      cmd[0:2] = DEBUG_COMMAND, DEBUG_READMEM_32BIT
      cmd[2:8] = struct.pack('<IH', address, length)
      reply = self.send_recv(cmd, length) # expect memory back!
      return reply

   # Helper 2 functions:
   def send_recv(self, tx, rxsize=0):
      """ Helper function that transmits and receives data in bulk mode. """
      # TODO: we could use here the non-blocking libusb api.
      tx = bytes(tx)
      #assert len(tx) == 16
      self.devHandle.bulkWrite(2, tx) # write to endpoint 2
      if rxsize > 0:
         return self.devHandle.bulkRead(1, rxsize) # read from endpoint 1
   def recv_ep3(self, rxsize):
      return self.devHandle.bulkRead(3, rxsize)

if __name__ == '__main__':
   # Test program
   sl = STLink2()
   sl.open()
   sl.reset()
   print('version:', sl.Version)
   print('mode before doing anything:', sl.CurrentModeString)
   if sl.CurrentMode == DFU_MODE:
      sl.exitDfuMode()
   sl.enterSwdMode()
   print('mode after entering swd mode:', sl.CurrentModeString)

   i = sl.ChipId
   print('chip id: 0x{0:X}'.format(i))
   print('cpu: {0}'.format(sl.CpuId))

   print('status: {0}'.format(sl.StatusString))

   # test registers:
   sl.write_reg(0, 0xdeadbeef)
   sl.write_reg(1, 0xcafebabe)
   sl.write_reg(2, 0xc0ffee)
   sl.write_reg(3, 0x1337)
   sl.write_reg(5, 0x1332)
   sl.write_reg(6, 0x12345)
   assert sl.read_reg(3) == 0x1337
   assert sl.read_reg(5) == 0x1332
   assert sl.read_reg(6) == 0x12345
   regs = sl.read_all_regs()
   for i in range(len(regs)):
      print('R{0}=0x{1:X}'.format(i, regs[i]))

   print('tracing')
   sl.traceEnable()
   sl.run()
   sl.writePort0(0x1337) # For test
   time.sleep(0.1)
   td = sl.readTraceData()
   print('trace data:', td)
   
   # Test CoreSight registers:
   idr4 = sl.read_debug32(0xE0041fd0)
   print('idr4 =', idr4)

   print('== ADI ==')
   a = adi.Adi(sl)
   a.parseRomTable(0xE00FF000) # why is rom table at 0xE00FF000?
   print('== ADI ==')

   # Detect ROM table:
   id4 = sl.read_debug32(0xE00FFFD0)
   id5 = sl.read_debug32(0xE00FFFD4)
   id6 = sl.read_debug32(0xE00FFFD8)
   id7 = sl.read_debug32(0xE00FFFDC)
   id0 = sl.read_debug32(0xE00FFFE0)
   id1 = sl.read_debug32(0xE00FFFE4)
   id2 = sl.read_debug32(0xE00FFFE8)
   id3 = sl.read_debug32(0xE00FFFEC)
   pIDs = [id0, id1, id2, id3, id4, id5, id6, id7]
   print(pIDs)

   print('reading from 0xE00FF000')
   scs = sl.read_debug32(0xE00FF000)
   print('scs {0:08X}'.format(scs))
   dwt = sl.read_debug32(0xE00FF004)
   print('dwt {0:08X}'.format(dwt))
   fpb = sl.read_debug32(0xE00FF008)
   print('fpb {0:08X}'.format(fpb))
   itm = sl.read_debug32(0xE00FF00C)
   print('itm {0:08X}'.format(itm))
   tpiu = sl.read_debug32(0xE00FF010)
   print('tpiu {0:08X}'.format(tpiu))
   etm = sl.read_debug32(0xE00FF014)
   print('etm {0:08X}'.format(etm))
   assert sl.read_debug32(0xE00FF018) == 0x0 # end marker

   devid = sl.read_debug32(0xE0040FC8)
   print('TPIU_DEVID: {0:X}'.format(devid))
   devtype = sl.read_debug32(0xE0040FCC)
   print('TPIU_TYPEID: {0:X}'.format(devtype))

   sl.exitDebugMode()
   print('mode at end:', sl.CurrentModeString)

   sl.close()
   print('Test succes!')

