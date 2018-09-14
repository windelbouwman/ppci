module bsp;

const byte* DR = 0x84000004;

public function void putc(byte c)
{
  *DR = c;
}

public function void exit()
{
    putc(4); // End of transmission
}

function void memcpy(uint8_t* dst, uint8_t* src, int count)
{
}
