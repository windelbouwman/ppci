
#include <stdio.h>

typedef struct { int a; char b; int c; } foo_t;

void do3(int x, foo_t y, int z)
{
  printf("Enter do\n");
  int g;
  g = x + y.a + (int)y.b + y.c + z;
  printf("v:%d\n", g);
  printf("Exit do\n");
}

void main_main()
{
  printf("Enter main\n");
  foo_t bar;
  bar.a = 5;
  bar.b = 99;
  bar.c = 124;
  do3(0x1337, bar, 0x42);
  printf("Exit main\n");
}

