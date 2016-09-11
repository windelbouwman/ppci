module irq;
import io;
import bsp;
import gdbstub;

var byte[280] outbuffer;
var byte[80] inbuffer;
var int breakopcode;


function void irq(byte* regs,int irqs)
{
 var int i = 0 , j = 0;
 var byte bch;
 var byte* outptr = 0;
 var byte* regsptr = 0;
 var bool debug = true;
 var int res = 0;

 while(debug) {
     res = gdbstub.get_packet(&inbuffer);
     bch = inbuffer[0];
     if(bch == 0x6d) {
         gdbstub.readmem(&inbuffer[2],&outbuffer[0]);
         gdbstub.put_packet(&outbuffer);
         }
     if(bch == 0x4d) {
         gdbstub.writemem(&inbuffer[2]);
        }
     if(bch == 0x67) {
         outptr=&outbuffer[0];
         regsptr = regs;
         for(i=0;i<33;i=i+1) {
             for(j=0;j<4;j=j+1){
                 bch = *regsptr;
                 *outptr = gdbstub.highhex(bch);
                 outptr += 1;
                 *outptr = gdbstub.lowhex(bch);
                 outptr += 1;
                 regsptr += 1;
                }
            }
            *outptr=0;
            gdbstub.put_packet(&outbuffer[0]);
        }
        if(bch == 0x5a) {
            gdbstub.setbreak(&inbuffer[3], &breakopcode);
        }
        if(bch == 0x7a) {
            gdbstub.clearbreak(&inbuffer[3], &breakopcode);
        }
        if(bch == 0x3f) {
            gdbstub.status(irqs, regs, &outbuffer[0]);
            gdbstub.put_packet(&outbuffer);
        }
        if(bch == 0x63) {
             debug=false;
        }
    }
}