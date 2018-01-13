
typedef struct D {
  int a;
  char b;
  int c[14];
} D_t;


int foo(D_t d, int e)
{
  d.b = 3;
  return d.c[2] + e;
}



void main_main()
{
  D_t d;
  d.b = 2;
  d.c[2] = 55;
  int g = 10;
  int res = foo(d, g);
//   printf("Res = %d\n", res);
}

