module main;
import io;

// This test actually tests the qemu pipe system when values go
// beyond 1000 loops.

function void main()
{
    var int i;
    for (i=0; i<100; i = i + 1)
    {
      io.print2("A = ", i);
    }
}
