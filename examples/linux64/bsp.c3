module bsp;

public function void putc(byte c);

public function void sleep(int ms)
{
    // TODO
}

function void exit();

var int global_tick;

public function bool get_key(int* key)
{
    return false;
}
