module main;
import io;
import bsp;

var int a, b;
var int[10] buffer;
var float[10] b2;


function void fillbuffer()
{
  var int i;
  for (i=0;i<10;i = i+1)
  {
    buffer[i] = i;
  }
}

/*
function void printf(float v)
{
    bsp.putc(65);
}*/

function void main()
{
    a = 0;
    b = 1;
    fillbuffer();
    var int i, tmp;

    for (i=0; i<10; i = i+1) {
        io.print2("f= ", b);
        tmp = a + b + buffer[i];
        a = b;
        b = tmp;
        //b2[i] = b * 0.213;
    }

    //for (i=0;i<10;i+=1) {
    //    printf(b2[i] + 3.14);
    //}
}

