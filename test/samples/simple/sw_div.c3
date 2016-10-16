
module main;
import io;

function int sdiv(int num, int den)
{
  var int res = 0;
  var int current = 1;

  while (den < num)
  {
    den = den << 1;
    current = current << 1;
  }

  while (current != 0)
  {
    if (num >= den)
    {
      num -= den;
      res = res | current;
    }
    den = den >> 1;
    current = current >> 1;
  }
  return res;
}

function void main()
{
  io.print2("10/5=", sdiv(10, 5));
  io.print2("13/6=", sdiv(13, 6));
  io.print2("31/7=", sdiv(31, 7));
  io.print2("10/2=", sdiv(10, 2));
}
