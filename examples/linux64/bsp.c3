module bsp;

public function void putc(byte c)
{
  syscall(1, 1, cast<int64_t>(&c), 1);
}

public function void sleep(int ms)
{
    // TODO
    var struct { int seconds; int nanos; } delay;
    delay.seconds = 0;
    delay.nanos = ms * 1000000;
    var int64_t delay_addr = cast<int64_t>(&delay);
    syscall(35, delay_addr, 0, 0);
}

function void exit()
{
    syscall(60, 0, 0, 0);
}

var int global_tick;

public function bool get_key(int* key)
{
    return false;
}

// rax contains the syscall number
// rdi is parameter 1
// rsi is paramater 2
// rdx is paramater 3
// TODO: check return value:
function void syscall(int64_t nr, int64_t a, int64_t b, int64_t c);

