
module main;
import io;

var double volatile a, b;

function void main()
{
    a = 2;
    b = a / 10;
    io.print2("B=", cast<int>(b * 10));
}

