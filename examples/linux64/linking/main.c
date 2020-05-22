
#include <stdio.h>

int barf(int);

void main()
{
    printf("Invoking other function\n");
    int res = barf(65);
    printf("Done: %i!\n", res);
}
