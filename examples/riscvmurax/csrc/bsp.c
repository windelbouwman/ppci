
typedef struct uart{
int dr;
int sr;
int ack;
} UART;

UART* uart1 = (UART*)(0x20000000);

void bsp_putc(char c)
{
    uart1->dr = c;
}