module bsp;
public function void putc(byte c)
{
var int *UART0DR;
var int *UART0SR;
UART0DR = cast<int*>(0x1A100008);
UART0SR = cast<int*>(0x1A100004);
  while (((*UART0SR)&8)!=0) {}
 *UART0DR=c;
}