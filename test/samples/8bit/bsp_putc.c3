// Test if bsp putc works

module main;
import bsp;

function void main()
{
   bsp.putc(65);
   bsp.putc(66);
   bsp.putc(67);
   bsp.putc(68);
   bsp.putc(69);
   bsp.putc(10);
}
