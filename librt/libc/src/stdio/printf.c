#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdarg.h>
#include <string.h>

void puts(char *s)
{
    while (*s) {
        putc(*s++);
    }
    putc('\n');
}

void putc(char c)
{   
    syscall(1, 1, (long int)&c, 1);
}

// Variadic argument function!
int printf(const char* txt, ...)
{
  va_list args;
  va_start(args, txt);
  char buffer[20];

  while (*txt != 0)
  {
    if (*txt == '%')
    {
      txt++; // Consume '%'

      // Parse width:
      while (*txt >= '0' && *txt <= '9')
      {
        txt++;
      }

      // Parse length field:
      while (*txt == 'l')
      {
        txt++;
      }

      // Parse type field:
      if (*txt == 'd')
      {
        txt++;
        int v = va_arg(args, int);
        itoa(v, buffer, 10);
        puts(buffer);
      }
      else if (*txt == 'u')  // unsigned int
      {
        txt++;
        int v = va_arg(args, int);
        itoa(v, buffer, 10);
        puts(buffer);
      }
      else if (*txt == 'x')  // hexadecimal int
      {
        txt++;
        int v = va_arg(args, int);
        itoa(v, buffer, 16);
        puts(buffer);
      }
      else if (*txt == 'c')
      {
        txt++;
        // TODO: how to grab a character from varargs?
        // during calling, it is promoted to integer!
        char c = va_arg(args, int);
        putc(c);
      }
      else if (*txt == 's')
      {
        txt++;
        char* s = va_arg(args, char*);
        puts(s);
      }
#ifdef __x86_64__
      else if (*txt == 'f')
      {
        txt++;
        double real = va_arg(args, double);
        // TODO: ugh, float formatting?
        itoa((int)real, buffer, 10);
        puts(buffer);
      }
#endif
      else
      {
        txt--;
        putc(*txt);
        txt++;
        putc(*txt);
      }
    }
    else
    {
      putc(*txt);
      txt++;
    }
  }

  va_end(args);
}

