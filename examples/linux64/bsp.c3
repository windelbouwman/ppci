module bsp;

public function void putc(byte c);
function void exit();

var int global_tick;

public function bool get_key(int* key)
{
    return false;
}
