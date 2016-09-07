
module main;
import io;

function int find_first(int *a, int b, int size, int stride) {
    var int i = 0;
    var int ptr = 0;
    for ( i=0; i<size; i+=1 ) {
      if ( *(a + ptr) == b ) {
        return i;
      }
      ptr += stride;
    }

    return 0xff;
}

const int N = 10;

function void main()
{
    var int[N] a;
    a[0] = 12;
    a[1] = 7;
    a[2] = 3;
    a[3] = 5;
    a[4] = 42;
    a[5] = 8;
    a[6] = 3;
    a[7] = 5;
    a[8] = 8;
    a[9] = 1;
    io.print2("I=", find_first(&a[0], 42, N, sizeof(int)));
}
