module main;
import io;

function void main()
{
    var int[10] x;
    var int[10] y;
    y[1] = 0x11;
    y[2] = 0x33;
    x[1] = 0x44;
    x[2] = 0x55;
    io.print2("y[1]=", y[1]);
    io.print2("x[1]=", x[1]);
}