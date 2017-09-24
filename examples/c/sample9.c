
// #include <stdio.h>

void printf(char*, int);

int doit()
{
  printf("B %d\n", 0);
  return 0;
}

int main()
{
  printf("A = %i\n", sizeof(doit()));
  goto part2;

  part2: goto part2;
  switch(2) {
   case 34:
     break;
   default:
     break;
  }
}
