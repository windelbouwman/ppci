
module main;
import bsp;

function void main()
{
   var int i;
   for (i=0;i<10;i = i+1)
   {
       switch(i)
       {
         case 2:
           { bsp.putc(66); }
         case 5:
           { bsp.putc(67); }
         case 8:
           { bsp.putc(65); }
         default:
           { bsp.putc(68); }
       }
   }
   bsp.putc(10);
}
