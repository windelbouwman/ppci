
module swmuldiv;

function int __div(int num, int den)
{
  var int res = 0;
  var int current = 1;

  while (den < num)
  {
    den = den << 1;
    current = current << 1;
  }

  while (current != 0)
  {
    if (num >= den)
    {
      num -= den;
      res = res | current;
    }
    den = den >> 1;
    current = current >> 1;
  }
  return res;
}

function int __mul(int a, int b)
{
  var int res = 0;
  while (b > 0)
  {
    if ((b & 1) == 1)
    {
      res += a;
    }
    a = a << 1;
    b = b >> 1;
  }
  return res;
}
