module bsp;

const byte* DR = 0x90000000;

public function void putc(byte c)
{
  *DR = c;
}

public function void exit()
{
    putc(4); // End of transmission
}

public function bool get_key(int* k)
{
  return false;
}

public function void sleep(int ms)
{
}
