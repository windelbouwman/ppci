import cmd
import sys
import select
import binascii
import time
from ppci.binutils.dbg import *
from ppci.binutils.dbg_cli import DebugCli
from socket import *
from ppci.arch.riscv import RiscvArch
from ppci.common import str2int

class PulpinoDebugDriver(DebugDriver):
    def __init__(self):
        self.status = STOPPED
        self.s = socket(AF_INET, SOCK_STREAM)
        self.s.connect(("localhost", 1234))
        self.timeout = 10
        self.retries = 3
        
    def pack(self, data):
        """ formats data into a RSP packet """
        for a, b in [(x, chr(ord(x) ^ 0x20)) for x in ['}','*','#','$']]:
            data = data.replace(a,'}%s' % b)
        return "$%s#%02X" % (data, (sum(ord(c) for c in data) % 256))
    
    def unpack(self, pkt):
        """ unpacks an RSP packet, returns the data"""
        if pkt[0:1]!=b'$' or pkt[-3:-2]!=b'#':
            raise ValueError('bad packet')
        if (sum(c for c in pkt[1:-3]) % 256) != int(pkt[-2:],16):
            raise ValueError('bad checksum')
        pkt = pkt[1:-3]
        return pkt
    
    def switch_endian(self, data):
        """ byte-wise reverses a hex encoded string """
        return ''.join(reversed(list(self.split_by_n( data ,2))))

    def split_by_n( self, seq, n ):
        """A generator to divide a sequence into chunks of n units.
        src: http://stackoverflow.com/questions/9475241/split-python-string-every-nth-character"""
        while seq:
            yield seq[:n]
            seq = seq[n:]

    def sendpkt(self, data ,retries=50):
        """ sends data via the RSP protocol to the device """
        self.get_status(0)
        self.s.send(self.pack(data).encode())
        res = None
        while not res:
            res = self.s.recv(1)
        discards = []
        while res!=b'+' and retries>0:
            discards.append(res)
            self.s.send(self.pack(data).encode())
            retries-=1
            res = self.s.recv(1)
        if len(discards)>0: print('send discards', discards)
        if retries==0:
            raise ValueError("retry fail")
    
    def readpkt(self, timeout=0):
        """ blocks until it reads an RSP packet, and returns it's
           data"""
        c=None
        discards=[]
        if timeout>0:
            start = time.time()
        while(c!=b'$'):
            if c: discards.append(c)
            c=self.s.recv(1)
            if timeout>0 and start+timeout < time.time():
                return
        if len(discards)>0: print('discards', discards)
        res=[c]

        while True:
            res.append(self.s.recv(1))
            if res[-1]==b'#' and res[-2]!=b"'":
                    res.append(self.s.recv(1))
                    res.append(self.s.recv(1))
                    try:
                        res=self.unpack(b''.join(res))
                    except:
                        self.s.send(b'-')
                        res=[]
                        continue
                    self.s.send(b'+')
                    return res
                    
    def sendbrk(self):
        """ sends break command to the device """
        self.s.send(chr(0x03).encode())

    def get_pc(self):
        """ read the PC of the device"""
        self.sendpkt("p 20",self.retries)
        pc=int(self.switch_endian(self.readpkt(self.timeout).decode()),16)
        print("PC value read:%x"%pc)
        return(pc)

    def run(self):
        """start the device"""
        if(self.status==STOPPED):
            adr=self.get_pc()
            self.sendpkt("c%x"%adr)
        self.status = RUNNING
        
    def restart(self):
        """restart the device"""
        if(self.status==STOPPED):
             self.sendpkt("c00000080")
        self.status = RUNNING

    def step(self):
        """restart the device"""
        if(self.status==STOPPED):
             self.sendpkt("s")
             self.get_status(self.timeout)
             time.sleep(1)
             self.get_pc()
        

    def stop(self):
        self.sendbrk()
        self.status = STOPPED

    def get_status(self,timeout=5):
        if timeout>0:
            start = time.time()
        readable, writable, exceptional = select.select([self.s], [], [], 0)
        while(readable==0):
            readable, writable, exceptional = select.select([self.s], [], [], 0)
            if timeout>0 and start+timeout < time.time():
                return
        if readable:
            res=self.readpkt(self.timeout)
            print(res)
            if(res==b"S05"): 
                print("Target stopped..")
                self.status = STOPPED
                return(STOPPED)
            else:
                return(RUNNING)
        return self.status


    def get_registers(self, registers):
        self.sendpkt("g",3)
        data=self.readpkt(3)
        res={}
        for r in enumerate(registers):
            v = binascii.a2b_hex(data[r[0]*8:r[0]*8+8])
            res[r[1]] = struct.unpack('<I', v)[0]
        return res
        
    def set_breakpoint(self, address):
        self.sendpkt("Z0,%x,4"%address,self.retries)
        self.readpkt(self.timeout)
        pass
        
    def clear_breakpoint(self, address):
        self.sendpkt("z0,%x,4"%address,self.retries)
        self.readpkt(self.timeout)
        pass

    def read_mem(self, address, size):
         self.sendpkt("m %x,%x"%(address,size),self.retries)
         ret = binascii.unhexlify(self.readpkt(self.timeout))
         return ret

    def write_mem(self, address, data):
        length=len(data)
        data=self.switch_endian(binascii.hexlify(data).decode())
        self.sendpkt("M %x,%x:%s"%(address,length,data),self.retries)
        pass

def main():
    #  Main
    debugger = Debugger('riscv', PulpinoDebugDriver())
    f = 'samples.txt'
    debugger.load_symbols(f)
    DebugCli(debugger).cmdloop()
    f.close()

if __name__ == "__main__":
    main()
