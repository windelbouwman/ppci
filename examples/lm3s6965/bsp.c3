module bsp;
import main;

function void putc(byte c)
{
    var int *UART0DR;
    UART0DR = 0x4000C000 + 0x000; // UART0 Data register
    *UART0DR = c;
}

function void boot()
{
    // Init pins

    // enter main app:
    main.main();
}

function void exit()
{
    putc(4); // End of transmission
}
