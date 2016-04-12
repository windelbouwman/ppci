import time, cmd, sys
from socket import *
import select

def str2int(s):
    if(s.find("0x")>=0):
        s=s[2:]
        return(int(s,16))
    return(int(s))

class rsp:
    def __init__(self, port):
        self.s = socket(AF_INET, SOCK_STREAM)
        self.s.connect(("localhost", port))
        self.targetstopped = True
        self.timeout = 3
        
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
    
    
    def sendpkt(self, data ,retries=50):
        """ sends data via the RSP protocol to the device """
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
        
    def sendbrk(self):
        """ sends data via the RSP protocol to the device """
        self.s.send(chr(0x03).encode())
    
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
    
    def checktarget(self):
        readable, writable, exceptional = select.select([Rsp.s], [], [], 0)
        if readable:
            res=Rsp.readpkt(Rsp.timeout)
            print(res)
            if(res==b"S05"): 
                print("Target stopped..")
                self.targetstopped = True
        
                    
    def close(self):
        self.s.close()

Rsp = rsp(1234)

class command_interpreter(cmd.Cmd):

    intro="""
    Idbg: Interactive textmode debugger
    """
    prompt=">>> "
    
    def __init__(self):
        self.address_line={}
        self.line_address={}
        self.linetable=False
        self.maxline=0
        super().__init__()
        
    def checktable(self):
        if(self.linetable==False):
            print("Please first load debug-information with rdltab.")
            return(False)
        else:
            return(True)
            
    def checkstopped(self):
        if(Rsp.targetstopped==False):
            print("Command not possible, Target not stopped. Please send break.")
            return(False)
        else:
            return(True)
        
    def do_exit(self, line): 
        """exit the interpreter session"""
        Rsp.close()
        sys.exit(-1)
    
    def do_rd(self, line): 
        """rd adr,len: read len bytes from memory at adr"""
        x = line.split(',')
        adr = str2int(x[0])
        count = str2int(x[1])
        Rsp.sendpkt("m %x,%x"%(adr,count),3)
        print(Rsp.readpkt(Rsp.timeout))
      
    def do_wr(self, line): 
        """wr adr,len,hexdata: write len bytes with hexdata to adr in memory"""
        x = line.split(',')
        adr = str2int(x[0])
        count = str2int(x[1])
        data = x[2]
        Rsp.sendpkt("M %x,%x:%s"%(adr,count,data),3)
        print(Rsp.readpkt(Rsp.timeout))
      
    def do_restart(self, line):
        """restart: reset the processor"""
        if(self.checkstopped()==True):
            Rsp.sendpkt("c00000080")
            Rsp.targetstopped = False
        
    
    def do_contadr(self, line):
        """cont adr: start the processor from adr"""
        if(self.checkstopped()==True):
            adr=str2int(line)
            Rsp.sendpkt("c%x"%adr)
            Rsp.targetstopped = False
    
    def do_contline(self, line):
        """contline line: start the processor from line"""
        if(self.checkstopped()==True):
            adr=str2int(line)
            if(self.checktable()==True):
                iline=str2int(line)
                while line not in self.line_address and iline<self.maxline:
                    iline+=1
                adr=self.line_address[iline]
                Rsp.sendpkt("c%x"%adr)
                Rsp.targetstopped = False
        
    
    def do_break(self, line):
        """break: send break to the processor"""
        Rsp.sendbrk()
        Rsp.checktarget()
    
    def do_setbrkadr(self, line):
        """setbreak adr"""
        if(self.checkstopped()==True):
            adr=str2int(line)
            Rsp.sendpkt("Z0,%x,4"%adr)
            Rsp.readpkt(Rsp.timeout)
        
    def do_setbrkline(self, line):
        """setbrkline line"""
        if(self.checkstopped()==True):
            if(self.checktable()==True):
                iline=str2int(line)
                while line not in self.line_address and iline<self.maxline:
                    iline+=1
                adr=self.line_address[iline]
                Rsp.sendpkt("Z0,%x,4"%adr)
                Rsp.readpkt(Rsp.timeout)
    
    def do_clearbrkadr(self, line):
        """clearbrkadr adr: clears breakpoint at adr"""
        if(self.checkstopped()==True):
            adr=str2int(line)
            Rsp.sendpkt("z0,%x,4"%adr)
            Rsp.readpkt(Rsp.timeout)
        
    def do_clearbrkline(self, line):
        """clearbrkline line: clears breakpoint at line"""
        if(self.checktable()==True):
            iline=str2int(line)
            while line not in self.line_address and iline<self.maxline:
                iline+=1
            adr=self.line_address[iline]
            Rsp.sendpkt("z0,%x,4"%adr)
            Rsp.readpkt(Rsp.timeout)
    
    def do_rdltab(self, line):
        """rdltab file,fsrc: read the debug-line-information for fsrc from file"""
        split=line.split(",")
        fname=split[0]
        fsrc=split[1]
        f=open(fname,"r")
        for line in f:
            split = line.split()
            address = int(split[-1][2:], 16)
            if split[0] == 'line:':
                colon = split[1].rfind(':')
                filename, line = split[1][1:colon-1], int(split[1][colon+1:])
                if filename == fsrc+'.c3':
                    if address not in self.address_line:
                        self.line_address[line] = address
                        self.address_line[address] = line
                        if(line>self.maxline):
                            self.maxline=line
        f.close()
        self.linetable=True
        
    def precmd(self, line):
        Rsp.checktarget()
        return cmd.Cmd.precmd(self, line)
        

        

def main():
    #  Main
    command_interpreter().cmdloop()

if __name__ == "__main__":
    main()
