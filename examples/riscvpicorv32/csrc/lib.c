#include <stdio.h>
#include <stdarg.h>
// #include <stdlib.h>
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
    str[i++] = rem + '0';
    value = value / base;
  }

  // Append minus:
  if (neg)
    str[i++] = '-';

  str[i] = 0;

  reverse(str, i);

  return str;
}

// Variadic argument function!
void printfdbg(char* txt, ...)
{
  va_list args;
  va_start(args, txt);
  char buffer[20];

  while (*txt != 0)
  {
    if (*txt == '%')
    {
      txt++;
      if (*txt == 'd')
      {
        txt++;
        int v = va_arg(args, int);
        itoa(v, buffer, 10);
        printfdbg(buffer);
      }
      else
      {
        txt--;
        bsp_putc(*txt);
        txt++;
        bsp_putc(*txt);
      }
    }
    else
    {
      bsp_putc(*txt);
      txt++;
    }
  }

  va_end(args);
}

