
module bsp;

// var byte* UCSRA=0xc0, UCSRB=0xc1, UCSRC, UBRRL, UBRRH, UDR;
var byte* UCSRA, UCSRB, UCSRC, UBRRL, UBRRH, UDR;

public function void init()
{
  UCSRA = 0xc0;
  UCSRB = 0xc1;
  UCSRC = 0xc2;
  UBRRL = 0xc4;
  UBRRH = 0xc5;
  UDR = 0xc6;

  *UCSRA = 0x00;
  *UCSRB = 0x98;
  *UCSRC = 0x86;
  *UBRRH = 0x00;
  *UBRRL = 0x33;
  *UDR = 65;
}

public function void putc(byte x)
{
  *UDR = x;
}


