import time
import logging
from .devices import Device, registerDevice
from . import stlink

# F4 specifics:
STM32_FLASH_BASE = 0x08000000
STM32_SRAM_BASE = 0x20000000


# flash registers:
FLASH_F4_REGS_ADDR = 0x40023c00
FLASH_F4_KEYR = FLASH_F4_REGS_ADDR + 0x04
FLASH_F4_SR = FLASH_F4_REGS_ADDR + 0x0c
FLASH_F4_CR = FLASH_F4_REGS_ADDR + 0x10

FLASH_F4_CR_START = 16
FLASH_F4_CR_LOCK = 31
FLASH_CR_PG = 0
FLASH_F4_CR_SER = 1
FLASH_CR_MER = 2
FLASH_F4_CR_SNB = 3
FLASH_F4_CR_SNB_MASK = 0x38
FLASH_F4_SR_BSY = 16


class STLinkException(Exception):
    """ Exception used for interfaces and devices """
    pass


class Stm32F4(Device):
    """
      Implementation of the specifics of the STM32F4xx device series.
    """
    def __init__(self, iface):
        super().__init__(iface)
        self.logger = logging.getLogger('stm32')

    def __str__(self):
        return 'STM32F4 device size=0x{1:X} id=0x{0:X}'.format(\
            self.UID, self.FlashSize)

    def calculate_F4_sector(self, address):
      sectorstarts = []
      a = STM32_FLASH_BASE
      for sectorsize in self.sectorsizes:
         sectorstarts.append(a)
         a += sectorsize
      # linear search:
      sec = 0
      while sec < len(self.sectorsizes) and address >= sectorstarts[sec]:
         sec += 1
      sec -= 1 # one back.
      return sec, self.sectorsizes[sec]

    def calcSectors(self, address, size):
        off = 0
        sectors = []
        while off < size:
            sectornum, sectorsize = self.calculate_F4_sector(address + off)
            sectors.append((sectornum, sectorsize))
            off += sectorsize
        return sectors

    # Device registers:
    @property
    def UID(self):
        uid_base = 0x1FFF7A10
        uid1 = self.iface.read_debug32(uid_base)
        uid2 = self.iface.read_debug32(uid_base + 0x4)
        uid3 = self.iface.read_debug32(uid_base + 0x8)
        return (uid3 << 64) | (uid2 << 32) | uid1

    @property
    def FlashSize(self):
        f_id = self.iface.read_debug32(0x1FFF7A22)
        f_id = f_id >> 16
        return f_id * 1024

    @property
    def Running(self):
        return self.iface.Status == stlink.CORE_RUNNING

    # flashing commands:
    def writeFlash(self, address, content):
      flashsize = self.FlashSize
      pagesize = min(self.sectorsizes)

      # Check address range:
      if address < STM32_FLASH_BASE:
         raise STLinkException('Flashing below flash start')
      if address + len(content) > STM32_FLASH_BASE + flashsize:
         raise STLinkException('Flashing above flash size')
      if address & 1 == 1:
         raise STLinkException('Unaligned flash')
      if len(content) & 1 == 1:
         self.logger.warning('unaligned length, padding with zero')
         content += bytes([0])
      if address & (pagesize - 1) != 0:
         raise STLinkException('Address not aligned with pagesize')
      # erase required space
      sectors = self.calcSectors(address, len(content))
      self.logger.info('erasing {0} sectors'.format(len(sectors)))
      for sector, secsize in sectors:
         self.logger.info('erasing sector {0} of {1} bytes'.format(sector, secsize))
         self.eraseFlashSector(sector)
      # program pages:
      self.unlockFlashIf()
      self.writeFlashCrPsiz(2) # writes are 32 bits aligned
      self.setFlashCrPg()
      self.logger.info('writing {0} bytes'.format(len(content)))
      offset = 0
      t1 = time.time()
      while offset < len(content):
         size = len(content) - offset
         if size > 0x8000:
            size = 0x8000
         chunk = content[offset:offset + size]
         while len(chunk) % 4 != 0:
            chunk = chunk + bytes([0])
         # Use simple mem32 writes:
         self.iface.write_mem32(address + offset, chunk)
         offset += size
         self.logger.info('{}%'.format(offset*100/len(content)))
      self.logger.info('Done!')
      self.lockFlash()
      # verfify program:
      self.verifyFlash(address, content)

    def eraseFlashSector(self, sector):
        self.waitFlashBusy()
        self.unlockFlashIf()
        self.writeFlashCrSnb(sector)
        self.setFlashCrStart()
        self.waitFlashBusy()
        self.lockFlash()

    def eraseFlash(self):
      self.waitFlashBusy()
      self.unlockFlashIf()
      self.setFlashCrMer()
      self.setFlashCrStart()
      self.waitFlashBusy()
      self.clearFlashCrMer()
      self.lockFlash()

    def verifyFlash(self, address, content):
        device_content = self.readFlash(address, len(content))
        ok = content == device_content
        if ok:
            self.logger.info('Verify: OK')
        else:
            self.logger.warning('Verify: Mismatch')

    def readFlash(self, address, size):
      self.logger.info('Reading {1} bytes from 0x{0:X}'.format(address, size))
      offset = 0
      tmp_size = 0x1800
      image = bytes()
      while offset < size:
         # Correct for last page:
         if offset + tmp_size > size:
            tmp_size = size - offset

         # align size to 4 bytes:
         aligned_size = tmp_size
         while aligned_size % 4 != 0:
            aligned_size += 1

         mem = self.iface.read_mem32(address + offset, aligned_size)
         image += mem[:tmp_size]

         # indicate progress:
         self.logger.info('{}%'.format(100*len(image) / size))

         # increase for next piece:
         offset += tmp_size
      assert size == len(image)
      self.logger.info('Done!')
      return image

    def waitFlashBusy(self):
        """ block until flash operation completes. """
        while self.isFlashBusy():
            time.sleep(0.01)

    def isFlashLocked(self):
        mask = 1 << FLASH_F4_CR_LOCK
        return self.Cr & mask == mask

    def unlockFlashIf(self):
        FLASH_KEY1, FLASH_KEY2 = 0x45670123, 0xcdef89ab
        if self.isFlashLocked():
            self.iface.write_debug32(FLASH_F4_KEYR, FLASH_KEY1)
            self.iface.write_debug32(FLASH_F4_KEYR, FLASH_KEY2)
            if self.isFlashLocked():
                raise STLinkException('Failed to unlock')

    def lockFlash(self):
        self.Cr = self.Cr | (1 << FLASH_F4_CR_LOCK)

    def readFlashSr(self):
        return self.iface.read_debug32(FLASH_F4_SR)

    def readFlashCr(self):
        return self.iface.read_debug32(FLASH_F4_CR)

    def writeFlashCr(self, x):
        self.iface.write_debug32(FLASH_F4_CR, x)

    Cr = property(readFlashCr, writeFlashCr)

    def writeFlashCrSnb(self, sector):
        x = self.Cr
        x &= ~FLASH_F4_CR_SNB_MASK
        x |= sector << FLASH_F4_CR_SNB
        x |= 1 << FLASH_F4_CR_SER
        self.Cr = x

    def setFlashCrMer(self):
        self.Cr = self.Cr | (1 << FLASH_CR_MER)

    def setFlashCrPg(self):
        self.Cr = self.Cr | (1 << FLASH_CR_PG)

    def writeFlashCrPsiz(self, n):
        x = self.Cr
        x &= (0x3 << 8)
        x |= n << 8
        self.Cr = x

    def clearFlashCrMer(self):
        x = self.Cr
        x &= ~(1 << FLASH_CR_MER)
        self.Cr = x

    def setFlashCrStart(self):
        self.Cr = self.Cr | (1 << FLASH_F4_CR_START)

    def isFlashBusy(self):
      mask = 1 << FLASH_F4_SR_BSY
      sr = self.readFlashSr()
      # Check for error bits:
      errorbits = {}
      errorbits[7] = 'Programming sequence error'
      errorbits[6] = 'Programming parallelism error'
      errorbits[5] = 'Programming alignment error'
      errorbits[4] = 'Write protection error'
      errorbits[1] = 'Operation error'
      #errorbits[0] = 'End of operation'
      for bit, msg in errorbits.items():
         if sr & (1 << bit) == (1 << bit):
            raise STLinkException(msg)
      return sr & mask == mask


@registerDevice(0x10016413)
class Stm32F40x(Stm32F4):
    """ STM32F40x and STM32F41x device series """
    def __init__(self, iface):
        super().__init__(iface)
        # Assert the proper size for this device:
        assert self.FlashSize == 0x100000
        """
         from 0x8000000 to 0x80FFFFF
         4 sectors of 0x4000 (16 kB)
         1 sector of 0x10000 (64 kB)
         7 of 0x20000 (128 kB)
        """
        self.sectorsizes = [0x4000] * 4 + [0x10000] + [0x20000] * 7
