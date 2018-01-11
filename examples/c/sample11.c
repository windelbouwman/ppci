

typedef struct { int x, y, z, a, b; } foo_t;
int foo(foo_t bar)
{
  printf("%i", bar.a);
}

volatile int g;
volatile void do2(int x)
{
 g = x;
}

int add(int a, int b)
{
  volatile foo_t my;
  my.x = 1234;
  do2(my.a);
  foo(my);
  return a + b;
}
