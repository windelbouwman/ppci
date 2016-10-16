// This test case is very generic, but requires 32 bit or more

module main;
import io;

function void main()
{
   var int i;
   var int b = 2;
   for (i=0; i<10; i = i + 1)
   {
     io.print2("A = ", i);
     b *= i + 1;
   }
   io.print2("B = ", b);
}
