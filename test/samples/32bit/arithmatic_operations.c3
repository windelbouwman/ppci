// Check arithmatics

module main;
import io;

var int x;

function void set_x(int v)
{
    x = v;
}

var int d;

function void main()
{
    var int w;
    d = 2;
    set_x(13);
    w = x / d;
    io.print2("w=", w);

    w = x - d;
    io.print2("w=", w);

    w = x % d;
    io.print2("w=", w);

    w = x + d;
    io.print2("w=", w);

    w = x ^ 0xf;
    io.print2("w=", w);
}
