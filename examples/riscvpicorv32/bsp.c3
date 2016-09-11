module bsp;
type struct {
    int DR; // 0x0
    int SR; // 0x4
} uart_t; 

var uart_t* UART0;


public function void putc(byte c)
{
    UART0 = 0x10000000;
    // Wait for busy:
    while (UART0->SR & 0x1 == 0x1)
    {
    }
    // Transmit char:
    UART0->DR = c;
}

public function byte getc()
{
    var int c;
    UART0 = 0x10000000;
    // Wait for RX-available:
    while (UART0->SR & 0x2 == 0x0)
    {
    }
    // Receive char:
    c = UART0->DR;
    return cast<byte>(c);
} 