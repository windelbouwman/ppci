
#include <stdio.h>

typedef struct D {
  int a;
  char b;
  int c[14];
} D_t;


int foo(D_t d, int e)
{
  d.b = 3;  // Modify value in copy of struct. This should be local only.
  return d.c[2] + e;
}



void main_main()
{
  printf("Welcome to the structs passed by value demo!\n");
  D_t d;
  d.b = 2;
  d.c[2] = 55;
  int g = 10;
  int res = foo(d, g);
  printf("Res = %d (was it 65?)\n", res);
  printf("Expecting 2 here: %d\n", (int)d.b);
}

