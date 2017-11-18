
#include <stdio.h>

char ch = 'A';

struct stype{
    int a;
} s = {5};

void show(struct stype* sptr)
{
 printf("%d\n",sptr->a);
}

void main_main()
{
  show(&s);
}

