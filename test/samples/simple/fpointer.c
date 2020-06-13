
#include <stdio.h>

void do1(int x)
{
  printf("do1 %d\n", x);
}

void do2(int x)
{
  printf("do2 %d\n", x);
}

int do3(int x)
{
  printf("do3 %d</do3>\n", x);
  return x + 4;
}

int do4(int x)
{
  return x + 4;
}

void main_main()
{
  void (*f)(int x);
  f = do1;
  f(30);
  (*f)(30);
  (***f)(30);
  f = &do2;
  f(33);
  (*f)(33);
  (***f)(33);

  int (*fp[4])(int x) = {
    do3, do4, &do4, do3
  };

  int sum = 0, i;
  for (i=0; i<4;i++) {
    sum += fp[i](i);
  }

  printf("Sum = %d flops\n", sum);
}
