
#include <stdio.h>


void printf(char* txt)
{
  while (*txt != 0)
  {
    bsp_putc(*txt);
    txt++;
  }
}

void myprint(char* label, int num)
{
  printf(label);
}
