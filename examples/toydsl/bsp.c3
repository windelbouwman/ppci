
module bsp;

public function void putc(byte c)
{
  syscall(1, 1, cast<int64_t>(&c), 1);
}

function void exit()
{
    syscall(60, 0, 0, 0);
}

function void syscall(int64_t nr, int64_t a, int64_t b, int64_t c);

