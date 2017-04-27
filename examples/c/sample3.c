
int add(int a, int b)
{
  return a + b;
}


int calculate(int x)
{
    int y, i;
  for (i=0;i<10;i++)
  {
    y = add(12, x + y);
  }
   return add(x, y);
}

