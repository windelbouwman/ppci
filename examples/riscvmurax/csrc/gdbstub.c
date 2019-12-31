#define true 1
#define false 0

typedef unsigned char byte;
typedef struct uart {
unsigned int dr;
unsigned int sr;
unsigned int ackint;
unsigned int setint;
} UART;

UART* uart0 = (UART*)(0x10000000);
//UART* uart0;
byte outbuffer[280];
byte inbuffer[80];
int breakopcode;



void putc(byte c)
{
    // wait while busy:
    while ((uart0->sr & 0x1) == 0x1);
    // transmit char:
    uart0->dr = c;
}

byte getc()
{
    // wait for rx available:
    while ((uart0->sr & 0x2) == 0x0);
    // receive char:
    return uart0->dr;
}

void ackint()
{
    uart0->ackint = 1;
}

void ioprint(char* txt)
{
    while (*txt)
    {
        putc(*txt);
        txt++;
    }
}

void ioprint_int(int i)
{
    int b;
    int c;
    ioprint("0x");
    for (b = 28; b >= 0; b = b - 4)
    {
        c = (i >> b) & 0xF;
        if (c < 10)
        {
            putc( 48 + c );
        }
        else
        {
            putc( 65 - 10 + c );
        }
    }
    putc(10); // Newline!
}

int hexchar2int(byte ch)
{
    if(ch>=0x61 && ch<0x67) {
        return(ch-0x61+10);
    }
    if(ch>=0x30 && ch<0x3A) {
        return(ch-0x30);
    }
    if(ch>=0x41 && ch<0x47) {
        return(ch-0x41+10);
    }
    return(-1);
}

byte highhex(byte ch)
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


byte lowhex(byte ch)
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

