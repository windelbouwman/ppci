
# Implementation of the ADI (ARM Debug Interface) v5 interface.

COMPONENT_CLASSES = {0x1: 'ROM table'}

class Adi:
   def __init__(self, iface):
      self.iface = iface
   def r32(self, address):
      return self.iface.read_debug32(address)
   def w32(self, address, value):
      self.iface.write_debug32(address, value)
   def getId(self, offset):
      print('reading id from {0:X}'.format(offset))
      pid4 = self.r32(offset + 0xFD0)
      #print('pid4', pid4)
      pid5 = self.r32(offset + 0xFD4)
      pid6 = self.r32(offset + 0xFD8)
      pid7 = self.r32(offset + 0xFDC)
      pid0 = self.r32(offset + 0xFE0)
      pid1 = self.r32(offset + 0xFE4)
      pid2 = self.r32(offset + 0xFE8)
      pid3 = self.r32(offset + 0xFEC)
      cid0 = self.r32(offset + 0xFF0)
      cid1 = self.r32(offset + 0xFF4)
      cid2 = self.r32(offset + 0xFF8)
      cid3 = self.r32(offset + 0xFFC)
      pids = [pid0, pid1, pid2, pid3, pid4, pid5, pid6, pid7]
      cids = [cid0, cid1, cid2, cid3]
      print('cids:', [hex(x) for x in cids], 'pids', [hex(x) for x in pids])
      valid = cid0 == 0xD and (cid1 & 0xF) == 0x0 and cid2 == 0x5 and cid3 == 0xB1
      if valid:
         component_class = cid1 >> 4
      else:
         print('invalid class')
         component_class = 0
      # TODO: use pids
      return component_class, pids
      
   def parseRomTable(self, offset):
      assert (offset & 0xFFF) == 0
      component_class, pid = self.getId(offset)
      assert component_class == 1
      print('Component class:', COMPONENT_CLASSES[component_class])
      print('memory also on this bus:', self.r32(offset + 0xFCC))
      idx = 0
      entry = self.r32(offset + idx * 4)
      while entry != 0:
         #print('Entry: {0:X}'.format(entry))
         entryOffset = entry & 0xFFFFF000
         cls, pids = self.getId((offset + entryOffset) & 0xFFFFFFFF)
         print('class:', cls)
         if cls == 9:
            print('Debug block found!')

         idx += 1
         entry = self.r32(offset + idx * 4)


