/*
 Test some random examples regarding flow control in C.

 Notable candidates here:
 - if statement
 - for loop
 - while loop
 - do while
 - switch - case unit
*/

#include <stdio.h>

void main_main()
{
    int i, j, k;
    for (i = 0; i < 3; i++) {
        for (j = 0; j < 3; j++) {
            for (k = 0; k < 3; k++) {
                printf("i=%d j=%d k=%d\n", i, j, k);
            }
        }
    }

    long long fuu = 0x123400000000LL;

    // Check if fuu is non-zero:
    if (fuu) {
        printf("True 1\n");  // this is expected
    } else {
        printf("False 1\n");
    }

    short bar = 0x1234;

    if (bar) {
        printf("True 2\n");  // this is expected
    } else {
        printf("False 2\n");
    }

}
