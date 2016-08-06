module bsp;

public function void putc(byte c);

function void exit()
{
    putc(4); // End of transmission
}

