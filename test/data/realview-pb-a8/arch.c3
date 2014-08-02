module arch;
import io;

function void putc(int c)
{
    var int *UART0DR;
    UART0DR = cast<int*>(0x10009000);
    *UART0DR = c;
}

