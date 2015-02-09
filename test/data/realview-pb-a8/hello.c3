module hello;

function void main()
{
  var int* UART0DR;
  UART0DR = 0x10009000; // UART0 Data register
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

  // EOT:
  *UART0DR = 4;
    while(true)
    {
    }
}

