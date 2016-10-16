
// Check large local stack frame (larger than 128 bytes)

module main;
import io;

const int buffer_size = 150;

function int heavy_stuff()
{
   var int[buffer_size] buffer;
   var int i;
   var int result;
   result = 0;
   for (i = 0; i< buffer_size; i += 1)
   {
     buffer[i] = i;
   }

   for (i = 0; i< buffer_size; i += 1)
   {
     result += buffer[i] * 3;
   }

   return result;
}

function void main()
{
   var int w;
   w = heavy_stuff();
   io.print2("w=", w);
}