int hexstring2int(byte* ptr, int* val)
{
   int numchars = 0;
   byte ch;
   int res;
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


int get_packet(byte* data)
{
    byte checksum;
    int xmitcsum;
    byte bch;

    // wait for $
    bch=getc();
    while (bch != 0x24) {
          bch=getc();
          }

    checksum = 0;
    xmitcsum = -1;

    // read until #
    bch = getc();
    while (bch!=0x23) {
         checksum = checksum + bch;
         *data = bch;
         data += 1;
         bch = getc();
         }
    *data = 0;
    bch = getc();
    xmitcsum = hexchar2int(bch) << 4;
    bch = getc();
    xmitcsum =  xmitcsum + hexchar2int(bch);
    checksum &= 0xff;
    if (checksum != xmitcsum) {
         // failed checksum -
         putc(0x2d);
         ioprint("Received:");
         ioprint_int(xmitcsum);
         ioprint("Calculated:");
         ioprint_int(checksum);
         return(-1);
         } else {
         // successful transfer +
         putc(0x2b);
         return(0);
         }
}

void put_packet(byte* data)
{
    byte checksum;
    int count;
    byte bch;

    putc(0x24);
    checksum = 0;

    bch = *data;
    while (bch != 0) {
        putc(bch);
        checksum += bch;
        data += 1;
        bch=*data;
        }
    checksum&=0xff;
    putc(0x23);
    putc(highhex(checksum));
    putc(lowhex(checksum));
    bch=getc();
}

void readmem(byte* cmdptr,byte* dataptr)
{
  int addr = 0;
  int length = 0;
  int res = 0;
  byte ch;
  byte* memptr;
  res=hexstring2int(cmdptr,&addr);
  cmdptr+=res+1;
  res=hexstring2int(cmdptr,&length);
  memptr=(byte*)addr;
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

void readreg(byte* cmdptr,byte* regs, byte* dataptr)
{
  int regnr = 0;
  int res = 0;
  int i;
  byte bch;
  byte* memptr;
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

void readregs(byte* regs, byte* dataptr)
{
  int i,j;
  byte bch = 0;
  for(i=0;i<33;i=i+1) {
      for(j=0;j<4;j+=1) {
         bch = *regs;
         *dataptr = highhex(bch);
         dataptr += 1;
         *dataptr = lowhex(bch);
         dataptr += 1;
         regs += 1;
      }
  }
  *dataptr=0;
}



void writereg(byte* cmdptr,byte* regs)
{
  int regnr = 0;
  int res = 0;
  int i;
  byte ch = 0;
  byte* memptr;
  res = hexstring2int(cmdptr,&regnr);
  cmdptr += res+1;
  regs += regnr*4;
  for(i=0;i<4;i+=1) {
     ch = *cmdptr;
     res = hexchar2int(ch);
     cmdptr += 1;
     ch = *cmdptr;
     res = (res<<4) + hexchar2int(ch);
     cmdptr += 1;
     *regs = res;
     regs += 1;
  }
}

void writeregs(byte* cmdptr,byte* regs)
{
  int i,j;
  int res = 0;
  byte ch = 0;
  for(i=0;i<33;i=i+1) {
    for(j=0;j<4;j+=1) {
       ch = *cmdptr;
       res = hexchar2int(ch);
       cmdptr += 1;
       ch = *cmdptr;
       res = (res<<4) + hexchar2int(ch);
       cmdptr += 1;
       *regs = res;
       regs += 1;
       }
    }
}

void writemem(byte* cmdptr)
{
  int addr = 0;
  int length = 0;
  int res = 0;
  byte ch;
  byte* memptr;
  res = hexstring2int(cmdptr,&addr);
  cmdptr += res+1;
  res = hexstring2int(cmdptr,&length);
  memptr = (byte*)addr;
  cmdptr += res+1;
  while(length>0) {
      ch = *cmdptr;
      res = hexchar2int(ch);
      cmdptr += 1;
      ch = *cmdptr;
      res = (res<<4) + hexchar2int(ch);
      cmdptr += 1;
      *memptr = res;
      memptr += 1;
      length -= 1;
  }
}

void setbreak(byte* cmdptr, int* memval)
{
  int addr = 0;
  int* memptr;
  int res = 0;
  res=hexstring2int(cmdptr,&addr);
  memptr=(int*)addr;
  *memval=*memptr;
  *memptr=0x100073;
}

void clearbreak(byte* cmdptr, int* memval)
{
  int addr = 0;
  int* memptr;
  int res = 0;
  res=hexstring2int(cmdptr,&addr);
  memptr=(int*)addr;
  *memptr=*memval;
}

void status(byte id, byte* regs, byte* dataptr)
{
 int i;
 byte bch;
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

int irq_irq(byte* regs,int irqs)
{
 int i = 0 , j = 0;
 byte bch;
 byte* outptr = 0;
 byte* regsptr = 0;
 int debug = true;
 int res = 0;
 int steps = 0;
// uart0 = (UART*)(0x10000000);

 status(irqs, regs, &outbuffer[0]);
 put_packet(&outbuffer[0]);

 while(debug) {
     res = get_packet(&inbuffer[0]);
     bch = inbuffer[0];
     if(bch == 0x6d) {
         readmem(&inbuffer[2],&outbuffer[0]);
         put_packet(&outbuffer[0]);
         }
     if(bch == 0x4d) {
         writemem(&inbuffer[2]);
         outbuffer[0] = 0x4f;
         outbuffer[1] = 0x4b;
         outbuffer[2] = 0;
         put_packet(&outbuffer[0]);
        }
     if(bch == 0x70) {
         readreg(&inbuffer[2], regs, &outbuffer[0]);
         put_packet(&outbuffer[0]);
         }
     if(bch == 0x50) {
         writereg(&inbuffer[2], regs);
         outbuffer[0] = 0x4f;
         outbuffer[1] = 0x4b;
         outbuffer[2] = 0;
         put_packet(&outbuffer[0]);
         }
     if(bch == 0x67) {
         readregs(regs, &outbuffer[0]);
         put_packet(&outbuffer[0]);
        }
     if(bch == 0x47) {
        writeregs(&inbuffer[2], regs);
        outbuffer[0] = 0x4f;
        outbuffer[1] = 0x4b;
        outbuffer[2] = 0;
        put_packet(&outbuffer[0]);
        }
     if(bch == 0x5a) {
        setbreak(&inbuffer[3], &breakopcode);
        outbuffer[0] = 0x4f;
        outbuffer[1] = 0x4b;
        outbuffer[2] = 0;
        put_packet(&outbuffer[0]);
        }
     if(bch == 0x7a) {
        clearbreak(&inbuffer[3], &breakopcode);
        outbuffer[0] = 0x4f;
        outbuffer[1] = 0x4b;
        outbuffer[2] = 0;
        put_packet(&outbuffer[0]);
        }
     if(bch == 0x3f) {
        status(irqs, regs, &outbuffer[0]);
        put_packet(&outbuffer[0]);
        }
     if(bch == 0x63) {
        debug=false;
        }
     if(bch == 0x73) {
        uart0->setint = 1;
        return(1);
        }
     if(bch == 0x6e) {
        res = hexstring2int(&inbuffer[2],&steps);
        uart0->setint = 1;
        return(steps);
        }
    }
 ackint();
 return(0);
}

