#include <stdio.h>

typedef int A[];      // array of unknow size (incomplete type)

A a1 = { 1, 2, 3, };  // initialized array of 3 ints
A a2 = { 5, 6, };     // initialized array of 2 ints
//A a3;                 // illegal: cannot determine size

int main_main() {
  printf("length of a1: %d\n", (int)(sizeof(a1) / sizeof(int)));
  printf("a1=%d,%d,%d\n",a1[0], a1[1], a1[2]);

  printf("length of a2: %d\n", (int)(sizeof(a2) / sizeof(int)));
  printf("a2=%d,%d\n",a2[0], a2[1]);
  return 0;
}
