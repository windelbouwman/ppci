
module main;
import io;

var float volatile a, b;

function void main()
{
    a = 2;
    b = a / 10;
    io.print2("A=", cast<int>(a));
    io.print2("B=", cast<int>(b));
    io.print2("B*10=", cast<int>(b * 10));
}

