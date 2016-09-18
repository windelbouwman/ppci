module gdbstub;
import bsp;
import io;



public function int hexchar2int(byte ch)
{
    if(ch>=0x61 and ch<0x67) {
        return(ch-0x61+10);
    }
    if(ch>=0x30 and ch<0x3A) {
        return(ch-0x30);
    }
    if(ch>=0x41 and ch<0x47) {
        return(ch-0x41+10);
    }
    return(-1);
}

public function byte highhex(byte ch)
{
    ch=ch>>4 & 0xf;
    if(ch>9) {
        ch+= 0x37;
    }
    else {
        ch+= 0x30;
    }
    return(ch);
}


public function byte lowhex(byte ch)
{
    ch&= 0xf;
    if(ch>9) {
        ch+= 0x37;
    }
    else {
        ch+= 0x30;
    }
    return(ch);
}

function int hexstring2int(byte* ptr, int* val)
{
   var int numchars = 0;
   var byte ch;
   var int res;
   ch = *ptr;
   res = hexchar2int(ch);
   //io.print_int(res);
   while(res != -1) {
     *val=(*val<<4)+res;
     numchars+=1;
     ptr+=1;
     ch=*ptr;
     res = hexchar2int(ch);
     //io.print_int(res);
   }
   return(numchars);
}

// read sequence $<data>#<checksum>
public function int get_packet(byte* data)
{
    var byte checksum;
    var byte xmitcsum;
    var byte bch;

    // wait for $
    bch=bsp.getc();
    while (bch != 0x24) {
          bch=bsp.getc();
          }

    checksum = 0;
    xmitcsum = -1;

    // read until #
    bch = bsp.getc();
    while (bch!=0x23) {
         checksum = checksum + bch;
         *data = bch;
         data += 1;
         bch = bsp.getc();
         }
    *data = 0;
    bch = bsp.getc();
    xmitcsum = hexchar2int(bch) << 4;
    bch = bsp.getc();
    xmitcsum =  xmitcsum + hexchar2int(bch);
    checksum &= 0xff;
    if (checksum != xmitcsum) {
         // failed checksum -
         bsp.putc(0x2d);
         io.print("Received:");
         io.print_int(xmitcsum);
         io.print("Calculated:");
         io.print_int(checksum);
         return(-1);
         } else {
         // successful transfer +
         bsp.putc(0x2b);
         return(0);
         }
}

// $<packet info>#<checksum>
public function void put_packet(byte* data)
{
    var byte checksum;
    var int count;
    var byte bch;

    bsp.putc(0x24);
    checksum = 0;

    bch = *data
    while (bch != 0) {
        bsp.putc(bch);
        checksum += bch;
        data += 1;
        bch=*data
        }
    checksum&=0xff;
    bsp.putc(0x23);
    bsp.putc(highhex(checksum));
    bsp.putc(lowhex(checksum));
    bch=bsp.getc();
}

 public function void readmem(byte* cmdptr,byte* dataptr)
{
  var int addr = 0;
  var int length = 0;
  var int res = 0;
  var byte ch;
  var byte* memptr;
  res=hexstring2int(cmdptr,&addr);
  cmdptr+=res+1;
  res=hexstring2int(cmdptr,&length);
  memptr=addr;
  while(length>0) {
      ch=*memptr;
      *dataptr=highhex(ch);
      dataptr+=1;
      *dataptr=lowhex(ch);
      memptr+=1;
      dataptr+=1;
      length-=1;
  }
  *dataptr=0;
}

public function void readreg(byte* cmdptr,byte* regs, byte* dataptr)
{
  var int regnr = 0;
  var int res = 0;
  var int i;
  var byte bch;
  var byte* memptr;
  res=hexstring2int(cmdptr,&regnr);
  regs+=regnr*4;
  for(i=0;i<4;i+=1) {
     bch = *regs;
     *dataptr = highhex(bch);
     dataptr += 1;
     *dataptr = lowhex(bch);
     dataptr += 1;
     regs += 1;
  }
  *dataptr=0;
}

public function void writemem(byte* cmdptr)
{
  var int addr = 0;
  var int length = 0;
  var int res = 0;
  var byte ch;
  var byte* memptr;
  res=hexstring2int(cmdptr,&addr);
  cmdptr+=res+1;
  res=hexstring2int(cmdptr,&length);
  memptr=addr;
  cmdptr+=res+1;
  while(length>0) {
      ch=*cmdptr;
      res=hexchar2int(ch);
      cmdptr+=1;
      ch=*cmdptr;
      res=(res<<4)+hexchar2int(ch);
      cmdptr+=1;
      *memptr=res;
      memptr+=1;
      length-=1;
  }
}

public function void setbreak(byte* cmdptr, int* memval)
{
  var int addr = 0;
  var int* memptr;
  var int res = 0;
  res=hexstring2int(cmdptr,&addr);
  memptr=addr;
  *memval=*memptr;
  *memptr=0x100073
}

public function void clearbreak(byte* cmdptr, int* memval)
{
  var int addr = 0;
  var int* memptr;
  var int res = 0;
  res=hexstring2int(cmdptr,&addr);
  memptr=addr;
  *memptr=*memval;
}

public function void status(byte id, byte* regs, byte* dataptr)
{
 var int i;
 var byte bch;
 *dataptr = 0x54; // "T"
 dataptr += 1;
 *dataptr = highhex(id);
 dataptr += 1;
 *dataptr = lowhex(id);
 dataptr += 1;
 *dataptr = 0x32;  //"2" = PC
 dataptr += 1;
 *dataptr = 0x30;  //"0" = PC
 dataptr += 1;
 *dataptr = 0x3a; // ":"
 dataptr += 1;
 regs+=128;
 for(i=0;i<4;i+=1) {
     bch = *regs;
     *dataptr = highhex(bch);
     dataptr += 1;
     *dataptr = lowhex(bch);
     dataptr += 1;
     regs += 1;
 }
 *dataptr=0x3b; // ";"
 dataptr+=1;
 *dataptr=0;
}