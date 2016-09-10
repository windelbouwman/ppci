// Check if 8 bits pointer assignments work with 32 bit pointers.
// This test is architecture dependent!
// Assume little endianess.

module main;
import io;

function void main()
{
    var int w;
    var int* pw;
    var byte* pb;
    var byte* pb2;
    var byte** ppb;
    pw = &w;
    pb = cast<byte*>(pw);
    pb2 = pb + 2;
    *pw = 0x11223344;
    *pb = 0x88;
    ppb = &pb2;
    **ppb = 0x66; // double pointer hackzzz
    io.print2("w=", w);
}
