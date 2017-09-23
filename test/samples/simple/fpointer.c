
#include <stdio.h>

void do1(int x)
{
  printf("do1 %d\n", x);
}

void do2(int x)
{
  printf("do2 %d\n", x);
}

void main_main()
{
  void (*f)(int x);
  f = do1;
  f(30);
  f = &do2;
  f(33);
}
