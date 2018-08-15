
// Demonstrates bitfields
// See also: https://en.cppreference.com/w/c/language/bit_field
//

#include <stdio.h>

struct S {
 // three-bit unsigned field,
 // allowed values are 0...7
 unsigned int b : 3;
 unsigned int c : 12;
};

int main_main(void)
{
    struct S s = {7, 42};
    printf("s.b=%d\n", (int)s.b); // output: 7
    ++s.b; // unsigned overflow
    printf("s.b=%d\n", (int)s.b); // output: 0
    printf("s.c=%d\n", (int)s.c); // output: 42
    s.c++;
    printf("s.c=%d\n", (int)s.c); // output: 43
}

