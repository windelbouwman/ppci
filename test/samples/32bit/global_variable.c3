module main;
import io;

var int MyGlob;
var struct {int a; int b;}[10] cplx1;
var struct {int a; int b;}[10] cplx2;

function void do1()
{
    MyGlob = MyGlob + 1;
    io.print2("G=", MyGlob);
}

function void do5()
{
    MyGlob = MyGlob + 5;
    io.print2("G=", MyGlob);
}

function int* get_ptr()
{
    return &MyGlob;
}

function void main()
{
    MyGlob = 0;
    do1();
    do1();
    do5();
    do1();
    do5();
    *(get_ptr()) += 2;
    *(get_ptr()) += 8;
    do5();
    cplx1[1].b = 2;
    cplx2[1].a = 22;
    io.print2("cplx1 1 b =", cplx1[1].b);
    io.print2("cplx2 1 a =", cplx2[1].a);
}
