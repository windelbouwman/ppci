
#include <stdio.h>

char ch = 'A';

struct stype {
    int a;
} s = {5};

typedef struct {
  int i;
  char c;
} STR;

void show(struct stype* sptr)
{
 printf("%d\n",sptr->a);
}

void f()
{
  STR s;
  s.c = 5;
  s.i = 0x12345678;
}

void main_main()
{
  show(&s);
  f();
}

