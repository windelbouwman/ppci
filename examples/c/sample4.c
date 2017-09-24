int main() {
  int d,i,c;
  c = 2;
  d = 20 + c * 10 + (c >> 2) - 123;
  if (d < 10)
  {
    while (d < 20)
    {
      d = d + c * 4;
    }
  }

  if (d > 20)
  {
    do {
      d += c;
    } while (d < 100);
  }
  else
  {
    for (i=0;i<10;i++)
    {

    }
  }
  return d;
}
