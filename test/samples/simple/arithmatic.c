
#include <stdio.h>

char *ptr = (char*) 0x1000;

void main_main()
{
  int c = 14;
  int res = 65 - 10 + c;
  printf("x = %d\n", res);
}
