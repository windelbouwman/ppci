
module bsp;

public function void putc(byte c)
{
  syscall(1, 1, cast<int>(&c), 1);
}

function void exit()
{
    syscall(60, 0, 0, 0);
}

function void syscall(int nr, int a, int b, int c);

