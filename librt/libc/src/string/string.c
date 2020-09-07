#include <string.h>

// Reverse a string!
void reverse(char *str, int length)
{
  int start = 0;
  int end = length - 1;
  char tmp;
  while (start < end)
  {
    // Swap:
    tmp = str[start];
    str[start] = str[end];
    str[end] = tmp;

    start++;
    end--;
  }
}

// Integer to ascii:
char* itoa(int value, char* str, int base)
{
  int i = 0, neg = 0;

  // Handle 0 case:
  if (value == 0)
  {
    str[i++] = '0';
    str[i] = '\0';
    return str;
  }

  if (value < 0)
  {
    neg = 1;
    value = -value;
  }

  while (value != 0)
  {
    int rem = value % base;
    char c;
    if (rem < 10)
    {
      c = rem + '0';
    }
    else 
    {
      c = rem - 10 + 'a';
    }
    str[i++] = c;
    value = value / base;
  }

  // Append minus:
  if (neg)
    str[i++] = '-';

  str[i] = 0;

  reverse(str, i);

  return str;
}