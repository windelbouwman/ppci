
#include <stdio.h>

char *ptr = (char*) 0x1000;

void main_main()
{
  int c = 14;
  int res = 65 - 10 + c;
  printf("x = %d\n", res);

  // Dark pointer voodoo:

  int w, x[4], *y, *z;
  x[0] = 1042;
  x[1] = 1043;
  x[2] = 1044;
  x[3] = 1045;

  y = x;
  z = x;

  printf("*y -> %d\n", *y);
  y = y + 3;
  printf("*y -> %d\n", *y);
  y = y - 2;
  printf("*y -> %d\n", *y);
  y++;
  printf("*y -> %d\n", *y);
  y--;
  printf("*y -> %d\n", *y);
  y += 2;
  printf("*y -> %d\n", *y);
  w = y - z;  // pointer - pointer
  printf("pointer diff = %d\n", w);
  y -= 3;
  printf("*y -> %d\n", *y);

}
