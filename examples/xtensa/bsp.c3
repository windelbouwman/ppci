
module bsp;

const byte* thr = cast<byte*>(0xfd050020);

public function void putc(byte c)
{
  *(thr + 2) = c;
}

function void exit()
{
}
