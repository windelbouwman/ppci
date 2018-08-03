
#include <stdio.h>

float f_pi = 3.14159;
double d_pi = 3.14159;

float f_area(float radius)
{
  return radius * radius * f_pi;
}

double d_area(double radius)
{
  return radius * radius * d_pi;
}

void main_main()
{
  int res;
  res = (int)f_area(3);
  printf("f_area(3) = %d\n", res);
  res = (int)d_area(3);
  printf("d_area(3) = %d\n", res);
}
