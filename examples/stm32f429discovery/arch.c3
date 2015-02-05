module arch;

function void putc(byte c)
{
    // Route data over ITM trace port.
    // 0xE000 0000 is the base address for the streaming case.

    var int *ITM_PORT;
    ITM_PORT  = cast<int*>(0xE0000000);
    // TODO: wait while port[0] == 0

    while (*ITM_PORT == 0)
    {
    }

    *ITM_PORT = c;

}

function void exit()
{
    putc(4); // End of transmission
}
