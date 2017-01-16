
// This test checks the handling of a lot of arguments

module main;
import io;

function int sum(int a, int b, int c, int d, int e, int f, int g, int h)
{
    return a+b+c+d+e+f+g+h;
}

function void main()
{
   var int a = sum(1,2,3,4,5,6,7,8);
   io.print2("SUM=", a);
}
