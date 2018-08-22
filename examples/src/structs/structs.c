
#include <stdio.h>

typedef struct D {
  int a;
  char b;
  int c[14];
} D_t;


int foo(D_t d, int e)
{
  d.b = 3;  // Modify value in copy of struct. This should be local only.
  printf("d.c[2] = %d\n", d.c[2]);
  return d.c[2] + e;
}

/* Demo of a function returning a structure */
//*
D_t initial_d(int a)
{
  D_t d;
  d.a = a;
  d.b = (char)a;
  return d;
}
//*/

void main_main()
{
  printf("Welcome to the structs passed by value demo!\n");
  int g = 10;

  {
    D_t d;
    d.b = 2;
    d.c[2] = 55;
    int res = foo(d, g);
    printf("Res = %d (was it 65?)\n", res);
    printf("Expecting 2 here: %d\n", (int)d.b);
  }

//*
  {
    D_t e = initial_d(9);
    e.c[2] = 35;
    int res = foo(e, g);
    printf("Res = %d (was it 45?)\n", res);
    printf("Expecting 9 here: %d\n", (int)e.b);
  }
//*/
}

void main()
{
  main_main();
}
