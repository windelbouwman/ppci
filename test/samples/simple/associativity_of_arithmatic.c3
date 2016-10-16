
module main;
import io;

function void main()
{
   var int w;
   var int d;
   var int x;
   d = 2;
   x = 10;

   // 100 / 10 / 2 = 10 / 2 = 5, not 100 / 5 = 20
   w = 100 / x / d;
   io.print2("w=", w);

   // 100 - 10 - 2 = 88 = 0x58
   w = 100 - x - d;
   io.print2("w=", w);
}
