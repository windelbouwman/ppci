
// #include <stdio.h>

static volatile unsigned int a[] = {1,2}, w[2], v;
int g = 10;

enum A;
typedef enum A* Ap;

enum A {
  x, y, z, zz = x - 12 * (sizeof(a) / 2),
};

typedef volatile int S;

enum A b;
enum A c[10];
Ap h;

int funcX() { return 0; }; int funcY(), varX;

