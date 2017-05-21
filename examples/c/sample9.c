
#include <stdio.h>

int doit()
{
  printf("B\n");
}

int main()
{
  printf("A = %i\n", sizeof(doit()));
}
