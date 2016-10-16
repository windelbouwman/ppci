
module main;
import io;

function int smul(int a, int b)
{
  var int res = 0;
  while (b > 0)
  {
    if ((b & 1) == 1)
    {
      res += a;
    }
    a = a << 1;
    b = b >> 1;
  }
  return res;
}

function void main()
{
  io.print2("10*5=", smul(10, 5));
  io.print2("13*6=", smul(13, 6));
  io.print2("31*7=", smul(31, 7));
}
