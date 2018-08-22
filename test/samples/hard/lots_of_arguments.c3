
// This test checks the handling of a lot of arguments

module main;
import io;

function int sum(int a, int b, int c, int d, int e, int f, int g, int h, int32_t i, int j)
{
    return a+b+c+d+e+f+g+h+i+j;
}

function void main()
{
   var int a = sum(1,2,3,4,5,6,7,8,cast<int32_t>(9),10);
   io.print2("SUM=", a);
}
