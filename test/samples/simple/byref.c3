
module main;
import io;
import bsp;

function void putc1(byte ch)
{
  putc2(&ch);
}

function void putc2(byte* ch)
{
  bsp.putc(*ch);
}

function void main()
{
   var string a = "he";
   var byte x;
   x = 0xa;
   putc1(a->txt[0]);
   putc1(x);
}
