
module main;
import io;

var int[50] G;

function void do1()
{
   var int i;
   for (i=0;i<50;i = i+1)
   {
     G[i] = i;
   }
}

function void do5()
{
   var int a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p;
   var int sum;
   a = G[0];
   b = G[1];
   c = G[2];
   d = G[3];
   e = G[4];
   f = G[5];
   g = G[6];
   h = G[7];
   i = G[8];
   j = G[9];
   k = G[10];
   l = G[11];
   sum = a + b + c + d + e + f + g + h + i + j + k + l;
   io.print2("w00t=", sum);
}

function void main()
{
   do1();
   do5();
}
