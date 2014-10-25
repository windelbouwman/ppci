module hello;

function void main()
{
  var int* UART0DR;
  UART0DR = cast<int*>(0x4000C000 + 0x000); // UART0 Data register
  *UART0DR = 72;
  *UART0DR = 101;
  *UART0DR = 108;
  *UART0DR = 108;
  *UART0DR = 111;
  *UART0DR = 32;
  *UART0DR = 119;
  *UART0DR = 111;
  *UART0DR = 114;
  *UART0DR = 108;
  *UART0DR = 101;

// End of transmission:
  *UART0DR = 4;
    while(true) {}
}

