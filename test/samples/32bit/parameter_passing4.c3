module main;
import io;

// Check that parameter passing works as expected

function void dump(int a, int b, int c, int d)
{
    io.print2("a=", a);
    io.print2("b=", b);
    io.print2("c=", c);
    io.print2("d=", d);
}

function void dump2(int a, int b, int c, int d)
{
    dump(a,b,c,d);
}

function void main()
{
    dump(4,55,66,0x1337);
    dump2(4,55,66,0x1337);
}
