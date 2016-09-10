module main;
import io;
var int b;

// Apparently function arguments get sorted by name???

function void cpy(byte* dst, byte* src, int size)
{
    io.print2("to=", cast<int>(dst));
    io.print2("from=", cast<int>(src));
    io.print2("size=", size);
}

function void main()
{
    var byte[4] data;
    data[0] = 4;
    data[1] = 3;
    data[2] = 0;
    data[3] = 0;
    var byte* image_ptr = &data[0];
    var int x = *cast<int*>(image_ptr);
    io.print2("x=", x);
    cpy(1, 2, x);
}