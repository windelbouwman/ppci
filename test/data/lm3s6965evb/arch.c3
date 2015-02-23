module arch;

public function void putc(int c)
{
    var int *UART0DR;
    UART0DR = cast<int*>(0x4000C000 + 0x000); // UART0 Data register
    *UART0DR = c;
}

function void exit()
{
    putc(4); // End of transmission
}
