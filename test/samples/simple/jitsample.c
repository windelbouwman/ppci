
#include <stdio.h>

int x(int*a, int*b, int count)
{
  int sum;
  int i;
  sum = 0;
  for (i=0; i<count; i++)
    sum += a[i] * b[i];
  return sum;
}

void main_main()
{
  int a[3] = {1,2,3};
  struct {int foo; int b[3];} b = {1927, {5,4,9}};
  myprint("a=", a[2]);
  int count = 3;
  count = 3;
  int res;
  res = x(a, b.b, count);
  myprint("x=", res);
}
