
// Test recursive function with fibonacci algorithm

module main;
import io;

function int fib(int x)
{
    if (x < 3)
    {
        return 1;
    }
    else
    {
        return fib(x - 1) + fib(x - 2);
    }
}

function void main()
{
    var int i;
    i = fib(13);
    io.print2("fib(13)=", i);
}

// fib(13) == 233 == 0xe9
