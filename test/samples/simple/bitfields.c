
// Demonstrates bitfields
// See also: https://en.cppreference.com/w/c/language/bit_field
//

#include <stdio.h>

struct U {
 // three-bit unsigned field,
 // allowed values are 0...7
 unsigned int b : 3;
 unsigned int c : 12;
};

struct S {
 // three-bit signed field,
 // allowed values are -4...3
 int b : 3;
 int c : 4;
 int d : 2;
};

int main_main(void)
{
    struct U u = {7, 42};
    printf("u.b=%d\n", (int)u.b); // output: 7
    ++u.b; // unsigned overflow
    printf("u.b=%d\n", (int)u.b); // output: 0
    printf("u.c=%d\n", (int)u.c); // output: 42
    u.c++;
    printf("u.c=%d\n", (int)u.c); // output: 43

    struct S s = {3, 7, 1};
    printf("s.b=%d\n", (int)s.b); // output: 3
    ++s.b; // unsigned overflow
    printf("s.b=%d\n", (int)s.b); // output: -4
    printf("s.c=%d\n", (int)s.c); // output: 42
    s.c++;
    printf("s.c=%d\n", (int)s.c); // output: 43
    printf("s.d=%d\n", (int)s.d); // output: 1
    s.d++;
    printf("s.d=%d\n", (int)s.d); // output: -2
}

