
module main;
import io;

var int boo = 2;
var int[2] a = {9, 5};

function void main()
{
   var int w = 2;
   io.print2("w=", w);
   var int d;
   d = a[1];
   io.print2("d=", d);

   var int x = woot(20);
   io.print2("x=", x);

   var int[4] z = {woot(20), woot(30), 2+ 2, 111};
   io.print2("z[2]=", z[2]);
}

function int woot(int x)
{
  return x - 10;
}
