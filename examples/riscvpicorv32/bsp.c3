module bsp;
public function void putc(byte c)
{
var int *UART0DR;
UART0DR = cast<int*>(0x10000000);
 *UART0DR=c;
}