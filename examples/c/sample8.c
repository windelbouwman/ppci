
double (*a)(void);
double (*b)(int, float a);
double* c(void);
int B = sizeof(double (*)(int, float a));

union U;
union U u;
union U {int x;};

// error: int x, volatile *y;

struct s;
// int;
// int b:3;

struct l {
 int b:2+4, c:9;
 struct l*next;
} G, H;

struct l LL;
volatile struct l VL;

int main () {
B = sizeof( union U);
enum E { A, B2,C};
enum E e;
e = A;
e =  2;;
e =  B2;;
}
