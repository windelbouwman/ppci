// This sample contains a recursive tailcall
// This tailcall is food for optimizations.

module main;
import io;

function int f(int a, int b)
{
  if (a > 10)
  {
   return a + b;
  }
  else
  {
    return f(a+1, b);
  }
}

function void main()
{
  io.print2("f=", f(1, 2));
}
