
#include <stdio.h>


void printf(char* txt)
{
  while (*txt != 0)
  {
    bsp_putc(*txt);
    txt++;
  }
}

void print_int(unsigned int num)
{
  int i, v;
  for (i = 28; i>=0; i-=4) {
    v = (num >> i) & 0xF;
    if (v > 9) {
      bsp_putc(v + 55);
    } else {
      bsp_putc(v + 48);
    }
  }

  bsp_putc(10);
}

void myprint(char* label, int num)
{
  printf(label);
  print_int((unsigned int)num);
}
