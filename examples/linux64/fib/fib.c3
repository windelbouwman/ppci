module main;
import io;

var int a, b;

function void main()
{
    a = 0;
    b = 1;
    var int i, tmp;
    for (i=0; i<10; i = i+1) {
        io.print2("f= ", b);
        tmp = a + b;
        a = b;
        b = tmp;
    }
}

