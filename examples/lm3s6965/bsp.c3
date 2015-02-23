module bsp;
import main;

type struct {
    int DR; // 0x0
    int RSR; // 0x4
    int dummy1; // 0x8
    int dummy2; // 0xC
    int dummy3; // 0x10
    int dummy4; // 0x14
    int FR; // 0x18
} uart_t;

type struct {
    int STCTRL; // 0x10
    int STRELOAD; // 0x14
} systick_t;

type struct {
    int EN0;
} nvic_t;

var uart_t* UART0;
var systick_t* SYSTICK;
var nvic_t* NVIC;

var int global_tick;

public function void putc(byte c)
{
    // Wait for busy:
    while (UART0->FR & 0x8 == 0x8)
    {
    }

    // Transmit char:
    UART0->DR = c;
}

public function bool get_key(int* k)
{
    if (UART0->FR & 0x10 == 0)
    {
        *k = UART0->DR;
    }
    else
    {
        return false;
    }
    return true;
}

function void boot()
{
    // Init pins
    UART0 = 0x4000C000; // UART0 address
    SYSTICK = 0xE000E010;
    NVIC = 0xE000E100;

    global_tick = 0;

    NVIC->EN0 |= (1 << 15); // Enable interrupt on systick
    SYSTICK->STRELOAD = 0x100000;
    SYSTICK->STCTRL |= 7; // enable

    // enter main app:
    main.main();
}

function void systick_isr()
{
    global_tick += 1;
    // putc(67);
}

function void exit()
{
    putc(4); // End of transmission
}
