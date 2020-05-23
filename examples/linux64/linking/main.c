
#include <stdio.h>

int barf(int, double);

extern double a;

void main()
{
    a = 3.14;
    printf("Invoking other function\n");
    int res = barf(65, 7.0);
    printf("Done: %i! (should be 62)\n", res);
}
