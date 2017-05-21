module bsp;

const byte* DR = 0x900001;

public function void putc(byte c)
{
  *DR = c;
}

public function void exit()
{
    putc(4); // End of transmission
}

